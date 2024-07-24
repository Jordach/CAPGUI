import os
import random

artist_min = 75
meta_min = 100

styles = {}

with open("../autocomplete/csv/resonance_furry.csv", "r", encoding="utf-8") as csv_data:
	lines = csv_data.readlines()
	for line in lines:
		l = line.strip()
		col = l.split(",")
		og_t = col[0].strip()
		tag = col[0].strip()
		tag = tag.replace("_", " ")
		tag = tag.replace("(", "\\(")
		tag = tag.replace(")", "\\)")
		cat = int(col[1])
		cnt = int(col[2])
		if cat == 1 and cnt > artist_min:
			if tag not in styles:
				styles[tag] = True
		elif cat == 7 and cnt > meta_min:
			if tag not in styles:
				styles[tag] = True

with open("../autocomplete/csv/resonance_anime.csv", "r", encoding="utf-8") as csv_data:
	lines = csv_data.readlines()
	for line in lines:
		l = line.strip()
		col = l.split(",")
		tag = col[0].strip()
		tag = tag.replace("_", " ")
		tag = tag.replace("(", "\\(")
		tag = tag.replace(")", "\\)")
		tag_fix = f"by {tag}"
		cat = 0
		try:
			cat = int(col[1])
		except:
			continue
		cnt = 0
		try:
			cnt = int(col[2])
		except:
			continue
		if cat == 1 and cnt > artist_min:
			if tag_fix not in styles:
				styles[tag_fix] = True
		elif cat == 5 and cnt > meta_min:
			if tag not in styles:
				styles[tag] = True

keys = list(styles.keys())
random.shuffle(keys)
out_keys = []
for k in keys:
	out_keys.append(f"{k}\n")

with open("reso_r1_styles.txt", "w", encoding="utf-8") as wc:
	wc.writelines(out_keys)