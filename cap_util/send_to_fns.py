import json
import random
import cap_util
import gradio as gr
from PIL import Image

# Create blank PIL image constructs
def create_empty_PIL_img(width, height, rgba=False):
	return Image.new("RGBA" if rgba else "RGB", (width, height), (0, 0, 0, 0) if rgba else (255, 255, 255))

# Create a blank img2img canvas
def create_blank_canvas(width, height):
	return {
		"background": create_empty_PIL_img(width, height, rgba=False), 
		"layers": create_empty_PIL_img(width, height, rgba=True), 
		"composite": None
	}

# Processes the send_to global inside of cap_util:
def process_params():
	if "params" in cap_util.send_to:
		# Generics
		pos = ""
		neg = ""
		width = 1024
		height = 1024
		compression = 32
		acf = True
		batch = 1
		batch_id = 0

		# Stage C
		c_steps = 20
		c_seed = -1
		c_cfg = 4
		c_rescale = 0
		c_sampler = cap_util.ksampler_samplers[0][1]
		c_schedule = cap_util.ksampler_schedules[0][1]
		shift = 2

		# Stage B
		b_steps = 12
		b_seed = -1
		b_cfg = 1.5
		b_sampler = cap_util.ksampler_samplers[0][1]
		b_schedule = cap_util.ksampler_schedules[0][1]

		image_return = None

		# If it feels like Gradio got into a loop
		# uncomment this to validate that
		# print("Something went wrong")
		params = cap_util.send_to["params"]

		if "prompt" in params:
			pos = params["prompt"]
		if "negative" in params:
			neg = params["negative"]
		if "width" in params and "height" in params:
			width = params["width"]
			height = params["height"]
		if "compression" in params:
			compression = params["compression"]
			# Turn off the ACF when using a supplied compression
			acf = False
		if "batch" in params:
			batch = params["batch"]
			batch_id = 0

		if "c_steps" in params:
			c_steps = params["c_steps"]
		if "c_seed" in params:
			c_seed = params["c_seed"]
		if "c_cfg" in params:
			c_cfg = params["c_cfg"]
		if "c_rescale" in params:
			c_rescale = params["c_rescale"]
		if "c_sampler" in params:
			c_sampler = params["c_sampler"]
		if "c_schdule" in params:
			c_schedule = params["c_schedule"]
		if "shift" in params:
			shift = params["shift"]
		
		if "b_steps" in params:
			b_steps = params["b_steps"]
		if "b_seed" in params:
			b_seed = params["b_seed"]
		if "b_cfg" in params:
			b_cfg = params["b_cfg"]
		if "b_sampler" in params:
			b_sampler = params["b_sampler"]
		if "b_schdule" in params:
			b_schedule = params["b_schedule"]
		
		return pos, neg, width, height, compression, acf, batch, batch_id, c_steps, c_seed, c_cfg, shift, b_steps, b_seed, b_cfg, c_sampler, c_schedule, b_sampler, b_schedule, c_rescale
	else:
		return gr.Textbox(), gr.Textbox(), gr.Slider(), gr.Slider(), gr.Slider(), gr.Checkbox(), gr.Slider(), gr.Slider(), gr.Slider(), gr.Number(), gr.Slider(), gr.Slider(), gr.Slider(), gr.Number(), gr.Slider(), gr.Dropdown(), gr.Dropdown(), gr.Dropdown(), gr.Dropdown(), gr.Slider()

def process_params_and_image():
	pos, neg, width, height, compression, acf, batch, batch_id, c_steps, c_seed, c_cfg, shift, b_steps, b_seed, b_cfg, c_sampler, c_schedule, b_sampler, b_schedule, c_rescale = process_params()
	image = cap_util.send_to["image"]
	return pos, neg, width, height, compression, acf, batch, batch_id, c_steps, c_seed, c_cfg, shift, b_steps, b_seed, b_cfg, c_sampler, c_schedule, b_sampler, b_schedule, c_rescale, image

def get_image_from_input(input_image, image_id=1):
	if input_image is not None:
		editor_img = {
			"background": None, 
			"layers": [], 
			"composite": None
		}

		# Detect the differences between a Gallery, Image Upload and Image Editor image
		# Plain PIL image
		if isinstance(input_image, Image.Image):
			w, h = input_image.size
			editor_img["background"] = input_image.copy()
			editor_img["layers"].append(create_empty_PIL_img(w, h, rgba=True))
			return editor_img
		# A gallery's batch of images
		elif isinstance(input_image, list):
			# Prevent idiots using an invalid ID
			img_id = min(image_id, len(input_image))-1
			img_data = input_image[img_id][0]

			# Further type check the sent data
			# Handle raw file paths
			if isinstance(img_data, str):
				tmp_img = Image.open(img_data)
				w, h = tmp_img.size
				editor_img["background"] = tmp_img.copy()
				editor_img["layers"].append(create_empty_PIL_img(w, h, rgba=True))
				return editor_img
			# Handle PIL images in a gallery object (rare but can happen in say img2img or inpainting)
			elif isinstance(img_data, Image.Image):
				w, h = img_data.size
				editor_img["background"] = img_data.copy()
				editor_img["layers"].append(create_empty_PIL_img(w, h, rgba=True))
				return editor_img
			
			# And for anything else, there's MasterCard
			return None
		return None
	return None

# This is merely to stimulate the gr.Markdown box hidden in each tab 
# so that it triggers element updates through a callback function
# defined in post hook functions.
def send_to_tab(
	target_tab, infodict, input_image=None, image_id=1, randomise_seeds=True, 
):
	t2i = gr.Textbox()
	i2i = gr.Textbox()
	inp = gr.Textbox()

	if infodict == "{}":
		gr.Info("Old CAP App PNG info found, but cannot send generation settings to the chosen tab, only the image as an input. No setting changes made.")
	
	# This is merely to make the hidden text areas trigger a callback
	if target_tab == "txt2img":
		t2i = f"{random.randint(0, 12345689)}"
	elif target_tab == "img2img":
		i2i = f"{random.randint(0, 12345689)}"
	elif target_tab == "inpaint":
		inp = f"{random.randint(0, 12345689)}"

	cap_util.send_to = {}
	if infodict != "{}":
		cap_util.send_to["params"] = json.loads(infodict)
		if randomise_seeds:
			cap_util.send_to["params"]["c_seed"] = -1
			cap_util.send_to["params"]["b_seed"] = -1

	cap_util.send_to["image"] = get_image_from_input(input_image, image_id)

	return t2i, i2i, inp