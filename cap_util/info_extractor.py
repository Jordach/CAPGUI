import json
import gzip
import cap_util
from xml.dom import minidom

# borrowed from https://github.com/receyuki/stable-diffusion-prompt-reader/blob/master/sd_prompt_reader/image_data_reader.py
EASYDIFFUSION_MAPPING_A = {
	"prompt": "Prompt",
	"negative_prompt": "Negative Prompt",
	"seed": "Seed",
	"use_stable_diffusion_model": "Stable Diffusion model",
	"clip_skip": "Clip Skip",
	"use_vae_model": "VAE model",
	"sampler_name": "Sampler",
	"width": "Width",
	"height": "Height",
	"num_inference_steps": "Steps",
	"guidance_scale": "Guidance Scale",
}

EASYDIFFUSION_MAPPING_B = {
	"prompt": "prompt",
	"negative_prompt": "negative_prompt",
	"seed": "seed",
	"use_stable_diffusion_model": "use_stable_diffusion_model",
	"clip_skip": "clip_skip",
	"use_vae_model": "use_vae_model",
	"sampler_name": "sampler_name",
	"width": "width",
	"height": "height",
	"num_inference_steps": "num_inference_steps",
	"guidance_scale": "guidance_scale",
}

def handle_auto1111(params):
	if params and "\nSteps:" in params:
		# has a negative:
		if "Negative prompt:" in params:
			prompt_index = [params.index("\nNegative prompt:"), params.index("\nSteps:")]
			neg = params[prompt_index[0] + 1 + len("Negative prompt: "):prompt_index[-1]]
		else:
			prompt_index = [params.index("\nSteps:")]
			neg = ""

		pos = params[:prompt_index[0]]
		return f"STYLE(A1111) {pos}", f"STYLE(A1111) {neg}"
	elif params:
		# has a negative:
		if "Negative prompt:" in params:
			prompt_index = [params.index("\nNegative prompt:")]
			neg = params[prompt_index[0] + 1 + len("Negative prompt: "):]
		else:
			prompt_index = [len(params)]
			neg = ""
		
		pos = params[:prompt_index[0]]
		return f"STYLE(A1111) {pos}", f"STYLE(A1111) {neg}"
	else:
		return "", ""

def handle_ezdiff(params):
	data = json.loads(params)
	if data.get("prompt"):
		ed = EASYDIFFUSION_MAPPING_B
	else:
		ed = EASYDIFFUSION_MAPPING_A

	pos = data.get(ed["prompt"])
	data.pop(ed["prompt"])
	neg = data.get(ed["negative_prompt"])
	return pos, neg

def handle_invoke_modern(params):
	meta = json.loads(params.get("sd-metadata"))
	img = meta.get("image")
	prompt = img.get("prompt")
	index = [prompt.rfind("["), prompt.rfind("]")]

	# negative
	if -1 not in index:
		pos = prompt[:index[0]]
		neg = prompt[index[0] + 1:index[1]]
		return pos, neg
	else:
		return prompt, ""

def handle_invoke_legacy(params):
	dream = params.get("Dream")
	pi = dream.rfind('"')
	ni = [dream.rfind("["), dream.rfind("]")]

	# has neg
	if -1 not in ni:
		pos = dream[1:ni[0]]
		neg = dream[ni[0] + 1:ni[1]]
		return pos, neg
	else:
		pos = dream[1:pi]
		return pos, ""

def handle_novelai(params):
	pos = params.get("Description")
	comment = params.get("Comment") or {}
	comment_json = json.loads(comment)
	neg = comment_json.get("uc")
	return pos, neg

def handle_drawthings(params):
	try:
		data = minidom.parseString(params.get("XML:com.adobe.xmp"))
		data_json = json.loads(data.getElementByTagName("exif:UserComment")[0].childNodes[1].childNodes[1].childNodes[0].data)
	except:
		return "", ""
	else:
		pos = data_json.get("c")
		neg = data_json.get("uc")
		return pos, neg

