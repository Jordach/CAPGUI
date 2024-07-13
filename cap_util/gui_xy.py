import gradio as gr
import json
import io
from PIL import Image
import random
import json
import time
import copy
import os
import cap_util
from cap_util.metadata import save_image_with_meta
import workflows
import re
from PIL import Image, ImageDraw, ImageFont

def gui_xy(global_ctx, local_ctx):

        xy_types = ["None","stage_c", "stage_b", "clip", "Positive S/R","Negative S/R","Steps C","Steps B","Compression","CFG C","CFG B","Seed"]

        local_ctx["xy_x_type"] = gr.Dropdown(xy_types, multiselect=False, interactive=True, label="X Type", value="None")
        local_ctx["xy_x_string"] = gr.TextArea(value="", visible=False,label="X Values")
        local_ctx["xy_x_dropdown"] = gr.Dropdown(choices=[], multiselect=True, interactive=True, label="X Values", visible=False)

        local_ctx["xy_y_type"] = gr.Dropdown(xy_types, multiselect=False, interactive=True, label="Y Type", value="None")
        local_ctx["xy_y_string"] = gr.TextArea(value="", visible=False, label="Y Values")
        local_ctx["xy_y_dropdown"] = gr.Dropdown(choices=[], multiselect=True, interactive=True, label="Y Values", visible=False)			

        local_ctx["xy_x_type"].change(xy_check_visibility, inputs=local_ctx["xy_x_type"], outputs=local_ctx["xy_x_string"])
        local_ctx["xy_x_type"].change(xy_check_dropdown_visibility, inputs=local_ctx["xy_x_type"], outputs=local_ctx["xy_x_dropdown"])
        local_ctx["xy_y_type"].change(xy_check_visibility, inputs=local_ctx["xy_y_type"], outputs=local_ctx["xy_y_string"])
        local_ctx["xy_y_type"].change(xy_check_dropdown_visibility, inputs=local_ctx["xy_y_type"], outputs=local_ctx["xy_y_dropdown"])
        local_ctx["xy_x_type"].change(update_dropdown_choices, inputs=local_ctx["xy_x_type"], outputs=local_ctx["xy_x_dropdown"])
        local_ctx["xy_y_type"].change(update_dropdown_choices, inputs=local_ctx["xy_y_type"], outputs=local_ctx["xy_y_dropdown"])


def xy_check_visibility(type):
    return gr.TextArea(visible=bool(type != 'stage_c' and type != 'stage_b' and type != 'clip' and type != 'None'))

def xy_check_dropdown_visibility(type):
    return gr.Dropdown(visible=bool(type == 'stage_c' or type == 'stage_b' or type == 'clip'))

def update_dropdown_choices(type):
	match type:
		case "stage_c":
			_, _, stage_c_models = cap_util.scan_for_comfy_models()
			return gr.Dropdown(choices=stage_c_models)

		case "stage_b":
			_, stage_b_models, _ = cap_util.scan_for_comfy_models()
			return gr.Dropdown(choices=stage_b_models)
		case "clip":
			clip_models, _, _ = cap_util.scan_for_comfy_models()
			return gr.Dropdown(choices=clip_models)
		case _:
			return []
    
