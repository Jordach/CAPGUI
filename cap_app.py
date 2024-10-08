import os
import cap_util
from cap_util import gui_generics
from cap_gui import txt, img, inpainting, tools, donate, settings
import websocket
import uuid
import gradio as gr
from packaging import version
# Do not start up with older Gradio versions
if version.parse(gr.__version__) < version.parse("4.42"):
	raise ValueError("Your installed version of Gradio is too old, please update Gradio via updates_requirements.bat or running ' pip install -r requirements.txt ' inside this directory. Sorry about that.")

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

def register_tab(g_tabs, p_hooks, tab_name, friendly_name, tab_code_function, post_tab_code_function, send_to_state, image_send_to, available):
	# Do not create tabs where they may not be availble, such as Anonymous Mode.
	if not available:
		return

	g_tabs[tab_name] = {}
	g_tabs[tab_name]["__send_to__"] = send_to_state
	g_tabs[tab_name]["image_send_to"] = image_send_to
	g_tabs[tab_name]["__tab_name__"] = tab_name
	g_tabs[tab_name]["__name_pair__"] = (friendly_name, tab_name)
	g_tabs[tab_name]["__friendly_name__"] = friendly_name
	g_tabs[tab_name]["tab_ref"] = gr.Tab(label=friendly_name, elem_id=f"tab_{tab_name}")
	with g_tabs[tab_name]["tab_ref"]:
		tab_code_function(global_tabs, global_tabs[tab_name])
	# Run this code later at the end of tab registering
	p_hooks.append((post_tab_code_function, g_tabs, g_tabs[tab_name]))

with gr.Blocks(title=f"{'[ANON MODE] ' if cap_util.gui_default_settings['ui_anonymous_mode'] else ''}CAP App", analytics_enabled=False, ) as app:
	post_hooks = []
	global_tabs = {}
	topbar.create_topbar(global_tabs, stage_c_models, stage_c_default, stage_b_models, stage_b_default, clip_models, clip_default)

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
	register_tab(global_tabs, post_hooks, "txt2img", "Text to Image", txt.txt2img_tab, txt.txt2img_tab_post_hook, True, False, True)
	register_tab(global_tabs, post_hooks, "img2img", "Image to Image", img.img2img_tab, img.img2img_tab_post_hook, True, True, True)
	register_tab(global_tabs, post_hooks, "inpaint", "Inpainting", inpainting.inpaint_tab, inpainting.inpaint_tab_post_hook, True, True, True)
	register_tab(global_tabs, post_hooks, "tools", "Tools", tools.tools_tab, tools.tools_tab_post_hook, False, False, True)
	register_tab(global_tabs, post_hooks, "settings", "Settings", settings.settings_tab, gui_generics.dummy_post_hook, False, False, True)
	register_tab(global_tabs, post_hooks, "donate", "Donate", donate.donate_tab, gui_generics.dummy_post_hook, False, False, True)
	# Special: Handle the quick access topbar:
	post_hooks.append((topbar.topbar_post_hook, global_tabs, global_tabs["topbar"]))
	# Gradio element Functions that work on the current and or other tabs go here:
	for func in post_hooks:
		func[0](func[1], func[2])

	# Update all Send to Tab dropdown lists:
	for tab in global_tabs.keys():
		if "send_to_dropdown" in global_tabs[tab] and "send_to_button" in global_tabs[tab]:
				# Check if the destination is the same as the source tab
				full_tab_list = gui_generics.send_to_targets(global_tabs, tab)
				global_tabs[tab]["send_to_dropdown"].choices = full_tab_list
				global_tabs[tab]["send_to_dropdown"].value = full_tab_list[0][1]

	# Footer
	gr.Markdown(f"CAP App{', **GENERATIONS WILL NOT BE SAVED IN ANONYMOUS MODE!**' if cap_util.gui_default_settings['ui_anonymous_mode'] else ''}")

# Magical stuff to make basic keybinds and JavaScript that need the full DOM work,
# this is atrocious and should probably be made part of the gradio library to append
# the <head> and <body> headers respectively.
if not hasattr(cap_util, "gradio_response_header"):
	cap_util.gradio_response_header = gr.routes.templates.TemplateResponse

appended_script = f'''<script type="text/javascript" src="file=custom_js.js?{os.path.getmtime("custom_js.js")}"></script>
<link rel="stylesheet" href="file=custom_css.css?{os.path.getmtime("custom_css.css")}">
<script type="text/javascript" src="file=autocomplete/util.js?{os.path.getmtime("autocomplete/util.js")}"></script>
<script type="text/javascript" src="file=autocomplete/tagcomplete.js?{os.path.getmtime("autocomplete/tagcomplete.js")}"></script>
<link rel="stylesheet" href="file=autocomplete/tagcomplete.css?{os.path.getmtime("autocomplete/tagcomplete.css")}">
'''

def new_resp(*args, **kwargs):
	new_response = cap_util.gradio_response_header(*args, **kwargs)
	new_response.body = new_response.body.replace(b'</head>', f"{appended_script}</head>".encode("utf8"))
	new_response.init_headers()
	return new_response

gr.routes.templates.TemplateResponse = new_resp
local_wd = os.getcwd()
print(f"Current Working Dir: {local_wd}")
app.launch(server_port=6969, server_name="0.0.0.0", allowed_paths=[local_wd])