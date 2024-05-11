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
	# This is never shown to the user - but it's saved in config.yaml for fast retrieval
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
	"gen_size_max": 8192,
	"gen_size_step": 32,

	"gen_c_steps": 20,
	"gen_c_steps_min": 1,
	"gen_c_steps_max": 150,
	"gen_c_steps_step": 1,

	"gen_c_shift": 2.0,
	"gen_c_shift_min": 1.0,
	"gen_c_shift_max": 12.0,
	"gen_c_shift_step": 0.01,

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

	"gen_b_steps": 12,
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
	"ui_anonymous_mode": False,
	"ui_img2img_include_original": True,
}

img2img_crop_types = [
	"Resize Only",
	"Crop to Latent Size",
]

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
import base64
import math
import hashlib
from cap_util.metadata import save_image_with_meta

def load_config():
	global gui_default_settings

	# Only read the config file if it exists.
	if os.path.exists("config.yaml"):
		with open("config.yaml", "r", encoding="utf-8") as config:
			yaml_data = yaml.safe_load(config)
			# Only load it if it returns a dict
			if isinstance(yaml_data, dict):
				gui_default_settings |= yaml_data
		return True
	return False

def save_config(backup=False):
	global gui_default_settings

	# Only make a backup if the config file already exists
	# and whether the changes recommend a backup.
	if os.path.exists("config.yaml") and backup:
		with open("config.yaml", "r", encoding="utf-8") as config:
			old_default_settings = yaml.safe_load(config)
			if not os.path.exists("log/"):
				os.makedirs("log/")
			current_date = datetime.datetime.now()
			with open(f"log/config_{current_date.strftime('%Y-%m-%d')}.yaml", "w", encoding="utf-8") as backup:
				yaml.dump(old_default_settings, backup)

	# Write out the new settings
	with open("config.yaml", "w", encoding="utf-8") as config:
		yaml.dump(gui_default_settings, config)

# Generic Math Functions:
def remap(val, min_val, max_val, min_map, max_map):
	return (val-min_val)/(max_val-min_val) * (max_map-min_map) + min_map

def clamp(val, min, max):
	if val < min:
		return min
	elif val > max:
		return max
	else:
		return val

def get_image_save_path(subfolder):
	current_date = time.strftime("%Y-%m-%d")
	path = os.path.join("generations", subfolder, current_date)
	os.makedirs(path, exist_ok=True)
	counter = 0
	while True:
		filename = f"image_{counter:05}.png"
		full_path = os.path.join(path, filename)
		if os.path.exists(full_path):
			counter += 1
			continue
		else:
			return full_path

def compression_curve(x):
	return math.pow(x, 0.9)

# Handle Gradio based GUI interactions:
def dummy_gradio_function():
	pass

def set_random_seed():
	return -1

def get_websocket_address():
	global gui_default_settings
	return f"ws://{gui_default_settings['comfy_address']}:{gui_default_settings['comfy_port']}/ws?clientId={gui_default_settings['comfy_uuid']}"

def calc_compression_factor(width, height):
	min_len = min(width, height)
	max_len = max(width, height)
	# Clamp ratio to a specific length
	ratio = max_len/min_len
	ratio = clamp(ratio, 1, 2.25)
	# Remap the aspect ratio from linear to an eased curve
	r_factor = compression_curve(
		remap(ratio, 1, 2.25, 0, 1)
	)
	# Figure out if the max latent length is clamped at 32 to 60
	max_fac_len = int(clamp(
		remap(r_factor, 0, 1, 48, 60),
		32, 60
	))

	final_compression_factor = 0
	found_factor = False
	# Start from the highest compression factor as lower factors have better quality
	for compression in range(80, 31, -1):
		# Find our current latent edge
		latent_size = (max_len) // compression
		if latent_size <= max_fac_len:
			final_compression_factor = compression
			found_factor = True
		
		# Fixes extreme aspect ratios snapping to 32
		if not found_factor:
			final_compression_factor = 80
	return clamp(final_compression_factor, 32, 80)

