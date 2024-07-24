# This file returns tools specific features

import gradio as gr
import cap_util
from cap_util import info_extractor, gui_generics, send_to_fns
from PIL import Image
import json

def tools_tab(global_ctx, local_ctx):
	with gr.Accordion("Image Meta Reader:"):
		with gr.Row():
			with gr.Column():
				local_ctx["image_reader"] = gr.File(None, file_count="single", file_types=["image"], type="filepath", show_label=False, height="300px")
				local_ctx["image_viewer"] = gr.Image(None, show_download_button=False, container=True, interactive=False, image_mode="RGBA", type="pil", show_label=False, height="auto", elem_id=f"{local_ctx['__tab_name__']}_image")
			with gr.Column():
				with gr.Accordion(label="Generation Info:"):
					local_ctx["image_infotext"] = gr.Markdown("", line_breaks=True, label="Generation Info:")
					with gr.Row():
						with gr.Column():
							local_ctx["send_to_dropdown"] = gui_generics.get_send_to_dropdown(global_ctx)
						with gr.Column():
							local_ctx["send_to_randomise_seed"] = gr.Checkbox(False, label="Randomise Seeds?")
					local_ctx["send_to_button"] = gui_generics.get_send_to_button()
					local_ctx["image_json"] = gr.Markdown("", visible=False, label="Generation JSON:")

	with gr.Accordion("Wildcard Creator:"):
		gr.Markdown("todo - helps create and deduplicate new wildcards")

	with gr.Accordion("Prompt Control Templates:"):
		gr.Markdown("todo")

def handle_image_upload(file):
	image = Image.open(file)
	infotext, infodict = info_extractor.read_infodict_from_image(image)
	return infotext, json.dumps(infodict), image.copy()

def send_to_tab_special(dropdown, image_json, image, random_seeds):
	return send_to_fns.send_to_tab(dropdown, image_json, image, randomise_seeds=random_seeds)

def tools_tab_post_hook(global_ctx, local_ctx):
	local_ctx["image_reader"].upload(
		handle_image_upload,
		inputs=[local_ctx["image_reader"]],
		outputs = [local_ctx["image_infotext"], local_ctx["image_json"], local_ctx["image_viewer"]]
	)
	
	local_ctx["send_to_button"].click(
		send_to_tab_special,
		inputs=[local_ctx["send_to_dropdown"], local_ctx["image_json"], local_ctx["image_viewer"], local_ctx["send_to_randomise_seed"]],
		outputs=[global_ctx["txt2img"]["send_to_target"], global_ctx["img2img"]["send_to_target"], global_ctx["inpaint"]["send_to_target"]]
	)