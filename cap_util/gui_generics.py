# This file is used for importing the generic GUI pieces such as the Generate button
import cap_util
import gradio as gr
import copy
from cap_util import presets
from cap_util.gui_xy import gui_xy

# Functions
def dummy_post_hook(global_ctx, local_ctx):
	pass

def set_rand_seed():
	return -1

def send_to_targets(global_ctx, current_tab):
	# Get a list of tabs used for generation
	known_tabs = global_ctx.keys()
	targets = []
	for tab in known_tabs:
		# Don't send to the same tab
		if current_tab == tab:
			continue

		if "__send_to__" in global_ctx[tab]:
			if global_ctx[tab]["__send_to__"]:
				targets.append(global_ctx[tab]["__name_pair__"])
	
	return targets

# Component functions for loading, refreshing and saving of Sampling presets
def startup_preset_c():
	presets.load_all_user_presets(c=True)
	return cap_util.ksampler_presets_stage_c_dropdown

def reload_preset_c():
	presets.load_all_user_presets(c=True)
	return gr.Dropdown(choices=cap_util.ksampler_presets_stage_c_dropdown, value=cap_util.ksampler_presets_stage_c_dropdown[0])

def load_preset_settings_c(preset):
	settings = cap_util.ksampler_presets_stage_c[preset]
	return settings["sampler"], settings["scheduler"], settings["steps"], settings["cfg"], settings["shift"]

def save_preset_settings_c(sampler, scheduler, steps, cfg, shift, filename, desc):
	presets.save_as_new_preset(filename, desc, "c", steps, cfg, sampler, scheduler, shift)

def startup_preset_b():
	presets.load_all_user_presets(b=True)
	return cap_util.ksampler_presets_stage_b_dropdown

def reload_preset_b():
	presets.load_all_user_presets(b=True)
	return gr.Dropdown(choices=cap_util.ksampler_presets_stage_b, value=cap_util.ksampler_presets_stage_b_dropdown[0])

def load_preset_settings_b(preset):
	settings = cap_util.ksampler_presets_stage_b[preset]
	return settings["sampler"], settings["scheduler"], settings["steps"], settings["cfg"]

def save_preset_settings_b(sampler, scheduler, steps, cfg, filename, desc):
	presets.save_as_new_preset(filename, desc, "b", steps, cfg, sampler, scheduler)

# Components that are shared or common to multiple tabs
# these usually do not come with functions
def get_pos_prompt_box():
	return gr.Textbox(label=None, show_label=False, placeholder="Enter a prompt here.", lines=3, elem_id="pos_prompt", elem_classes=["prompt"], container=False)

def get_neg_prompt_box():
	return gr.Textbox(label=None, show_label=False, placeholder="Enter a negative prompt here.", lines=3, elem_id="neg_prompt", elem_classes=["prompt"], container=False)

def get_generate_button(local_ctx):
	return gr.Button("Generate!", variant="primary", elem_id=f"generate_{local_ctx['__tab_name__']}")

def get_load_last_button():
	return gr.Button("Load Last Generation", elem_id="reload_txt2img")

def get_gen_forever_checkbox(local_ctx):
	return gr.Checkbox(False, label="Generate Forever?", elem_id=f"gen_forever_{local_ctx['__tab_name__']}")

def get_send_to_button():
	return gr.Button("Send to Selected Tab.", elem_id="send2tab")

def get_send_to_dropdown(global_ctx):
	return gr.Dropdown(["not initialised"], multiselect=False, interactive=True, label="Send To Tab:")