def calc_aspect_string(x, y):
	x1 = int(x)
	y1 = int(y)
	if x1 < y1:
		lval = y1/x1
		if lval.is_integer():
			return f"1:{int(lval)}"
		else:
			return f"1:{lval:.2f}"
	else:
		lval = x1/y1
		if lval.is_integer():
			return f"{int(lval)}:1"
		else:
			return f"{lval:.2f}:1"

def swap_width_height(a, b):
	return copy.deepcopy(b), copy.deepcopy(a), calc_aspect_string(b, a)

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

def image_to_b64(image):
	bytes_buffer = io.BytesIO()
	image.save(bytes_buffer, format="png")
	return base64.b64encode(bytes_buffer.getvalue()).decode()

def create_markdown_infotext(
	pos, neg, width, height, 
	c_steps, c_seed, c_cfg, batch, 
	compression, shift, b_steps, b_seed,
	b_cfg, stage_b, stage_c, clip, use_hq
):
	gi_pos = pos.strip().replace('\\', '\\\\')
	gi_neg = neg.strip().replace('\\', '\\\\')
	infotext = f"""Prompt: **{gi_pos}**
Negative Prompt: **{gi_neg}**
Resolution: **{width}x{height}**
Compression: **{compression}**
Batch Size: **{batch}**

Base Steps: **{c_steps}**
Base Seed: **{c_seed}**
Base CFG: **{c_cfg}**
Base Shift: **{shift}**
Base Model: **{stage_c}**
CLIP Model: **{clip}**

Refiner Steps: **{b_steps}**
Refiner Seed: **{b_seed}**
Refiner CFG: **{b_cfg}**
Refiner Model: **{stage_b}**
High Quality Decoder: **{'True' if use_hq else 'False'}**
"""
	return infotext

# Easier to mechanically process down the line
def create_embed_text(
	pos, neg, width, height, 
	c_steps, c_seed, c_cfg, batch, 
	compression, shift, b_steps, b_seed,
	b_cfg, stage_b, stage_c, clip, use_hq
):
	gi_pos = pos.strip()
	gi_neg = neg.strip()
	embedtext = f"""Prompt: {gi_pos}
Negative Prompt: {gi_neg}
Resolution: {width}x{height}
Compression: {compression}
Batch Size: {batch}
Base Steps: {c_steps}
Base Seed: {c_seed}
Base CFG: {c_cfg}
Base Shift: {shift}
Base Model: {stage_c}
CLIP Model: {clip}
Refiner Steps: {b_steps}
Refiner Seed: {b_seed}
Refiner CFG: {b_cfg}
Refiner Model: {stage_b}
High Quality Decoder: {'True' if use_hq else 'False'}
"""
	return embedtext

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

