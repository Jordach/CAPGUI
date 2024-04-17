import os
import cap_util
from cap_util import gui_generics
import websocket
import uuid
import gradio as gr

from cap_gui import topbar

config_status = cap_util.load_config()

cap_util.ws = websocket.WebSocket()
try:
	cap_util.ws.connect(f"ws://{cap_util.gui_default_settings['comfy_address']}:{cap_util.gui_default_settings['comfy_port']}/ws?clientId={cap_util.gui_default_settings['comfy_uuid']}")
except Exception as e:
	raise e

# Memorise a list of checkpoints with their partial paths inside the comfy folders
clip_models, stage_b_models, stage_c_models = cap_util.scan_for_comfy_models()

# Selecting defaults or falling back to the first model entry
# Fallback to RESCAN MODELS notice if no_path is seen
stage_c_default = cap_util.gui_default_settings["comfy_stage_c"] if cap_util.gui_default_settings["comfy_stage_c"] in stage_c_models else stage_c_models[0]
stage_c_default = "RESCAN MODELS" if cap_util.gui_default_settings["comfy_stage_c"] == "no_path" else stage_c_default

stage_b_default = cap_util.gui_default_settings["comfy_stage_b"] if cap_util.gui_default_settings["comfy_stage_b"] in stage_b_models else stage_b_models[0]
stage_b_default = "RESCAN MODELS" if cap_util.gui_default_settings["comfy_stage_b"] == "no_path" else stage_b_default

clip_default = cap_util.gui_default_settings["comfy_clip"] if cap_util.gui_default_settings["comfy_clip"] in clip_models else clip_models[0]
clip_default = "RESCAN MODELS" if cap_util.gui_default_settings["comfy_clip"] == "no_path" else clip_default

global_tabs = {}
def register_tab(tab_name, friendly_name, tab_code_function, send_to_state):
	global global_tabs, tab_friendly_name
	global_tabs[tab_name] = {}
	global_tabs[tab_name]["__tab_name__"] = tab_name
	global_tabs[tab_name]["__friendly_name__"] = friendly_name
	global_tabs[tab_name]["__send_to__"] = send_to_state
	tab_code_function(global_tabs, global_tabs[tab_name], tab_name)

