# This file returns txt2img specific features
import gradio as gr
import cap_util
from cap_util import gui_generics, send_to_fns, gui_xy

def txt2img_tab(global_ctx, local_ctx):
	gui_generics.get_prompt_row(global_ctx, local_ctx, 6)
	with gr.Row():
		with gr.Column(scale=1):
			gui_generics.get_generation_settings_column(global_ctx, local_ctx)
		with gr.Column():
			gui_generics.get_gallery_column(global_ctx, local_ctx, "70vh", add_send_to_text=True)

# HEY YOU FUTURE PERSON - FUTURE GENERATION ARGS WILL BE SPLIT INTO DICTS:
# common =     {pos, neg, width, height, input_image, batch, backend, ...}
# c_sampling = {steps, seed, cfg, sampler, schedule, shift}
# b_sampling = {steps, seed, cfg, sampler, schedule}
# models =     {stage_c, stage_b, clip, stage_a_hq_flag}
def process_generate_button(
	pos, neg, c_steps, c_seed, width, height,
	c_cfg, batch, compression, shift, latent_id,
	b_seed, b_cfg, b_steps, stage_b, stage_c,
	clip, backend, use_hq_stage_a, save_images,
	xy_x_string, xy_x_dropdown, xy_x_type, xy_y_string, xy_y_dropdown, xy_y_type,
	c_sampler, c_scheduler, b_sampler, b_scheduler
):
	if xy_x_type != 'None' or xy_y_type != 'None':
		return gui_xy.process_xy_images(
			pos, neg, c_steps, c_seed, width, height,
			c_cfg, batch, compression, shift, latent_id,
			b_seed, b_cfg, b_steps, stage_b, stage_c,
			clip, backend, use_hq_stage_a, save_images,
			xy_x_string, xy_x_dropdown, xy_x_type, xy_y_string, xy_y_dropdown, xy_y_type,
			c_sampler, c_scheduler, b_sampler, b_scheduler
		)
	else:
		return cap_util.process_basic_txt2img(
			pos, neg, c_steps, c_seed, width, height,
			c_cfg, batch, compression, shift, latent_id,
			b_seed, b_cfg, b_steps, stage_b, stage_c,
			clip, backend, use_hq_stage_a, save_images,
			c_sampler, c_scheduler, b_sampler, b_scheduler
		)

# This sets up the functions like the generate button after elements have been initialised
def txt2img_tab_post_hook(global_ctx, local_ctx):
	local_ctx["generate"].click(
		process_generate_button,
		inputs = [
			local_ctx["pos_prompt"],          local_ctx["neg_prompt"],     local_ctx["stage_c_steps"], local_ctx["stage_c_seed"],
			local_ctx["stage_c_width"],       local_ctx["stage_c_height"], local_ctx["stage_c_cfg"],   local_ctx["stage_c_batch"],
			local_ctx["stage_c_compression"], local_ctx["stage_c_shift"],  local_ctx["stage_c_single_latent"],
			local_ctx["stage_b_seed"],        local_ctx["stage_b_cfg"],    local_ctx["stage_b_steps"],
			global_ctx["topbar"]["stage_b"], global_ctx["topbar"]["stage_c"], global_ctx["topbar"]["clip"], global_ctx["topbar"]["backend"],
			local_ctx["use_stage_a_hq"],      local_ctx["stage_c_save_images"],
			local_ctx["xy_x_string"],local_ctx["xy_x_dropdown"],local_ctx["xy_x_type"],local_ctx["xy_y_string"],local_ctx["xy_y_dropdown"],local_ctx["xy_y_type"],
			local_ctx["stage_c_sampler"], local_ctx["stage_c_scheduler"], local_ctx["stage_b_sampler"], local_ctx["stage_b_scheduler"]
		],
		outputs=[local_ctx["gallery"], local_ctx["gen_info_box"], local_ctx["gen_json"]],
		show_progress="minimal", 
	)

	local_ctx["send_to_button"].click(
		send_to_fns.send_to_tab,
		inputs=[local_ctx["send_to_dropdown"], local_ctx["gen_json"], local_ctx["gallery"], local_ctx["send_to_which_image"]],
		outputs=[global_ctx["txt2img"]["send_to_target"], global_ctx["img2img"]["send_to_target"], global_ctx["inpaint"]["send_to_target"]]
	)

	local_ctx["send_to_target"].change(
		send_to_fns.process_params,
		inputs=[],
		outputs=[
			local_ctx["pos_prompt"], local_ctx["neg_prompt"], local_ctx["stage_c_width"], local_ctx["stage_c_height"],
			local_ctx["stage_c_compression"], local_ctx["stage_c_auto_compressor"], local_ctx["stage_c_batch"], local_ctx["stage_c_single_latent"],
			local_ctx["stage_c_steps"], local_ctx["stage_c_seed"], local_ctx["stage_c_cfg"], local_ctx["stage_c_shift"],
			local_ctx["stage_b_steps"], local_ctx["stage_b_seed"], local_ctx["stage_b_cfg"],
			local_ctx["stage_c_sampler"], local_ctx["stage_c_scheduler"], local_ctx["stage_b_sampler"], local_ctx["stage_b_scheduler"]
		], show_progress="minimal", trigger_mode="once", queue=False,
	)