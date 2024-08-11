# Utility functions for writing metadata into images:

import gzip
import json
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import gradio as gr

# Taken as-is from Stealth PNG Info
def prepare_data_for_embedding(params, mode='alpha', compressed=False):
	signature = f"stealth_{'png' if mode == 'alpha' else 'rgb'}{'info' if not compressed else 'comp'}"
	binary_signature = ''.join(format(byte, '08b') for byte in signature.encode('utf-8'))
	param = params.encode('utf-8') if not compressed else gzip.compress(bytes(params, 'utf-8'))
	binary_param = ''.join(format(byte, '08b') for byte in param)
	binary_param_len = format(len(binary_param), '032b')

	return binary_signature + binary_param_len + binary_param

def add_data_to_pixels(image, text, mode='alpha', compressed=False):
	binary_data = prepare_data_for_embedding(text, mode, compressed)
	if mode == 'alpha':
		image.putalpha(255)
	width, height = image.size
	pixels = image.load()
	index = 0
	end_write = False
	for x in range(width):
		for y in range(height):
			if index >= len(binary_data):
				end_write = True
				break
			values = pixels[x, y]
			if mode == 'alpha':
				r, g, b, a = values
			else:
				r, g, b = values
			if mode == 'alpha':
				a = (a & ~1) | int(binary_data[index])
				index += 1
			else:
				r = (r & ~1) | int(binary_data[index])
				if index + 1 < len(binary_data):
					g = (g & ~1) | int(binary_data[index + 1])
				if index + 2 < len(binary_data):
					b = (b & ~1) | int(binary_data[index + 2])
				index += 3
			pixels[x, y] = (r, g, b, a) if mode == 'alpha' else (r, g, b)
		if end_write:
			break

	return image

def save_image_no_meta(image, path):
	img = image.convert("RGBA")
	img.save(path, compression=4)

def save_image_with_meta(image, workflow, text, path):
	img = image.convert("RGBA")

	newimg = add_data_to_pixels(img, text)
	metadata = PngInfo()
	metadata.add_text("prompt", json.dumps(workflow))
	
	newimg.save(path, pnginfo=metadata, compression=4)