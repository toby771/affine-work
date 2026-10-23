import json
from pathlib import Path

original_path = Path("/mnt/d/Exercise/Affine_work/merged_dataset.jsonl")
update_path = Path("/mnt/d/Exercise/Affine_work/make_dataset.jsonl")
output_path = Path("/mnt/d/Exercise/Affine_work/merged_add_dataset.jsonl")

# # Load updates by index
# updates = {}
# with update_path.open("r", encoding="utf-8") as f:
#     for line in f:
#         line = line.strip()
#         if not line:
#             continue
#         obj = json.loads(line)
#         updates[obj["index"]] = obj

# # Merge while preserving original order
# seen = set()
# with original_path.open("r", encoding="utf-8") as fin, output_path.open("w", encoding="utf-8") as fout:
#     for line in fin:
#         line = line.strip()
#         if not line:
#             continue
#         obj = json.loads(line)
#         idx = obj["index"]

#         if idx in updates:
#             obj = updates[idx]
#             seen.add(idx)

#         fout.write(json.dumps(obj, ensure_ascii=False) + "\n")

#     # Optional: append any update records whose index was not in the original file
#     for idx, obj in updates.items():
#         if idx not in seen:
#             fout.write(json.dumps(obj, ensure_ascii=False) + "\n")

# print(f"Merged output written to: {output_path}")

def iter_json_objects(path: Path):
    """Yield every top-level JSON object in the file, regardless of newlines."""
    decoder = json.JSONDecoder()
    text = path.read_text(encoding="utf-8-sig")
    n, i = len(text), 0
    while i < n:
        while i < n and text[i].isspace():
            i += 1
        if i >= n:
            break
        obj, i = decoder.raw_decode(text, i)
        yield obj


# 1) updates by index
updates = {obj["index"]: obj for obj in iter_json_objects(update_path)}
print(f"Loaded {len(updates)} update records: {sorted(updates)}")

# 2) merge, preserving original order
seen = set()
with output_path.open("w", encoding="utf-8") as fout:
    for obj in iter_json_objects(original_path):
        idx = obj["index"]
        if idx in updates:
            obj = updates[idx]
            seen.add(idx)
        fout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    # append updates whose index wasn't in the original
    for idx, obj in updates.items():
        if idx not in seen:
            fout.write(json.dumps(obj, ensure_ascii=False) + "\n")

print(f"Replaced {len(seen)} records")
print(f"Missing from original (appended): {set(updates) - seen}")
print(f"Wrote {output_path}")