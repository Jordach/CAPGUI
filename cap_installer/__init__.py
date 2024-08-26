import requests
import os
import shutil
import gradio as gr
import cap_util

comfy_check_messages = []
comfy_check_messages.append("Valid ComfyUI install detected.")
comfy_check_messages.append("Do not use shell expanding characters such as ~ which expands to /home/username on macOS and Linux.")
comfy_check_messages.append("The root folder for ComfyUI does not exist. Are you sure this is a ComfyUI path?")
comfy_check_messages.append("The custom_nodes folder of ComfyUI does not exist. Is this a real installation of ComfyUI?")
comfy_check_messages.append("The websocket API node doesn't exist. Is this an out of date installation of ComfyUI?")
comfy_check_messages.append("The comfy_extras folder of ComfyUI does not exist. Is this a real installation of ComfyUI?")
comfy_check_messages.append("Your ComfyUI appears to be out of date and does not support Stable Cascade. Please update it.")
comfy_check_messages.append("The models folder of ComfyUI does not exist. Is this a real installation of ComfyUI?")
comfy_check_messages.append("The main Python script of ComfyUI does not exist. Is this a real installation of ComfyUI?")

def test_comfyui_install(path):
	if "~" in path:
		return 1

	# Check for existence of ComfyUI base dir:
	if not os.path.exists(path):
		return 2

	# Check for existence of certain ComfyUI pathings:
	check_custom_nodes = os.path.join(path, "custom_nodes/")
	if not os.path.exists(check_custom_nodes):
		return 3

	check_websocket_node = os.path.join(check_custom_nodes, "websocket_image_save.py")
	if not os.path.exists(check_websocket_node):
		return 4

	check_comfy_extas = os.path.join(path, "comfy_extras/")
	if not os.path.exists(check_comfy_extas):
		return 5

	check_s_cascade = os.path.join(check_comfy_extas, "nodes_stable_cascade.py")
	if not os.path.isfile(check_s_cascade):
		return 6
	
	check_models = os.path.join(path, "models/")
	if not os.path.exists(check_models):
		return 7

	check_main_py = os.path.join(path, "main.py")
	if not os.path.isfile(check_main_py):
		return 8

	return 0

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

	"dl_start_proto": "Downloading Resonance Prototypes Delta and Epsilon.",
	"dl_done_proto": "Finished downloading Resonance Prototypes Delta and Epsilon.",

	"dl_start_reso_lite": "Downloading Resonance R1 Lite.",
	"dl_done_reso_lite": "Finished downloading Resonance R1 Lite.",

	"dl_start_reso": "Downloading Resonance R1.",
	"dl_done_reso": "Finished downloading R1.",
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
	shutil.copytree("comfyui_nodes", custom_nodes, dirs_exist_ok=True)

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

	if models_dict["reso_r1_lite"]:
		print_or_Info(use_gradio, status_messages["dl_start_reso_lite"])
		reso_r1_clip = os.path.join(clip_folder,   "resonance_r1_final_te.safetensors")
		reso_r1_lite = os.path.join(unet_folder_c, "resonance_lite_r1_e11.safetensors")

		if not os.path.isfile(reso_r1_clip):
			download_single_model(reso_r1_clip, "https://cdn.spectrometer.art/resonance_r1_final_te.safetensors", use_gradio)
		if not os.path.isfile(reso_r1_lite):
			download_single_model(reso_r1_lite, "https://cdn.spectrometer.art/resonance_lite_r1_e12.safetensors", use_gradio)

		print_or_Info(use_gradio, status_messages["dl_done_reso_lite"])
	
	if models_dict["reso_r1_huge"]:
		print_or_Info(use_gradio, status_messages["dl_start_reso"])
		reso_r1_clip = os.path.join(clip_folder,   "resonance_r1_final_te.safetensors")
		reso_r1_huge = os.path.join(unet_folder_c, "resonance_r1_e1.safetensors")

		if not os.path.isfile(reso_r1_clip):
			download_single_model(reso_r1_clip, "https://cdn.spectrometer.art/resonance_r1_final_te.safetensors", use_gradio)
		if not os.path.isfile(reso_r1_huge):
			# NOTE Not Released Yet
			pass

		print_or_Info(use_gradio, status_messages["dl_done_reso"])

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
		base_stage_a_hq_path = os.path.join(vae_folder, "stage_a_ft_hq.safetensors")
		if not os.path.isfile(base_effnet_enc_path):
			download_single_model(base_effnet_enc_path, "https://huggingface.co/stabilityai/stable-cascade/resolve/main/effnet_encoder.safetensors?download=true", use_gradio)
		
		if not os.path.isfile(base_stage_a_path):
			download_single_model(base_stage_a_path, "https://huggingface.co/stabilityai/stable-cascade/resolve/main/stage_a.safetensors?download=true", use_gradio)

		if not os.path.isfile(base_stage_a_hq_path):
			download_single_model(base_stage_a_hq_path, "https://huggingface.co/madebyollin/stage-a-ft-hq/resolve/main/stage_a_ft_hq.safetensors?download=true", use_gradio)
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