def process_xy_images(
		pos, neg, steps_c, seed_c, width, height, 
		cfg_c, batch, compression, shift, latent_id, 
		seed_b, cfg_b, steps_b, stage_b, 
		stage_c, clip_model, backend, use_hq_stage_a,
		save_images, xy_x_string, xy_x_dropdown, xy_x_type, xy_y_string, xy_y_dropdown, xy_y_type,
		c_sampler, c_schedule, b_sampler, b_schedule, c_rescale
):
	pos_original = pos
	neg_original = neg

	workflow_list = []

	#Split by commas, ignoring within double quotes
	def find_strings(text):
		return [str.replace("\"","").strip() for str in re.findall(r'"[^"]*"|[^,]+', text.replace("\n",","))]

	# Make sure to define xy_x_dropdown and xy_y_dropdown before using them

	x_list = (
		xy_x_dropdown if xy_x_type in ['stage_c', 'stage_b', 'clip' ] else
		find_strings(xy_x_string) if xy_x_type not in ['None', None] else
		['']
	)

	y_list = (
		xy_y_dropdown if xy_y_type in ['stage_c', 'stage_b', 'clip' ] else
		find_strings(xy_y_string) if xy_y_type not in ['None', None] else
		['']
	)


	if len(x_list) == 0 or len(y_list) == 0:
		raise ValueError("There should be at least one image created")
	
	random_seed_b = random.randint(0, 2147483647)
	random_seed_c = random.randint(0, 2147483647)

	# Loop over each X and Y element
	for y in y_list:
		for x in x_list:	
			try:
				def checkint(value):
					try:
						test = int(value)
					except:
						raise ValueError("Value should be integer")

				def checkfloat(value):
					try:
						test = float(value)
					except:
						raise ValueError("Value should be a float")

				def do_substitute(type, list, value):
					match type:
						case 'None': pass

						case 'Positive S/R': 
							if value is None or value == "":
								raise ValueError("Value should not be empty")
							nonlocal pos
							search = list[0]
							if search not in pos:
								raise ValueError(f"{search} not found in positive prompt")
							if value == "__SR_DELETE__":
								pos = pos.replace(search, "")
							else:
								pos = pos.replace(search, value)

						case 'Negative S/R': 
							if value is None or value == "":
								raise ValueError("Value should not be empty")
							nonlocal neg
							search = list[0]
							if search not in neg:
								raise ValueError(f"{search} not found in negative prompt")
							if value == "__SR_DELETE__":
								neg = neg.replace(search, "")
							else:
								neg = neg.replace(search, value)

						case 'stage_c': nonlocal stage_c; stage_c = value

						case 'stage_b': nonlocal stage_b; stage_b = value

						case 'clip': nonlocal clip_model; clip_model = value

						case 'Steps C': checkint(value); nonlocal steps_c; steps_c = int(value)

						case 'Steps B': checkint(value); nonlocal steps_b; steps_b = int(value)

						case 'CFG C': checkfloat(value); nonlocal cfg_c; cfg_c = float(value)

						case 'CFG B': checkfloat(value); nonlocal cfg_b; cfg_b = float(value)

						case 'Compression': checkint(value); nonlocal compression; compression = int(value)

						case 'Seed': 
							checkint(value)
							nonlocal seed_c
							seed_c = int(value)

							nonlocal random_seed_b
							random_seed_b = random.randint(0, 2147483647)

							if seed_c < 0:
								nonlocal random_seed_c
								random_seed_c = random.randint(0, 2147483647)

						case _: raise ValueError(f"Not implemented {xy_x_type}")

				pos = pos_original
				neg = neg_original
				do_substitute(xy_x_type, x_list, x)
				do_substitute(xy_y_type, y_list, y)

				# Modify template JSON to fit parameters.
				workflow = json.loads(workflows.get_txt2img())
				# Stage C settings:

				# Prompts
				workflow["97"]["inputs"]["text"] = pos
				workflow["98"]["inputs"]["text"]  = neg

				# Stage C KSampler
				workflow["3"]["inputs"]["steps"] = steps_c
				workflow["3"]["inputs"]["seed"]  = seed_c if seed_c > -1 else random_seed_c
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
				workflow["33"]["inputs"]["seed"]  = seed_b if seed_b > -1 else random_seed_b
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

				gen_info, gen_dict = cap_util.create_infotext_objects(
					pos, neg, width, height, steps_c, workflow["3"]["inputs"]["seed"],
					cfg_c, batch, compression, shift, steps_b, workflow["33"]["inputs"]["seed"],
					cfg_b, stage_b, stage_c, clip_model, use_hq_stage_a, "Text to Image", markdown=True
				)		

				workflow_list.append({'workflow':workflow,'gen_info':gen_info,'gen_dict':gen_dict})

			except Exception as e:		
					print(f"XY Validation Failed: {e}")
					return [],None,None

	timer_start = time.time()
	gr.Info("Generating grid images, this may take a while.")
	cells = gen_xy_images_websocket(cap_util.ws, workflow_list)
	
	# Save images to disk if enabled
	local_paths = []
	if save_images:
		gr.Info("Saving individual grid images to disk.")
		for i, cell in enumerate(cells):
			image = cell['image']
			workflow = cell['workflow']
			gen_dict = cell['gen_dict']
			file_path = cap_util.get_image_save_path("txt2img")
			save_image_with_meta(image[0], workflow, json.dumps(gen_dict), file_path)

	gr.Info("Now creating the stitched grid image, this may take a while.")
	gallery_images = [cell['image'] for cell in cells]
	gallery_images = [create_grid_image(x_list, y_list, gallery_images, width, height)]
	file_path = cap_util.get_image_save_path("txt2img_grid")
	gr.Info("Now saving grid to disk, this may take a while.")
	save_image_with_meta(gallery_images[0], workflow, json.dumps(gen_dict), file_path)
	local_paths.append(file_path)
	timer_finish = f"{time.time()-timer_start:.2f}"
	
	gen_info = cells[0]['gen_info']
	gen_dict = cells[0]['gen_dict']

	gen_info += f"\nTotal Time: **{timer_finish}s**"

	global last_generation
	last_generation = copy.deepcopy(gen_dict)
	gen_dict["batch"] = 1
	return gallery_images if not save_images else local_paths, gen_info, json.dumps(gen_dict)

