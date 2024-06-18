# This file returns settings tab related features

import gradio as gr
import json
import cap_util

# Add keys here for the browser to be entirely unaware of
# This means that misbehaving clients cannot peer into other memory secrets from JavaScript
banned_settings_values = {
	"cap_login_expiry": True,
	"cap_login_token": True,
	"cap_use_cap_workers": True,
	"comfy_address": True,
	"comfy_path": True,
	"comfy_port": True,
	"comfy_uuid": True,
	"ui_anonymous_mode": True
}

def create_settings_json_for_browser():
	keys = cap_util.gui_default_settings.keys()
	output_dict = {}
	for key in keys:
		if key in banned_settings_values:
			continue
		output_dict[key] = cap_util.gui_default_settings[key]

	return json.dumps(output_dict)

def settings_tab(global_ctx, local_ctx):
	with gr.Accordion("Tag Auto Complete:"):
		gr.Markdown("soon")
	with gr.Accordion("GUI Startup Defaults:"):
		gr.Markdown("soon")
	gr.Markdown("soon")
	local_ctx["settings_json"] = gr.Textbox(create_settings_json_for_browser(), elem_id="settings_json", visible=True)
	pass