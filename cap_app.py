import os
import cap_util
from cap_util import gui_generics
from cap_gui import txt
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

def register_tab(global_tabs, post_hooks, tab_name, friendly_name, tab_code_function, post_tab_code_function, send_to_state, available):
	# Do not create tabs where they may not be availble, such as Anonymous Mode.
	if not available:
		return

	global_tabs[tab_name] = {}
	global_tabs[tab_name]["__send_to__"] = send_to_state
	global_tabs[tab_name]["__tab_name__"] = tab_name
	global_tabs[tab_name]["__name_pair__"] = (tab_name, friendly_name)
	global_tabs[tab_name]["__friendly_name__"] = friendly_name
	global_tabs[tab_name]["tab_ref"] = gr.Tab(label=friendly_name, elem_id=f"tab_{tab_name}")
	with global_tabs[tab_name]["tab_ref"]:
		tab_code_function(global_tabs, global_tabs[tab_name])
	# Run this code later at the end of tab registering
	post_hooks.append((post_tab_code_function, global_tabs, global_tabs[tab_name]))

with gr.Blocks(title=f"{'[ANON MODE] ' if cap_util.gui_default_settings['ui_anonymous_mode'] else ''}CAP App", analytics_enabled=False, css="custom_css.css") as app:
	post_hooks = []
	global_tabs = {}
	topbar.create_topbar(global_tabs, stage_c_models, stage_c_default, stage_b_models, stage_b_default, clip_models, clip_default)

	# with gr.Tab("Image to Image", elem_id="tab_img2img"):
	# 	gr.Markdown("Soon")
	# 	# Internal self contained tab functions go here:
	
	# with gr.Tab("Inpainting", elem_id="tab_inpainting"):
	# 	gr.Markdown("Soon")
	# 	# Internal self contained tab functions go here:

	# if not cap_util.gui_default_settings["ui_anonymous_mode"]:
	# 	with gr.Tab("Gallery", elem_id="tab_gallery"):
	# 		gr.Markdown("Soon")

	# with gr.Tab("Settings", elem_id="tab_settings"):
	# 	with gr.Accordion(label="Community AI Platform Settings:", open=False):
	# 		gr.Markdown("soon")
	# 	with gr.Accordion(label="Generation Settings:", open=False):
	# 		gr.Markdown("Change these defaults if you know what you're doing!")
	# 	with gr.Accordion(label="GUI Settings:", open=False):
	# 		gr.Markdown("soon")
	# 	gr.Markdown("Other Settings:")
	# 	gr.Markdown("**Note: Changes will be used after saving.**")
	# 	setting_save_changes = gr.Button("Save Configuration Changes.", variant="primary")
		
	# 	gr.Markdown("Soon")
	# 	# Internal self contained tab functions go here:

	# with gr.Tab("Hints and Tips", elem_id="tab_hints"):
	# 	gr.Markdown("Soon")
	# 	# Internal self contained tab functions go here:

	# with gr.Tab("Community", elem_id="tab_community"):
	# 	gr.Markdown("Soon")
	# 	# Internal self contained tab functions go here:

	# Register tabs here
	register_tab(global_tabs, post_hooks, "txt2img", "Text to Image", txt.txt2img_tab, txt.txt2img_tab_post_hook, True, True)

	# Gradio element Functions that work on the current and or other tabs go here:
	for func in post_hooks:
		func[0](func[1], func[2])

	# Update all Send to Tab dropdown lists:
	for key in global_tabs.keys():
		if "send_to_dropdown" in global_tabs[key]:
			if "send_to_button" in global_tabs[key]:
				# Check if the destination is the same as the source tab
				full_tab_list = gui_generics.send_to_targets(global_tabs)
				global_tabs[key]["send_to_dropdown"].choices = full_tab_list

	# Footer
	gr.Markdown(f"CAP App Prototype{', **GENERATIONS WILL NOT BE SAVED IN ANONYMOUS MODE!**' if cap_util.gui_default_settings['ui_anonymous_mode'] else ''}")

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