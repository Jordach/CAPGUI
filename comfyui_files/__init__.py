import comfy
import folder_paths

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

NODE_CLASS_MAPPINGS = {
	"UNETLoaderCAPGUI": UNETLoaderCAP,
	"CLIPLoaderCAPGUI": CLIPLoaderCAP,
}

NODE_DISPLAY_NAME_MAPPINGS = {
	"UNETLoaderCAPGUI": "CAPGUI API UNETLoader",
	"CLIPLoaderCAPGUI": "CAPGUI API CLIPLoader"
}