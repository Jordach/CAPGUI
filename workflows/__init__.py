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
			"73",
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
			"96",
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
			"74",
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
			"seed": 227279383,
			"steps": 20,
			"cfg": 4,
			"sampler_name": "euler_ancestral",
			"scheduler": "simple",
			"denoise": 0.5,
			"model": [
				"73",
				0
			],
			"positive": [
				"103",
				0
			],
			"negative": [
				"105",
				0
			],
			"latent_image": [
				"97",
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
			"seed": 2011967413,
			"steps": 12,
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
				"102",
				0
			],
			"latent_image": [
				"99",
				0
			]
			},
			"class_type": "KSampler",
			"_meta": {
			"title": "KSampler B"
			}
		},
		"36": {
			"inputs": {
			"conditioning": [
				"103",
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
			"title": "Load VAE Decoder"
			}
		},
		"73": {
			"inputs": {
			"shift": 2,
			"model": [
				"104",
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
			"title": "Stage C Loader"
			}
		},
		"75": {
			"inputs": {
			"clip_name": "",
			"type": "stable_cascade"
			},
			"class_type": "CLIPLoaderCAPGUI",
			"_meta": {
			"title": "CLIP Loader"
			}
		},
		"77": {
			"inputs": {
			"unet_name": "cascade/stage_b/stage_b_bf16.safetensors"
			},
			"class_type": "UNETLoaderCAPGUI",
			"_meta": {
			"title": "Stage B Loader"
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
			"vae_name": ""
			},
			"class_type": "VAELoader",
			"_meta": {
			"title": "Load VAE Encoder"
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
			"title": "StableCascade_StageC_VAEEncode"
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
			"batch_index": 0,
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
		},
		"101": {
			"inputs": {
			"text": ""
			},
			"class_type": "PromptToScheduleCAPGUI",
			"_meta": {
			"title": "Positive Prompt"
			}
		},
		"102": {
			"inputs": {
			"text": "",
			"clip": [
				"75",
				0
			]
			},
			"class_type": "CLIPTextEncode",
			"_meta": {
			"title": "Empty Negative"
			}
		},
		"103": {
			"inputs": {
			"clip": [
				"75",
				0
			],
			"prompt_schedule": [
				"101",
				0
			]
			},
			"class_type": "ScheduleToCondCAPGUI",
			"_meta": {
			"title": "CAPGUI Schedule To Conditioning"
			}
		},
		"104": {
			"inputs": {
			"model": [
				"74",
				0
			],
			"prompt_schedule": [
				"101",
				0
			]
			},
			"class_type": "ScheduleToModelCAPGUI",
			"_meta": {
			"title": "CAPGUI Schedule To Model"
			}
		},
		"105": {
			"inputs": {
			"clip": [
				"75",
				0
			],
			"prompt_schedule": [
				"106",
				0
			]
			},
			"class_type": "ScheduleToCondCAPGUI",
			"_meta": {
			"title": "CAPGUI Schedule To Conditioning"
			}
		},
		"106": {
			"inputs": {
			"text": ""
			},
			"class_type": "PromptToScheduleCAPGUI",
			"_meta": {
			"title": "Negative Prompt"
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
		}
	}
	"""

	return workflow.replace("\\", "\\\\")

def get_img2img_canny():
	pass

def get_img2img_super_res():
	pass

def get_inpaint():
	workflow = """
	{
		"3": {
			"inputs": {
			"seed": 326861713972909,
			"steps": 20,
			"cfg": 4,
			"sampler_name": "euler_ancestral",
			"scheduler": "simple",
			"denoise": 0.5,
			"model": [
				"109",
				0
			],
			"positive": [
				"103",
				0
			],
			"negative": [
				"105",
				0
			],
			"latent_image": [
				"97",
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
			"seed": 759980859599392,
			"steps": 12,
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
				"102",
				0
			],
			"latent_image": [
				"99",
				0
			]
			},
			"class_type": "KSampler",
			"_meta": {
			"title": "KSampler B"
			}
		},
		"36": {
			"inputs": {
			"conditioning": [
				"103",
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
			"title": "Load VAE Decoder"
			}
		},
		"73": {
			"inputs": {
			"shift": 2,
			"model": [
				"104",
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
			"title": "Stage C Loader"
			}
		},
		"75": {
			"inputs": {
			"clip_name": "cascade/reso_proto_delta_e5_te.safetensors",
			"type": "stable_cascade"
			},
			"class_type": "CLIPLoaderCAPGUI",
			"_meta": {
			"title": "CLIP Loader"
			}
		},
		"77": {
			"inputs": {
			"unet_name": ""
			},
			"class_type": "UNETLoaderCAPGUI",
			"_meta": {
			"title": "Stage B Loader"
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
			"vae_name": ""
			},
			"class_type": "VAELoader",
			"_meta": {
			"title": "Load VAE Encoder"
			}
		},
		"95": {
			"inputs": {
			"compression": 32,
			"image": [
				"129",
				0
			],
			"vae": [
				"94",
				0
			]
			},
			"class_type": "StableCascade_StageC_VAEEncode",
			"_meta": {
			"title": "StableCascade_StageC_VAEEncode"
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
				"121",
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
			"batch_index": 0,
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
		"101": {
			"inputs": {
			"text": ""
			},
			"class_type": "PromptToScheduleCAPGUI",
			"_meta": {
			"title": "Positive Prompt"
			}
		},
		"102": {
			"inputs": {
			"text": "",
			"clip": [
				"75",
				0
			]
			},
			"class_type": "CLIPTextEncode",
			"_meta": {
			"title": "Empty Negative"
			}
		},
		"103": {
			"inputs": {
			"clip": [
				"75",
				0
			],
			"prompt_schedule": [
				"101",
				0
			]
			},
			"class_type": "ScheduleToCondCAPGUI",
			"_meta": {
			"title": "CAPGUI Schedule To Conditioning"
			}
		},
		"104": {
			"inputs": {
			"model": [
				"74",
				0
			],
			"prompt_schedule": [
				"101",
				0
			]
			},
			"class_type": "ScheduleToModelCAPGUI",
			"_meta": {
			"title": "CAPGUI Schedule To Model"
			}
		},
		"105": {
			"inputs": {
			"clip": [
				"75",
				0
			],
			"prompt_schedule": [
				"106",
				0
			]
			},
			"class_type": "ScheduleToCondCAPGUI",
			"_meta": {
			"title": "CAPGUI Schedule To Conditioning"
			}
		},
		"106": {
			"inputs": {
			"text": ""
			},
			"class_type": "PromptToScheduleCAPGUI",
			"_meta": {
			"title": "Negative Prompt"
			}
		},
		"109": {
			"inputs": {
			"model": [
				"73",
				0
			]
			},
			"class_type": "DifferentialDiffusion",
			"_meta": {
			"title": "Differential Diffusion"
			}
		},
		"121": {
			"inputs": {
			"samples": [
				"95",
				0
			],
			"mask": [
				"122",
				0
			]
			},
			"class_type": "SetLatentNoiseMask",
			"_meta": {
			"title": "Set Latent Noise Mask"
			}
		},
		"122": {
			"inputs": {
			"channel": "red",
			"image": [
				"130",
				0
			]
			},
			"class_type": "ImageToMask",
			"_meta": {
			"title": "Convert Image to Mask"
			}
		},
		"129": {
			"inputs": {
			"base64_image": ""
			},
			"class_type": "Base64ToImageCAPGUI",
			"_meta": {
			"title": "Input Image"
			}
		},
		"130": {
			"inputs": {
			"base64_image": ""
			},
			"class_type": "Base64ToImageCAPGUI",
			"_meta": {
			"title": "Input Mask"
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
		}
	}
	"""

	return workflow.replace("\\", "\\\\")

def get_inpaint_canny():
	pass