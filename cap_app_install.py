import cap_util
import cap_installer
import gradio as gr
import uuid
import websocket
import os
import argparse
import json
import time
import sys
parser = argparse.ArgumentParser(description="CAPGUI Gradio based installer.")
parser.add_argument("--gradio", default=False, action="store_true", help="Whether to use Gradio")
parser.add_argument("--update_nodes", default=False, action="store_true", help="Whether to just update the ComfyUI custom nodes required for CAPGUI.")
args = parser.parse_args()
exit_app = False
"""
Notes on model installation:

choices = {
	"stage_c_big":  True (Downloads the 3.6B base bf16 model and required clip model)
	"stage_c_lite": True (Downloads the 1B base bf16 model and required clip model)
	"reso_c_big"    True (Downloads the 3.6B Reso R1 model and required clip model)
	"reso_c_lite"   True (Downloads the 1B Reso R1 model and required clip model)
	"stage_b_big":  True (Downloads the larger refiner bf16 model)
	"stage_b_lite": True (Downloads the smaller refiner bf16 model)
	"controlnet":   True (Downloads the controlnet models)
	"misc":         True (Downloads the image to latent encoder and latent decoder)
}
"""

cap_util.load_config()

if "comfy_uuid" not in cap_util.gui_default_settings:
	# This is more cosmetic in nature and just provides a manner in which to use ComfyUI
	# without it forgetting who you are.
	cap_util.gui_default_settings["comfy_uuid"] = str(uuid.uuid4())
	cap_util.save_config()

if args.update_nodes:
	# Check for existence of certain ComfyUI pathings:
	comfy_install_state = cap_installer.test_comfyui_install(cap_util.gui_default_settings["comfy_path"])
	if comfy_install_state > 0:
		print(cap_installer.comfy_check_messages[comfy_install_state])
	else:
		cap_installer.install_CAPGUI_nodes()
		print("Please restart ComfyUI to use the updated nodes and features.")
