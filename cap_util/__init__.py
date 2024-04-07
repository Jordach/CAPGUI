# These settings are loaded at launch and overridden by the config.yaml
ws = ""

gui_default_settings = {
	# Path settings for ComfyUI
	"comfy_address": "127.0.0.1",
	"comfy_port": "8188",
	"comfy_path": "no_path",
	"comfy_clip": "no_path",
	"comfy_stage_b": "no_path",
	"comfy_stage_c": "no_path",

	# CAP settings
	"cap_use_cap_workers": False,
	# This is never shown to the user - but saved in config.yaml
	"cap_login_token": "unauthenticated",
	"cap_login_expiry": "unauthenticated",

	# Generation Settings
	"gen_compression": 42,

	"gen_batch_size": 1,
	"gen_batch_size_min": 1,
	"gen_batch_size_max": 32,
	"gen_batch_size_step": 1,

	"gen_size": 1024,
	"gen_size_min": 256,
	"gen_size_max": 4096,
	"gen_size_step": 32,

	"gen_c_steps": 20,
	"gen_c_steps_min": 1,
	"gen_c_steps_max": 150,
	"gen_c_steps_step": 1,

	"gen_c_cfg": 4.0,
	"gen_c_cfg_min": 1.0,
	"gen_c_cfg_max": 15.0,
	"gen_c_cfg_step": 0.05,
	
	"gen_c_denoise": 1.0,
	"gen_c_denoise_min": 0.0,
	"gen_c_denoise_max": 1.0,
	"gen_c_denoise_step": 0.01,

	"gen_c_cnet_strength": 1.0,
	"gen_c_cnet_strength_min": 0.0,
	"gen_c_cnet_strength_max": 1.0,
	"gen_c_cnet_strength_step": 0.01,

	"gen_b_steps": 10,
	"gen_b_steps_min": 1,
	"gen_b_steps_max": 50,
	"gen_b_steps_step": 1,

	"gen_b_cfg": 1.5,
	"gen_b_cfg_min": 1.0,
	"gen_b_cfg_max": 3.5,
	"gen_b_cfg_step": 0.05,

	"gen_b_denoise": 1.0,
	"gen_b_denoise_min": 0.0,
	"gen_b_denoise_max": 1.0,
	"gen_b_denoise_step": 0.05,

	# UI and functionality:
	"ui_img2img_include_original": True,
}

# Imports for functions and actions
import json
import urllib
import io
from PIL import Image
import workflows
import random
import json
import urllib.request
import urllib.parse
import time
import datetime
import copy
import yaml
import os
import requests
import gradio as gr
import shutil

def load_config():
	global gui_default_settings

	# Only read the config file if it exists.
	if os.path.exists("config.yaml"):
		with open("config.yaml", "r", encoding="utf-8") as config:
			yaml_data = yaml.safe_load(config)
			# Only load it if it returns a dict
			if isinstance(yaml_data, dict):
				gui_default_settings |= yaml_data

def save_config():
	global gui_default_settings

	# Only make a backup if the config file already exists
	if os.path.exists("config.yaml"):
		with open("config.yaml", "r", encoding="utf-8") as config:
			old_default_settings = yaml.safe_load(config)

			current_date = datetime.datetime.now()
			with open(f"log/config_{current_date.strftime('%Y-%m-%d')}.yaml", "w", encoding="utf-8") as backup:
				yaml.dump(old_default_settings, backup)

	# Write out the new settings
	with open("config.yaml", "w", encoding="utf-8") as config:
		yaml.dump(gui_default_settings, config)

# Handle Gradio based GUI interactions:
def get_websocket_address():
	global gui_default_settings
	return f"ws://{gui_default_settings['comfy_address']}:{gui_default_settings['comfy_port']}/ws?clientId={gui_default_settings['comfy_uuid']}"

def swap_width_height(a, b):
	return copy.deepcopy(b), copy.deepcopy(a)

def download_single_model(path, url):
	model_data = requests.get(url, stream=True)
	with open(path, "wb") as model:
		for chunk in model_data.iter_content(chunk_size=(1024*1024)*64):
			if chunk:
				model.write(chunk)