def get_prompt_row(global_ctx, local_ctx, prompt_scale, extra_buttons_fn=dummy_post_hook):
	with gr.Row(elem_id="promptbar"):
		with gr.Column(scale=prompt_scale):
			local_ctx["pos_prompt"] = get_pos_prompt_box()
			local_ctx["neg_prompt"] = get_neg_prompt_box()
		with gr.Column(elem_id="buttons"):
			local_ctx["generate"] = get_generate_button(local_ctx)
			local_ctx["load_last"] = get_load_last_button()
			local_ctx["gen_forever"] = get_gen_forever_checkbox(local_ctx)
			extra_buttons_fn(global_ctx, local_ctx)

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

				local_ctx["stage_c_seed"] = gr.Number(value=-1, minimum=-1, maximum=2147483647, precision=0, label="Base Seed:", scale=2, interactive=True)
				with gr.Row():
					local_ctx["stage_c_seed_rand"] = gr.Button("🎲", size="sm", scale=1, variant="secondary")
					local_ctx["stage_c_swap_ratio"] = gr.Button("🔀", size="sm", scale=1, variant="secondary")
				local_ctx["stage_c_seed_rand"].click(set_rand_seed, inputs=[], outputs=[local_ctx["stage_c_seed"]], show_progress=False, queue=False)
		
		with gr.Row():
			with gr.Column(scale=2):
				local_ctx["stage_c_cfg"] = gr.Slider(
					minimum=cap_util.gui_default_settings["gen_c_cfg_min"],
					maximum=cap_util.gui_default_settings["gen_c_cfg_max"],
					value=cap_util.gui_default_settings["gen_c_cfg"],
					step=cap_util.gui_default_settings["gen_c_cfg_step"],
					label="CFG:", interactive=True, scale=5
				)
				local_ctx["stage_c_rescale"] = gr.Slider(
					minimum=cap_util.gui_default_settings["gen_c_rescale_min"],
					maximum=cap_util.gui_default_settings["gen_c_rescale_max"],
					value=cap_util.gui_default_settings["gen_c_rescale"],
					step=cap_util.gui_default_settings["gen_c_rescale_step"],
					label="CFG Rescale:", interactive=True, scale=5,
					info="How much to rescale CFG by during sampling. Values over 0.8 tend to cause issues."
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
				with gr.Row():
					local_ctx["aspect_info"] = gr.Textbox("1:1", label="Aspect Ratio:", lines=1, max_lines=1, interactive=False)
					local_ctx["latent_res"] = gr.Textbox(
						f"{cap_util.gui_default_settings['gen_size']//cap_util.gui_default_settings['gen_compression']}x{cap_util.gui_default_settings['gen_size']//cap_util.gui_default_settings['gen_compression']}",
						label="Latent Resolution:", lines=1, max_lines=1, interactive=False
					)

				local_ctx["stage_c_width"] = gr.Slider(
					minimum=cap_util.gui_default_settings["gen_size_min"],
					maximum=cap_util.gui_default_settings["gen_size_max"],
					value=cap_util.gui_default_settings["gen_size"],
					step=cap_util.gui_default_settings["gen_size_step"],
					label="Width:", interactive=True,
				)
				
				local_ctx["stage_c_height"] = gr.Slider(
					minimum=cap_util.gui_default_settings["gen_size_min"],
					maximum=cap_util.gui_default_settings["gen_size_max"],
					value=cap_util.gui_default_settings["gen_size"],
					step=cap_util.gui_default_settings["gen_size_step"],
					label="Height:", interactive=True
				)
				
				local_ctx["stage_c_shift"] = gr.Slider(
					minimum=cap_util.gui_default_settings["gen_c_shift_min"],
					maximum=cap_util.gui_default_settings["gen_c_shift_max"],
					value=cap_util.gui_default_settings["gen_c_shift"],
					step=cap_util.gui_default_settings["gen_c_shift_step"],
					label='"Shift"', interactive=True,
					info='This value "shifts" the denoising process of Stage C, which can somewhat create seed variations.'
				)

				local_ctx["stage_c_compression"] = gr.Slider(
					minimum=16,
					maximum=80,
					info="The recommended default compression factor is 42. Automatic Compression Finder will find the compression factor that results in the best quality for your resolution. When compression reaches 80, higher resolutions can become unstable.",
					value=cap_util.gui_default_settings["gen_compression"],
					step=1, scale=3,
					label="Compression:", interactive=True
				)
				local_ctx["stage_c_auto_compressor"] = gr.Checkbox(value=True, label="Automatic Compression Finder", scale=1, interactive=True)
						
				def calc_compression_factor(width, height, apply_change, compression):
					aspect_text = cap_util.calc_aspect_string(width, height)
					if apply_change:
						comp = cap_util.calc_compression_factor(width, height)
						lw, lh = 0, 0
						if comp is not None:
							lw, lh = width//comp, height//comp
						else:
							lw, lh = width//compression, height//compression
						
						latent_text = f"{lw}x{lh}"
						add_warning = False
						if lw < 16 or lw > 64:
							add_warning = True
						if lh < 16 or lh > 64:
							add_warning = True

						if add_warning:
							latent_text += " ⚠️"
						return comp if comp is not None else gr.Slider(), aspect_text, latent_text
					else:
						lw, lh = width//compression, height//compression
						latent_text = f"{lw}x{lh}"
						add_warning = False
						if lw < 16 or lw > 64:
							add_warning = True
						if lh < 16 or lh > 64:
							add_warning = True
							
						if add_warning:
							latent_text += " ⚠️"
						return gr.Slider(), aspect_text, latent_text

				def compression_factor_change(width, height, compression):
					aspect_text = cap_util.calc_aspect_string(width, height)
					lw, lh = width//compression, height//compression
					latent_text = f"{lw}x{lh}"
					add_warning = False
					if lw < 16 or lw > 64:
						add_warning = True
					if lh < 16 or lh > 64:
						add_warning = True
						
					if add_warning:
						latent_text += " ⚠️"
					return aspect_text, latent_text

				local_ctx["stage_c_width"].change(
					calc_compression_factor,
					inputs=[local_ctx["stage_c_width"], local_ctx["stage_c_height"], local_ctx["stage_c_auto_compressor"], local_ctx["stage_c_compression"]],
					outputs = [local_ctx["stage_c_compression"], local_ctx["aspect_info"], local_ctx["latent_res"]], show_progress=False, queue=False
				)

				local_ctx["stage_c_height"].change(
					calc_compression_factor,
					inputs=[local_ctx["stage_c_width"], local_ctx["stage_c_height"], local_ctx["stage_c_auto_compressor"], local_ctx["stage_c_compression"]],
					outputs = [local_ctx["stage_c_compression"], local_ctx["aspect_info"], local_ctx["latent_res"]], show_progress=False, queue=False
				)

				local_ctx["stage_c_compression"].input(
					compression_factor_change,
					inputs=[local_ctx["stage_c_width"], local_ctx["stage_c_height"], local_ctx["stage_c_compression"]],
					outputs=[local_ctx["aspect_info"], local_ctx["latent_res"]], show_progress=False, queue=False
				)
		# KSampler Settings
		with gr.Row():
			local_ctx["stage_c_preset_dropdown"] = gr.Dropdown(startup_preset_c(), scale=6, label="Load Preset:", value=cap_util.ksampler_presets_stage_c_dropdown[0][1], multiselect=False, filterable=False)
			local_ctx["stage_c_preset_reload"] = gr.Button("🔄", scale=1)
			local_ctx["stage_c_preset_reload"].click(reload_preset_c, inputs=None, outputs=[local_ctx["stage_c_preset_dropdown"]], show_progress="hidden")
		with gr.Accordion(label="Advanced Sampling Settings:", open=False):
			with gr.Row():
				local_ctx["stage_c_preset_save"] = gr.Button("Save Preset", scale=1)
				local_ctx["stage_c_preset_name"] = gr.Textbox(value="", lines=1, max_lines=1, placeholder="my_custom_file_name", label="Preset File Name:", scale=3)
				local_ctx["stage_c_preset_desc"] = gr.Textbox(value="", lines=1, max_lines=1, placeholder="My Custom Label", label="Preset Label:", scale=3)
			with gr.Row():
				local_ctx["stage_c_sampler"] = gr.Dropdown(cap_util.ksampler_samplers, value=cap_util.ksampler_samplers[0][1], label="Denoising Sampler:")
				local_ctx["stage_c_scheduler"] = gr.Dropdown(cap_util.ksampler_schedules, value=cap_util.ksampler_schedules[0][1], label="Denoising Schedule:")
		local_ctx["stage_c_preset_dropdown"].input(load_preset_settings_c, inputs=[local_ctx["stage_c_preset_dropdown"]], 
			outputs=[local_ctx["stage_c_sampler"], local_ctx["stage_c_scheduler"], local_ctx["stage_c_steps"], local_ctx["stage_c_cfg"], local_ctx["stage_c_shift"]], show_progress=None
		)
		local_ctx["stage_c_preset_save"].click(save_preset_settings_c, 
			inputs=[local_ctx["stage_c_sampler"], local_ctx["stage_c_scheduler"], local_ctx["stage_c_steps"], local_ctx["stage_c_cfg"], local_ctx["stage_c_shift"], local_ctx["stage_c_preset_name"], local_ctx["stage_c_preset_desc"]], 
			outputs=None
		)


	with gr.Accordion(label="Refiner Settings:", open=False, elem_id="refiner_settings"):
		gr.Markdown("These settings are for the Stage B portion of Stable Cascade.\n\nIt's advised that you don't touch these - but if an image seems to come out wrong or has some kind of artifacting, try changing these settings.\n\nYou have been warned.", line_breaks=True)
		with gr.Row():
			local_ctx["stage_b_preset_dropdown"] = gr.Dropdown(startup_preset_b(), scale=6, label="Load Preset:", value=cap_util.ksampler_presets_stage_b_dropdown[0][1], multiselect=False, filterable=False)
			local_ctx["stage_b_preset_reload"] = gr.Button("🔄", scale=1)
			local_ctx["stage_b_preset_reload"].click(reload_preset_b, inputs=None, outputs=[local_ctx["stage_b_preset_dropdown"]])
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

		# KSampler Settings
		with gr.Row():
			local_ctx["stage_b_preset_save"] = gr.Button("Save Preset", scale=1)
			local_ctx["stage_b_preset_name"] = gr.Textbox(value="", lines=1, max_lines=1, placeholder="my_custom_file_name", label="Preset File Name:", scale=3)
			local_ctx["stage_b_preset_desc"] = gr.Textbox(value="", lines=1, max_lines=1, placeholder="My Custom Label", label="Preset Label:", scale=3)
		with gr.Row():
			local_ctx["stage_b_sampler"] = gr.Dropdown(cap_util.ksampler_samplers, value=cap_util.ksampler_samplers[0][1], label="Denoising Sampler:")
			local_ctx["stage_b_scheduler"] = gr.Dropdown(cap_util.ksampler_schedules, value=cap_util.ksampler_schedules[0][1], label="Denoising Schedule:")
		local_ctx["stage_b_preset_dropdown"].input(load_preset_settings_b, inputs=[local_ctx["stage_b_preset_dropdown"]], 
			outputs=[local_ctx["stage_b_sampler"], local_ctx["stage_b_scheduler"], local_ctx["stage_b_steps"], local_ctx["stage_b_cfg"]], show_progress="None"
		)
		local_ctx["stage_b_preset_save"].click(save_preset_settings_b, 
			inputs=[local_ctx["stage_b_sampler"], local_ctx["stage_b_scheduler"], local_ctx["stage_b_steps"], local_ctx["stage_b_cfg"], local_ctx["stage_b_preset_name"], local_ctx["stage_b_preset_desc"]], 
			outputs=None
		)

	with gr.Accordion("Extras:", open=False, elem_id="extra_settings"):
		local_ctx["use_stage_a_hq"] = gr.Checkbox(True, label="Use High Quality Decoder?", info="Uses a custom finetune of Stage A to decode latents with less overall blur.")
		with gr.Accordion(label="X/Y Settings:", open=False, elem_id="base_settings") as xy_block:
			gui_xy(global_ctx, local_ctx)
		
		gr.Markdown("To be continued")
	
	# Make the swapping of aspect ratios universal across tabs
	local_ctx["stage_c_swap_ratio"].click(
		cap_util.swap_width_height, 
		inputs=[local_ctx["stage_c_height"], local_ctx["stage_c_width"]],
		outputs=[local_ctx["stage_c_height"], local_ctx["stage_c_width"], local_ctx["aspect_info"]],
		show_progress=False, queue=False
	)

def get_gallery_column(global_ctx, local_ctx, gallery_height="70vh", add_send_to_text=False):
	local_ctx["gallery"] = gr.Gallery(
		allow_preview=True, preview=True, show_download_button=True, object_fit="contain", 
		show_label=False, label=None, elem_id=f"{local_ctx['__tab_name__']}_gallery", height=gallery_height,
		interactive=False,
	)
	with gr.Accordion(label="Generation Info:", open=True):
		local_ctx["gen_info_box"] = gr.Markdown("", line_breaks=True)
		with gr.Column():
			local_ctx["send_to_which_image"] = gr.Slider(
				minimum=1, maximum=cap_util.gui_default_settings["gen_batch_size_max"], value=1, step=1, 
				label="Which Image to Send?", info="1 sends the first image, 2 sends the second image, and so on."
			)
			local_ctx["send_to_dropdown"] = get_send_to_dropdown(global_ctx)
			local_ctx["send_to_button"] = get_send_to_button()
	
			# Whether a tab can receive infotext to update prompts, generation parameters and images
			if add_send_to_text:
				local_ctx["send_to_target"] = gr.Textbox("INIT", visible=False)
				local_ctx["gen_json"] = gr.Markdown("INIT", visible=False)