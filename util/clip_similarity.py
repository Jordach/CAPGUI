from transformers import AutoTokenizer, CLIPTextModelWithProjection
import torch
import numpy as np
import matplotlib.pyplot as plt
import csv
import umap as mp
import sys
import os

# Installation as part of CAPGUI's venv:
# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
# pip install umap-learn transformers

clip_path = "clip_model/"
allowed_categories = [0,4,5,99]
excluded_tags = ['avoid_posting','conditional_dnp']
num_post_threshold = 100000
device = "cuda"
caption_pre = "by novelai, detailed background, anthro, solo, "

if not os.path.exists("tag_list.conf"):
	raise Exception("There's no tag_list.conf file to load, so stopping.")

tags = []
with open("tag_list.conf", "r", encoding="utf-8") as file:
	tags = file.readlines()

print(len(tags))

tokenizer = AutoTokenizer.from_pretrained("laion/CLIP-ViT-bigG-14-laion2B-39B-b160k")
text_model = CLIPTextModelWithProjection.from_pretrained(clip_path, use_safetensors=True, local_files_only=True).to(device)

# tag_categories = {}
# tag_counts = {}

# csv.field_size_limit(sys.maxsize)

# with open(tag_csv, 'r') as file:
#     csv_reader = csv.DictReader(file)
#     for row in csv_reader:
#         tag = row['name']
#         category = int(row['category'])
#         post_count = int(row['post_count'])

#         if "(" not in tag and ")" not in tag and category in allowed_categories and post_count > num_post_threshold and tag not in excluded_tags:
#             tags.append(tag)
#             tag_categories[tag] = category
#             tag_counts[tag] = post_count


def get_clip_embedding(text):
    text = text+","
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=77).to(device)
    with torch.no_grad():
        outputs = text_model(**inputs)

    comma_indices = (inputs.input_ids == 267).nonzero(as_tuple=True)[1]
    last_comma_index = comma_indices[-1] if len(comma_indices) > 0 else -1
    return outputs.last_hidden_state[:, last_comma_index, :]

tag_embeddings = {tag: get_clip_embedding(tag) for tag in tags}

embedding_array = np.array([embedding.cpu().numpy().flatten() for embedding in tag_embeddings.values()])

reducer = mp.UMAP(n_neighbors=5, min_dist=0.3, n_components=2, random_state=42)
reduced_embeddings = reducer.fit_transform(embedding_array)

plt.figure(figsize=(12, 8))
plt.scatter(reduced_embeddings[:, 0], reduced_embeddings[:, 1], alpha=0.5)

for i, tag in enumerate(tags):
    plt.annotate(tag, (reduced_embeddings[i, 0], reduced_embeddings[i, 1]), xytext=(5, 2), 
                 textcoords='offset points', ha='left', va='bottom')

plt.title("Tag Similarity Cloud (UMAP)")
plt.xlabel("UMAP dimension 1")
plt.ylabel("UMAP dimension 2")
plt.tight_layout()

plt.savefig("tag_similarity_cloud_umap.png")
plt.close()