def scan_for_comfy_models():
	global gui_default_settings
	if not os.path.exists(gui_default_settings["comfy_path"]):
		return ["RESCAN MODELS"], ["RESCAN MODELS"], ["RESCAN MODELS"]
	
	clip_folder   = os.path.join(gui_default_settings["comfy_path"], "models", "clip", "cascade")
	unet_folder_b = os.path.join(gui_default_settings["comfy_path"], "models", "unet", "cascade", "stage_b")
	unet_folder_c = os.path.join(gui_default_settings["comfy_path"], "models", "unet", "cascade", "stage_c")

	clip_models = []
	for (root, dir, models) in os.walk(clip_folder):
		for model in models:
			if os.path.splitext(model)[1].lower() == ".safetensors":
				clip_models.append(f"cascade/{model}")

	stage_b_models = []
	for (root, dir, models) in os.walk(unet_folder_b):
		for model in models:
			if os.path.splitext(model)[1].lower() == ".safetensors":
				stage_b_models.append(f"cascade/stage_b/{model}")

	stage_c_models = []
	for (root, dir, models) in os.walk(unet_folder_c):
		for model in models:
			if os.path.splitext(model)[1].lower() == ".safetensors":
				stage_c_models.append(f"cascade/stage_c/{model}")
	return clip_models, stage_b_models, stage_c_models

def install_CAPGUI_nodes():
	global gui_default_settings
	custom_nodes = os.path.join(gui_default_settings["comfy_path"], "custom_nodes", "CAPGUI_Nodes")
	if not os.path.exists(custom_nodes):
		os.makedirs(custom_nodes)
	shutil.copy(os.path.join("comfyui_files", "__init__.py"), os.path.join(custom_nodes, "__init__.py"))
	gr.Info("ComfyUI Custom Nodes were installed - please restart ComfyUI to generate locally.")

