# save_image_websocket_node is always the key for the save image websocket node, must be that string

def get_txt2img():
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
			"34",
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
	"8": {
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
			"89",
			0
		]
		},
		"class_type": "KSampler",
		"_meta": {
		"title": "Stage B Sampling"
		}
	},
	"34": {
		"inputs": {
		"width": 1024,
		"height": 1024,
		"compression": 42,
		"batch_size": 4
		},
		"class_type": "StableCascade_EmptyLatentImage",
		"_meta": {
		"title": "StableCascade_EmptyLatentImage"
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
		"vae_name": "cascade\\stage_a.safetensors"
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
			"8",
			0
		]
		},
		"class_type": "SaveImageWebsocket",
		"_meta": {
		"title": "SaveImageWebsocket"
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

