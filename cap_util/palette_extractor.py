import numpy as np
import matplotlib.pyplot as plt
import extcolors
import colorsys
from PIL import ImageColor, Image, ImageOps

palette_extraction_type = [("Median-Cut", "pil"), ("CIE76", "extcolors")]
palette_sort_type = [
	("HSV", "hsv"),
	("RGB", "rgb"),
	("Sum of RGB Values", "sum_rgb"),
	("Square of RGB Values", "sqr_rgb"),
	("Random", "random"),
]

sort_func_dict = {
	"rgb": (lambda r,g,b: (r, g, b)),
	"sum_rgb": (lambda r,g,b: r+g+b),
	"sqr_rgb": (lambda r,g,b: r**2+g**2+b**2),
	"hsv": (lambda r, g, b : (colorsys.rgb_to_hsv(r, g, b)[0], colorsys.rgb_to_hsv(r, g, b)[1], colorsys.rgb_to_hsv(r, g, b)[2])),
	"random": (lambda r, g, b: np.random.random()),
}

def rgb_to_hex(rgb):
	return '#%02x%02x%02x' % tuple(rgb)

def get_pil_palette(image, p_size, sort):
	small_image = image.copy()
	#small_image = small_image.resize((320, 320))
	ps = p_size
	if ps > 256:
		ps = 256
	res = small_image.convert("P", palette=Image.ADAPTIVE, colors=ps)

	pal = res.getpalette()
	col_count = sorted(res.getcolors(), reverse=True)

	colors = []
	for i in range(ps):
		index = col_count[i][1]
		dom_col = pal[index * 3 : index * 3 + 3]
		colors.append(tuple(dom_col))

	palette = []
	for col in colors:
		palette.append(list(col))
	palette.sort(key=lambda rgb : sort_func_dict[sort](*rgb))
	return palette

def get_cie_palette(image, tolerance, p_size, sort):
	colors, count = extcolors.extract_from_image(image, int(tolerance), int(p_size))

	palette = []
	for col in colors:
		palette.append(list(col[0]))
	palette.sort(key=lambda rgb : sort_func_dict[sort](*rgb))
	return palette

def create_palette_strip(palette_hex):
	palette = np.array([ImageColor.getcolor(color, "RGB") for color in palette_hex])
	fig, ax = plt.subplots(dpi=100)
	ax.imshow(palette[np.newaxis, :, :])
	ax.axis('off')
	return fig

def create_palette_scatter(pal, hide_axis):
	hsv = []
	for c in pal:
		hsv.append(colorsys.rgb_to_hsv(r=c[0]/255, g=c[1]/255, b=c[2]/255))
	# Sort by saturation to render those first
	hsv.sort(key=lambda hsv: hsv[1])

	hue = []
	luma = []
	palnorm = []
	for c in hsv:
		if c[1] != 0:
			hue.append(c[0] * 360)
		else:
			hue.append(-20)
		rgb = colorsys.hsv_to_rgb(c[0], c[1], c[2])
		palnorm.append(rgb)
		luma.append(0.2126*(rgb[0]) + 0.7152*(rgb[1]) + 0.0722*(rgb[2]))
	fig, ax = plt.subplots()
	ax.scatter(hue, luma, facecolor=palnorm)
	# Dark theme me
	ax.set_facecolor('#333333')
	fig.set_facecolor("#333333")
	if not hide_axis:
		ax.set_xlabel('Hue')
		ax.set_ylabel('Luminance')
		ax.xaxis.label.set_color('white')
		ax.yaxis.label.set_color('white')
		ax.spines["bottom"].set_color("white")
		ax.spines["top"].set_color("white")
		ax.spines["left"].set_color("white")
		ax.spines["right"].set_color("white")
		ax.tick_params(axis='x', colors='white')
		ax.tick_params(axis='y', colors='white')
	else:
		ax.axis('off')
	return fig