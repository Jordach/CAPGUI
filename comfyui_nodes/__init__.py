import comfy
import folder_paths
import math
import torch
from PIL import Image
import numpy as np
from io import BytesIO
import base64
import logging

from .prompt_control import ScheduleToCond, ScheduleToModel, PromptToSchedule

@torch.no_grad()
def cosine_scheduler(model_sampling, steps):
	s = model_sampling
	sigs = []
	# This stops it blowing things out at the start of sampling
	# but decays linearly to allow normal cosine sampling after a few steps
	doffset = 0.25
	dmin = 1
	dmax = 1 + doffset
	dpct = 4
	for x in range(steps):
		cos = (-0.5 * (1 + math.cos(math.pi * x / (steps - 1)))) + 1
		ind = int(cos * (len(s.sigmas) - 1))

		div = dmin if x == 0 else dmax
		if x != 0:
			div -= doffset * ((x-1) / (max((steps//dpct), 1)))
			#print((x-1) / (max((steps//dpct), 1)), max(min(div, dmax), dmin))
		sigma = s.sigmas[-(1+ind)].item() / div
		sigs += [sigma]
	sigs += [0.0]
	
	sigmas = torch.FloatTensor(sigs)
	return sigmas.to(s.sigmas.device)

# Wrapper functions for schedulers that are not directly using two function arguments
def karras_wrapper(model_sampling, steps):
	return comfy.k_diffusion.sampling.get_sigmas_karras(n=steps, sigma_min=float(model_sampling.sigma_min), sigma_max=float(model_sampling.sigma_max))

def exponential_wrapper(model_sampling, steps):
	return comfy.k_diffusion.sampling.get_sigmas_exponential(n=steps, sigma_min=float(model_sampling.sigma_min), sigma_max=float(model_sampling.sigma_max))

def sgm_wrapper(model_sampling, steps):
	return comfy.samplers.normal_scheduler(model_sampling, steps, sgm=True)

# Flexible extensible schedulers for normal KSamplers
@torch.no_grad()
def new_calculate_sigmas(model_sampling, scheduler_name, steps):
	if scheduler_name not in comfy.samplers.SCHEDULER_FUNCS:
		logging.error("error invalid scheduler {}".format(scheduler_name))
	else:
		sigmas = comfy.samplers.SCHEDULER_FUNCS[scheduler_name](model_sampling, steps)
		return sigmas

# Avoid overwriting at start-up
if getattr(comfy.samplers, "SCHEDULER_FUNCS", None) is None:
	setattr(comfy.samplers, "SCHEDULER_FUNCS", {})
	comfy.samplers.SCHEDULER_FUNCS["normal"]         = comfy.samplers.normal_scheduler
	comfy.samplers.SCHEDULER_FUNCS["karras"]         = karras_wrapper
	comfy.samplers.SCHEDULER_FUNCS["exponential"]    = exponential_wrapper
	comfy.samplers.SCHEDULER_FUNCS["sgm_uniform"]    = sgm_wrapper
	comfy.samplers.SCHEDULER_FUNCS["simple"]         = comfy.samplers.simple_scheduler
	comfy.samplers.SCHEDULER_FUNCS["ddim_uniform"]   = comfy.samplers.ddim_scheduler
	comfy.samplers.SCHEDULER_FUNCS["beta"]           = comfy.samplers.beta_scheduler

	# Patch the calculate sigmas function once
	setattr(comfy.samplers, "calculate_sigmas", new_calculate_sigmas)

# Check for cosine_cascade in SCHEDULER_NAMES
found_cosine = False
for s in comfy.samplers.SCHEDULER_NAMES:
	if s == "cosine_cascade":
		found_cosine = True
		break

if not found_cosine:
	comfy.samplers.SCHEDULER_NAMES.append("cosine_cascade")
	comfy.samplers.SCHEDULER_FUNCS["cosine_cascade"] = cosine_scheduler

class UNETLoaderCAP:
	@classmethod
	def INPUT_TYPES(s):
		return {"required": { "unet_name": ("STRING", {"multiline": False}),
							 }}
	RETURN_TYPES = ("MODEL",)
	FUNCTION = "load_unet"

	CATEGORY = "advanced/loaders"

	def load_unet(self, unet_name):
		unet_path = folder_paths.get_full_path("unet", unet_name)
		model = comfy.sd.load_unet(unet_path)
		return (model,)

class CLIPLoaderCAP:
	@classmethod
	def INPUT_TYPES(s):
		return {"required": { "clip_name": ("STRING", {"multiline": False}),
							  "type": (["stable_diffusion", "stable_cascade"], ),
							 }}
	RETURN_TYPES = ("CLIP",)
	FUNCTION = "load_clip"

	CATEGORY = "advanced/loaders"

	def load_clip(self, clip_name, type="stable_diffusion"):
		clip_type = comfy.sd.CLIPType.STABLE_DIFFUSION
		if type == "stable_cascade":
			clip_type = comfy.sd.CLIPType.STABLE_CASCADE

		clip_path = folder_paths.get_full_path("clip", clip_name)
		clip = comfy.sd.load_clip(ckpt_paths=[clip_path], embedding_directory=folder_paths.get_folder_paths("embeddings"), clip_type=clip_type)
		return (clip,)

def conv_pil_tensor(img):
	return (torch.from_numpy(np.array(img).astype(np.float32) / 255.0).unsqueeze(0),)

def conv_tensor_pil(tsr):
	return Image.fromarray(np.clip(255. * tsr.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))

class B64Decoder:
	@classmethod
	def INPUT_TYPES(s):
		return {
			"required": {"base64_image": ("STRING", {"multiline": False})}
		}
	RETURN_TYPES = ("IMAGE",)
	FUNCTION = "load_image"

	CATEGORY = "api/image"

	def load_image(self, base64_image):
		img_data = base64.b64decode(base64_image)
		pil_img = Image.open(BytesIO(img_data))
		return conv_pil_tensor(pil_img.convert("RGB"))

NODE_CLASS_MAPPINGS = {
	"UNETLoaderCAPGUI": UNETLoaderCAP,
	"CLIPLoaderCAPGUI": CLIPLoaderCAP,
	"Base64ToImageCAPGUI": B64Decoder,
	"ScheduleToCondCAPGUI": ScheduleToCond,
	"ScheduleToModelCAPGUI": ScheduleToModel,
	"PromptToScheduleCAPGUI": PromptToSchedule,
	# "StageCCondPatcher": PatchStageCEmbeddings,
}

NODE_DISPLAY_NAME_MAPPINGS = {
	"UNETLoaderCAPGUI": "CAPGUI API UNETLoader",
	"CLIPLoaderCAPGUI": "CAPGUI API CLIPLoader",
	"Base64ToImageCAPGUI": "CAPGUI API Base64 Image Decoder",
	"ScheduleToCondCAPGUI": "CAPGUI Schedule To Conditioning",
	"ScheduleToModelCAPGUI": "CAPGUI Schedule To Model",
	"PromptToScheduleCAPGUI": "CAPGUI Prompt To Schedule",
	# "StageCCondPatcher": "Patch Stage C Cond Token Extension"
}