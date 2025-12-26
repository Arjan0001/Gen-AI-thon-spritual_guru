import json
import toml

def convert_json_to_toml(json_path, toml_path):
    # Read JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Write TOML
    with open(toml_path, 'w', encoding='utf-8') as f:
        toml.dump({"verses": data}, f)
    
    print(f"✅ Converted {json_path} → {toml_path}")

# Convert all files
convert_json_to_toml("indexes/quran_id_map.json", "indexes/quran_id_map.toml")
convert_json_to_toml("indexes/gita_id_map.json", "indexes/gita_id_map.toml")
convert_json_to_toml("indexes/bible_id_map.json", "indexes/bible_id_map.toml")