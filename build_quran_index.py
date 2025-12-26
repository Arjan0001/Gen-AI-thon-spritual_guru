import json
import faiss
import numpy as np
import os
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

INPUT_JSON = "data/quran_structured.json"
INDEX_PATH = "indexes/quran.index"
ID_MAP_PATH = "indexes/quran_id_map.json"

# ✅ CREATE DIRECTORY
os.makedirs("indexes", exist_ok=True)

print("Loading embedding model...")
model = SentenceTransformer("all-mpnet-base-v2")

with open(INPUT_JSON, "r", encoding="utf-8") as f:
    verses = json.load(f)

print(f"Loaded {len(verses)} Quran verses")

texts = [v["content"] for v in verses]

embeddings = model.encode(
    texts,
    show_progress_bar=True,
    convert_to_numpy=True,
    normalize_embeddings=True
)

dimension = embeddings.shape[1]
index = faiss.IndexFlatIP(dimension)
index.add(embeddings)

faiss.write_index(index, INDEX_PATH)

with open(ID_MAP_PATH, "w", encoding="utf-8") as f:
    json.dump(verses, f, indent=2, ensure_ascii=False)

print("✅ Quran index created successfully")
