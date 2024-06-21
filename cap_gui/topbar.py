import cap_util
import os
import gradio as gr

# Components in a fixed, static position 
def get_stage_c_dropdown(stage_c, default):
	sc_dropdown = gr.Dropdown(
		stage_c, filterable=False,
		value=default, label="Cascade Base Model:", scale=1
	)

	def save_sc_ckpt(v):
		cap_util.gui_default_settings["comfy_stage_c"] = v
		cap_util.save_config()
	
	sc_dropdown.input(save_sc_ckpt, inputs=[sc_dropdown])
	return sc_dropdown

def get_clip_dropdown(clip, default):
	clip_dropdown = gr.Dropdown(
		clip, filterable=False,
		value=default, label="Cascade Text Model:", scale=1
	)

	def save_clip_ckpt(v):
		cap_util.gui_default_settings["comfy_clip"] = v
		cap_util.save_config()

	clip_dropdown.input(save_clip_ckpt, inputs=[clip_dropdown])
	return clip_dropdown

def get_stage_b_dropdown(stage_b, default):
	sb_dropdown = gr.Dropdown(
		stage_b, filterable=False,
		value=default, label="Cascade Refiner Model:", scale=1
	)

	def save_sb_ckpt(v):
		cap_util.gui_default_settings["comfy_stage_b"] = v
		cap_util.save_config()

	sb_dropdown.input(save_sb_ckpt, inputs=[sb_dropdown])
	return sb_dropdown

def get_model_refresh_button(local_ctx):
	button = gr.Button("Refresh ComfyUI Models.", scale=1, size="sm")
	def refresh_models(ctx=None):
		clip, stage_b, stage_c = cap_util.scan_for_comfy_models()
		return gr.Dropdown(choices=stage_c), gr.Dropdown(choices=stage_b), gr.Dropdown(choices=clip)
	button.click(refresh_models, inputs=[local_ctx["backend"]] if "backend" in local_ctx else None, outputs=[local_ctx["stage_c"], local_ctx["stage_b"], local_ctx["clip"]])
	return button

def get_restart_websocket_button():
	button = gr.Button("Restart ComfyUI WebSocket.", scale=1, size="sm")
	def restart_socket():
		comfy_ws = cap_util.get_websocket_address()
		try:
			cap_util.ws.ping()
		except:
			pass

		cap_util.ws.close()
		try:
			cap_util.ws.connect(comfy_ws)
		except:
			raise gr.Error("ComfyUI does not appear to be available at that address and port.\nTry checking settings or that ComfyUI is running.")
		gr.Info("Successfully reconnected to ComfyUI!")
	button.click(restart_socket, inputs=None, outputs=None)
	return button

def get_autocomplete_dropdown(global_ctx):
	csvs = cap_util.search_for_csvs()
	dropdown = gr.Dropdown(csvs, label="Auto Complete CSV:", value=cap_util.gui_default_settings["tac_tagFile"], filterable=False, allow_custom_value=False)

	return dropdown

def save_auto_csv_changes(autocomplete):
	# Don't update the settings_json field if we're just updating the list
	if autocomplete == "updating_the.csv":
		csvs = cap_util.search_for_csvs()
		return gr.Textbox(), gr.Dropdown(choices=csvs, value=cap_util.gui_default_settings["tac_tagFile"])

	cap_util.gui_default_settings["tac_tagFile"] = autocomplete
	cap_util.save_config(backup=False)
	return cap_util.create_settings_json_for_browser(), gr.Dropdown()

def create_topbar(global_ctx, sc_m, sc_d, sb_m, sb_d, cl_m, cl_d):
	global_ctx["topbar"] = {}
	global_ctx["topbar"]["__tab_name__"] = "quicksettings_header"
	global_ctx["topbar"]["__send_to__"] = False
	global_ctx["topbar"]["__friendly_name__"] = "QuickSettings Header"
	with gr.Row(elem_id="model_select"):
		global_ctx["topbar"]["stage_c"] = get_stage_c_dropdown(sc_m, sc_d)
		global_ctx["topbar"]["clip"] = get_clip_dropdown(cl_m, cl_d)
		global_ctx["topbar"]["stage_b"] = get_stage_b_dropdown(sb_m, sb_d)

		with gr.Column(scale=0):
			global_ctx["topbar"]["model_rescan"] = get_model_refresh_button(global_ctx["topbar"])
			global_ctx["topbar"]["restart_websocket"] = get_restart_websocket_button()
		global_ctx["topbar"]["autocomplete_csv"] = get_autocomplete_dropdown(global_ctx)

def topbar_post_hook(global_ctx, local_ctx):
	local_ctx["autocomplete_csv"].input(
		save_auto_csv_changes, 
		inputs=global_ctx["topbar"]["autocomplete_csv"],
		outputs=[global_ctx["settings"]["settings_json"], local_ctx["autocomplete_csv"]]
	)