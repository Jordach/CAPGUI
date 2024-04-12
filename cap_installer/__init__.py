import requests
import os
import shutil
import gradio as gr
import cap_util

status_messages = {
	"dl_fail": "Failed to download - is there a working HTTP connection?",

	"dl_start_clip": "Downloading CLIP.",
	"dl_done_clip": "Finished downloading CLIP.",
	
	"dl_start_stage_c": "Downloading base (Stage C) model[s].",
	"dl_done_stage_c": "Finished downloading base (Stage C) model[s].",
	
	"dl_start_stage_b": "Downloading refiner (Stage B) model[s].",
	"dl_done_stage_b": "Finished downloading refiner (Stage B) model[s].",
	
	"dl_start_cnet": "Downloading ControlNet models.",
	"dl_done_cnet": "Finished downloading ControlNet models.",
	
	"dl_start_misc": "Downloading required encoders/decoders.",
	"dl_done_misc": "Finished downloading required encoders/decoders.",
}

def print_or_Info(use_gr, msg):
	if use_gr:
		gr.Info(msg)
	print(msg)

def download_single_model(path, url, ugr):
	try:
		model_data = requests.get(url, stream=True)
		with open(path, "wb") as model:
			for chunk in model_data.iter_content(chunk_size=(1024*1024)*64):
				if chunk:
					model.write(chunk)
	except Exception as e:
		print(e)
		print_or_Info(ugr, status_messages["dl_fail"])

def install_CAPGUI_nodes():
	custom_nodes = os.path.join(cap_util.gui_default_settings["comfy_path"], "custom_nodes", "CAPGUI_Nodes")
	if not os.path.exists(custom_nodes):
		os.makedirs(custom_nodes)
	shutil.copy(os.path.join("comfyui_nodes", "__init__.py"), os.path.join(custom_nodes, "__init__.py"))

def download_base_models(models_dict, use_gradio):
	clip_folder = os.path.join(cap_util.gui_default_settings["comfy_path"], "models", "clip", "cascade")
	unet_folder_c = os.path.join(cap_util.gui_default_settings["comfy_path"], "models", "unet", "cascade", "stage_c")

	if not os.path.exists(clip_folder):
		os.makedirs(clip_folder)
	if not os.path.exists(unet_folder_c):
		os.makedirs(unet_folder_c)

	if models_dict["stage_c_big"] or models_dict["stage_c_lite"]:
		# Download CLIP:
		print_or_Info(use_gradio, status_messages["dl_start_clip"])
		base_clip_path = os.path.join(clip_folder, "stable_cascade_clip.safetensors")
		if not os.path.isfile(base_clip_path):
			download_single_model(base_clip_path, "https://huggingface.co/stabilityai/stable-cascade/resolve/main/text_encoder/model.safetensors?download=true", use_gradio)
		print_or_Info(use_gradio, status_messages["dl_done_clip"])

		# Download Base models / Stage C:
		print_or_Info(use_gradio, status_messages["dl_start_stage_c"])
		if models_dict["stage_c_big"]:
			base_stage_c_path = os.path.join(unet_folder_c, "stage_c_bf16.safetensors")
			if not os.path.isfile(base_stage_c_path):
				download_single_model(base_stage_c_path, "https://huggingface.co/stabilityai/stable-cascade/resolve/main/stage_c_bf16.safetensors?download=true", use_gradio)
		if models_dict["stage_c_lite"]:
			base_stage_c_lite_path = os.path.join(unet_folder_c, "stage_c_lite_bf16.safetensors")
			if not os.path.isfile(base_stage_c_lite_path):
				download_single_model(base_stage_c_lite_path, "https://huggingface.co/stabilityai/stable-cascade/resolve/main/stage_c_lite_bf16.safetensors?download=true", use_gradio)
		print_or_Info(use_gradio, status_messages["dl_done_stage_c"])


def download_reso_models(models_dict, use_gradio):
	clip_folder = os.path.join(cap_util.gui_default_settings["comfy_path"], "models", "clip", "cascade")
	unet_folder_c = os.path.join(cap_util.gui_default_settings["comfy_path"], "models", "unet", "cascade", "stage_c")

	if not os.path.exists(clip_folder):
		os.makedirs(clip_folder)
	if not os.path.exists(unet_folder_c):
		os.makedirs(unet_folder_c)

	# TODO: Complete Reso R1 model training

