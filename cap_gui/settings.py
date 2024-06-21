# This file returns settings tab related features

import gradio as gr
import json
import cap_util
import random

def get_backend_dropdown():
	dropdown = gr.Dropdown(["ComfyUI", "CAP"], label="Generation Backend:", value="ComfyUI", filterable=False, scale=1)
	return dropdown

def settings_tab(global_ctx, local_ctx):
	local_ctx["settings_save_changes"] = gr.Button("Save Changes")
	with gr.Accordion("Tag Auto Complete:", open=False):
		gr.Markdown("soon")
	with gr.Accordion("GUI Startup Defaults:", open=False):
		gr.Markdown("soon")
	with gr.Accordion("Generation Backend:", open=False):
		global_ctx["topbar"]["backend"] = get_backend_dropdown()
	local_ctx["settings_json"] = gr.Textbox(cap_util.create_settings_json_for_browser(), elem_id="settings_json", visible=False)

	local_ctx["settings_save_changes"].click(cap_util.create_settings_json_for_browser, outputs=[local_ctx["settings_json"]]).then()