def read_info_from_image_alpha(image):
	# possible_sigs = {'stealth_pnginfo', 'stealth_pngcomp', 'stealth_rgbinfo', 'stealth_rgbcomp'}
	# trying to read stealth pnginfo
	geninfo = ""
	width, height = image.size
	pixels = image.load()

	has_alpha = True if image.mode == 'RGBA' else False
	mode = None
	compressed = False
	binary_data = ''
	buffer_a = ''
	buffer_rgb = ''
	index_a = 0
	index_rgb = 0
	sig_confirmed = False
	confirming_signature = True
	reading_param_len = False
	reading_param = False
	read_end = False
	for x in range(width):
		for y in range(height):
			if has_alpha:
				r, g, b, a = pixels[x, y]
				buffer_a += str(a & 1)
				index_a += 1
			else:
				r, g, b = pixels[x, y]
			buffer_rgb += str(r & 1)
			buffer_rgb += str(g & 1)
			buffer_rgb += str(b & 1)
			index_rgb += 3
			if confirming_signature:
				if index_a == len('stealth_pnginfo') * 8:
					decoded_sig = bytearray(int(buffer_a[i:i + 8], 2) for i in
											range(0, len(buffer_a), 8)).decode('utf-8', errors='ignore')
					if decoded_sig in {'stealth_pnginfo', 'stealth_pngcomp'}:
						confirming_signature = False
						sig_confirmed = True
						reading_param_len = True
						mode = 'alpha'
						if decoded_sig == 'stealth_pngcomp':
							compressed = True
						buffer_a = ''
						index_a = 0
					else:
						read_end = True
						break
				elif index_rgb == len('stealth_pnginfo') * 8:
					decoded_sig = bytearray(int(buffer_rgb[i:i + 8], 2) for i in
											range(0, len(buffer_rgb), 8)).decode('utf-8', errors='ignore')
					if decoded_sig in {'stealth_rgbinfo', 'stealth_rgbcomp'}:
						confirming_signature = False
						sig_confirmed = True
						reading_param_len = True
						mode = 'rgb'
						if decoded_sig == 'stealth_rgbcomp':
							compressed = True
						buffer_rgb = ''
						index_rgb = 0
			elif reading_param_len:
				if mode == 'alpha':
					if index_a == 32:
						param_len = int(buffer_a, 2)
						reading_param_len = False
						reading_param = True
						buffer_a = ''
						index_a = 0
				else:
					if index_rgb == 33:
						pop = buffer_rgb[-1]
						buffer_rgb = buffer_rgb[:-1]
						param_len = int(buffer_rgb, 2)
						reading_param_len = False
						reading_param = True
						buffer_rgb = pop
						index_rgb = 1
			elif reading_param:
				if mode == 'alpha':
					if index_a == param_len:
						binary_data = buffer_a
						read_end = True
						break
				else:
					if index_rgb >= param_len:
						diff = param_len - index_rgb
						if diff < 0:
							buffer_rgb = buffer_rgb[:diff]
						binary_data = buffer_rgb
						read_end = True
						break
			else:
				# impossible
				read_end = True
				break
		if read_end:
			break
	if sig_confirmed and binary_data != '':
		# Convert binary string to UTF-8 encoded text
		byte_data = bytearray(int(binary_data[i:i + 8], 2) for i in range(0, len(binary_data), 8))
		try:
			if compressed:
				decoded_data = gzip.decompress(bytes(byte_data)).decode('utf-8')
			else:
				decoded_data = byte_data.decode('utf-8', errors='ignore')
			geninfo = decoded_data
		except:
			pass
	return geninfo

def get_image_info(i):
	prompt, negative = "", ""
	if i.format == "PNG":
		# auto1111
		if "parameters" in i.info:
			params = i.info.get("parameters")
			prompt, negative = handle_auto1111(params)

		# easy diffusion
		elif "negative_prompt" in i.info or "Negative Prompt" in i.info:
			params = str(i.info).replace("'", '"')
			prompt, negative = handle_ezdiff(params)
		# invokeai modern
		elif "sd-metadata" in i.info:
			prompt, negative = handle_invoke_modern(i.info)
		# legacy invokeai
		elif "Dream" in i.info:
			prompt, negative = handle_invoke_legacy(i.info)
		# novelai
		elif i.info.get("Software") == "NovelAI":
			prompt, negative = handle_novelai(i.info)
		# qdiffusion
		# elif ????:
		# drawthings (iPhone, iPad, macOS)
		elif "XML:com.adobe.xmp" in i.info:
			prompt, negative = handle_drawthings(i.info)

	return prompt, negative

import gradio as gr
def read_infodict_from_image(image, safe_resize):
	# Try reading parameters first from other GUIs:
	prompt, negative = get_image_info(image)
	width, height = image.size

	if prompt != "" or negative != "":
		# Only apply resizing to non CAPGUI metadata images
		if safe_resize:
			s_edge = min(width, height)
			l_edge = max(width, height)
			ratio = l_edge/s_edge

			if width == s_edge:
				width = 1024
				height = int(((1024 * ratio) // 32) * 32)
			else:
				width = int(((1024 * ratio) // 32) * 32)
				height = 1024

		infotext, infodict = cap_util.create_infotext_objects(prompt, negative, width, height, markdown=True)
		return infotext, infodict
	# Try reading stealth PNG:
	else:
		alpha_data = read_info_from_image_alpha(image)
		# Try loading the string as JSON data - on exception try loading Auto1111 style meta
		try:
			infodict = json.loads(alpha_data)
			# Handle older CAPGUI json data that predate the sampler/scheduler settings
			if "c_sampler" not in infodict:
				infodict["c_sampler"] = "euler_ancestral"
			if "c_schedule" not in infodict:
				infodict["c_schedule"] = "simple"
			if "b_sampler" not in infodict:
				infodict["b_sampler"] = "euler_ancestral"
			if "b_schedule" not in infodict:
				infodict["b_schedule"] = "simple"
			if "c_rescale" not in infodict:
				infodict["c_rescale"] = 0
			infotext = cap_util.create_infotext_from_dict(infodict, markdown=True)
			return infotext, infodict
		except Exception as e1:
			try:
				prompt, negative = handle_auto1111(alpha_data)
				if prompt != "" or negative != "":
					# Only apply resizing to non CAPGUI metadata images
					if safe_resize:
						s_edge = min(width, height)
						l_edge = max(width, height)
						ratio = l_edge/s_edge

						if width == s_edge:
							width = 1024
							height = int(((1024 * ratio) // 32) * 32)
						else:
							width = int(((1024 * ratio) // 32) * 32)
							height = 1024
					infotext, infodict = cap_util.create_infotext_objects(prompt, negative, width, height, markdown=True)
					return infotext, infodict
				# Handle older CAPGUI stealth PNG data
				else:
					infotext = alpha_data
					infodict = {}
					return infotext, infodict
			# Handle older CAPGUI stealth PNG data
			except Exception as e2:
				infotext = alpha_data
				infodict = {}
				return infotext, infodict