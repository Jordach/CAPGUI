# This file returns img2img specific features
import gradio as gr
import cap_util
from cap_util import gui_generics
from PIL import Image

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

def img2img_tab(global_ctx, local_ctx):
	local_ctx["stage_c_image_editor"] = gr.ImageEditor(
		None, type="pil", layers=True, image_mode="RGB", format="png", show_label=False, 
		interactive=True, elem_id="img2img_canvas", width="100%", height="auto",
	)
	gui_generics.get_prompt_row(global_ctx, local_ctx, 6)
	with gr.Row():
		with gr.Column(scale=1):
			with gr.Accordion("Image to Image Settings:"):
				with gr.Row():
					local_ctx["stage_c_image_resize"] = gr.Slider(
						minimum=0.1, maximum=10, step=0.01, value=1, label="Resize by Multiplier:", interactive=True
					)
					local_ctx["stage_c_crop_type"] = gr.Dropdown(
						cap_util.img2img_crop_types, label="Resize Type:", value=cap_util.img2img_crop_types[0]
					)
				with gr.Row():
					local_ctx["copy_to_gallery"] = gr.Checkbox(cap_util.gui_default_settings["ui_img2img_include_original"], label="Show Input Image in Gallery?")
					local_ctx["create_blank_canvas"] = gr.Button("Create Blank Canvas", variant="primary")
				local_ctx["stage_c_denoise"] = gr.Slider(
					minimum=0, maximum=1, value=0.75, step=0.01, label="Denoise Strength:"
				)
			gui_generics.get_generation_settings_column(global_ctx, local_ctx)
		with gr.Column():
			gui_generics.get_gallery_column(global_ctx, local_ctx)

def process_image_editor(
		input_image, copy_orig, crop_type, pos, neg, 
		steps_c, seed_c, width, height, cfg_c, 
		batch, compression, shift, latent_id, 
		seed_b, cfg_b, steps_b, 
		stage_b, stage_c, clip_model, backend,
		denoise, use_hq_stage_a, save_images
):
	src_image = input_image["composite"]

	images, info = cap_util.process_basic_img2img(
		src_image, copy_orig, crop_type, pos, neg, 
		steps_c, seed_c, width, height, cfg_c, 
		batch, compression, shift, latent_id, 
		seed_b, cfg_b, steps_b, 
		stage_b, stage_c, clip_model, backend,
		denoise, use_hq_stage_a, save_images)
	
	return images, info

def create_blank_canvas(width, height):
	return {
		"background": Image.new("RGB", (width, height), (255, 255, 255)), 
		"layers": [Image.new("RGBA", (width, height), (0, 0, 0, 0))], 
		"composite": None
	}

# This sets up the functions like the generate button after elements have been initialised
def img2img_tab_post_hook(global_ctx, local_ctx):
	local_ctx["stage_c_image_editor"].upload(
		handle_upload,
		inputs=[local_ctx["stage_c_image_editor"], local_ctx["stage_c_image_resize"]],
		outputs=[local_ctx["stage_c_width"], local_ctx["stage_c_height"]], show_progress=False, queue=False
	)

	local_ctx["generate"].click(
		process_image_editor,
		inputs = [
			local_ctx["stage_c_image_editor"], local_ctx["copy_to_gallery"],   local_ctx["stage_c_crop_type"],
			local_ctx["pos_prompt"],           local_ctx["neg_prompt"],        local_ctx["stage_c_steps"], local_ctx["stage_c_seed"],
			local_ctx["stage_c_width"],        local_ctx["stage_c_height"],    local_ctx["stage_c_cfg"],   local_ctx["stage_c_batch"],
			local_ctx["stage_c_compression"],  local_ctx["stage_c_shift"],     local_ctx["stage_c_single_latent"],
			local_ctx["stage_b_seed"],         local_ctx["stage_b_cfg"],       local_ctx["stage_b_steps"],
			global_ctx["topbar"]["stage_b"],   global_ctx["topbar"]["stage_c"], global_ctx["topbar"]["clip"], global_ctx["topbar"]["backend"],
			local_ctx["stage_c_denoise"],      local_ctx["use_stage_a_hq"], local_ctx["stage_c_save_images"]
		],
		outputs=[local_ctx["gallery"], local_ctx["gen_info_box"]],
		show_progress="minimal"
	)

	local_ctx["create_blank_canvas"].click(
		create_blank_canvas,
		inputs=[local_ctx["stage_c_width"], local_ctx["stage_c_height"]],
		outputs=[local_ctx["stage_c_image_editor"]]
	)