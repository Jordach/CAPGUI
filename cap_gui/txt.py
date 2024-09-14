# This file returns txt2img specific features
import gradio as gr
import cap_util
from cap_util import gui_generics, send_to_fns, gui_xy
from PIL import Image

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
	c_sampler, c_scheduler, b_sampler, b_scheduler, c_rescale,
	use_hr_fix, hr_resize, hr_compression, hr_denoise, hr_save, hr_show
):
	tab_src = "txt2img"
	if xy_x_type != 'None' or xy_y_type != 'None':
		return gui_xy.process_xy_images(
			pos, neg, c_steps, c_seed, width, height,
			c_cfg, batch, compression, shift, latent_id,
			b_seed, b_cfg, b_steps, stage_b, stage_c,
			clip, backend, use_hq_stage_a, save_images,
			xy_x_string, xy_x_dropdown, xy_x_type, xy_y_string, xy_y_dropdown, xy_y_type,
			c_sampler, c_scheduler, b_sampler, b_scheduler, c_rescale,
		)
	elif not use_hr_fix:
		return cap_util.process_basic_txt2img(
			"txt2img_grid", pos, neg, c_steps, c_seed, width, height,
			c_cfg, batch, compression, shift, latent_id,
			b_seed, b_cfg, b_steps, stage_b, stage_c,
			clip, backend, use_hq_stage_a, save_images,
			c_sampler, c_scheduler, b_sampler, b_scheduler,
			c_rescale
		)
	else:
		images, info, infodict = cap_util.process_basic_txt2img(
			tab_src, pos, neg, c_steps, c_seed, width, height,
			c_cfg, 1, compression, shift, latent_id,
			b_seed, b_cfg, b_steps, stage_b, stage_c,
			clip, backend, use_hq_stage_a, hr_save,
			c_sampler, c_scheduler, b_sampler, b_scheduler,
			c_rescale
		)
		if isinstance(images[0], str):
			img = Image.open(images[0], mode="r")
		else:
			img = images[0]
		
		w, h = int(img.width * hr_resize), int(img.height * hr_resize)
		step = cap_util.gui_default_settings["gen_size_step"]
		w = (w // step) * step
		h = (h // step) * step

		gr.Info("Running Hi-Res Fix / Refining Pass, this may take a while.")
		hr_images, hr_info, hr_infodict = cap_util.process_basic_img2img(
			tab_src, img, False, cap_util.img2img_crop_types[0], pos, neg,
			c_steps, c_seed, w, h, c_cfg, batch, hr_compression,
			shift, latent_id, b_seed, b_cfg, b_steps, stage_b, stage_c,
			clip, backend, hr_denoise, use_hq_stage_a, save_images,
			c_sampler, c_scheduler, b_sampler, b_scheduler, c_rescale
		)

		all_images = []
		if hr_show:
			all_images.append(img)
		all_images.extend(hr_images)
		return all_images, info, infodict

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
			local_ctx["stage_c_sampler"], local_ctx["stage_c_scheduler"], local_ctx["stage_b_sampler"], local_ctx["stage_b_scheduler"],
			local_ctx["stage_c_rescale"], local_ctx["hi_res_enabled"], local_ctx["hi_res_resize"], local_ctx["hi_res_compression"],
			local_ctx["hi_res_denoise"], local_ctx["hi_res_save_original"], local_ctx["hi_res_show_original"]
		],
		outputs=[local_ctx["gallery"], local_ctx["gen_info_box"], local_ctx["gen_json"]],
		show_progress="minimal", concurrency_id="system_queue"
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
			local_ctx["stage_c_sampler"], local_ctx["stage_c_scheduler"], local_ctx["stage_b_sampler"], local_ctx["stage_b_scheduler"],
			local_ctx["stage_c_rescale"]
		], show_progress="minimal", trigger_mode="once", queue=False,
	)