with gr.Blocks(title=f"{'[ANON MODE] ' if cap_util.gui_default_settings['ui_anonymous_mode'] else ''}CAP App", analytics_enabled=False, css="custom_css.css") as app:
	topbar.create_topbar(global_tabs, stage_c_models, stage_c_default, stage_b_models, stage_b_default, clip_models, clip_default)

	with gr.Tab("Text to Image", elem_id="tab_txt2img"):
		with gr.Row(elem_id="promptbar"):
			with gr.Column(scale=6, elem_id="prompts"):
				txt_pos_prompt = gr.Textbox(label=None, show_label=False, placeholder="Enter a prompt here.", lines=3)
				txt_neg_prompt = gr.Textbox(label=None, show_label=False, placeholder="Enter a negative prompt here.", lines=3)
			with gr.Column(elem_id="buttons"):
				txt_generate = gr.Button("Generate!", variant="primary", elem_id="generate_txt2img")
				txt_rec_last_prompt = gr.Button("Load Last Generation", elem_id="reload_txt2img")
				txt_send_to_img2img = gr.Button("Send to Image to Image", elem_id="s2img_txt2img")
				txt_send_to_inpaint = gr.Button("Send to Inpainting", elem_id="s2inp_txt2img")
		with gr.Row(elem_id="tabcontent"):
			with gr.Column(scale=1, elem_id="settings"):
				with gr.Accordion(label="Base Settings:", open=False, elem_id="accordion_base_settings"):
					with gr.Column():
						with gr.Row():
							txt_stage_c_steps = gr.Slider(
								minimum=cap_util.gui_default_settings["gen_c_steps_min"],
								maximum=cap_util.gui_default_settings["gen_c_steps_max"],
								value=cap_util.gui_default_settings["gen_c_steps"],
								step=cap_util.gui_default_settings["gen_c_steps_step"],
								scale=10, label="Base Steps:", interactive=True,
							)
							txt_stage_c_seed = gr.Number(value=-1, minimum=-1, maximum=2147483647, precision=0, label="Base Seed:", scale=2, interactive=True,)
							with gr.Row():
								txt_stage_c_set_seed_rand = gr.Button("🎲", size="sm", scale=1, variant="secondary")
								txt_stage_c_swap_aspects = gr.Button("🔀", size="sm", scale=1, variant="secondary")

					with gr.Row():
						with gr.Column(scale=2):
							txt_stage_c_cfg = gr.Slider(
								minimum=cap_util.gui_default_settings["gen_c_cfg_min"],
								maximum=cap_util.gui_default_settings["gen_c_cfg_max"],
								value=cap_util.gui_default_settings["gen_c_cfg"],
								step=cap_util.gui_default_settings["gen_c_cfg_step"],
								label="Base CFG:", interactive=True, scale=5
							)
							txt_stage_c_batch = gr.Slider(
								minimum=cap_util.gui_default_settings["gen_batch_size_min"],
								maximum=cap_util.gui_default_settings["gen_batch_size_max"],
								value=cap_util.gui_default_settings["gen_batch_size"],
								step=cap_util.gui_default_settings["gen_batch_size_step"],
								label="Batch Size:", interactive=True, scale=2
							)
							txt_stage_c_single_latent = gr.Slider(
								minimum=0,
								maximum=cap_util.gui_default_settings["gen_batch_size_max"]+1,
								value=0, step=cap_util.gui_default_settings["gen_batch_size_step"],
								info="When generating a batch, if this is set to 1, it will only generate the first image of that batch. Zero generates the whole batch.",
								label="Select From Batch:"
							)
							
							txt_save_images = gr.Checkbox(value=not cap_util.gui_default_settings["ui_anonymous_mode"], label="Save Generated Images", 
								interactive=not cap_util.gui_default_settings["ui_anonymous_mode"]
							)

						with gr.Column(scale=4):
							txt_aspect_info = gr.Textbox("1:1", label="Aspect Ratio:", lines=1, max_lines=1, interactive=False)
							txt_aspect_info.change(cap_util.dummy_gradio_function, inputs=[], outputs=[], show_progress=False, queue=False)
							txt_stage_c_width = gr.Slider(
								minimum=cap_util.gui_default_settings["gen_size_min"],
								maximum=cap_util.gui_default_settings["gen_size_max"],
								value=cap_util.gui_default_settings["gen_size"],
								step=cap_util.gui_default_settings["gen_size_step"],
								label="Width:", interactive=True,
							)
							txt_stage_c_width.change(cap_util.dummy_gradio_function, inputs=[], outputs=[], show_progress=False, queue=False)
							txt_stage_c_height = gr.Slider(
								minimum=cap_util.gui_default_settings["gen_size_min"],
								maximum=cap_util.gui_default_settings["gen_size_max"],
								value=cap_util.gui_default_settings["gen_size"],
								step=cap_util.gui_default_settings["gen_size_step"],
								label="Height:", interactive=True
							)
							txt_stage_c_height.change(cap_util.dummy_gradio_function, inputs=[], outputs=[], show_progress=False, queue=False)
							txt_stage_c_shift = gr.Slider(
								minimum=cap_util.gui_default_settings["gen_c_shift_min"],
								maximum=cap_util.gui_default_settings["gen_c_shift_max"],
								value=cap_util.gui_default_settings["gen_c_shift"],
								step=cap_util.gui_default_settings["gen_c_shift_step"],
								label='"Shift"', interactive=True,
								info='This value "shifts" the denoising process of Stage C, which can somewhat create seed variations.'
							)

							txt_stage_c_compression = gr.Slider(
								minimum=32,
								maximum=80,
								info="The recommended default compression factor is 42. Automatic Compression Finder will find the compression factor that results in the best quality for your resolution. When compression reaches 80, higher resolutions can become unstable.",
								value=cap_util.gui_default_settings["gen_compression"],
								step=1, scale=3,
								label="Compression:", interactive=True
							)

							txt_stage_c_compression.change(cap_util.dummy_gradio_function, inputs=[], outputs=[], show_progress=False, queue=False)
							txt_stage_c_auto_compression = gr.Checkbox(value=True, label="Automatic Compression Finder", scale=1, interactive=True)
							
							def calc_compression_factor(width, height, apply_change):
								aspect_text = cap_util.calc_aspect_string(width, height)
								if apply_change:
									return cap_util.calc_compression_factor(width, height), aspect_text
								else:
									return gr.Slider(), aspect_text
							# txt_stage_c_width.release(
							# 	calc_compression_factor, 
							# 	inputs=[txt_stage_c_width, txt_stage_c_height, txt_stage_c_auto_compression], 
							# 	outputs=[txt_stage_c_compression, txt_aspect_info], show_progress=False, queue=False
							# )
							txt_stage_c_width.input(
								calc_compression_factor, 
								inputs=[txt_stage_c_width, txt_stage_c_height, txt_stage_c_auto_compression], 
								outputs=[txt_stage_c_compression, txt_aspect_info], show_progress=False, queue=False
							)
							# txt_stage_c_height.release(
							# 	calc_compression_factor, 
							# 	inputs=[txt_stage_c_width, txt_stage_c_height, txt_stage_c_auto_compression], 
							# 	outputs=[txt_stage_c_compression, txt_aspect_info], show_progress=False, queue=False
							# )
							txt_stage_c_height.input(
								calc_compression_factor, 
								inputs=[txt_stage_c_width, txt_stage_c_height, txt_stage_c_auto_compression], 
								outputs=[txt_stage_c_compression, txt_aspect_info], show_progress=False, queue=False
							)

				with gr.Accordion(label="Refiner Settings:", open=False, elem_id="accordion_refiner_settings"):
					gr.Markdown("These settings are for the Stage B portion of Stable Cascade.\n\nIt's advised that you don't touch these - but if an image seems to come out wrong or has some kind of artifacting, try changing these settings.\n\nYou have been warned.")
					txt_stage_b_seed = gr.Number(value=-1, minimum=-1, maximum=2147483647, precision=0, label="Seed:", scale=2, interactive=True)
					txt_stage_b_steps = gr.Slider(
						minimum=cap_util.gui_default_settings["gen_b_steps_min"],
						maximum=cap_util.gui_default_settings["gen_b_steps_max"],
						value=cap_util.gui_default_settings["gen_b_steps"],
						step=cap_util.gui_default_settings["gen_b_steps_step"],
						label="Refiner Steps:", interactive=True
					)
					txt_stage_b_cfg = gr.Slider(
						minimum=cap_util.gui_default_settings["gen_b_cfg_min"],
						maximum=cap_util.gui_default_settings["gen_b_cfg_max"],
						value=cap_util.gui_default_settings["gen_b_cfg"],
						step=cap_util.gui_default_settings["gen_b_cfg_step"],
						label="Refiner CFG:", interactive=True
					)

				with gr.Accordion(label="Extras:", open=False, elem_id="accordion_extras"):
					gr.Markdown("Soon")

			with gr.Column():
				txt_gallery = gr.Gallery(allow_preview=True, preview=True, show_download_button=True, object_fit="contain", show_label=False, label=None, elem_id="txt2img_gallery", height="70vh")
				#txt_gallery.change(cap_util.dummy_gradio_function, inputs=[], outputs=[], show_progress=False)
				with gr.Accordion("Generation Info:", open=True):
					txt_gen_info_box = gr.Markdown("")

		# Internal self contained tab functions go here:
		txt_stage_c_swap_aspects.click(cap_util.swap_width_height, inputs=[txt_stage_c_height, txt_stage_c_width], outputs=[txt_stage_c_height, txt_stage_c_width, txt_aspect_info])
		txt_generate.click(cap_util.process_basic_txt2img, inputs=[
			txt_pos_prompt,          txt_neg_prompt,     txt_stage_c_steps,             txt_stage_c_seed,
			txt_stage_c_width,       txt_stage_c_height, txt_stage_c_cfg,               txt_stage_c_batch,
			txt_stage_c_compression, txt_stage_c_shift,  txt_stage_c_single_latent,
			txt_stage_b_seed,        txt_stage_b_cfg,    txt_stage_b_steps,             global_tabs["topbar"]["stage_b"], 
			global_tabs["topbar"]["stage_c"],            global_tabs["topbar"]["clip"], global_tabs["topbar"]["backend"]
		], outputs=[txt_gallery, txt_gen_info_box])

	with gr.Tab("Image to Image", elem_id="tab_img2img"):
		with gr.Row(elem_id="topbar"):
			with gr.Column(scale=6, elem_id="prompts"):
				img_pos_prompt = gr.Textbox(label=None, show_label=False, placeholder="Enter a prompt here.", lines=3)
				img_neg_prompt = gr.Textbox(label=None, show_label=False, placeholder="Enter a negative prompt here.", lines=3)
			with gr.Column(elem_id="buttons"):
				img_generate = gr.Button("Generate!", variant="primary", elem_id="generate_img2img")
				img_rec_last_prompt = gr.Button("Load Last Generation", elem_id="reload_img2img")
				img_send_to_txt2img = gr.Button("Send to Text to Image", elem_id="s2txt_img2img")
				img_send_to_inpaint = gr.Button("Send to Inpainting", elem_id="s2inp_img2img")
		with gr.Row(elem_id="tabcontent"):
			with gr.Column(scale=1, elem_id="settings"):
				with gr.Accordion(label="Base Settings:", open=False, elem_id="accordion_base_settings"):
					with gr.Column():
						with gr.Row():
							img_stage_c_steps = gr.Slider(
								minimum=cap_util.gui_default_settings["gen_c_steps_min"],
								maximum=cap_util.gui_default_settings["gen_c_steps_max"],
								value=cap_util.gui_default_settings["gen_c_steps"],
								step=cap_util.gui_default_settings["gen_c_steps_step"],
								scale=10, label="Base Steps:", interactive=True,
							)
							img_stage_c_seed = gr.Number(value=-1, minimum=-1, maximum=2147483647, precision=0, label="Base Seed:", scale=2, interactive=True)
							with gr.Row():
								img_stage_c_set_seed_rand = gr.Button("🎲", size="sm", scale=1, variant="secondary")
								img_stage_c_swap_aspects = gr.Button("🔀", size="sm", scale=1, variant="secondary")
					with gr.Row():
						with gr.Column(scale=2):
							pass

						with gr.Column(scale=4):
							pass
				pass

			with gr.Column(elem_id="output"):
				img_gallery = gr.Gallery(allow_preview=True, preview=True, show_download_button=True, object_fit="contain", show_label=False, label=None, elem_id="img2img_gallery", height="70vh")
				with gr.Accordion("Generation Info:", open=True):
					img_gen_info_box = gr.Markdown("")
			gr.Markdown("Soon")
		# Internal self contained tab functions go here:
	
	with gr.Tab("Inpainting", elem_id="tab_inpainting"):
		gr.Markdown("Soon")
		# Internal self contained tab functions go here:

	if not cap_util.gui_default_settings["ui_anonymous_mode"]:
		with gr.Tab("Gallery", elem_id="tab_gallery"):
			gr.Markdown("Soon")

	with gr.Tab("Settings", elem_id="tab_settings"):
		with gr.Accordion(label="Community AI Platform Settings:", open=False):
			gr.Markdown("soon")
		with gr.Accordion(label="Generation Settings:", open=False):
			gr.Markdown("Change these defaults if you know what you're doing!")
		with gr.Accordion(label="GUI Settings:", open=False):
			gr.Markdown("soon")
		gr.Markdown("Other Settings:")
		gr.Markdown("**Note: Changes will be used after saving.**")
		setting_save_changes = gr.Button("Save Configuration Changes.", variant="primary")
		
		gr.Markdown("Soon")
		# Internal self contained tab functions go here:

	with gr.Tab("Hints and Tips", elem_id="tab_hints"):
		gr.Markdown("Soon")
		# Internal self contained tab functions go here:

	with gr.Tab("Community", elem_id="tab_community"):
		gr.Markdown("Soon")
		# Internal self contained tab functions go here:

	gr.Markdown(f"CAP App Prototype{', **GENERATIONS WILL NOT BE SAVED IN ANONYMOUS MODE!**' if cap_util.gui_default_settings['ui_anonymous_mode'] else ''}")
	# Element functions that work on the current and or other tabs go here:
	# pass

# Magical stuff to make basic keybinds and JavaScript that need the full DOM work,
# this is atrocious and should probably be made part of the gradio library to append
# the <head> and <body> headers respectively.
if not hasattr(cap_util, "gradio_response_header"):
	cap_util.gradio_response_header = gr.routes.templates.TemplateResponse

appended_script = '<script type="text/javascript" src="file=custom_js.js"></script>\n'

def new_resp(*args, **kwargs):
	new_response = cap_util.gradio_response_header(*args, **kwargs)
	new_response.body = new_response.body.replace(b'</head>', f"{appended_script}</head>".encode("utf8"))
	new_response.init_headers()
	return new_response

gr.routes.templates.TemplateResponse = new_resp
app.launch(server_port=6969, server_name="0.0.0.0", allowed_paths=[os.getcwd()])