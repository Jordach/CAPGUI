# save_image_websocket_node is always the key for the save image websocket node, must be that string

def get_txt2img():
	workflow = """
	{
	"3": {
		"inputs": {
		"seed": 665095051496395,
		"steps": 20,
		"cfg": 4,
		"sampler_name": "euler_ancestral",
		"scheduler": "simple",
		"denoise": 1,
		"model": [
			"96",
			0
		],
		"positive": [
			"94",
			0
		],
		"negative": [
			"95",
			0
		],
		"latent_image": [
			"34",
			0
		]
		},
		"class_type": "KSampler",
		"_meta": {
		"title": "KSampler C"
		}
	},
	"33": {
		"inputs": {
		"seed": 679789055914725,
		"steps": 10,
		"cfg": 1.5,
		"sampler_name": "euler_ancestral",
		"scheduler": "simple",
		"denoise": 1,
		"model": [
			"77",
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
			"89",
			0
		]
		},
		"class_type": "KSampler",
		"_meta": {
		"title": "KSampler B"
		}
	},
	"34": {
		"inputs": {
		"width": 1024,
		"height": 1024,
		"compression": 32,
		"batch_size": 1
		},
		"class_type": "StableCascade_EmptyLatentImage",
		"_meta": {
		"title": "Image Size"
		}
	},
	"36": {
		"inputs": {
		"conditioning": [
			"94",
			0
		],
		"stage_c": [
			"90",
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
		"vae_name": ""
		},
		"class_type": "VAELoader",
		"_meta": {
		"title": "Load Stage A"
		}
	},
	"63": {
		"inputs": {
		"text": "",
		"clip": [
			"75",
			0
		]
		},
		"class_type": "CLIPTextEncode",
		"_meta": {
		"title": "Empty Stage B Neg"
		}
	},
	"73": {
		"inputs": {
		"shift": 2,
		"model": [
			"74",
			0
		]
		},
		"class_type": "ModelSamplingStableCascade",
		"_meta": {
		"title": "Shift"
		}
	},
	"74": {
		"inputs": {
		"unet_name": ""
		},
		"class_type": "UNETLoaderCAPGUI",
		"_meta": {
		"title": "CAPGUI API UNETLoader"
		}
	},
	"75": {
		"inputs": {
		"clip_name": "",
		"type": "stable_cascade"
		},
		"class_type": "CLIPLoaderCAPGUI",
		"_meta": {
		"title": "CAPGUI API CLIPLoader"
		}
	},
	"77": {
		"inputs": {
		"unet_name": ""
		},
		"class_type": "UNETLoaderCAPGUI",
		"_meta": {
		"title": "CAPGUI API UNETLoader"
		}
	},
	"save_image_websocket_node": {
		"inputs": {
		"images": [
			"93",
			0
		]
		},
		"class_type": "SaveImageWebsocket",
		"_meta": {
		"title": "save_image_websocket_node"
		}
	},
	"89": {
		"inputs": {
		"batch_index": 0,
		"length": 1,
		"samples": [
			"34",
			1
		]
		},
		"class_type": "LatentFromBatch",
		"_meta": {
		"title": "Latent From Batch B"
		}
	},
	"90": {
		"inputs": {
		"batch_index": 0,
		"length": 1,
		"samples": [
			"3",
			0
		]
		},
		"class_type": "LatentFromBatch",
		"_meta": {
		"title": "Latent From Batch C"
		}
	},
	"93": {
		"inputs": {
		"tile_size": 1024,
		"samples": [
			"33",
			0
		],
		"vae": [
			"47",
			0
		]
		},
		"class_type": "VAEDecodeTiled",
		"_meta": {
		"title": "Tiled VAE Decode"
		}
	},
	"94": {
		"inputs": {
		"clip": [
			"75",
			0
		],
		"prompt_schedule": [
			"97",
			0
		]
		},
		"class_type": "ScheduleToCondCAPGUI",
		"_meta": {
		"title": "Prompt Cond"
		}
	},
	"95": {
		"inputs": {
		"clip": [
			"75",
			0
		],
		"prompt_schedule": [
			"98",
			0
		]
		},
		"class_type": "ScheduleToCondCAPGUI",
		"_meta": {
		"title": "Negative Cond"
		}
	},
	"96": {
		"inputs": {
		"model": [
			"73",
			0
		],
		"prompt_schedule": [
			"97",
			0
		]
		},
		"class_type": "ScheduleToModelCAPGUI",
		"_meta": {
		"title": "LoRA Loader"
		}
	},
	"97": {
		"inputs": {
		"text": ""
		},
		"class_type": "PromptToScheduleCAPGUI",
		"_meta": {
		"title": "Prompt"
		}
	},
	"98": {
		"inputs": {
		"text": ""
		},
		"class_type": "PromptToScheduleCAPGUI",
		"_meta": {
		"title": "Negative Prompt"
		}
	}
	}
	"""

	return workflow.replace("\\", "\\\\")

def get_txt2img_canny():
	pass

