# This file is a monument to my hubris,
# but serves as a quick example to directly patching a model's forwards pass under ComfyUI

import torch
import inspect
import types

def patch_forwards(self, x, r, clip_text, clip_text_pooled, clip_img, control=None, **kwargs):
	print("using modified forwards pass")
	# Process the conditioning embeddings
	r_embed = self.gen_r_embedding(r).to(dtype=x.dtype)
	for c in self.t_conds:
		t_cond = kwargs.get(c, torch.zeros_like(r))
		r_embed = torch.cat([r_embed, self.gen_r_embedding(t_cond).to(dtype=x.dtype)], dim=1)

	print(clip_text.shape)
	print(clip_text_pooled.shape)
	print(clip_img.shape)

	clip = self.gen_c_embeddings(clip_text, clip_text_pooled, clip_img)
	print(clip.shape)

	if control is not None:
		cnet = control.get("input")
	else:
		cnet = None

	# Model Blocks
	x = self.embedding(x)
	level_outputs = self._down_encode(x, r_embed, clip, cnet)
	x = self._up_decode(level_outputs, r_embed, clip, cnet)
	return self.clf(x)

class PatchStageCEmbeddings():
	@classmethod
	def INPUT_TYPES(s):
		return {"required": {"model": ("MODEL", ),}}
	
	RETURN_TYPES = ("MODEL",)
	FUNCTION = "apply_patch"
	CATEGORY = "_for_testing"

	def apply_patch(self, model):
		model = model.clone()
		model.model._modules["diffusion_model"].forward = types.MethodType(patch_forwards, model.model._modules["diffusion_model"])
		return (model,)


