import re
import torch
import numpy as np
import itertools
import inspect

from . import utils as utils
from .utils import Timer, equalize, safe_float, get_function, parse_floats, unpatch_model, clone_model, set_callback, apply_loras_from_spec
from .parser import parse_prompt_schedules, parse_cuts
from .hijack import do_hijack
from .perp_weight import perp_encode

from math import gcd

from comfy import model_management
from comfy_extras.nodes_mask import FeatherMask, MaskComposite
from comfy.sdxl_clip import SDXLClipModel, SDXLRefinerClipModel, SDXLClipG
from comfy.samplers import CFGGuider

# ADV CLIP Embed code
def _grouper(n, iterable):
	it = iter(iterable)
	while True:
		chunk = list(itertools.islice(it, n))
		if not chunk:
			return
		yield chunk

def _norm_mag(w, n):
	d = w - 1
	return  1 + np.sign(d) * np.sqrt(np.abs(d)**2 / n)
	#return  np.sign(w) * np.sqrt(np.abs(w)**2 / n)

def mask_word_id(tokens, word_ids, target_id, mask_token):
		new_tokens = [[mask_token if wid == target_id else t 
					   for t, wid in zip(x,y)] for x,y in zip(tokens, word_ids)]
		mask = np.array(word_ids) == target_id
		return (new_tokens, mask)

def A1111_renorm(base_emb, weighted_emb):
	embeddings_final = (base_emb.mean() / weighted_emb.mean()) * weighted_emb
	return embeddings_final

