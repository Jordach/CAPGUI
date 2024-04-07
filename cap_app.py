import os
import cap_util
try:
	import websocket #pip install websocket-client (https://github.com/websocket-client/websocket-client)
except:
	raise Exception("Please install websocket-client with:\npip install websocket-client")
import uuid
import gradio as gr

cap_util.load_config()

if "comfy_uuid" not in cap_util.gui_default_settings:
	# This is more cosmetic in nature and just provides a manner in which to use ComfyUI
	# without it forgetting who you are.
	cap_util.gui_default_settings["comfy_uuid"] = str(uuid.uuid4())
	cap_util.save_config()

working_websocket = True
cap_util.ws = websocket.WebSocket()
try:
	cap_util.ws.connect(f"ws://{cap_util.gui_default_settings['comfy_address']}:{cap_util.gui_default_settings['comfy_port']}/ws?clientId={cap_util.gui_default_settings['comfy_uuid']}")
except Exception as e:
	working_websocket = False
	raise e

# Memorise a list of checkpoints with their partial paths inside the comfy folders
if cap_util.gui_default_settings["comfy_path"] != "no_path":
	if os.path.exists(cap_util.gui_default_settings["comfy_path"]):
		pass

clip_models, stage_b_models, stage_c_models = cap_util.scan_for_comfy_models()