def get_basic_img2img():
	workflow = """
	{
	"3": {
		"inputs": {
		"seed": 42069,
		"steps": 20,
		"cfg": 4,
		"sampler_name": "euler_ancestral",
		"scheduler": "simple",
		"denoise": 1,
		"model": [
			"73",
			0
		],
		"positive": [
			"68",
			0
		],
		"negative": [
			"7",
			0
		],
		"latent_image": [
			"97",
			0
		]
		},
		"class_type": "KSampler",
		"_meta": {
		"title": "Stage C Sampling"
		}
	},
	"7": {
		"inputs": {
		"text": "",
		"clip": [
			"75",
			0
		]
		},
		"class_type": "CLIPTextEncode",
		"_meta": {
		"title": "Negative Prompt"
		}
	},
	"33": {
		"inputs": {
		"seed": 80085,
		"steps": 10,
		"cfg": 1.5,
		"sampler_name": "euler_ancestral",
		"scheduler": "simple",
		"denoise": 1,
		"model": [
			"77",
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
			"99",
			0
		]
		},
		"class_type": "KSampler",
		"_meta": {
		"title": "Stage B Sampling"
		}
	},
	"36": {
		"inputs": {
		"conditioning": [
			"68",
			0
		],
		"stage_c": [
			"90",
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
		"vae_name": ""
		},
		"class_type": "VAELoader",
		"_meta": {
		"title": "Stage A"
		}
	},
	"63": {
		"inputs": {
		"text": "",
		"clip": [
			"75",
			0
		]
		},
		"class_type": "CLIPTextEncode",
		"_meta": {
		"title": "Empty Stage B Negative"
		}
	},
	"68": {
		"inputs": {
		"text": "",
		"clip": [
			"75",
			0
		]
		},
		"class_type": "CLIPTextEncode",
		"_meta": {
		"title": "Positive Prompt"
		}
	},
	"73": {
		"inputs": {
		"shift": 2,
		"model": [
			"74",
			0
		]
		},
		"class_type": "ModelSamplingStableCascade",
		"_meta": {
		"title": "ModelSamplingStableCascade"
		}
	},
	"74": {
		"inputs": {
		"unet_name": ""
		},
		"class_type": "UNETLoaderCAPGUI",
		"_meta": {
		"title": "Stage C UNETLoader"
		}
	},
	"75": {
		"inputs": {
		"clip_name": "",
		"type": "stable_cascade"
		},
		"class_type": "CLIPLoaderCAPGUI",
		"_meta": {
		"title": "Cascade CLIP"
		}
	},
	"77": {
		"inputs": {
		"unet_name": ""
		},
		"class_type": "UNETLoaderCAPGUI",
		"_meta": {
		"title": "Stage B UNETLoader"
		}
	},
	"save_image_websocket_node": {
		"inputs": {
		"images": [
			"93",
			0
		]
		},
		"class_type": "SaveImageWebsocket",
		"_meta": {
		"title": "SaveImageWebsocket"
		}
	},
	"90": {
		"inputs": {
		"batch_index": 0,
		"length": 1,
		"samples": [
			"3",
			0
		]
		},
		"class_type": "LatentFromBatch",
		"_meta": {
		"title": "Latent From Batch C"
		}
	},
	"93": {
		"inputs": {
		"tile_size": 1024,
		"samples": [
			"33",
			0
		],
		"vae": [
			"47",
			0
		]
		},
		"class_type": "VAEDecodeTiled",
		"_meta": {
		"title": "VAE Decode (Tiled)"
		}
	},
	"94": {
		"inputs": {
		"vae_name": "cascade\\effnet_encoder.safetensors"
		},
		"class_type": "VAELoader",
		"_meta": {
		"title": "Load VAE"
		}
	},
	"95": {
		"inputs": {
		"compression": 42,
		"image": [
			"100",
			0
		],
		"vae": [
			"94",
			0
		]
		},
		"class_type": "StableCascade_StageC_VAEEncode",
		"_meta": {
		"title": "Stage C Encode"
		}
	},
	"96": {
		"inputs": {
		"amount": 1,
		"samples": [
			"95",
			1
		]
		},
		"class_type": "RepeatLatentBatch",
		"_meta": {
		"title": "Repeat Latent Batch B"
		}
	},
	"97": {
		"inputs": {
		"amount": 1,
		"samples": [
			"95",
			0
		]
		},
		"class_type": "RepeatLatentBatch",
		"_meta": {
		"title": "Repeat Latent Batch C"
		}
	},
	"99": {
		"inputs": {
		"batch_index": 3,
		"length": 1,
		"samples": [
			"96",
			0
		]
		},
		"class_type": "LatentFromBatch",
		"_meta": {
		"title": "Latent From Batch B"
		}
	},
	"100": {
		"inputs": {
		"base64_image": ""
		},
		"class_type": "Base64ToImageCAPGUI",
		"_meta": {
		"title": "CAPGUI API Base64 Image Decoder"
		}
	}
	}
	"""

	return workflow.replace("\\", "\\\\")

def get_img2img_canny():
	pass

def get_img2img_super_res():
	pass

def get_inpaint():
	pass

def get_inpaint_canny():
	pass