def batched_clip_encode(tokens, length, encode_func, num_chunks):
	embs = []
	for e in _grouper(32, tokens):
		enc, pooled = encode_func(e)
		enc = enc.reshape((len(e), length, -1))
		embs.append(enc)
	embs = torch.cat(embs)
	embs = embs.reshape((len(tokens) // num_chunks, length * num_chunks, -1))
	return embs

def down_weight(tokens, weights, word_ids, base_emb, length, encode_func, m_token=266):
	w, w_inv = np.unique(weights,return_inverse=True)

	if np.sum(w < 1) == 0:
		return base_emb, tokens, base_emb[0,length-1:length,:]
	#m_token = (clip.tokenizer.end_token, 1.0) if  clip.tokenizer.pad_with_end else (0,1.0)
	#using the comma token as a masking token seems to work better than aos tokens for SD 1.x
	m_token = (m_token, 1.0)

	masked_tokens = []

	masked_current = tokens
	for i in range(len(w)):
		if w[i] >= 1:
			continue
		masked_current = mask_inds(masked_current, np.where(w_inv == i)[0], m_token)
		masked_tokens.extend(masked_current)

	embs = batched_clip_encode(masked_tokens, length, encode_func, len(tokens))
	embs = torch.cat([base_emb, embs])
	w = w[w<=1.0]
	w_mix = np.diff([0] + w.tolist())
	w_mix = torch.tensor(w_mix, dtype=embs.dtype, device=embs.device).reshape((-1,1,1))

	weighted_emb = (w_mix * embs).sum(axis=0, keepdim=True)
	return weighted_emb, masked_current, weighted_emb[0,length-1:length,:]

def from_masked(tokens, weights, word_ids, base_emb, length, encode_func, m_token=266):
	pooled_base = base_emb[0,length-1:length,:]
	wids, inds = np.unique(np.array(word_ids).reshape(-1), return_index=True)
	weight_dict = dict((id,w) 
						for id,w in zip(wids ,np.array(weights).reshape(-1)[inds]) 
						if w != 1.0)

	if len(weight_dict) == 0:
		return torch.zeros_like(base_emb), base_emb[0,length-1:length,:]

	weight_tensor = torch.tensor(weights, dtype=base_emb.dtype, device=base_emb.device)
	weight_tensor = weight_tensor.reshape(1,-1,1).expand(base_emb.shape)

	#m_token = (clip.tokenizer.end_token, 1.0) if  clip.tokenizer.pad_with_end else (0,1.0)
	#TODO: find most suitable masking token here
	m_token = (m_token, 1.0)

	ws = []
	masked_tokens = []
	masks = []

	#create prompts
	for id, w in weight_dict.items():
		masked, m = mask_word_id(tokens, word_ids, id, m_token)
		masked_tokens.extend(masked)
		
		m = torch.tensor(m, dtype=base_emb.dtype, device=base_emb.device)
		m = m.reshape(1,-1,1).expand(base_emb.shape)
		masks.append(m)

		ws.append(w)
	
	#batch process prompts
	embs = batched_clip_encode(masked_tokens, length, encode_func, len(tokens))
	masks = torch.cat(masks)
	
	embs = (base_emb.expand(embs.shape) - embs)
	pooled = embs[0,length-1:length,:]

	embs *= masks
	embs = embs.sum(axis=0, keepdim=True)

	pooled_start = pooled_base.expand(len(ws), -1)
	ws = torch.tensor(ws).reshape(-1,1).expand(pooled_start.shape)
	pooled = (pooled - pooled_start) * (ws - 1)
	pooled = pooled.mean(axis=0, keepdim=True)

	return ((weight_tensor - 1) * embs), pooled_base + pooled

def mask_inds(tokens, inds, mask_token):
	clip_len = len(tokens[0])
	inds_set = set(inds)
	new_tokens = [[mask_token if i*clip_len + j in inds_set else t 
				   for j, t in enumerate(x)] for i, x in enumerate(tokens)]
	return new_tokens

def divide_length(word_ids, weights):
	sums = dict(zip(*np.unique(word_ids, return_counts=True)))
	sums[0] = 1
	weights = [[_norm_mag(w, sums[id]) if id != 0 else 1.0
				for w, id in zip(x, y)] for x, y in zip(weights, word_ids)]
	return weights

def shift_mean_weight(word_ids, weights):
	delta = 1 - np.mean([w for x, y in zip(weights, word_ids) for  w, id in zip(x,y) if id != 0])
	weights = [[w if id == 0 else w+delta 
				for w, id in zip(x, y)] for x, y in zip(weights, word_ids)]
	return weights

def scale_to_norm(weights, word_ids, w_max):
	top = np.max(weights)
	w_max = min(top, w_max)
	weights = [[w_max if id == 0 else (w/top) * w_max
				for w, id in zip(x, y)] for x, y in zip(weights, word_ids)]
	return weights

def from_zero(weights, base_emb):
	weight_tensor = torch.tensor(weights, dtype=base_emb.dtype, device=base_emb.device)
	weight_tensor = weight_tensor.reshape(1,-1,1).expand(base_emb.shape)
	return base_emb * weight_tensor

def encode_token_weights_g(model, token_weight_pairs):
	return model.clip_g.encode_token_weights(token_weight_pairs)

def encode_token_weights_l(model, token_weight_pairs):
	l_out, _ = model.clip_l.encode_token_weights(token_weight_pairs)
	return l_out, None

def encode_token_weights(model, token_weight_pairs, encode_func):
	if model.layer_idx is not None:
		model.cond_stage_model.clip_layer(model.layer_idx)
	
	model_management.load_model_gpu(model.patcher)
	return encode_func(model.cond_stage_model, token_weight_pairs)

def prepareXL(embs_l, embs_g, pooled, clip_balance):
	l_w = 1 - max(0, clip_balance - .5) * 2
	g_w = 1 - max(0, .5 - clip_balance) * 2
	if embs_l is not None:
		return torch.cat([embs_l * l_w, embs_g * g_w], dim=-1), pooled
	else:
		return embs_g, pooled

def advanced_encode_from_tokens(tokenized, token_normalization, weight_interpretation, encode_func, m_token=266, length=77, w_max=1.0, return_pooled=False, apply_to_pooled=True):
	tokens = [[t for t,_,_ in x] for x in tokenized]
	weights = [[w for _,w,_ in x] for x in tokenized]
	word_ids = [[wid for _,_,wid in x] for x in tokenized]

	#weight normalization
	#====================

	#distribute down/up weights over word lengths
	if token_normalization.startswith("length"):
		weights = divide_length(word_ids, weights)
		
	#make mean of word tokens 1
	if token_normalization.endswith("mean"):
		weights = shift_mean_weight(word_ids, weights)        

	#weight interpretation
	#=====================
	pooled = None

	if weight_interpretation == "comfy":
		weighted_tokens = [[(t,w) for t, w in zip(x, y)] for x, y in zip(tokens, weights)]
		weighted_emb, pooled_base = encode_func(weighted_tokens)
		pooled = pooled_base
	else:
		unweighted_tokens = [[(t,1.0) for t, _,_ in x] for x in tokenized]
		base_emb, pooled_base = encode_func(unweighted_tokens)
	
	if weight_interpretation == "A1111":
		weighted_emb = from_zero(weights, base_emb)
		weighted_emb = A1111_renorm(base_emb, weighted_emb)
		pooled = pooled_base
	
	if weight_interpretation == "compel":
		pos_tokens = [[(t,w) if w >= 1.0 else (t,1.0) for t, w in zip(x, y)] for x, y in zip(tokens, weights)]
		weighted_emb, _ = encode_func(pos_tokens)
		weighted_emb, _, pooled = down_weight(pos_tokens, weights, word_ids, weighted_emb, length, encode_func)
	
	if weight_interpretation == "comfy++":
		weighted_emb, tokens_down, _ = down_weight(unweighted_tokens, weights, word_ids, base_emb, length, encode_func)
		weights = [[w if w > 1.0 else 1.0 for w in x] for x in weights]
		#unweighted_tokens = [[(t,1.0) for t, _,_ in x] for x in tokens_down]
		embs, pooled = from_masked(unweighted_tokens, weights, word_ids, base_emb, length, encode_func)
		weighted_emb += embs

	if weight_interpretation == "down_weight":
		weights = scale_to_norm(weights, word_ids, w_max)
		weighted_emb, _, pooled = down_weight(unweighted_tokens, weights, word_ids, base_emb, length, encode_func)

	if return_pooled:
		if apply_to_pooled:
			return weighted_emb, pooled
		else:
			return weighted_emb, pooled_base
	return weighted_emb, None

# # # # # # # # # #
# Prompt Control: #
# # # # # # # # # #
have_advanced_encode = True
AVAILABLE_STYLES = ["comfy", "A1111", "compel", "comfy++", "down_weight", "perp"]
AVAILABLE_NORMALIZATIONS = ["none", "mean", "length", "length+mean"]

SHUFFLE_GEN = torch.Generator(device="cpu")
def shuffle_chunk(shuffle, c):
	func, shuffle = shuffle
	shuffle_count = int(safe_float(shuffle[0], 0))
	_, separator, joiner = shuffle
	if separator == "default":
		separator = ","

	if not separator:
		separator = ","

	joiner = {
		"default": ",",
		"separator": separator,
	}.get(joiner, joiner)

	separated = c.split(separator)
	if func == "SHIFT":
		shuffle_count = shuffle_count % len(separated)
		permutation = separated[shuffle_count:] + separated[:shuffle_count]
	elif func == "SHUFFLE":
		SHUFFLE_GEN.manual_seed(shuffle_count)
		permutation = [separated[i] for i in torch.randperm(len(separated), generator=SHUFFLE_GEN)]
	else:
		# ??? should never get here
		permutation = separated

	permutation = [p for p in permutation if p.strip()]
	if permutation != separated:
		c = joiner.join(permutation)
	return c

def linear_interpolate_cond(
	start, end, from_step=0.0, to_step=1.0, step=0.1, start_at=None, end_at=None, prompt_start="N/A", prompt_end="N/A"
):
	count = min(len(start), len(end))

	all_res = []
	for idx in range(count):
		res = []
		from_cond, to_cond = equalize(start[idx][0], end[idx][0])
		from_pooled = start[idx][1].get("pooled_output")
		to_pooled = end[idx][1].get("pooled_output")
		start_at = start_at if start_at is not None else from_step
		end_at = end_at if end_at is not None else to_step
		total_steps = int(round((to_step - from_step) / step, 0))
		num_steps = int(round((end_at - from_step) / step, 0))
		start_on = int(round((start_at - from_step) / step, 0))
		start_pct = start_at
		x = 1 / (total_steps + 1)
		for s in range(start_on, num_steps):
			factor = round((s + 1) * x, 2)
			new_cond = from_cond + (to_cond - from_cond) * factor
			if from_pooled is not None and to_pooled is not None:
				from_pooled, to_pooled = equalize(from_pooled, to_pooled)
				new_pooled = from_pooled + (to_pooled - from_pooled) * factor
			elif from_pooled is not None:
				new_pooled = from_pooled

			n = [new_cond, start[idx][1].copy()]
			if new_pooled is not None:
				n[1]["pooled_output"] = new_pooled
			n[1]["start_percent"] = round(start_pct, 2)
			n[1]["end_percent"] = min(round((start_pct + step), 2), 1.0)
			start_pct += step
			start_pct = round(start_pct, 2)
			if prompt_start:
				n[1]["prompt"] = f"linear:{round(1.0 - factor, 2)} / {factor}"
			res.append(n)
		if res:
			res[-1][1]["end_percent"] = round(end_at, 2)
			all_res.extend(res)
	return all_res

def get_control_points(schedule, steps, encoder):
	assert len(steps) > 1
	new_steps = set(steps)

	for step in (s[0] for s in schedule if s[0] >= steps[0] and s[0] <= steps[-1]):
		new_steps.add(step)
	control_points = [(s, encoder(schedule.at_step(s)[1])) for s in new_steps]
	return sorted(control_points, key=lambda x: x[0])


def linear_interpolator(control_points, step, start_pct, end_pct):
	o_start, start = control_points[0]
	o_end, _ = control_points[-1]
	t_start = o_start
	conds = []
	for t_end, end in control_points[1:]:
		if t_start < start_pct:
			t_start, start = t_end, end
			continue
		if t_start >= end_pct:
			break
		cs = linear_interpolate_cond(start, end, o_start, o_end, step, start_at=t_start, end_at=end_pct)
		if cs:
			conds.extend(cs)
		else:
			break
		t_start = t_end
		start = end
	return conds

def encode_regions(clip, tokens, regions, weight_interpretation="comfy", token_normalization="none"):
	from custom_nodes.ComfyUI_Cutoff.cutoff import CLIPSetRegion, finalize_clip_regions

	clip_regions = {
		"clip": clip,
		"base_tokens": tokens,
		"regions": [],
		"targets": [],
		"weights": [],
	}

	strict_mask = 1.0
	start_from_masked = 1.0
	mask_token = ""

	for region in regions:
		region_text, target_text, w, sm, sfm, mt = region
		if w is not None:
			w = safe_float(w, 0)
		else:
			w = 1.0
		if sm is not None:
			strict_mask = safe_float(sm, 1.0)
		if sfm is not None:
			start_from_masked = safe_float(sfm, 1.0)
		if mt is not None:
			mask_token = mt
		(clip_regions,) = CLIPSetRegion.add_clip_region(None, clip_regions, region_text, target_text, w)

	(r,) = finalize_clip_regions(
		clip_regions, mask_token, strict_mask, start_from_masked, token_normalization, weight_interpretation
	)
	cond, pooled = r[0][0], r[0][1].get("pooled_output")
	return cond, pooled

def encode_prompt(clip, text, default_style="comfy", default_normalization="none"):
	style, normalization, text = get_style(text, default_style, default_normalization)
	text, regions = parse_cuts(text)
	# defaults=None means there is no argument parsing at all
	text, l_prompts = get_function(text, "CLIP_L", defaults=None)
	chunks = re.split(r"\bBREAK\b", text)
	token_chunks = []
	for c in chunks:
		c, shuffles = get_function(c.strip(), "(SHIFT|SHUFFLE)", ["0", "default", "default"], return_func_name=True)
		r = c
		for s in shuffles:
			r = shuffle_chunk(s, r)
		if r != c:
			c = r
		# Tokenizer returns padded results
		t = clip.tokenize(c, return_word_ids=len(regions) > 0 or (have_advanced_encode and style != "perp"))
		token_chunks.append(t)
	tokens = token_chunks[0]
	for c in token_chunks[1:]:
		for key in tokens:
			tokens[key].extend(c[key])

	word_count = 0
	for k in tokens:
		for ci in range(len(tokens[k])):
			for i, chunk in enumerate(tokens[k][ci]):
				if chunk[2] != 0:
					tokens[k][ci][i] = (chunk[0], chunk[1], chunk[2] + word_count)
			word_count = max(word_count, max([x for _,_,x in tokens[k][ci]]))

	# Non-SDXL has only "l"
	if "g" in tokens and l_prompts:
		text_l = " ".join(l_prompts)
		tokens["l"] = clip.tokenize(
			text_l, return_word_ids=len(regions) > 0 or (have_advanced_encode and style != "perp")
		)["l"]

	if "g" in tokens and "l" in tokens and len(tokens["l"]) != len(tokens["g"]):
		empty = clip.tokenize(text_l, return_word_ids=len(regions) > 0 or (have_advanced_encode and style != "perp"))
		while len(tokens["l"]) < len(tokens["g"]):
			tokens["l"] += empty["l"]
		while len(tokens["l"]) > len(tokens["g"]):
			tokens["g"] += empty["g"]

	if len(regions) > 0:
		return encode_regions(clip, tokens, regions, style, normalization)

	if style == "perp":
		return perp_encode(clip, tokens)

	if have_advanced_encode:
		if "g" in tokens:
			embs_l = None
			embs_g = None
			pooled = None
			if "l" in tokens:
				embs_l, _ = advanced_encode_from_tokens(
					tokens["l"],
					normalization,
					style,
					lambda x: encode_token_weights(clip, x, encode_token_weights_l),
					return_pooled=False,
				)
			if "g" in tokens:
				embs_g, pooled = advanced_encode_from_tokens(
					tokens["g"],
					normalization,
					style,
					lambda x: encode_token_weights(clip, x, encode_token_weights_g),
					return_pooled=True,
					apply_to_pooled=False,
				)
			# Hardcoded clip_balance
			return prepareXL(embs_l, embs_g, pooled, 0.5)
		return advanced_encode_from_tokens(
			tokens["l"],
			normalization,
			style,
			lambda x: clip.encode_from_tokens({"l": x}, return_pooled=True),
			return_pooled=True,
			apply_to_pooled=True,
		)
	else:
		return clip.encode_from_tokens(tokens, return_pooled=True)

def get_area(text):
	text, areas = get_function(text, "AREA", ["0 1", "0 1", "1"])
	if not areas:
		return text, None

	args = areas[0]
	x, w = parse_floats(args[0], [0.0, 1.0], split_re="\\s+")
	y, h = parse_floats(args[1], [0.0, 1.0], split_re="\\s+")
	weight = safe_float(args[2], 1.0)

	def is_pct(f):
		return f >= 0.0 and f <= 1.0

	def is_pixel(f):
		return f == 0 or f > 1

	if all(is_pct(v) for v in [h, w, y, x]):
		area = ("percentage", h, w, y, x)
	elif all(is_pixel(v) for v in [h, w, y, x]):
		area = (int(h) // 8, int(w) // 8, int(y) // 8, int(x) // 8)
	else:
		raise Exception(
			f"AREA specified with invalid size {x} {w}, {h} {y}. They must either all be percentages between 0 and 1 or positive integer pixel values excluding 1"
		)

	return text, (area, weight)

def make_mask(args, size, weight):
	x1, x2 = parse_floats(args[0], [0.0, 1.0], split_re="\\s+")
	y1, y2 = parse_floats(args[1], [0.0, 1.0], split_re="\\s+")

	def is_pct(f):
		return f >= 0.0 and f <= 1.0

	def is_pixel(f):
		return f == 0 or f > 1

	if all(is_pct(v) for v in [x1, x2, y1, y2]):
		w, h = size
		xs = int(w * x1), int(w * x2)
		ys = int(h * y1), int(h * y2)
	elif all(is_pixel(v) for v in [x1, x2, y1, y2]):
		w, h = size
		xs = int(x1), int(x2)
		ys = int(y1), int(y2)
	else:
		raise Exception(
			f"MASK specified with invalid size {x1} {x2}, {y1} {y2}. They must either all be percentages between 0 and 1 or positive integer pixel values excluding 1"
		)

	mask = torch.full((h, w), 0, dtype=torch.float32, device="cpu")
	mask[ys[0] : ys[1], xs[0] : xs[1]] = weight
	mask = mask.unsqueeze(0)
	return mask

def get_mask(text, size):
	"""Parse MASK(x1 x2, y1 y2, weight) and FEATHER(left top right bottom)"""
	# TODO: combine multiple masks
	text, masks = get_function(text, "MASK", ["0 1", "0 1", "1", "multiply"])
	text, feathers = get_function(text, "FEATHER", ["0 0 0 0"])
	text, maskw = get_function(text, "MASKW", ["1.0"])
	if not masks:
		return text, None, None

	def feather(f, mask):
		l, t, r, b, *_ = [int(x) for x in parse_floats(f[0], [0, 0, 0, 0], split_re="\\s+")]
		mask = FeatherMask().feather(mask, l, t, r, b)[0]
		return mask

	mask = None
	totalweight = 1.0
	if maskw:
		totalweight = safe_float(maskw[0][0], 1.0)
	i = 0
	for m in masks:
		weight = safe_float(m[2], 1.0)
		op = m[3]
		value = 1.0
		if len(masks) > 1:
			value = weight
		else:
			totalweight = weight
		nextmask = make_mask(m, size, value)
		if i < len(feathers):
			nextmask = feather(feathers[i], nextmask)
		i += 1
		if mask is not None:
			mask = MaskComposite().combine(mask, nextmask, 0, 0, op)[0]
		else:
			mask = nextmask

	# apply leftover FEATHER() specs to the whole
	for f in feathers[i:]:
		mask = feather(f, mask)
	return text, mask, totalweight

def get_noise(text):
	text, noises = get_function(
		text,
		"NOISE",
		["0.0", "none"],
	)
	if not noises:
		return text, None, None
	w = 0
	# Only take seed from first noise spec, for simplicity
	seed = safe_float(noises[0][1], "none")
	if seed == "none":
		gen = None
	else:
		gen = torch.Generator()
		gen.manual_seed(int(seed))
	for n in noises:
		w += safe_float(n[0], 0.0)
	return text, max(min(w, 1.0), 0.0), gen

def apply_noise(cond, weight, gen):
	if cond is None or not weight:
		return cond

	n = torch.randn(cond.size(), generator=gen).to(cond)
	return cond * (1 - weight) + n * weight

def get_sdxl(text, defaults):
	# Defaults fail to parse and get looked up from the defaults dict
	text, sdxl = get_function(text, "SDXL", ["none", "none", "none"])
	if not sdxl:
		return text, {}
	args = sdxl[0]
	d = defaults
	w, h = parse_floats(args[0], [d.get("sdxl_width", 1024), d.get("sdxl_height", 1024)], split_re="\\s+")
	tw, th = parse_floats(args[1], [d.get("sdxl_twidth", 1024), d.get("sdxl_theight", 1024)], split_re="\\s+")
	cropw, croph = parse_floats(args[2], [d.get("sdxl_cwidth", 0), d.get("sdxl_cheight", 0)], split_re="\\s+")

	opts = {
		"width": int(w),
		"height": int(h),
		"target_width": int(tw),
		"target_height": int(th),
		"crop_w": int(cropw),
		"crop_h": int(croph),
	}
	return text, opts

def get_style(text, default_style="comfy", default_normalization="none"):
	text, styles = get_function(text, "STYLE", [default_style, default_normalization])
	if not styles:
		return default_style, default_normalization, text
	style, normalization = styles[0]
	style = style.strip()
	normalization = normalization.strip()
	if style not in AVAILABLE_STYLES:
		style = default_style

	if normalization not in AVAILABLE_NORMALIZATIONS:
		normalization = default_normalization

	return style, normalization, text

def get_mask_size(text, defaults):
	text, sizes = get_function(text, "MASK_SIZE", ["512", "512"])
	if not sizes:
		return text, (defaults.get("mask_width", 512), defaults.get("mask_height", 512))
	w, h = sizes[0]
	return text, (int(w), int(h))

def do_encode(clip, text, defaults):
	# First style modifier applies to ANDed prompts too unless overridden
	style, normalization, text = get_style(text)
	text, mask_size = get_mask_size(text, defaults)

	# Don't sum ANDs if this is in prompt
	alt_method = "COMFYAND()" in text
	text = text.replace("COMFYAND()", "")

	prompts = [p.strip() for p in re.split(r"\bAND\b", text)]

	p, sdxl_opts = get_sdxl(prompts[0], defaults)
	prompts[0] = p

	def weight(t):
		opts = {}
		m = re.search(r":(-?\d\.?\d*)(![A-Za-z]+)?$", t)
		if not m:
			return (1.0, opts, t)
		w = float(m[1])
		tag = m[2]
		t = t[: m.span()[0]]
		if tag == "!noscale":
			opts["scale"] = 1

		return w, opts, t

	conds = []
	res = []
	scale = sum(abs(weight(p)[0]) for p in prompts if not ("AREA(" in p or "MASK(" in p))
	for prompt in prompts:
		prompt, mask, mask_weight = get_mask(prompt, mask_size)
		w, opts, prompt = weight(prompt)
		text, noise_w, generator = get_noise(text)
		if not w:
			continue
		prompt, area = get_area(prompt)
		prompt, local_sdxl_opts = get_sdxl(prompt, defaults)
		cond, pooled = encode_prompt(clip, prompt, style, normalization)
		cond = apply_noise(cond, noise_w, generator)
		pooled = apply_noise(pooled, noise_w, generator)

		settings = {"prompt": prompt}
		if alt_method:
			settings["strength"] = w
		settings.update(sdxl_opts)
		settings.update(local_sdxl_opts)
		if area:
			settings["area"] = area[0]
			settings["strength"] = area[1]
			settings["set_area_to_bounds"] = False
		if mask is not None:
			settings["mask"] = mask
			settings["mask_strength"] = mask_weight

		if mask is not None or area or alt_method or local_sdxl_opts:
			if pooled is not None:
				settings["pooled_output"] = pooled
			conds.append([cond, settings])
		else:
			s = opts.get("scale", scale)
			res.append((cond, pooled, w / s))

	sumconds = [r[0] * r[2] for r in res]
	pooleds = [r[1] for r in res if r[1] is not None]

	if len(res) > 0:
		opts = sdxl_opts
		if pooleds:
			opts["pooled_output"] = sum(equalize(*pooleds))
		sumcond = sum(equalize(*sumconds))
		conds.append([sumcond, opts])
	return conds

def control_to_clip_common(clip, schedules, lora_cache=None, cond_cache=None):
	orig_clip = clip.clone()
	current_loras = {}
	if lora_cache is None:
		lora_cache = {}
	start_pct = 0.0
	conds = []
	cond_cache = cond_cache if cond_cache is not None else {}

	def c_str(c):
		r = [c["prompt"]]
		loras = c["loras"]
		for k in sorted(loras.keys()):
			r.append(k)
			r.append(loras[k]["weight_clip"])
			for lbw, val in loras[k].get("lbw", {}).items():
				r.append(lbw)
				r.append(val)
		return "".join(str(i) for i in r)

	def encode(c):
		nonlocal clip
		nonlocal current_loras
		prompt = c["prompt"]
		loras = c["loras"]
		cachekey = c_str(c)
		cond = cond_cache.get(cachekey)
		if cond is None:
			if loras != current_loras:
				_, clip = utils.apply_loras_from_spec(
					loras, clip=orig_clip, cache=lora_cache, applied_loras=current_loras
				)
				current_loras = loras
			cond_cache[cachekey] = do_encode(clip, prompt, schedules.defaults)
		return cond_cache[cachekey]

	for end_pct, c in schedules:
		interpolations = [
			i
			for i in schedules.interpolations
			if (start_pct >= i[0][0] and start_pct < i[0][-1]) or (end_pct > i[0][0] and start_pct < i[0][-1])
		]
		new_start_pct = start_pct
		if interpolations:
			min_step = min(i[1] for i in interpolations)
			for i in interpolations:
				control_points, _ = i
				interpolation_end_pct = min(control_points[-1], end_pct)
				interpolation_start_pct = max(control_points[0], start_pct)

				control_points = get_control_points(schedules, control_points, encode)
				cs = linear_interpolator(control_points, min_step, interpolation_start_pct, interpolation_end_pct)
				conds.extend(cs)
				new_start_pct = max(new_start_pct, interpolation_end_pct)
		start_pct = new_start_pct

		if start_pct < end_pct:
			cond = encode(c)
			# Node functions return lists of cond
			for n in cond:
				n = [n[0], n[1].copy()]
				n[1]["start_percent"] = round(start_pct, 2)
				n[1]["end_percent"] = round(end_pct, 2)
				n[1]["prompt"] = c["prompt"]
				conds.append(n)

		start_pct = end_pct

	return conds

class ScheduleToCond:
	@classmethod
	def INPUT_TYPES(s):
		return {
			"required": {"clip": ("CLIP",), "prompt_schedule": ("PROMPT_SCHEDULE",)},
		}

	RETURN_TYPES = ("CONDITIONING",)
	CATEGORY = "promptcontrol"
	FUNCTION = "apply"

	def apply(self, clip, prompt_schedule):
		r = (control_to_clip_common(clip, prompt_schedule),)
		return r

def apply_lora_for_step(schedules, step, total_steps, state, original_model, lora_cache, patch=True):
	# zero-indexed steps, 0 = first step, but schedules are 1-indexed
	sched = schedules.at_step(step + 1, total_steps)
	lora_spec = sched[1]["loras"]

	if state["applied_loras"] != lora_spec:
		m, _ = apply_loras_from_spec(
			lora_spec,
			model=state["model"],
			orig_model=original_model,
			cache=lora_cache,
			patch=patch,
			applied_loras=state["applied_loras"],
		)
		state["model"] = m
		state["applied_loras"] = lora_spec

def schedule_lora_common(model, schedules, lora_cache=None):
	do_hijack()
	orig_model = clone_model(model)
	orig_model.model_options["pc_schedules"] = schedules

	if lora_cache is None:
		lora_cache = {}

	def sampler_cb(orig_sampler, *args, **kwargs):
		split_sampling = args[0].model_options.get("pc_split_sampling")
		state = {}
		# For custom samplers, sigmas is not a keyword argument. Do the check this way to fall back to old behaviour if other hijacks exist.
		if "sigmas" in inspect.getfullargspec(orig_sampler).args:
			steps = len(args[4])
		else:
			steps = args[2]
		start_step = kwargs.get("start_step") or 0
		# The model patcher may change if LoRAs are applied
		state["model"] = args[0]
		state["applied_loras"] = {}

		orig_cb = kwargs["callback"]

		def step_callback(*args, **kwargs):
			current_step = args[0] + start_step
			apply_lora_for_step(schedules, current_step, steps, state, orig_model, lora_cache, patch=True)
			if orig_cb:
				return orig_cb(*args, **kwargs)

		kwargs["callback"] = step_callback

		apply_lora_for_step(schedules, start_step, steps, state, orig_model, lora_cache, patch=True)

		def filter_conds(conds, t, start_t, end_t):
			r = []
			for c in conds:
				x = c[1].copy()
				start_at = round(x["start_percent"], 2)
				end_at = round(x["end_percent"], 2)
				# Take any cond that has any effect before end_t, since the percentages may not perfectly match
				if end_t > start_at and end_t <= end_at:
					del x["start_percent"]
					del x["end_percent"]
					r.append([c[0].clone(), x])
			if len(r) == 0:
				raise RuntimeError("No %s conds between (%s, %s); Try adjusting your steps", t, start_t, end_t)
			return r

		def get_steps(conds):
			for c in conds:
				yield round(c[1].get("end_percent", 0), 2)

		if split_sampling:
			actual_end_step = kwargs["last_step"] or steps
			first_step = True
			s = args[8]
			all_steps = sorted(set(int(steps * i) for i in [1.0] + list(get_steps(args[6])) + list(get_steps(args[7]))))
			for end_step in all_steps:
				if end_step <= start_step:
					continue
				start_t = round(start_step / steps, 2)
				end_t = round(end_step / steps, 2)
				new_kwargs = kwargs.copy()
				new_args = list(args)
				new_args[0] = state["model"]
				new_args[6] = filter_conds(new_args[6], "positive", start_t, end_t)
				new_args[7] = filter_conds(new_args[7], "negative", start_t, end_t)
				new_args[8] = s
				new_kwargs["start_step"] = start_step
				new_kwargs["last_step"] = end_step
				if end_step >= min(steps, actual_end_step):
					new_kwargs["force_full_denoise"] = kwargs["force_full_denoise"]
				else:
					new_kwargs["force_full_denoise"] = False

				if not first_step:
					# disable_noise apparently does nothing currently, we need to override noise in args
					new_kwargs["disable_noise"] = True
					new_args[1] = torch.zeros_like(s)

				s = orig_sampler(*new_args, **new_kwargs)
				start_step = end_step
				first_step = False
		else:
			args = list(args)
			args[0] = state["model"]
			s = orig_sampler(*args, **kwargs)

		unpatch_model(state["model"])

		return s

	set_callback(orig_model, sampler_cb)

	return orig_model

class ScheduleToModel:
	@classmethod
	def INPUT_TYPES(s):
		return {
			"required": {
				"model": ("MODEL",),
				"prompt_schedule": ("PROMPT_SCHEDULE",),
			},
		}

	RETURN_TYPES = ("MODEL",)
	CATEGORY = "promptcontrol"
	FUNCTION = "apply"

	def apply(self, model, prompt_schedule):
		return (schedule_lora_common(model, prompt_schedule),)

class PromptToSchedule:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"multiline": True}),
            },
        }

    RETURN_TYPES = ("PROMPT_SCHEDULE",)
    CATEGORY = "promptcontrol"
    FUNCTION = "parse"

    def parse(self, text, settings=None):
        schedules = parse_prompt_schedules(text)
        return (schedules,)