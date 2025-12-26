import json
import re

# ===== CONFIG =====
INPUT_FILE = "data/bible_unstructured.json"      # your current file
OUTPUT_FILE = "data/bible_structured.json"

structured = []

# Regex to parse keys like: "Genesis 1:1"
pattern = re.compile(r"^([A-Za-z\s]+)\s+(\d+):(\d+)$")

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

for ref, text in raw_data.items():
    match = pattern.match(ref.strip())
    if not match:
        continue

    book = match.group(1).strip()
    chapter = int(match.group(2))
    verse = int(match.group(3))

    structured.append({
        "id": f"B{book[:3]}{chapter}.{verse}",
        "content": f"{book} {chapter}:{verse}: {text.lstrip('# ').strip()}",
        "metadata": {
            "source": "bible",
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "topic": "christian_scripture"
        }
    })

# Save output
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(structured, f, indent=2, ensure_ascii=False)

print(f"✅ Bible dataset generated: {len(structured)} verses")
print(f"📁 Saved to: {OUTPUT_FILE}")
