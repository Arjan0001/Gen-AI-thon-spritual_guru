import json

with open("data/quran_structured.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(data[0])
print(data[-1])
print("Total verses:", len(data))