def gen_xy_images_websocket(ws, workflows):

	cells = []
	prompt_ids = []

	for idx, workflow in enumerate(workflows):
		workflow_result = cap_util.queue_workflow_websocket(workflow['workflow'])
		id = workflow_result['prompt_id']
		cell = {'idx':idx, 'id':id, 'status':'In Progress', 'image':None, 'workflow':workflow['workflow'], 'gen_info':workflow['gen_info'], 'gen_dict': workflow['gen_dict']}
		cells.append(cell)
		prompt_ids.append(id)

	output_images = {}
	current_node = ""
	last_idx = -1

	while True:
		out = ws.recv()
		if isinstance(out, str):
			message = json.loads(out)
			if message['type'] == 'executing':
				data = message['data']
				if "prompt_id" in data:
					if data['prompt_id'] in prompt_ids:
						last_idx = prompt_ids.index(data['prompt_id'])
						if data['node'] is None:
							cells[last_idx]['status'] = 'Complete'
							if all(cell['status'] == 'Complete' for cell in cells):
								break #Execution is done
						else:
							current_node = data['node']
		else:
			if current_node == 'save_image_websocket_node':
				images_output = output_images.get(current_node, [])
				image_batch = out[8:]
				# images_output.append(image_batch)
				if last_idx > -1:
					cells[last_idx]['image'] = (Image.open(io.BytesIO(image_batch)), "")
					output_images[current_node] = images_output
				else:
					raise ValueError("Unknown prompt ID")	

	return cells

def create_grid_image(column_names, row_names, images, image_width, image_height):
		
		num_columns = len(column_names)
		num_rows = len(row_names)
		x_padding = 20 + 20 * max([len(c) for c in row_names])
		y_padding = 64
		grid_width = image_width * num_columns
		grid_height = image_height * num_rows
		grid_image = Image.new('RGB', (grid_width+x_padding, grid_height+y_padding), color='white')
		draw = ImageDraw.Draw(grid_image)
		font = ImageFont.load_default(36)

		for row in range(num_rows):
			for col in range(num_columns):
				x = x_padding+col * image_width
				y = y_padding+row * image_height

				image = images[row * len(column_names) + col][0]
				if image:
					grid_image.paste(image, (x, y))

				if row == 0:
					tx = x + image_width/2
					ty = y - y_padding/2
					_, _, w, h = draw.textbbox((0, 0), column_names[col], font=font)
					draw.text((tx-w/2, ty-h/2), column_names[col], font=font, fill='black')

				if col == 0:
					tx = x - x_padding/2
					ty = y + image_height/2
					_, _, w, h = draw.textbbox((0, 0), row_names[row], font=font)
					draw.text((tx-w/2, ty-h/2), row_names[row], font=font, fill='black')

		return grid_image
