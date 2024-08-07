import os
import random

def read_and_apply_wildcards(positive, negative):
	output_positive = positive
	output_negative = negative

	# Infinitely and Recursively Apply Wildcards
	while True:
		wc_dir = os.listdir("wildcards/active/")

		# Try and avoid loading files if a wildcard isn't used
		wc_used = False
		used_wcs = []
		for wc in wc_dir:
			ext = os.path.splitext(wc)
			# Only process wildcards ending in .txt
			if ext[1] == ".txt":
				pos_count = output_positive.count(ext[0])
				neg_count = output_negative.count(ext[0])

				# Wildcard was invoked, so don't return early
				if pos_count > 0 or neg_count > 0:
					wc_used = True
					used_wcs.append(wc)

		# Don't even bother replacing things when there's no wildcards left
		if not wc_used:
			return output_positive, output_negative

		for wc in used_wcs:
			ext = os.path.splitext(wc)
			# Only process wildcards ending in .txt
			if ext[1] == ".txt":
				replacements = []
				with open(os.path.join("wildcards", "active", wc), "r", encoding="utf-8") as wildcard:
					for line in wildcard.readlines():
						if line.strip() != "":
							if line.strip() == "||WC_EMPTY_LINE||":
								replacements.append("")
							else:
								replacements.append(line.strip())

				# Always pays off to be massively paranoid
				random.shuffle(replacements)
				pos_count = output_positive.count(ext[0])
				n_replacements = len(replacements) - 1
				for _ in range(pos_count):
					random_replacement = replacements[int(random.uniform(0, n_replacements))]
					output_positive = output_positive.replace(ext[0], random_replacement, 1)
				
				neg_count = output_negative.count(ext[0])
				for _ in range(neg_count):
					random_replacement = replacements[int(random.uniform(0, n_replacements))]
					output_negative = output_negative.replace(ext[0], random_replacement, 1)
			else:
				continue
		
		# print(positive)
		# print(output_positive)
		# print(negative)
		# print(output_negative)