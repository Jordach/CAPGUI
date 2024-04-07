def get_txt2img():
	workflow = """
	{
	"3": {
		"inputs": {
		"seed": 77975485718346,
		"steps": 20,
		"cfg": 4,
		"sampler_name": "euler_ancestral",
		"scheduler": "simple",
		"denoise": 1,
		"model": [
			"49",
			0
		],
		"positive": [
			"70",
			0
		],
		"negative": [
			"7",
			0
		],
		"latent_image": [
			"34",
			0
		]
		},
		"class_type": "KSampler",
		"_meta": {
		"title": "KSampler"
		}
	},
	"7": {
		"inputs": {
		"text": "",
		"clip": [
			"48",
			0
		]
		},
		"class_type": "CLIPTextEncode",
		"_meta": {
		"title": "CLIP Text Encode (Negative Prompt)"
		}
	},
	"8": {
		"inputs": {
		"samples": [
			"33",
			0
		],
		"vae": [
			"47",
			0
		]
		},
		"class_type": "VAEDecode",
		"_meta": {
		"title": "VAE Decode"
		}
	},
	"save_image_websocket_node": {
		"class_type": "SaveImageWebsocket",
		"inputs": {
			"images": [
			"8",
			0
			]
		}
	},
	"33": {
		"inputs": {
		"seed": 525404242549007,
		"steps": 10,
		"cfg": 1.5,
		"sampler_name": "euler_ancestral",
		"scheduler": "simple",
		"denoise": 1,
		"model": [
			"50",
			0
		],
		"positive": [
			"36",
			0
		],
		"negative": [
			"63",
			0
		],
		"latent_image": [
			"34",
			1
		]
		},
		"class_type": "KSampler",
		"_meta": {
		"title": "KSampler"
		}
	},
	"34": {
		"inputs": {
		"width": 1024,
		"height": 1280,
		"compression": 32,
		"batch_size": 1
		},
		"class_type": "StableCascade_EmptyLatentImage",
		"_meta": {
		"title": "StableCascade_EmptyLatentImage"
		}
	},
	"36": {
		"inputs": {
		"conditioning": [
			"70",
			0
		],
		"stage_c": [
			"3",
			0
		]
		},
		"class_type": "StableCascade_StageB_Conditioning",
		"_meta": {
		"title": "StableCascade_StageB_Conditioning"
		}
	},
	"47": {
		"inputs": {
		"vae_name": "stage_a.safetensors"
		},
		"class_type": "VAELoader",
		"_meta": {
		"title": "Load VAE"
		}
	},
	"48": {
		"inputs": {
		"clip_name": "reso_alpha_r2_te_e5\\model.safetensors",
		"type": "stable_cascade"
		},
		"class_type": "CLIPLoaderCAPGUI",
		"_meta": {
		"title": "CAPGUI API CLIPLoader"
		}
	},
	"49": {
		"inputs": {
		"unet_name": "reso_alpha_r2-e5.safetensors"
		},
		"class_type": "UNETLoaderCAPGUI",
		"_meta": {
		"title": "CAPGUI API UNETLoader"
		}
	},
	"50": {
		"inputs": {
		"unet_name": "stage_b_bf16.safetensors"
		},
		"class_type": "UNETLoaderCAPGUI",
		"_meta": {
		"title": "CAPGUI API UNETLoader"
		}
	},
	"63": {
		"inputs": {
		"text": "",
		"clip": [
			"48",
			0
		]
		},
		"class_type": "CLIPTextEncode",
		"_meta": {
		"title": "CLIP Text Encode (Negative Prompt)"
		}
	},
	"70": {
		"inputs": {
		"text": "",
		"clip": [
			"48",
			0
		]
		},
		"class_type": "CLIPTextEncode",
		"_meta": {
		"title": "CLIP Text Encode (Positive Prompt)"
		}
	}
	}
	"""

	return workflow.replace("\\", "\\\\")

def get_txt2img_remix():
	pass

def get_txt2img_hires():
	pass

def get_txt2img_canny():
	pass

def get_basic_img2img():
	pass

def get_img2img_canny():
	pass

def get_img2img_super_res():
	pass

def get_inpaint():
	pass

def get_inpaint_canny():
	pass