def download_refiner_models(models_dict, use_gradio):
	unet_folder_b = os.path.join(cap_util.gui_default_settings["comfy_path"], "models", "unet", "cascade", "stage_b")
	if not os.path.exists(unet_folder_b):
		os.makedirs(unet_folder_b)

	# Download Stage B models:
	print_or_Info(use_gradio, status_messages["dl_start_stage_b"])
	if models_dict["stage_b_big"]:
		base_stage_b_path = os.path.join(unet_folder_b, "stage_b_bf16.safetensors")
		if not os.path.isfile(base_stage_b_path):
			download_single_model(base_stage_b_path, "https://huggingface.co/stabilityai/stable-cascade/resolve/main/stage_b_bf16.safetensors?download=true", use_gradio)
	if models_dict["stage_b_lite"]:
		base_stage_b_lite_path = os.path.join(unet_folder_b, "stage_b_lite_bf16.safetensors")
		if not os.path.isfile(base_stage_b_lite_path):
			download_single_model(base_stage_b_lite_path, "https://huggingface.co/stabilityai/stable-cascade/resolve/main/stage_b_lite_bf16.safetensors?download=true", use_gradio)
	print_or_Info(use_gradio, status_messages["dl_done_stage_b"])

def download_controlnet_models(models_dict, use_gradio):
	controlnet_folder = os.path.join(cap_util.gui_default_settings["comfy_path"], "models", "controlnet", "cascade")
	if not os.path.exists(controlnet_folder):
		os.makedirs(controlnet_folder)

	# Download ControlNet Models:
	if models_dict["controlnet"]:
		print_or_Info(use_gradio, status_messages["dl_start_cnet"])
		base_cn_canny_path = os.path.join(controlnet_folder, "cn_canny.safetensors")
		base_cn_inpaint_path = os.path.join(controlnet_folder, "cn_inpainting.safetensors")
		base_cn_super_res_path = os.path.join(controlnet_folder, "cn_super_resolution.safetensors")
		if not os.path.isfile(base_cn_canny_path):
			download_single_model(base_cn_canny_path, "https://huggingface.co/stabilityai/stable-cascade/resolve/main/controlnet/canny.safetensors?download=true", use_gradio)
		if not os.path.isfile(base_cn_inpaint_path):
			download_single_model(base_cn_inpaint_path, "https://huggingface.co/stabilityai/stable-cascade/resolve/main/controlnet/inpainting.safetensors?download=true", use_gradio)
		if not os.path.isfile(base_cn_super_res_path):
			download_single_model(base_cn_super_res_path, "https://huggingface.co/stabilityai/stable-cascade/resolve/main/controlnet/super_resolution.safetensors?download=true", use_gradio)
		print_or_Info(use_gradio, status_messages["dl_done_cnet"])

def download_misc_models(models_dict, use_gradio):
	vae_folder = os.path.join(cap_util.gui_default_settings["comfy_path"], "models", "vae", "cascade")
	if not os.path.exists(vae_folder):
		os.makedirs(vae_folder)

	if models_dict["misc"]:
		print_or_Info(use_gradio, status_messages["dl_start_misc"])
		base_effnet_enc_path = os.path.join(vae_folder, "effnet_encoder.safetensors")
		base_stage_a_path    = os.path.join(vae_folder, "stage_a.safetensors")
		if not os.path.isfile(base_effnet_enc_path):
			download_single_model(base_effnet_enc_path, "https://huggingface.co/stabilityai/stable-cascade/resolve/main/effnet_encoder.safetensors?download=true", use_gradio)
		
		if not os.path.isfile(base_stage_a_path):
			download_single_model(base_stage_a_path, "https://huggingface.co/stabilityai/stable-cascade/resolve/main/stage_a.safetensors?download=true", use_gradio)
		print_or_Info(use_gradio, status_messages["dl_done_misc"])

def get_test_workflow():
	workflow = """
	{
		"1": {
			"inputs": {
			"image": "example.png",
			"upload": "image"
			},
			"class_type": "LoadImage",
			"_meta": {
			"title": "Load Image"
			}
		},
		"save_image_websocket_node": {
			"inputs": {
			"images": [
				"1",
				0
			]
			},
			"class_type": "SaveImageWebsocket",
			"_meta": {
			"title": "SaveImageWebsocket"
			}
		}
	}
	"""
	
	return workflow.replace("\\", "\\\\")