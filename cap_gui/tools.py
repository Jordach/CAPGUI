# This file returns tools specific features that aren't generative in a sense
import gradio as gr
import cap_util
import json
import matplotlib
from PIL import Image, ImageFilter
from cap_util import info_extractor, gui_generics, send_to_fns, palette_extractor
from cap_util.metadata import save_image_no_meta
from io import BytesIO

def create_fig_byte_stream(fig):
	buf = BytesIO()
	fig.savefig(buf, format="png", bbox_inches="tight")
	buf.seek(0)
	return buf

def palette_extraction_wrapper(image, blur, max_colors, mode, sort, tolerance, show_chart):
	input = handle_palette_image(image, blur)
	if input is None:
		return gr.Image(), gr.Gallery()
	
	# TODO figure out how to not break Gradio when yielding progress updates
	# yield input, input

	if mode == "pil":
		raw_palette = palette_extractor.get_pil_palette(input, max_colors, sort)
	elif mode == "extcolors":
		raw_palette = palette_extractor.get_cie_palette(input, tolerance, max_colors, sort)
	else:
		raw_palette = palette_extractor.get_pil_palette(input, max_colors, sort)
	
	raw_colors = {}
	for i in range(len(raw_palette)):
		raw_colors[f"col_{i}"] = '#%02x%02x%02x' % tuple(raw_palette[i])
	colors = {k: v for k, v in raw_colors.items() if k.startswith("col_")}
	sorted_colors = {k: colors[k] for k in sorted(colors, key=lambda k: int(k.split("_")[-1]))}
	matplot_palette = [col for col in sorted_colors.values()][:max_colors]

	# Create Gallery data
	output_palettes = []

	palette_strip = palette_extractor.create_palette_strip(matplot_palette)
	strip_bytes = create_fig_byte_stream(palette_strip)
	strip_path = cap_util.get_image_save_path("palettes", "palette_strip")
	save_image_no_meta(Image.open(strip_bytes), strip_path)
	output_palettes.append(strip_path)

	if show_chart:
		palette_chart = palette_extractor.create_palette_scatter(raw_palette, False)
		chart_bytes = create_fig_byte_stream(palette_chart)
		chart_path = cap_util.get_image_save_path("palettes", "palette_chart")
		save_image_no_meta(Image.open(chart_bytes), chart_path)
		output_palettes.append(chart_path)

	return input, output_palettes

# Only take effect if the mode is CIE and tolerance is changed
def palette_tolerance_wrapper(image, blur, colors, mode, sort, tolerance, show_chart):
	if mode == "extcolors":
		return palette_extraction_wrapper(image, blur, colors, mode, sort, tolerance, show_chart)
	else:
		return gr.Image(), gr.Gallery()

def handle_palette_image(file, blur):
	try:
		image = Image.open(file)
		img = image.copy()
		img = img.filter(ImageFilter.GaussianBlur(radius=blur))
		return img
	except:
		return None

def handle_image_upload(file):
	image = Image.open(file)
	infotext, infodict = info_extractor.read_infodict_from_image(image)
	return infotext, json.dumps(infodict), image.copy()

def send_to_tab_special(dropdown, image_json, image, random_seeds):
	return send_to_fns.send_to_tab(dropdown, image_json, image, randomise_seeds=random_seeds)

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

	with gr.Accordion("Palette Extractor:", open=False):
		with gr.Row():
			with gr.Column():
				local_ctx["palette_upload"] = gr.File(None, file_count="single", file_types=["image"], type="filepath", show_label=False, height="300px")
				local_ctx["palette_viewer"] = gr.Image(None, show_download_button=False, container=True, interactive=False, image_mode="RGBA", type="pil", show_label=False, height="auto", elem_id=f"{local_ctx['__tab_name__']}_image")
			with gr.Column():
				with gr.Accordion(label="Palette Extraction Settings:", open=True):
					local_ctx["palette_image_blur"] = gr.Slider(value=1, label="Image Blur Strength: (More Consistent Color Picking)", minimum=0, step=0.01, maximum=64)
					local_ctx["palette_show_chart"] = gr.Checkbox(True, label="Show Color Chart?")
					with gr.Row():
						local_ctx["palette_num_colors"] = gr.Number(value=35, label="Number of Colors: (Less is Faster)", maximum=10000, minimum=1)
						local_ctx["palette_mode"] = gr.Dropdown(palette_extractor.palette_extraction_type, value=palette_extractor.palette_extraction_type[0][1], label="Palette Extraction Method")
						local_ctx["palette_sort"] = gr.Dropdown(palette_extractor.palette_sort_type, value=palette_extractor.palette_sort_type[0][1], label="Palette Sorting Method:")
					with gr.Row():
						local_ctx["palette_cie_tolerance"] = gr.Slider(value=16, minimum=0, maximum=1024, step=1, label="CIE Extraction Tolerance:")
						local_ctx["palette_run_extract"] = gr.Button("Manually Extract Palette?", variant="primary")
				# TODO Figure out how to make this only apply to the host machine when clicked since it interacts with pyperclip,
				# otherwise it does nothing for now
				# local_ctx["palette_copy_strip_to_clipboard"] = gr.Button("Copy Strip to Clipboard?", variant="secondary")
				local_ctx["palette_outputs"] = gr.Gallery(
					allow_preview=True, preview=True, show_download_button=True, object_fit="contain",
					show_label=False, label=None, elem_id=f"pallete_gallery", interactive=False, format="png", type="filepath"
				)

	with gr.Accordion("Wildcard Creator:"):
		gr.Markdown("todo - helps create and deduplicate new wildcards")

	with gr.Accordion("Prompt Control Templates:"):
		gr.Markdown("todo")

def tools_tab_post_hook(global_ctx, local_ctx):
	# Metadata Reader:
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

	# Palette Extractor
	p_inputs = [
		local_ctx["palette_upload"], local_ctx["palette_image_blur"], local_ctx["palette_num_colors"], local_ctx["palette_mode"],
		local_ctx["palette_sort"], local_ctx["palette_cie_tolerance"], local_ctx["palette_show_chart"]
	]
	p_outputs = [local_ctx["palette_viewer"], local_ctx["palette_outputs"]]

	local_ctx["palette_upload"].upload(palette_extraction_wrapper, inputs=p_inputs, outputs=p_outputs)
	local_ctx["palette_image_blur"].input(palette_extraction_wrapper, inputs=p_inputs, outputs=p_outputs)
	local_ctx["palette_num_colors"].input(palette_extraction_wrapper, inputs=p_inputs, outputs=p_outputs)
	local_ctx["palette_mode"].input(palette_extraction_wrapper, inputs=p_inputs, outputs=p_outputs)
	local_ctx["palette_sort"].input(palette_extraction_wrapper, inputs=p_inputs, outputs=p_outputs)
	local_ctx["palette_cie_tolerance"].input(palette_tolerance_wrapper, inputs=p_inputs, outputs=p_outputs)
	local_ctx["palette_run_extract"].click(palette_extraction_wrapper, inputs=p_inputs, outputs=p_outputs)
