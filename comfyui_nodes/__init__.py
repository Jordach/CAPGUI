import comfy
import folder_paths
import math
import torch
from PIL import Image
import numpy as np
from io import BytesIO
import base64

from .prompt_control import ScheduleToCond, ScheduleToModel, PromptToSchedule

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
}

NODE_DISPLAY_NAME_MAPPINGS = {
	"UNETLoaderCAPGUI": "CAPGUI API UNETLoader",
	"CLIPLoaderCAPGUI": "CAPGUI API CLIPLoader",
	"Base64ToImageCAPGUI": "CAPGUI API Base64 Image Decoder",
	"ScheduleToCondCAPGUI": "CAPGUI Schedule To Conditioning",
	"ScheduleToModelCAPGUI": "CAPGUI Schedule To Model",
	"PromptToScheduleCAPGUI": "CAPGUI Prompt To Schedule",
}