with gr.Blocks(title="CAP App", analytics_enabled=False, css="custom_css.css") as app:
	with gr.Row(elem_id="model_select"):
		# Selecting defaults or falling back to the first model entry
		# Fallback to RESCAN MODELS notice if no_path is seen
		stage_c_default = cap_util.gui_default_settings["comfy_stage_c"] if cap_util.gui_default_settings["comfy_stage_c"] in stage_c_models else stage_c_models[0]
		stage_c_default = "RESCAN MODELS" if cap_util.gui_default_settings["comfy_stage_c"] == "no_path" else stage_c_default

		stage_b_default = cap_util.gui_default_settings["comfy_stage_b"] if cap_util.gui_default_settings["comfy_stage_b"] in stage_b_models else stage_b_models[0]
		stage_b_default = "RESCAN MODELS" if cap_util.gui_default_settings["comfy_stage_b"] == "no_path" else stage_b_default
		
		clip_default = cap_util.gui_default_settings["comfy_clip"] if cap_util.gui_default_settings["comfy_clip"] in clip_models else clip_models[0]
		clip_default = "RESCAN MODELS" if cap_util.gui_default_settings["comfy_clip"] == "no_path" else clip_default
		
		# Also handle saving for changes on a per dropdown basis
		stage_c_ckpt = gr.Dropdown(
			stage_c_models, filterable=False,
			value=stage_c_default,
			label="Cascade Base Model:", scale=1,
		)
		def save_sc_ckpt(entry):
			cap_util.gui_default_settings["comfy_stage_c"] = entry
			cap_util.save_config()
		stage_c_ckpt.input(save_sc_ckpt, inputs=[stage_c_ckpt])

		stage_b_ckpt = gr.Dropdown(
			stage_b_models, filterable=False,
			value=stage_b_default,
			label="Cascade Refiner Model:", scale=1,
		)
		def save_sb_ckpt(entry):
			cap_util.gui_default_settings["comfy_stage_b"] = entry
			cap_util.save_config()
		stage_b_ckpt.input(save_sb_ckpt, inputs=[stage_b_ckpt])

		clip_ckpt = gr.Dropdown(
			clip_models, filterable=False,
			value=clip_default,
			label="Cascade Text Model:", scale=1,
		)
		def save_clip_ckpt(entry):
			cap_util.gui_default_settings["comfy_clip"] = entry
			cap_util.save_config()
		clip_ckpt.input(save_clip_ckpt, inputs=[clip_ckpt])

		with gr.Column(scale=0):
			model_rescan_button = gr.Button("Rescan Comfy Models.", scale=1, size="sm")
			restart_socket_button = gr.Button("Reconnect ComfyUI WebSocket", elem_id="backend_reconnect_comfy", scale=1, size="sm")
		backend_dropdown = gr.Dropdown(["ComfyUI", "CAP"], label="Generation Backend:", value="ComfyUI", filterable=False, scale=1)

		def model_rescan_hook(backend):
			global clip_models
			global stage_b_models
			global stage_c_models
			#if backend == "ComfyUI":
			clip_models, stage_b_models, stage_c_models = cap_util.scan_for_comfy_models()
			return gr.Dropdown(choices=stage_c_models), gr.Dropdown(choices=stage_b_models), gr.Dropdown(choices=clip_models)
		model_rescan_button.click(model_rescan_hook, inputs=[backend_dropdown], outputs=[stage_c_ckpt, stage_b_ckpt, clip_ckpt])

		def restart_websocket():
			comfy_ws_addr = cap_util.get_websocket_address()
			try:
				cap_util.ws.ping()
			except:
				pass

			cap_util.ws.close()
			try:
				cap_util.ws.connect(comfy_ws_addr)
			except:
				raise gr.Error("ComfyUI does not appear to be available at that address and port.\nTry checking ComfyUI's settings.")
			gr.Info("Successfully reconnected to ComfyUI!")

		restart_socket_button.click(restart_websocket, inputs=None, outputs=None)

	with gr.Tab("Text to Image", elem_id="tab_txt2img"):
		with gr.Row(elem_id="topbar"):
			with gr.Column(scale=6, elem_id="prompts"):
				txt_pos_prompt = gr.Textbox(label=None, show_label=False, placeholder="Enter a prompt here.", lines=3)
				txt_neg_prompt = gr.Textbox(label=None, show_label=False, placeholder="Enter a negative prompt here.", lines=3)
			with gr.Column(elem_id="buttons"):
				txt_generate = gr.Button("Generate!", variant="primary", elem_id="generate_txt2img")
				txt_rec_last_prompt = gr.Button("Load Last Generation", elem_id="reload_txt2img")
				txt_send_to_img2img = gr.Button("Send to Image to Image", elem_id="s2img_txt2img")
				txt_send_to_inpaint = gr.Button("Send to Inpainting", elem_id="s2inp_txt2img")
		with gr.Row(elem_id="tabcontent"):
			with gr.Column(scale=1, elem_id="gen_settings"):
				with gr.Accordion(label="Base Settings:", open=False):
					with gr.Column():
						with gr.Row():
							txt_stage_c_steps = gr.Slider(
								minimum=cap_util.gui_default_settings["gen_c_steps_min"],
								maximum=cap_util.gui_default_settings["gen_c_steps_max"],
								value=cap_util.gui_default_settings["gen_c_steps"],
								step=cap_util.gui_default_settings["gen_c_steps_step"],
								scale=10, label="Steps:", interactive=True,
							)
							txt_stage_c_seed = gr.Number(value=-1, minimum=-1, maximum=2147483647, precision=0, label="Seed:", scale=2, interactive=True,)
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
								label="CFG:", interactive=True, scale=5
							)
							txt_stage_c_batch = gr.Slider(
								minimum=cap_util.gui_default_settings["gen_batch_size_min"],
								maximum=cap_util.gui_default_settings["gen_batch_size_max"],
								value=cap_util.gui_default_settings["gen_batch_size"],
								step=cap_util.gui_default_settings["gen_batch_size_step"],
								label="Batch Size:", interactive=True, scale=2
							)
						with gr.Column(scale=4):
							txt_stage_c_width = gr.Slider(
								minimum=cap_util.gui_default_settings["gen_size_min"],
								maximum=cap_util.gui_default_settings["gen_size_max"],
								value=cap_util.gui_default_settings["gen_size"],
								step=cap_util.gui_default_settings["gen_size_step"],
								label="Width:", interactive=True,
							)
							txt_stage_c_height = gr.Slider(
								minimum=cap_util.gui_default_settings["gen_size_min"],
								maximum=cap_util.gui_default_settings["gen_size_max"],
								value=cap_util.gui_default_settings["gen_size"],
								step=cap_util.gui_default_settings["gen_size_step"],
								label="Height:", interactive=True
								)

							txt_stage_c_compression = gr.Slider(
									minimum=32,
									maximum=42,
									value=cap_util.gui_default_settings["gen_compression"],
									step=1,
									label="Compression:", interactive=True
							)

				with gr.Accordion(label="Refiner Settings:", open=False):
					gr.Markdown("These settings are for the Stage B portion of Stable Cascade.\n\nIt's advised that you don't touch these - but if an image seems to come out wrong or has some kind of artifacting, try changing these settings.\n\nYou have been warned.")
					txt_stage_b_seed = gr.Number(value=-1, minimum=-1, maximum=2147483647, precision=0, label="Seed:", scale=2, interactive=True)
					txt_stage_b_cfg = gr.Slider(
						minimum=cap_util.gui_default_settings["gen_b_cfg_min"],
						maximum=cap_util.gui_default_settings["gen_b_cfg_max"],
						value=cap_util.gui_default_settings["gen_b_cfg"],
						step=cap_util.gui_default_settings["gen_b_cfg_step"],
						label="Refiner Steps:", interactive=True
					)
					txt_stage_b_steps = gr.Slider(
						minimum=cap_util.gui_default_settings["gen_b_steps_min"],
						maximum=cap_util.gui_default_settings["gen_b_steps_max"],
						value=cap_util.gui_default_settings["gen_b_steps"],
						step=cap_util.gui_default_settings["gen_b_steps_step"],
						label="Refiner Steps:", interactive=True
					)

				with gr.Accordion(label="Extras:", open=False):
					gr.Markdown("Soon")

			with gr.Column():
				txt_gallery = gr.Gallery(allow_preview=True, preview=True, show_download_button=True, object_fit="contain", show_label=False, label=None, elem_id="txt2img_gallery", height="70vh")
				with gr.Accordion("Generation Info:", open=True):
					txt_gen_info_box = gr.Markdown("")

		# Internal self contained tab functions go here:
		txt_stage_c_swap_aspects.click(cap_util.swap_width_height, inputs=[txt_stage_c_height, txt_stage_c_width], outputs=[txt_stage_c_height, txt_stage_c_width])
		txt_generate.click(cap_util.process_basic_txt2img, inputs=[
			txt_pos_prompt, txt_neg_prompt, txt_stage_c_steps, txt_stage_c_seed,
			txt_stage_c_width, txt_stage_c_height, txt_stage_c_cfg, txt_stage_c_batch,
			txt_stage_c_compression, txt_stage_b_seed, txt_stage_b_cfg, txt_stage_b_steps, 
			stage_b_ckpt, stage_c_ckpt, clip_ckpt, backend_dropdown
		], outputs=[txt_gallery, txt_gen_info_box])

	with gr.Tab("Image to Image", elem_id="tab_img2img"):
		gr.Markdown("Soon")
		# Internal self contained tab functions go here:
	
	with gr.Tab("Inpainting", elem_id="tab_inpainting"):
		gr.Markdown("Soon")
		# Internal self contained tab functions go here:

	with gr.Tab("Settings", elem_id="tab_settings"):
		with gr.Accordion(label="ComfyUI Settings:", open=False):
			gr.Markdown("The IP address of your ComfyUI instance.")
			setting_comfyui_addr = gr.Textbox(value=cap_util.gui_default_settings["comfy_address"], label="ComfyUI IP Address:", interactive=True)
			gr.Markdown("The networking port of your ComfyUI instance, this is the same as it's Node Editor webpage.")
			setting_comfyui_port = gr.Textbox(value=cap_util.gui_default_settings["comfy_port"], label="ComfyUI Port:", interactive=True)
			gr.Markdown("Where your local instance of ComfyUI is located.")
			setting_comfyui_path = gr.Textbox(value=cap_util.gui_default_settings["comfy_path"], label="ComfyUI Path:", interactive=True)
			with gr.Row():
				with gr.Column():
					setting_install_models = gr.Button("Install Cascade Models for ComfyUI.", variant="secondary")
					gr.Markdown("Download and install all related models such as ControlNet, Stage Bs, Stage A and the base models.")
					gr.Markdown("**20GB of space is required on the destination storage device.**")
					gr.Markdown("**Clicking Install will save all unsaved ComfyUI setting changes.**")
					def comfy_install_hook(comfy_addr, comfy_port, comfy_path):
						comfy_connector_changed = False
						if comfy_addr != cap_util.gui_default_settings["comfy_address"]:
							comfy_connector_changed = True
						if comfy_port != cap_util.gui_default_settings["comfy_port"]:
							comfy_connector_changed = True
						
						# Save ComfyUI changes
						if comfy_connector_changed:
							cap_util.gui_default_settings["comfy_address"] = comfy_addr
							cap_util.gui_default_settings["comfy_port"] = comfy_port

						if comfy_connector_changed:
							cap_util.ws.close()
							try:								
								cap_util.ws.connect(cap_util.get_websocket_address())
							except Exception as e:
								raise gr.Error("Invalid ComfyUI port and/or address - cannot connect.")
						
						rescan_model_folders = False
						global clip_models
						global stage_b_models
						global stage_c_models
						clip_models, stage_b_models, stage_c_models = [], [], []
						if comfy_path != cap_util.gui_default_settings["comfy_path"]:
							rescan_model_folders = True
							clip_models, stage_b_models, stage_c_models = cap_util.scan_for_comfy_models()
						
						cap_util.gui_default_settings["comfy_path"] = comfy_path
						if rescan_model_folders or comfy_connector_changed:
							cap_util.save_config()

						cap_util.install_CAPGUI_nodes()
						cap_util.download_cascade_models()
						clip_models, stage_b_models, stage_c_models = cap_util.scan_for_comfy_models()

						return gr.Dropdown(choices=stage_c_models), gr.Dropdown(choices=stage_b_models), gr.Dropdown(choices=clip_models)
					setting_install_models.click(comfy_install_hook, 
						inputs=[setting_comfyui_addr, setting_comfyui_port, setting_comfyui_path],
						outputs=[stage_c_ckpt, stage_b_ckpt, clip_ckpt], 
					)
						
				with gr.Column():
					setting_rescan_local_models = gr.Button("Rescan for Cascade Models.", variant="secondary")
					gr.Markdown("Rescans all models in the ComfyUI folders to be used. Does not save and use modified settings.\n\nSubfolders within the 'cascade' subfolder are not supported at this time.")
					def rescan_local_models_hook():
						global clip_models
						global stage_b_models
						global stage_c_models

						clip_models, stage_b_models, stage_c_models = cap_util.scan_for_comfy_models()
						return gr.Dropdown(choices=stage_c_models), gr.Dropdown(choices=stage_b_models), gr.Dropdown(choices=clip_models)
					setting_rescan_local_models.click(rescan_local_models_hook, inputs=None, outputs=[stage_c_ckpt, stage_b_ckpt, clip_ckpt])

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

	gr.Markdown(f"CAP App Prototype")
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
app.launch(server_port=6969, allowed_paths=[os.getcwd()])