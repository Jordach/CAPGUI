# This file returns txt2img specific features
import gradio as gr
import cap_util
from cap_util import gui_generics, send_to_fns, gui_xy
from cap_util.wildcards import read_and_apply_wildcards
from PIL import Image
import time

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
		img, info, infodict = gui_xy.process_xy_images(
			tab_src+"_grid", pos, neg, c_steps, c_seed, width, height,
			c_cfg, batch, compression, shift, latent_id,
			b_seed, b_cfg, b_steps, stage_b, stage_c,
			clip, backend, use_hq_stage_a, save_images,
			xy_x_string, xy_x_dropdown, xy_x_type, xy_y_string, xy_y_dropdown, xy_y_type,
			c_sampler, c_scheduler, b_sampler, b_scheduler, c_rescale,
		)

		yield img, info, infodict
	elif use_hr_fix:
		# Ensure that wildcards compile down into a single instance
		new_pos, new_neg = read_and_apply_wildcards(pos, neg)
		
		images, info, infodict = cap_util.process_basic_txt2img(
			tab_src, new_pos, new_neg, c_steps, c_seed, width, height,
			c_cfg, batch, compression, shift, latent_id,
			b_seed, b_cfg, b_steps, stage_b, stage_c,
			clip, backend, use_hq_stage_a, hr_save,
			c_sampler, c_scheduler, b_sampler, b_scheduler,
			c_rescale
		)

		b_imgs = []
		temp_images = []
		for image in images:
			if isinstance(image, str):
				img = Image.open(image, mode="r")
			else:
				img = image
			temp_images.append(img)
			b_imgs.append(img)

		info += f" (Original Batch)\n"
		yield images, info, infodict
		
		w, h = int(img.width * hr_resize), int(img.height * hr_resize)
		step = 32
		w = (w // step) * step
		h = (h // step) * step

		gr.Info("Running Hi-Res Fix / Refining Pass, this may take a while.")
		timer_start = time.time()
		all_hr = []
		for b_img in b_imgs:
			hr_images, hr_info, hr_infodict = cap_util.process_basic_img2img(
				tab_src, b_img, False, cap_util.img2img_crop_types[0], new_pos, new_neg,
				c_steps, c_seed, w, h, c_cfg, 1, hr_compression,
				shift, latent_id, b_seed, b_cfg, b_steps, stage_b, stage_c,
				clip, backend, hr_denoise, use_hq_stage_a, save_images,
				c_sampler, c_scheduler, b_sampler, b_scheduler, c_rescale
			)
			temp_images.extend(hr_images)
			all_hr.extend(hr_images)
			yield temp_images, info, infodict
		
		if batch > 1:
			timer_finish_avg = f"{(time.time()-timer_start)/batch:.2f}"
			info += f"Hi-Res Fix / Refining Pass Average Time: **{timer_finish_avg}s**\n"
		timer_finish_total = f"{time.time()-timer_start:.2f}"
		info += f"Hi-Res Fix / Refining Pass Total Time: **{timer_finish_total}s**"
		all_images = []
		if hr_show:
			all_images.extend(images)
		all_images.extend(all_hr)
		yield all_images, info, infodict
	else:
		yield cap_util.process_basic_txt2img(
			tab_src, pos, neg, c_steps, c_seed, width, height,
			c_cfg, batch, compression, shift, latent_id,
			b_seed, b_cfg, b_steps, stage_b, stage_c,
			clip, backend, use_hq_stage_a, save_images,
			c_sampler, c_scheduler, b_sampler, b_scheduler,
			c_rescale
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