def download_cascade_models():
	global gui_default_settings
	clip_folder       = os.path.join(gui_default_settings["comfy_path"], "models", "clip",       "cascade")
	controlnet_folder = os.path.join(gui_default_settings["comfy_path"], "models", "controlnet", "cascade")
	unet_folder_b     = os.path.join(gui_default_settings["comfy_path"], "models", "unet",       "cascade", "stage_b")
	unet_folder_c     = os.path.join(gui_default_settings["comfy_path"], "models", "unet",       "cascade", "stage_c")
	vae_folder        = os.path.join(gui_default_settings["comfy_path"], "models", "vae",        "cascade")
	
	if not os.path.exists(clip_folder):
		os.makedirs(clip_folder)
	if not os.path.exists(controlnet_folder):
		os.makedirs(controlnet_folder)
	if not os.path.exists(unet_folder_b):
		os.makedirs(unet_folder_b)
	if not os.path.exists(unet_folder_c):
		os.makedirs(unet_folder_c)
	if not os.path.exists(vae_folder):
		os.makedirs(vae_folder)

	# Download CLIP models
	base_clip_path = os.path.join(clip_folder, "stable_cascade_clip.safetensors")
	clip_reso_path = os.path.join(clip_folder, "resonance_r1_eX_clip.safetensors")
	print("Downloading CLIP models.")
	if not os.path.isfile(base_clip_path):
		try:
			download_single_model(base_clip_path, "https://huggingface.co/stabilityai/stable-cascade/resolve/main/text_encoder/model.safetensors?download=true")
		except Exception as e:
			print(e)
			raise gr.Error("Failed to download stable_cascade_clip.safetensors from Hugging Face - is there a working HTTP connection?")
	gr.Info("CLIP models downloaded.")

	# Download ControlNet Models:
	print("Downloading ControlNet models.")
	base_cn_canny_path = os.path.join(controlnet_folder, "cn_canny.safetensors")
	base_cn_inpaint_path = os.path.join(controlnet_folder, "cn_inpainting.safetensors")
	base_cn_super_res_path = os.path.join(controlnet_folder, "cn_super_resolution.safetensors")
	if not os.path.isfile(base_cn_canny_path):
		try:
			download_single_model(base_cn_canny_path, "https://huggingface.co/stabilityai/stable-cascade/resolve/main/controlnet/canny.safetensors?download=true")
		except:
			raise gr.Error("Failed to download cn_canny.safetensors from Hugging Face - is there a working HTTP connection?")
	
	if not os.path.isfile(base_cn_inpaint_path):
		try:
			download_single_model(base_cn_inpaint_path, "https://huggingface.co/stabilityai/stable-cascade/resolve/main/controlnet/inpainting.safetensors?download=true")
		except:
			raise gr.Error("Failed to download cn_inpainting.safetensors from Hugging Face - is there a working HTTP connection?")
	
	if not os.path.isfile(base_cn_super_res_path):
		try:
			download_single_model(base_cn_super_res_path, "https://huggingface.co/stabilityai/stable-cascade/resolve/main/controlnet/super_resolution.safetensors?download=true")
		except:
			raise gr.Error("Failed to download cn_super_resolution.safetensors from Hugging Face - is there a working HTTP connection?")
	gr.Info("ControlNet models downloaded.")

	# Download Stage B models:
	print("Downloading Refiner/Stage B models.")
	base_stage_b_path      = os.path.join(unet_folder_b, "stage_b_bf16.safetensors")
	base_stage_b_lite_path = os.path.join(unet_folder_b, "stage_b_lite_bf16.safetensors")
	reso_stage_b_path      = os.path.join(unet_folder_b, "resonance_stage_b.safetensors")
	reso_stage_b_lite_path = os.path.join(unet_folder_b, "resonance_stage_b_lite.safetensors")
	if not os.path.isfile(base_stage_b_path):
		try:
			download_single_model(base_stage_b_path, "https://huggingface.co/stabilityai/stable-cascade/resolve/main/stage_b_bf16.safetensors?download=true")
		except:
			raise gr.Error("Failed to download .safetensors from Hugging Face - is there a working HTTP connection?")
	
	if not os.path.isfile(base_stage_b_lite_path):
		try:
			download_single_model(base_stage_b_lite_path, "https://huggingface.co/stabilityai/stable-cascade/resolve/main/stage_b_lite_bf16.safetensors?download=true")
		except:
			raise gr.Error("Failed to download .safetensors from Hugging Face - is there a working HTTP connection?")
	gr.Info("Refiner models downloaded.")

	# Download Stage C models:
	print("Downloading Base/Stage C models.")
	base_stage_c_path      = os.path.join(unet_folder_c, "stage_c_bf16.safetensors")
	base_stage_c_lite_path = os.path.join(unet_folder_c, "stage_c_lite_bf16.safetensors")
	reso_stage_c_path      = os.path.join(unet_folder_c, "resonance_r1_eX.safetensors")
	reso_stage_c_lite_path = os.path.join(unet_folder_c, "resonance_r1_eX_lite.safetensors")

	if not os.path.isfile(base_stage_c_path):
		try:
			download_single_model(base_stage_c_path, "https://huggingface.co/stabilityai/stable-cascade/resolve/main/stage_c_bf16.safetensors?download=true")
		except:
			raise gr.Error("Failed to download .safetensors from Hugging Face - is there a working HTTP connection?")
	
	if not os.path.isfile(base_stage_c_lite_path):
		try:
			download_single_model(base_stage_c_lite_path, "https://huggingface.co/stabilityai/stable-cascade/resolve/main/stage_c_lite_bf16.safetensors?download=true")
		except:
			raise gr.Error("Failed to download .safetensors from Hugging Face - is there a working HTTP connection?")
	gr.Info("Base models downloaded.")

	# Download Latent Encoder and Decoder models:
	print("Downloading Latent models.")
	base_effnet_enc_path = os.path.join(vae_folder, "effnet_encoder.safetensors")
	base_stage_a_path    = os.path.join(vae_folder, "stage_a.safetensors")
	if not os.path.isfile(base_effnet_enc_path):
		try:
			download_single_model(base_effnet_enc_path, "https://huggingface.co/stabilityai/stable-cascade/resolve/main/effnet_encoder.safetensors?download=true")
		except:
			raise gr.Error("Failed to download .safetensors from Hugging Face - is there a working HTTP connection?")
	
	if not os.path.isfile(base_stage_a_path):
		try:
			download_single_model(base_stage_a_path, "https://huggingface.co/stabilityai/stable-cascade/resolve/main/stage_a.safetensors?download=true")
		except:
			raise gr.Error("Failed to download .safetensors from Hugging Face - is there a working HTTP connection?")
	
	print("Finished downloading.")


