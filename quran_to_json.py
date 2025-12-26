import json
import os

# ===== CONFIG =====
INPUT_DIR = "data/quran_jsons"
OUTPUT_FILE = "data/quran_structured.json"

structured_data = []

# ===== PROCESS FILES =====
for filename in sorted(os.listdir(INPUT_DIR)):
    if not filename.endswith(".json"):
        continue

    file_path = os.path.join(INPUT_DIR, filename)

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    surah_name = data["name"]
    surah_number = int(data["index"])
    verses = data["verse"]

    for key, text in verses.items():
        ayah_number = int(key.replace("verse_", ""))

        structured_data.append({
            "id": f"Q{surah_number}.{ayah_number}",
            "content": f"Surah {surah_name}, Ayah {ayah_number}: {text}",
            "metadata": {
                "source": "quran",
                "surah": surah_number,
                "ayah": ayah_number,
                "surah_name": surah_name,
                "topic": "islamic_scripture"
            }
        })

# ===== SAVE OUTPUT =====
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(structured_data, f, indent=2, ensure_ascii=False)

print(f"✅ Quran dataset generated: {len(structured_data)} verses")
print(f"📁 Saved to: {OUTPUT_FILE}")