elif args.gradio:
	with gr.Blocks(title="CAPGUI Easy Installer", analytics_enabled=False) as app:
		with gr.Accordion(label="ComfyUI Settings"):
			gui_comfy_path = gr.Textbox(label="ComfyUI Path:", lines=1, max_lines=1, value=cap_util.gui_default_settings["comfy_path"])
			gui_comfy_address = gr.Textbox(label="ComfyUI IP Address:", value=cap_util.gui_default_settings["comfy_address"], lines=1, max_lines=1)
			gui_comfy_port = gr.Textbox(label="ComfyUI Port:", lines=1, max_lines=1, value=cap_util.gui_default_settings["comfy_port"])
			validate_comfy_config = gr.Button("Test ComfyUI Path and WebSocket")
			validate_status = gr.Markdown("", label="Install Info:")
		
		download_models_accord = gr.Accordion(label="Download Chosen Models:", visible=False)
		with download_models_accord:
			gr.Markdown("# Base Models:\n\nThe requesite CLIP text model will also be downloaded as both share that model.")
			with gr.Column():
				casc_1b = gr.Checkbox(False, label="Stable Cascade 1B (3.3 GB Download)")
				casc_3b = gr.Checkbox(False, label="Stable Cascade 3.6B (8.3 GB Download)")
			gr.Markdown("## Resonance Prototype Delta/Epsilon:")
			with gr.Column():
				reso_proto = gr.Checkbox(False, label="Resonance Prototypes Delta + Epsilon")
			gr.Markdown("Custom Base Models Coming Soon.")
			with gr.Column():
				reso_1b = gr.Checkbox(False, label="Resonance R1 1B (3.3 GB Download)", interactive=False)
				reso_3b = gr.Checkbox(False, label="Resonance R1 3.6B (8.3 GB Download)", interactive=False)
			gr.Markdown("# Refiner Models:\n\nThe only difference between Refiner Large and Refiner Lite is that Refiner Large takes twice as long compared to Refiner Lite for not much difference in overall performance.")
			with gr.Column():
				ref_lite = gr.Checkbox(False, label="Refiner Lite (1.3 GB Download)")
				ref_large = gr.Checkbox(False, label="Refiner Large (3.05 GB Download)")
			
			gr.Markdown("# Other Models:")
			cn_models = gr.Checkbox(False, label="ControlNet Models (1.22 GB Download)")
			encoder_models = gr.Checkbox(True, label="Required Encoder/Decoder Models (151 MB Download)", interactive=False)
			gr.Markdown("# Model downloading may take a while based on your internet connection speed.")
			start_download = gr.Button("Start Download!")
			exit_installer = gr.Button("Exit Installer", variant="stop")

		def validate_comfyui_settings(path, address, port):
			# Check for existence of certain ComfyUI pathings:
			comfy_install_state = cap_installer.test_comfyui_install(path)
			if comfy_install_state > 0:
				return cap_installer.comfy_check_messages[comfy_install_state], gr.Accordion(visible=False)

			# Test ComfyUI websocket:
			ws = websocket.WebSocket()
			try:
				ws.connect(f"ws://{address}:{port}/ws?clientId={cap_util.gui_default_settings['comfy_uuid']}")
			except:
				return "Could not connect to ComfyUI, either ComfyUI is not running or ComfyUI is outdated and requires updating.", gr.Accordion(visible=False)

			# Validate that some firewall hasn't blocked it
			try:
				ws.ping()
			except:
				ws.close()
				return "Connection to ComfyUI lost. Please ensure ComfyUI is running or a firewall is blocking access.", gr.Accordion(visible=False)

			# Test websocket connection
			try:
				test_workflow = json.loads(cap_installer.get_test_workflow())
				images = cap_util.gen_images_websocket(ws, test_workflow)
				ws.close()
			except:
				return "Connection to ComfyUI lost or the example image is missing. Please ensure ComfyUI is running and that the example image exists.", gr.Accordion(visible=False)
			
			cap_util.gui_default_settings["comfy_path"] = path
			cap_util.gui_default_settings["comfy_address"] = address
			cap_util.gui_default_settings["comfy_port"] = port

			# Now that everything appears to work, save the config and install the custom nodes:
			cap_util.save_config(backup=False)
			cap_installer.install_CAPGUI_nodes()

			# Now allow the user to download models into their ComfyUI install.
			return "ComfyUI install is usable, and valid as a backend!", gr.Accordion(visible=True)

		validate_comfy_config.click(
			validate_comfyui_settings, 
			inputs=[gui_comfy_path, gui_comfy_address, gui_comfy_port], 
			outputs=[validate_status, download_models_accord]
		)

		def download_comfyui_models(c1b, c3b, res1b, res3b, reflite, refxl, cnet, encoders, respro):
			choices = {
				"stage_c_big":  c1b,
				"stage_c_lite": c3b,
				"reso_c_proto": respro,
				"reso_c_big":   res1b,
				"reso_c_lite":  res3b,
				"stage_b_big":  refxl,
				"stage_b_lite": reflite,
				"controlnet":   cnet,
				"misc":         encoders,
			}
			
			if not choices["stage_b_big"] and not choices["stage_b_lite"]:
				raise gr.Error("One or more Stage B models must be downloaded.")

			cap_installer.download_base_models(choices, True)
			cap_installer.download_reso_models(choices, True)
			cap_installer.download_refiner_models(choices, True)
			cap_installer.download_controlnet_models(choices, True)
			cap_installer.download_misc_models(choices, True)
			gr.Info("You may safely quit this installer.")

		start_download.click(download_comfyui_models, inputs=[
			casc_1b, casc_3b, reso_1b, reso_3b,
			ref_lite, ref_large, cn_models, encoder_models,
			reso_proto
		])
		def exit_gradio_hook():
			gr.Info("You may safely exit this tab now.")
			global exit_app
			exit_app = True
			
		exit_installer.click(exit_gradio_hook)

	app.launch(server_port=22744, inbrowser=True, server_name="0.0.0.0", prevent_thread_lock=True)

	import time
	while not exit_app:
		time.sleep(1)
