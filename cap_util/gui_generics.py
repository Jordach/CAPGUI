# This file is used for importing the generic GUI pieces such as the Generate button
import cap_util
import gradio as gr

# Functions
def dummy_post_hook(global_ctx, local_ctx):
	pass

def set_rand_seed():
	return -1

def send_to_targets(global_ctx):
	# Get a list of tabs used for generation
	targets = []
	known_tabs = global_ctx.keys()
	for tab in known_tabs:
		if "__send_to__" in global_ctx[tab]:
			if global_ctx[tab]["__send_to__"]:
				targets.append(global_ctx[tab]["__friendly_name__"])
	
	return targets

# Components that are shared or common to multiple tabs
# these usually do not come with functions

def get_pos_prompt_box():
	return gr.Textbox(label=None, show_label=False, placeholder="Enter a prompt here.", lines=3)

def get_neg_prompt_box():
	return gr.Textbox(label=None, show_label=False, placeholder="Enter a negative prompt here.", lines=3)

def get_generate_button(local_ctx):
	return gr.Button("Generate!", variant="primary", elem_id=f"generate_{local_ctx['__tab_name__']}")

def get_load_last_button():
	return gr.Button("Load Last Generation", elem_id="reload_txt2img")

def get_send_to_button():
	return gr.Button("Send to Selected Tab.", elem_id="send2tab")

def get_send_to_dropdown(global_ctx):
	return gr.Dropdown(send_to_targets(global_ctx), filterable=False, label="Send To Tab:")

def get_prompt_row(global_ctx, local_ctx, prompt_scale):
	with gr.Row(elem_id="promptbar"):
		with gr.Column(scale=prompt_scale):
			local_ctx["pos_prompt"] = get_pos_prompt_box()
			local_ctx["neg_prompt"] = get_neg_prompt_box()
		with gr.Column(elem_id="buttons"):
			local_ctx["generate"] = get_generate_button(local_ctx)
			local_ctx["load_last"] = get_load_last_button()
	pass