def process_basic_txt2img(
		pos, neg, steps_c, seed_c, width, height, 
		cfg_c, batch, compression, shift, latent_id, 
		seed_b, cfg_b, steps_b, stage_b, 
		stage_c, clip_model, backend, use_hq_stage_a,
		save_images
):
	global gui_default_settings
	global ws

	# Modify template JSON to fit parameters.
	workflow = json.loads(workflows.get_txt2img())
	# Stage C settings:

	# Prompts
	workflow["97"]["inputs"]["text"] = pos
	workflow["98"]["inputs"]["text"]  = neg

	# Stage C KSampler
	workflow["3"]["inputs"]["steps"] = steps_c
	workflow["3"]["inputs"]["seed"]  = seed_c if seed_c > -1 else random.randint(0, 2147483647)
	workflow["3"]["inputs"]["cfg"]   = cfg_c

	# EmptyLatentImage
	workflow["34"]["inputs"]["width"]       = width
	workflow["34"]["inputs"]["height"]      = height
	workflow["34"]["inputs"]["compression"] = compression
	workflow["34"]["inputs"]["batch_size"]  = batch

	# CLIP and Stage C UNET
	workflow["74"]["inputs"]["unet_name"] = stage_c
	workflow["75"]["inputs"]["clip_name"] = clip_model
	workflow["73"]["inputs"]["shift"]     = shift
	
	# Stage B settings:
	# Stage B UNET
	workflow["77"]["inputs"]["unet_name"] = stage_b

	# Stage B KSampler
	workflow["33"]["inputs"]["seed"]  = seed_b if seed_b > -1 else random.randint(0, 2147483647)
	workflow["33"]["inputs"]["steps"] = steps_b
	workflow["33"]["inputs"]["cfg"]   = cfg_b

	# Handle getting images from a batch:
	if batch > 1 and latent_id > 0:
		# Ensure that the batch index is zero indexed
		workflow["89"]["inputs"]["batch_index"] = latent_id - 1
		workflow["89"]["inputs"]["length"] = 1
		workflow["90"]["inputs"]["batch_index"] = latent_id - 1
		workflow["90"]["inputs"]["length"] = 1
	else:
		workflow["89"]["inputs"]["batch_index"] = 0
		workflow["89"]["inputs"]["length"]      = batch
		workflow["90"]["inputs"]["batch_index"] = 0
		workflow["90"]["inputs"]["length"]      = batch

	if use_hq_stage_a:
		workflow["47"]["inputs"]["vae_name"] = os.path.join("cascade", "stage_a_ft_hq.safetensors")
	else:
		workflow["47"]["inputs"]["vae_name"] = os.path.join("cascade", "stage_a.safetensors")

	if backend == "ComfyUI":
		try:
			ws.ping()
		except:
			raise gr.Error("Connection to ComfyUI's API websocket lost. Try restarting the ComfyUI websocket.")

		timer_start = time.time()
		gallery_images = gen_images_websocket(ws, workflow)
		timer_finish = f"{time.time()-timer_start:.2f}"
		
		# Save images to disk if enabled
		local_paths = []
		if save_images:
			gen_emb = create_embed_text(
				pos, neg, width, height, steps_c, workflow["3"]["inputs"]["seed"],
				cfg_c, batch, compression, shift, steps_b, workflow["33"]["inputs"]["seed"], cfg_b, stage_b, stage_c, clip_model, use_hq_stage_a
			)
			for image in gallery_images:
				file_path = get_image_save_path("txt2img")
				save_image_with_meta(image[0], workflow, gen_emb, file_path)
				local_paths.append(file_path)

		gen_info = create_markdown_infotext(
			pos, neg, width, height, steps_c, workflow["3"]["inputs"]["seed"],
			cfg_c, batch, compression, shift, steps_b, workflow["33"]["inputs"]["seed"], cfg_b, stage_b, stage_c, clip_model, use_hq_stage_a
		)
		gen_info += f"\nTotal Time: **{timer_finish}s**"
		return gallery_images if not save_images else local_paths, gen_info
	else:
		raise gr.Error("CAP Feature Unavailable.")

