# This file returns inpainting specific features
import gradio as gr
import cap_util
from cap_util import gui_generics, send_to_fns
from gradio import Brush
from PIL import Image, ImageFilter
import PIL.ImageOps

def inpaint_use_selected_as_input(global_ctx, local_ctx):
	with gr.Row():
		local_ctx["use_as_input"] = gr.Button("Use as Input", min_width=130)
		local_ctx["keep_mask"] = gr.Checkbox(False, label="Keep Mask?", min_width=130)

def inpaint_tab(global_ctx, local_ctx):
	local_ctx["stage_c_image_editor"] = gr.ImageEditor(
		None, type="pil", layers=False, image_mode="RGBA", format="png", show_label=False, 
		interactive=True, elem_id="inpaint_canvas", width="100%", height="auto",
	)
	gui_generics.get_prompt_row(global_ctx, local_ctx, 5, inpaint_use_selected_as_input)
	with gr.Row():
		with gr.Column(scale=1):
			with gr.Accordion(label="Inpainting Settings:"):
				with gr.Row():
					local_ctx["stage_c_mask_blur"] = gr.Slider(value=1, label="Mask Blur Strength:", minimum=0, step=0.01, maximum=64)
					local_ctx["stage_c_mask_mode"] = gr.Dropdown(cap_util.inpaint_mask_types, label="Mask Interpretation Mode:", value=cap_util.inpaint_mask_types[0])
				with gr.Row():
					local_ctx["stage_c_image_resize"] = gr.Slider(
						minimum=0.1, maximum=10, step=0.01, value=1, label="Resize Image by Multiplier:", interactive=True
					)
					local_ctx["stage_c_crop_type"] = gr.Dropdown(
						cap_util.img2img_crop_types, label="Resize Type:", value=cap_util.img2img_crop_types[0]
					)
				with gr.Row():
					local_ctx["copy_to_gallery"] = gr.Checkbox(cap_util.gui_default_settings["ui_img2img_include_original"], label="Show Input Image in Gallery?")
					local_ctx["save_mask"] = gr.Checkbox(True, label="Save ComfyUI Inpainting Mask?")
				local_ctx["stage_c_denoise"] = gr.Slider(
					minimum=0, maximum=1, value=0.75, step=0.01, label="Maximum Denoise Strength:"
				)
			gui_generics.get_generation_settings_column(global_ctx, local_ctx)
		with gr.Column():
			gui_generics.get_gallery_column(global_ctx, local_ctx, add_send_to_text=True)

def create_mask_and_gen(
		editor_images, mask_mode, blur_radius,
		copy_orig, crop_type, 
		pos, neg, steps_c, seed_c, width, 
		height, cfg_c, batch, compression, 
		shift, latent_id, seed_b, cfg_b, steps_b, 
		stage_b, stage_c, clip_model, backend,
		denoise, use_hq_stage_a, save_images, save_mask,
		c_sampler, c_scheduler, b_sampler, b_scheduler,
		c_rescale
):
	_img = editor_images["layers"][0]
	path = cap_util.get_image_save_path("inpainting")
	img = _img.copy()
	w, h = img.size
	pixels = img.load()

	alpha_pixel = ""
	if mask_mode == cap_util.inpaint_mask_types[0]:
		alpha_pixel = (255, 255, 255, 255)
	elif mask_mode == cap_util.inpaint_mask_types[1]:
		alpha_pixel = (0, 0, 0, 255)
	for x in range(w):
		for y in range(h):
			pixel = pixels[x, y]

			# Convert alpha to white in Auto mode and black in Comfy
			# Semi transparents get converted to full opacity
			if pixel[3] == 0:
				pixels[x, y] = alpha_pixel
			else:
				pixels[x, y] = (pixel[0], pixel[1], pixel[2], 255)
	
	# Drop the alpha channel to invert the image
	img = img.convert("RGB")
	# Invert the mask in auto mode so that it matches what comfyUI expects
	if mask_mode == cap_util.inpaint_mask_types[0]:
		img = PIL.ImageOps.invert(img)
	
	# Blur the mask to make soft inpainting nicer:
	if blur_radius > 0:
		img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))

	mask_image = img.convert("L")
	input_image = editor_images["background"]

	images, gen_info, infodict = cap_util.process_basic_inpaint(
		input_image, mask_image, copy_orig, crop_type,
		pos, neg, steps_c, seed_c, width,
		height, cfg_c, batch, compression,
		shift, latent_id, seed_b, cfg_b, steps_b,
		stage_b, stage_c, clip_model, backend,
		denoise, use_hq_stage_a, save_images, save_mask,
		c_sampler, c_scheduler, b_sampler, b_scheduler,
		c_rescale
	)

	return images, gen_info, infodict