def get_generation_settings_column(global_ctx, local_ctx):
	with gr.Accordion(label="Base Settings:", open=False, elem_id="base_settings"):
		with gr.Column():
			with gr.Row():
				local_ctx["stage_c_steps"] = gr.Slider(
					minimum=cap_util.gui_default_settings["gen_c_steps_min"],
					maximum=cap_util.gui_default_settings["gen_c_steps_max"],
					value=cap_util.gui_default_settings["gen_c_steps"],
					step=cap_util.gui_default_settings["gen_c_steps_step"],
					scale=10, label="Base Steps:", interactive=True,
				)

				local_ctx["stage_c_seed"] = gr.Number(value=-1, minimum=-1, maximum=2147483647, precision=0, label="Base Seed:", scale=2, interactive=True,)
				local_ctx["stage_c_seed"].change(cap_util.dummy_gradio_function, inputs=[], outputs=[], show_progress=False, queue=False)
				with gr.Row():
					local_ctx["stage_c_seed_rand"] = gr.Button("🎲", size="sm", scale=1, variant="secondary")
					local_ctx["stage_c_swap_ratio"] = gr.Button("🔀", size="sm", scale=1, variant="secondary")
				local_ctx["stage_c_seed_rand"].click(set_rand_seed, inputs=[], outputs=[local_ctx["stage_c_seed"]], show_progress=False, queue=True,)
		
		with gr.Row():
			with gr.Column(scale=2):
				local_ctx["stage_c_cfg"] = gr.Slider(
					minimum=cap_util.gui_default_settings["gen_c_cfg_min"],
					maximum=cap_util.gui_default_settings["gen_c_cfg_max"],
					value=cap_util.gui_default_settings["gen_c_cfg"],
					step=cap_util.gui_default_settings["gen_c_cfg_step"],
					label="Base CFG:", interactive=True, scale=5
				)
				local_ctx["stage_c_batch"] = gr.Slider(
					minimum=cap_util.gui_default_settings["gen_batch_size_min"],
					maximum=cap_util.gui_default_settings["gen_batch_size_max"],
					value=cap_util.gui_default_settings["gen_batch_size"],
					step=cap_util.gui_default_settings["gen_batch_size_step"],
					label="Batch Size:", interactive=True, scale=2
				)
				local_ctx["stage_c_single_latent"] = gr.Slider(
					minimum=0,
					maximum=cap_util.gui_default_settings["gen_batch_size_max"]+1,
					value=0, step=cap_util.gui_default_settings["gen_batch_size_step"],
					info="When generating a batch, if this is set to 1, it will only generate the first image of that batch. Zero generates the whole batch.",
					label="Select From Batch:"
				)
				local_ctx["stage_c_save_images"] = gr.Checkbox(value=not cap_util.gui_default_settings["ui_anonymous_mode"], label="Save Generated Images", 
					interactive=not cap_util.gui_default_settings["ui_anonymous_mode"]
				)

			with gr.Column(scale=4):
				local_ctx["aspect_info"] = gr.Textbox("1:1", label="Aspect Ratio:", lines=1, max_lines=1, interactive=False)
				local_ctx["aspect_info"].change(cap_util.dummy_gradio_function, inputs=[], outputs=[], show_progress=False, queue=False)

				local_ctx["stage_c_width"] = gr.Slider(
					minimum=cap_util.gui_default_settings["gen_size_min"],
					maximum=cap_util.gui_default_settings["gen_size_max"],
					value=cap_util.gui_default_settings["gen_size"],
					step=cap_util.gui_default_settings["gen_size_step"],
					label="Width:", interactive=True,
				)
				local_ctx["stage_c_width"].change(cap_util.dummy_gradio_function, inputs=[], outputs=[], show_progress=False, queue=False)
				
				local_ctx["stage_c_height"] = gr.Slider(
					minimum=cap_util.gui_default_settings["gen_size_min"],
					maximum=cap_util.gui_default_settings["gen_size_max"],
					value=cap_util.gui_default_settings["gen_size"],
					step=cap_util.gui_default_settings["gen_size_step"],
					label="Height:", interactive=True
				)
				local_ctx["stage_c_height"].change(cap_util.dummy_gradio_function, inputs=[], outputs=[], show_progress=False, queue=False)
				
				local_ctx["stage_c_shift"] = gr.Slider(
					minimum=cap_util.gui_default_settings["gen_c_shift_min"],
					maximum=cap_util.gui_default_settings["gen_c_shift_max"],
					value=cap_util.gui_default_settings["gen_c_shift"],
					step=cap_util.gui_default_settings["gen_c_shift_step"],
					label='"Shift"', interactive=True,
					info='This value "shifts" the denoising process of Stage C, which can somewhat create seed variations.'
				)

				local_ctx["stage_c_compression"] = gr.Slider(
					minimum=32,
					maximum=80,
					info="The recommended default compression factor is 42. Automatic Compression Finder will find the compression factor that results in the best quality for your resolution. When compression reaches 80, higher resolutions can become unstable.",
					value=cap_util.gui_default_settings["gen_compression"],
					step=1, scale=3,
					label="Compression:", interactive=True
				)
				local_ctx["stage_c_compression"].change(cap_util.dummy_gradio_function, inputs=[], outputs=[], show_progress=False, queue=False)
				local_ctx["stage_c_auto_compressor"] = gr.Checkbox(value=True, label="Automatic Compression Finder", scale=1, interactive=True)
						
				def calc_compression_factor(width, height, apply_change):
					aspect_text = cap_util.calc_aspect_string(width, height)
					if apply_change:
						return cap_util.calc_compression_factor(width, height), aspect_text
					else:
						return gr.Slider(), aspect_text
				
				local_ctx["stage_c_width"].input(
					calc_compression_factor,
					inputs=[local_ctx["stage_c_width"], local_ctx["stage_c_height"], local_ctx["stage_c_auto_compressor"]],
					outputs = [local_ctx["stage_c_compression"], local_ctx["aspect_info"]], show_progress=False, queue=False
				)

				local_ctx["stage_c_height"].input(
					calc_compression_factor,
					inputs=[local_ctx["stage_c_width"], local_ctx["stage_c_height"], local_ctx["stage_c_auto_compressor"]],
					outputs = [local_ctx["stage_c_compression"], local_ctx["aspect_info"]], show_progress=False, queue=False
				)
		
	with gr.Accordion(label="Refiner Settings:", open=False, elem_id="refiner_settings"):
		gr.Markdown("These settings are for the Stage B portion of Stable Cascade.\n\nIt's advised that you don't touch these - but if an image seems to come out wrong or has some kind of artifacting, try changing these settings.\n\nYou have been warned.", line_breaks=True)
		local_ctx["stage_b_seed"] = gr.Number(value=-1, minimum=-1, maximum=2147483647, precision=0, label="Seed:", scale=2, interactive=True)
		local_ctx["stage_b_steps"] = gr.Slider(
			minimum=cap_util.gui_default_settings["gen_b_steps_min"],
			maximum=cap_util.gui_default_settings["gen_b_steps_max"],
			value=cap_util.gui_default_settings["gen_b_steps"],
			step=cap_util.gui_default_settings["gen_b_steps_step"],
			label="Refiner Steps:", interactive=True
		)
		local_ctx["stage_b_cfg"] = gr.Slider(
			minimum=cap_util.gui_default_settings["gen_b_cfg_min"],
			maximum=cap_util.gui_default_settings["gen_b_cfg_max"],
			value=cap_util.gui_default_settings["gen_b_cfg"],
			step=cap_util.gui_default_settings["gen_b_cfg_step"],
			label="Refiner CFG:", interactive=True
		)
	
	with gr.Accordion("Extras:", open=False, elem_id="extra_settings"):
		gr.Markdown("To be continued")
	
	# Make the swapping of aspect ratios universal across tabs
	local_ctx["stage_c_swap_ratio"].click(
		cap_util.swap_width_height, 
		inputs=[local_ctx["stage_c_height"], local_ctx["stage_c_width"]],
		outputs=[local_ctx["stage_c_height"], local_ctx["stage_c_width"], local_ctx["aspect_info"]],
		show_progress=False, queue=False
	)

def get_gallery_column(global_ctx, local_ctx, gallery_height="70vh"):
	local_ctx["gallery"] = gr.Gallery(
		allow_preview=True, preview=True, show_download_button=True, object_fit="contain", 
		show_label=False, label=None, elem_id=f"{local_ctx['__tab_name__']}_gallery", height=gallery_height,
	)
	with gr.Accordion(label="Generation Info:", open=True):
		local_ctx["gen_info_box"] = gr.Markdown("", line_breaks=True)
		with gr.Column():
			local_ctx["send_to_dropdown"] = get_send_to_dropdown(global_ctx)
			local_ctx["send_to_button"] = get_send_to_button()