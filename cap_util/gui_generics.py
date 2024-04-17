# This file is used for importing the generic GUI pieces such as the Generate button
import cap_util
import gradio as gr

# Components that are shared or common to multiple tabs
# these usually do not come with functions

def get_pos_prompt_box():
	return gr.Textbox(label=None, show_label=False, placeholder="Enter a prompt here.", lines=3)

def get_neg_prompt_box():
	return gr.Textbox(label=None, show_label=False, placeholder="Enter a negative prompt here.", lines=3)

def get_generate_button(local_ctx):
	return gr.Button("Generate!", variant="primary", elem_id=f"generate_{local_ctx['__tabname__']}")

def get_load_last_button():
	return gr.Button("Load Last Generation", elem_id="reload_txt2img")

def get_send_to_button():
	return gr.Button("Send to Selected Tab.", elem_id="send2tab")

def get_send_to_dropdown(global_ctx):
	# Get a list of tabs used for generation
	send_to_targets = []
	known_tabs = global_ctx.keys()
	for tab in known_tabs:
		if "__send_to__" in known_tabs:
			if known_tabs[tab]["__send_to__"]:
				send_to_targets.append(known_tabs[tab]["__friendly_name__"])

	dropdown = gr.Dropdown(send_to_targets, filterable=False, label="Send To Tab:")

	return dropdown

def get_prompt_row(global_ctx, local_ctx, prompt_scale):
	with gr.Row(elem_id="promptbar"):
		with gr.Column(scale=prompt_scale):
			local_ctx["pos_prompt"] = get_pos_prompt_box()
			local_ctx["neg_prompt"] = get_neg_prompt_box()
		with gr.Column(elem_id="buttons"):
			local_ctx["generate"] = get_generate_button(local_ctx)
	pass

def get_generation_column(global_ctx, local_ctx):

	pass