# This file returns img2img specific features
import gradio as gr
import cap_util
from cap_util import gui_generics

def img2img_tab(global_ctx, local_ctx):
	gui_generics.get_prompt_row(global_ctx, local_ctx, 6)
	with gr.Row():
		with gr.Column(scale=1):
			local_ctx["stage_c_image_source"] = gr.Image(None, type="pil", image_mode="RGB", label="Input Image:", show_download_button=False,)
			gui_generics.get_generation_settings_column(global_ctx, local_ctx)
		with gr.Column():
			gui_generics.get_gallery_column(global_ctx, local_ctx)

# This sets up the functions like the generate button after elements have been initialised
def img2img_tab_post_hook(global_ctx, local_ctx):
	local_ctx["generate"].click(
		cap_util.process_basic_img2img,
		inputs = [
			local_ctx["pos_prompt"],          local_ctx["neg_prompt"],     local_ctx["stage_c_steps"], local_ctx["stage_c_seed"],
			local_ctx["stage_c_width"],       local_ctx["stage_c_height"], local_ctx["stage_c_cfg"],   local_ctx["stage_c_batch"],
			local_ctx["stage_c_compression"], local_ctx["stage_c_shift"],  local_ctx["stage_c_single_latent"],
			local_ctx["stage_b_seed"],        local_ctx["stage_b_cfg"],    local_ctx["stage_b_steps"],
			global_ctx["topbar"]["stage_b"], global_ctx["topbar"]["stage_c"], global_ctx["topbar"]["clip"], global_ctx["topbar"]["backend"],
		],
		outputs=[local_ctx["gallery"], local_ctx["gen_info_box"]],
		show_progress="minimal"
	)