def handle_upload(img, factor):
	try:
		w, h = (int(img["background"].width * factor), int(img["background"].height * factor))
		step = cap_util.gui_default_settings["gen_size_step"]
		w = (w // step) * step
		h = (h // step) * step
		return w, h,
	except:
		gr.Error("Gradio did the funny again and decided to not load the provided image. This is a Gradio issue.")
		return 1024, 1024

def send_output_to_input(gallery, image_editor, keep_mask, image_id):
	image = send_to_fns.get_image_from_input(gallery, image_id)
	new_image = {
		"background": image["background"].copy(),
		"layers": None,
		"composite": None
	}

	if keep_mask:
		w, h = image["background"].size
		resized_mask = image_editor["layers"][0].resize((w, h), Image.Resampling.LANCZOS)
		new_image["layers"] = [resized_mask]
	else:
		w, h = image["background"].size
		new_image["layers"] = [send_to_fns.create_empty_PIL_img(w, h, rgba=True)]

	return new_image

# This sets up the functions like the generate button after elements have been initialised
def inpaint_tab_post_hook(global_ctx, local_ctx):
	local_ctx["stage_c_image_resize"].change(
		handle_upload,
		inputs=[local_ctx["stage_c_image_editor"], local_ctx["stage_c_image_resize"]],
		outputs=[local_ctx["stage_c_width"], local_ctx["stage_c_height"]], show_progress=False, queue=False
	)

	local_ctx["stage_c_image_editor"].upload(
		handle_upload,
		inputs=[local_ctx["stage_c_image_editor"], local_ctx["stage_c_image_resize"]],
		outputs=[local_ctx["stage_c_width"], local_ctx["stage_c_height"]], show_progress=False, queue=False
	)

	local_ctx["generate"].click(
		create_mask_and_gen,
		inputs = [
			local_ctx["stage_c_image_editor"], local_ctx["stage_c_mask_mode"], local_ctx["stage_c_mask_blur"],
			local_ctx["copy_to_gallery"],  local_ctx["stage_c_crop_type"],
			local_ctx["pos_prompt"],          local_ctx["neg_prompt"],        local_ctx["stage_c_steps"], local_ctx["stage_c_seed"],
			local_ctx["stage_c_width"],       local_ctx["stage_c_height"],    local_ctx["stage_c_cfg"],   local_ctx["stage_c_batch"],
			local_ctx["stage_c_compression"], local_ctx["stage_c_shift"],     local_ctx["stage_c_single_latent"],
			local_ctx["stage_b_seed"],        local_ctx["stage_b_cfg"],       local_ctx["stage_b_steps"],
			global_ctx["topbar"]["stage_b"], global_ctx["topbar"]["stage_c"], global_ctx["topbar"]["clip"], global_ctx["topbar"]["backend"],
			local_ctx["stage_c_denoise"],    local_ctx["use_stage_a_hq"], local_ctx["stage_c_save_images"], local_ctx["save_mask"],
			local_ctx["stage_c_sampler"], local_ctx["stage_c_scheduler"], local_ctx["stage_b_sampler"], local_ctx["stage_b_scheduler"],
			local_ctx["stage_c_rescale"]
		],
		outputs=[local_ctx["gallery"], local_ctx["gen_info_box"], local_ctx["gen_json"]],
		show_progress="minimal",
	)

	local_ctx["send_to_button"].click(
		send_to_fns.send_to_tab,
		inputs=[local_ctx["send_to_dropdown"], local_ctx["gen_json"], local_ctx["gallery"], local_ctx["send_to_which_image"]],
		outputs=[global_ctx["txt2img"]["send_to_target"], global_ctx["img2img"]["send_to_target"], global_ctx["inpaint"]["send_to_target"]]
	)

	local_ctx["send_to_target"].change(
		send_to_fns.process_params_and_image,
		inputs=[],
		outputs=[
			local_ctx["pos_prompt"], local_ctx["neg_prompt"], local_ctx["stage_c_width"], local_ctx["stage_c_height"],
			local_ctx["stage_c_compression"], local_ctx["stage_c_auto_compressor"], local_ctx["stage_c_batch"], local_ctx["stage_c_single_latent"],
			local_ctx["stage_c_steps"], local_ctx["stage_c_seed"], local_ctx["stage_c_cfg"], local_ctx["stage_c_shift"],
			local_ctx["stage_b_steps"], local_ctx["stage_b_seed"], local_ctx["stage_b_cfg"],
			local_ctx["stage_c_sampler"], local_ctx["stage_c_scheduler"], local_ctx["stage_b_sampler"], local_ctx["stage_b_scheduler"],
			local_ctx["stage_c_rescale"],
			local_ctx["stage_c_image_editor"],
		], show_progress="minimal", trigger_mode="once", queue=False,
	)

	local_ctx["use_as_input"].click(
		send_output_to_input,
		inputs=[local_ctx["gallery"], local_ctx["stage_c_image_editor"], local_ctx["keep_mask"], local_ctx["send_to_which_image"]],
		outputs=[local_ctx["stage_c_image_editor"]]
	)