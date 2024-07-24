import os
import random

def read_and_apply_wildcards(positive, negative):
	output_positive = positive
	output_negative = negative
	wcs = os.listdir("wildcards/active/")
	# Don't even bother scanning a folder if it's potentially emptied by the user mistakenly
	if len(wcs) < 1:
		return positive, negative

	for wc in wcs:
		ext = os.path.splitext(wc)
		# Only process wildcards ending in .txt
		if ext[1] == ".txt":
			replacements = []
			with open(os.path.join("wildcards", "active", wc), encoding="utf-8") as wildcard:
				for line in wildcard.readlines():
					if line.strip() != "":
						replacements.append(line.strip())

			random_replacement = random.choice(replacements)
			output_positive = positive.replace(ext[0], random_replacement)
			random_replacement = random.choice(replacements)
			output_negative = negative.replace(ext[0], random_replacement)
		else:
			continue
		
	# print(positive)
	# print(output_positive)
	# print(negative)
	# print(output_negative)
	return output_positive, output_negative