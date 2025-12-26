import json
import faiss
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

# CONFIG
INDEX_PATH = "indexes/gita.index"
ID_MAP_PATH = "indexes/gita_id_map.json"
TOP_K = 5

# GEMINI (DIRECT KEY)
genai.configure(api_key="your gemini api Key")
model = genai.GenerativeModel("models/gemini-flash-latest")

# EMBEDDING MODEL
embed_model = SentenceTransformer("all-mpnet-base-v2")

# LOAD INDEX + DATA
index = faiss.read_index(INDEX_PATH)
with open(ID_MAP_PATH, "r", encoding="utf-8") as f:
    verses = json.load(f)

print(f"Loaded {len(verses)} Quran verses")

# QUESTION
question = "Why should I not fear?"

# SEARCH
query_vec = embed_model.encode([question], normalize_embeddings=True)
D, I = index.search(query_vec, TOP_K)
results = [verses[idx] for idx in I[0]]

# CONTEXT
context = "\n\n".join(f"{v['id']}: {v['content']}" for v in results)

# PROMPT
prompt = f"""
Answer ONLY using the verses below.
Do not add outside knowledge.

VERSES:
{context}

QUESTION:
{question}
"""

# GEMINI CALL
response = model.generate_content(prompt)

print("\nANSWER:\n")
print(response.text)

print("\nSOURCES:")
for v in results:
    print(v["id"])