def process_basic_img2img(
		input_image, copy_orig, crop_type, pos, neg, 
		steps_c, seed_c, width, height, cfg_c, 
		batch, compression, shift, latent_id, 
		seed_b, cfg_b, steps_b, 
		stage_b, stage_c, clip_model, backend,
		denoise, use_hq_stage_a, save_images
):
	workflow = json.loads(workflows.get_basic_img2img())

	# Temporary override until a 64x compression switch is implemented:
	compression = 32

	# Stage C settings:
	# Prompts:
	workflow["101"]["inputs"]["text"] = pos
	workflow["106"]["inputs"]["text"] = neg

	# KSampler:
	workflow["3"]["inputs"]["steps"] = steps_c
	workflow["3"]["inputs"]["seed"]  = seed_c if seed_c > -1 else random.randint(0, 2147483647)
	workflow["3"]["inputs"]["cfg"]   = cfg_c
	workflow["3"]["inputs"]["denoise"] = denoise

	# Handle Image Processing chain:
	output_width = 0
	output_height = 0
	# Handle resize only:
	if crop_type == img2img_crop_types[0]:
		output_width = (width // compression) * compression
		output_height = (height // compression) * compression
		resized_image = input_image.resize((output_width, output_height), Image.Resampling.LANCZOS)
		workflow["100"]["inputs"]["base64_image"] = image_to_b64(resized_image)
	# Resize and Crop to latent pixels:
	elif crop_type == img2img_crop_types[1]:
		output_width = (width // compression) * compression
		output_height = (height // compression) * compression

		resized_image = input_image.resize((output_width, output_height), Image.Resampling.LANCZOS)
		workflow["100"]["inputs"]["base64_image"] = image_to_b64(resized_image).encode()

	# CLIP and Stage C UNET:
	workflow["74"]["inputs"]["unet_name"] = stage_c
	workflow["75"]["inputs"]["clip_name"] = clip_model
	workflow["73"]["inputs"]["shift"]     = shift

	# Stage B settings:
	# Stage B UNET
	workflow["77"]["inputs"]["unet_name"] = stage_b

	# KSampler:
	workflow["33"]["inputs"]["seed"]  = seed_b if seed_b > -1 else random.randint(0, 2147483647)
	workflow["33"]["inputs"]["steps"] = steps_b
	workflow["33"]["inputs"]["cfg"]   = cfg_b

	# Handle Encoder/Decoder models
	workflow["94"]["inputs"]["vae_name"] = os.path.join("cascade", "effnet_encoder.safetensors")
	if use_hq_stage_a:
		workflow["47"]["inputs"]["vae_name"] = os.path.join("cascade", "stage_a_ft_hq.safetensors")
	else:
		workflow["47"]["inputs"]["vae_name"] = os.path.join("cascade", "stage_a.safetensors")

	# Handle Batch size
	workflow["96"]["inputs"]["amount"] = batch + 1
	workflow["97"]["inputs"]["amount"] = batch + 1

	# Handle getting images from a batch:
	if batch > 1 and latent_id > 0:
		# Ensure that the batch index is zero indexed
		workflow["90"]["inputs"]["batch_index"] = latent_id - 1
		workflow["90"]["inputs"]["length"] = 1
		workflow["99"]["inputs"]["batch_index"] = latent_id - 1
		workflow["99"]["inputs"]["length"] = 1
	else:
		workflow["90"]["inputs"]["batch_index"] = 0
		workflow["90"]["inputs"]["length"]      = batch
		workflow["99"]["inputs"]["batch_index"] = 0
		workflow["99"]["inputs"]["length"]      = batch

	if backend == "ComfyUI":
		try:
			ws.ping()
		except:
			raise gr.Error("Connection to ComfyUI's API websocket lost. Try restarting the ComfyUI websocket.")

		timer_start = time.time()
		gallery_images = gen_images_websocket(ws, workflow)
		timer_finish = f"{time.time()-timer_start:.2f}"

		local_paths = []
		if save_images:
			gen_emb = create_embed_text(
				pos, neg, width, height, steps_c, workflow["3"]["inputs"]["seed"],
				cfg_c, batch, compression, shift, steps_b, workflow["33"]["inputs"]["seed"], cfg_b, stage_b, stage_c, clip_model, use_hq_stage_a
			)
			# Zero out the base64 encoded image for space saving reasons
			workflow["100"]["inputs"]["base64_image"] = ""
			for image in gallery_images:
				file_path = get_image_save_path("img2img")
				save_image_with_meta(image[0], workflow, gen_emb, file_path)
				local_paths.append(file_path)

		if copy_orig:
			if not save_images:
				gallery_images.append(input_image)
			else:
				local_paths.append(input_image)

		gen_info = create_markdown_infotext(
			pos, neg, width, height, steps_c, workflow["3"]["inputs"]["seed"],
			cfg_c, batch, compression, shift, steps_b, workflow["33"]["inputs"]["seed"],
			cfg_b, stage_b, stage_c, clip_model, use_hq_stage_a
		)
		gen_info += f"\nTotal Time: **{timer_finish}s**"

		return gallery_images, gen_info