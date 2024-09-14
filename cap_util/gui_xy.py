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
	tab_source, pos, neg, steps_c, seed_c, width, height, 
	cfg_c, batch, compression, shift, latent_id, 
	seed_b, cfg_b, steps_b, stage_b, 
	stage_c, clip_model, backend, use_hq_stage_a,
	save_images, xy_x_string, xy_x_dropdown, xy_x_type, xy_y_string, xy_y_dropdown, xy_y_type,
	c_sampler, c_schedule, b_sampler, b_schedule, c_rescale
):
	pos_original = copy.copy(pos)
	neg_original = copy.copy(neg)

	#Split by commas, ignoring within double quotes
	def find_strings(text):
		return [str.replace("\"","").strip() for str in re.findall(r'"[^"]*"|[^,]+', text.replace("\n",","))]

	# Make sure to define xy_x_dropdown and xy_y_dropdown before using them

	x_list = (
		xy_x_dropdown if xy_x_type in ['stage_c', 'stage_b', 'clip' ] else
		find_strings(xy_x_string) if xy_x_type not in ['None', None] else
		['N/A']
	)

	y_list = (
		xy_y_dropdown if xy_y_type in ['stage_c', 'stage_b', 'clip' ] else
		find_strings(xy_y_string) if xy_y_type not in ['None', None] else
		['N/A']
	)

	if len(x_list) == 0 or len(y_list) == 0:
		raise ValueError("There should be at least one image created")
	
	random_seed_b = random.randint(0, 2147483647)
	random_seed_c = random.randint(0, 2147483647)

	timer_start = time.time()
	xy_data = []
	current_item = 1
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
						case 'N/A': pass

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

				toast_text = f"Now Generating {current_item}/{len(x_list)*len(y_list)}: [{xy_x_type}: {x}], [{xy_y_type}: {y}]"
				gr.Info(toast_text)
				tmp_img, tmp_info, tmp_dict = cap_util.process_basic_txt2img(
					tab_source, pos, neg,
					steps_c, seed_c if seed_c > -1 else random_seed_c,
					width, height, cfg_c, 1, compression,
					shift, 0, seed_b if seed_b > -1 else random_seed_c,
					cfg_b, steps_b, stage_b, stage_c, clip_model,
					backend, use_hq_stage_a, save_images, c_sampler,
					c_schedule, b_sampler, b_schedule, c_rescale,
				)

				for _ in tmp_img:
					xy_data.append({
						# Handle whether it's a file path or PIL Image
						"images": Image.open(_) if isinstance(_, str) else _,
						"gen_info": tmp_info,
						"gen_dict": tmp_dict,
						"workflow": copy.deepcopy(cap_util.xy_grid_workflow),
						"paths": _
					})
				
				current_item += 1

			except Exception as e:
				print(f"XY Validation Failed: {e}")
				return None, None, None

	local_paths = [cell['paths'] for cell in xy_data]

	gallery_images = [cell['images'] for cell in xy_data]
	gallery_images = [create_grid_image(x_list, y_list, gallery_images, width, height)]
	file_path = cap_util.get_image_save_path("txt2img_grid")
	gr.Info("Now saving grid to disk, this may take a while.")
	save_image_with_meta(gallery_images[0], xy_data[0]["workflow"], json.dumps(xy_data[0]["gen_dict"]), file_path)
	local_paths.insert(0, file_path)
	timer_finish = f"{time.time()-timer_start:.2f}"
	
	gen_info = xy_data[0]['gen_info']
	gen_dict = xy_data[0]['gen_dict']
	gen_info += f" (Per Image Average)\nGrid Total Time: **{timer_finish}s**"

	global last_generation
	last_generation = copy.deepcopy(gen_dict)
	return local_paths, gen_info, json.dumps(gen_dict)

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

			image = images[row * len(column_names) + col]
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