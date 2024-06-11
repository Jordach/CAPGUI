import cap_util
import os
import json
import gradio as gr
import copy

def load_all_user_presets(c=False, b=False):
	path_c = os.path.join("presets", "base")
	path_b = os.path.join("presets", "refiner")
	os.makedirs(path_c, exist_ok=True)
	os.makedirs(path_b, exist_ok=True)

	# Prefill Dropdown with defaults
	if c:
		cap_util.ksampler_presets_stage_c_dropdown = []
		for p in cap_util.ksampler_presets_stage_c_builtin:
			cap_util.ksampler_presets_stage_c_dropdown.append(p)
	if b:
		cap_util.ksampler_presets_stage_b_dropdown = []
		for p in cap_util.ksampler_presets_stage_b_builtin:
			cap_util.ksampler_presets_stage_b_dropdown.append(p)

	if c:
		c_files = os.listdir(path_c)
		for preset in c_files:
			ext = os.path.splitext(preset)
			if ext[1] == ".json":
				data = ""
				with open(os.path.join(path_c, preset), "r", encoding="utf-8") as f:
					data = json.load(f)
				steps = 20
				shift = 2
				cfg = 4
				sampler = "euler_ancestral"
				scheduler = "simple"
				description = "My Custom Base Model Preset"
				# Type check the inputs as user data cannot be trusted
				try:
					if "steps" in data:
						steps = int(data["steps"])
					if "shift" in data:
						shift = float(data["shift"])
					if "cfg" in data:
						cfg = float(data["cfg"])
					if "sampler" in data:
						sampler = str(data["sampler"])
					if "scheduler" in data:
						scheduler = str(data["scheduler"])
					if "description" in data:
						description = str(data["description"])
				except:
					gr.Info(f"It appears that the custom preset for the Base Model {preset} has an invalid type during loading, this preset will be skipped.")
					continue

				config = {
					"sampler": sampler,
					"scheduler": scheduler,
					"steps": steps,
					"cfg": cfg,
					"shift": shift
				}
				dict_key = f"custom_{ext[0]}"
				cap_util.ksampler_presets_stage_c_dropdown.append(
					(f"Custom: {description}", dict_key)
				)
				cap_util.ksampler_presets_stage_c[dict_key] = config
	
	if b:
		b_files = os.listdir(path_b)
		for preset in b_files:
			ext = os.path.splitext(preset)
			if ext[1] == ".json":
				data = ""
				with open(os.path.join(path_b, preset), "r", encoding="utf-8") as f:
					data = json.load(f)
				steps = 12
				cfg = 1.5
				sampler = "euler_ancestral"
				scheduler = "simple"
				description = "My Custom Refiner Model Preset"
				# Type check the inputs as user data cannot be trusted
				try:
					if "steps" in data:
						steps = int(data["steps"])
					if "cfg" in data:
						cfg = float(data["cfg"])
					if "sampler" in data:
						sampler = str(data["sampler"])
					if "scheduler" in data:
						scheduler = str(data["scheduler"])
					if "description" in data:
						description = str(data["description"])
				except:
					gr.Info(f"It appears that the custom preset for the Refiner Model {preset} has an invalid type during loading, this preset will be skipped.")
					continue

				config = {
					"sampler": sampler,
					"scheduler": scheduler,
					"steps": steps,
					"cfg": cfg,
				}
				dict_key = f"custom_{ext[0]}"
				cap_util.ksampler_presets_stage_b_dropdown.append(
					(f"Custom: {description}", dict_key)
				)
				cap_util.ksampler_presets_stage_b[dict_key] = config

def save_as_new_preset(filename, desc, preset_type, steps, cfg, sampler, schedule, shift=2):
	if "~" in filename:
		raise gr.Error("Please do not use a token that expands to the home directory on Linux systems.")
	if "/" in filename:
		raise gr.Error("Please do not use directory delimiters in a file name.")
	if "\\" in filename:
		raise gr.Error("Please do not use directory delimiters in a file name.")

	settings_dict = {
		"steps": steps,
		"cfg": cfg,
		"sampler": sampler,
		"schedule": schedule,
		"description": desc,
	}

	if preset_type == "c":
		settings_dict["shift"] = shift

	path_c = os.path.join("presets", "base")
	path_b = os.path.join("presets", "refiner")
	os.makedirs(path_c, exist_ok=True)
	os.makedirs(path_b, exist_ok=True)
	
	if preset_type == "c":
		with open(os.path.join(path_c, f"{filename}.json"), "w", encoding="utf-8") as json_data:
			json.dump(settings_dict, json_data, indent=2)
	else:
		with open(os.path.join(path_b, f"{filename}.json"), "w", encoding="utf-8") as json_data:
			json.dump(settings_dict, json_data, indent=2)