# Handle ComfyUI generation workflow specific actions:
def queue_workflow_websocket(workflow):
	p = {"prompt": workflow, "client_id": gui_default_settings["comfy_uuid"]}
	data = json.dumps(p).encode('utf-8')
	req =  urllib.request.Request(f"http://{gui_default_settings['comfy_address']}:{gui_default_settings['comfy_port']}/prompt", data=data)
	return json.loads(urllib.request.urlopen(req).read())

def gen_images_websocket(ws, workflow):
	workflow_result = queue_workflow_websocket(workflow)
	prompt_id = workflow_result['prompt_id']
	output_images = {}
	current_node = ""
	gallery_images = []
	while True:
		out = ws.recv()
		if isinstance(out, str):
			message = json.loads(out)
			if message['type'] == 'executing':
				data = message['data']
				if data['prompt_id'] == prompt_id:
					if data['node'] is None:
						break #Execution is done
					else:
						current_node = data['node']
		else:
			if current_node == 'save_image_websocket_node':
				images_output = output_images.get(current_node, [])
				image_batch = out[8:]
				# images_output.append(image_batch)
				gallery_images.append((Image.open(io.BytesIO(image_batch)), ""))
				output_images[current_node] = images_output

	return gallery_images

def process_basic_txt2img(pos, neg, steps_c, seed_c, width, height, cfg_c, batch, compression, seed_b, cfg_b, steps_b, stage_b, stage_c, clip_model, backend):
	global gui_default_settings
	global ws

	# Modify template JSON to fit parameters.
	workflow = json.loads(workflows.get_txt2img())
	# Stage C settings:
	workflow["70"]["inputs"]["text"]        = pos #pos.replace("\\", "\\\\")
	workflow["7"]["inputs"]["text"]         = neg #neg.replace("\\", "\\\\")
	workflow["3"]["inputs"]["steps"]        = steps_c
	workflow["3"]["inputs"]["seed"]         = seed_c if seed_c > -1 else random.randint(0, 2147483647)
	workflow["34"]["inputs"]["width"]       = width
	workflow["34"]["inputs"]["height"]      = height
	workflow["34"]["inputs"]["compression"] = compression
	workflow["3"]["inputs"]["cfg"]          = cfg_c
	workflow["34"]["inputs"]["batch_size"]  = batch
	workflow["48"]["inputs"]["clip_name"]   = clip_model
	workflow["49"]["inputs"]["unet_name"]   = stage_c
	# Stage B settings:
	workflow["50"]["inputs"]["unet_name"]   = stage_b
	workflow["33"]["inputs"]["seed"]  = seed_b if seed_b > -1 else random.randint(0, 2147483647)
	workflow["33"]["inputs"]["steps"] = steps_b
	workflow["33"]["inputs"]["cfg"]   = cfg_b

	# This is for saving images so they retain their metadata
	json_workflow = json.dumps(workflow).encode('utf-8')
	
	if backend == "ComfyUI":
		ws.recv()
		if ws.connected:
			timer_start = time.time()
			gallery_images = gen_images_websocket(ws, workflow)
			timer_finish = f"{time.time()-timer_start:.2f}"
			gen_info  = f"Prompt: **{pos.strip()}**\n"
			gen_info += f"\nNegative Prompt: **{neg.strip()}**\n"
			gen_info += f"\nResolution: **{width}x{height}**\n"
			gen_info += f"\nBatch Size: **{batch}**\n"
			
			gen_info += f"\nBase Steps: **{steps_c}**\n"
			gen_info += f"\nBase Seed: **{workflow['3']['inputs']['seed']}**\n"
			gen_info += f"\nBase CFG: **{cfg_c}**\n"
			gen_info += f"\nBase Model: **{stage_c}**\n"
			gen_info += f"\nCLIP Model: **{clip_model}**\n"

			gen_info += f"\nRefiner Steps: **{steps_b}**\n"
			gen_info += f"\nRefiner Seed: **{workflow['33']['inputs']['seed']}**\n"
			gen_info += f"\nRefiner CFG: **{cfg_b}**\n"
			gen_info += f"\nRefiner Model: **{stage_b}**\n"
			# gen_info += f""
			gen_info += f"\nTotal Time: **{timer_finish}s**"
			return gallery_images, gen_info
		else:
			raise gr.Error("Connection to ComfyUI's API websocket lost. Try restarting both this GUI and ComfyUI.")
	else:
		raise gr.Error("CAP Feature Unavailable.")