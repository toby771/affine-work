import json

file_path = "/mnt/d/Exercise/Affine_work/affine_work/dataset/only_length_filter.jsonl"
target_ids = {244, 591, 528, 648, 993, 1074,1391,1516,1537,1570,1604,1945,2376,3225,4127,1131,5622,5900,6016,6042,6044,6075,6181,6265,6345,6373,6383,6461,6582,6548,7014,7178,7216}

found_ids = set()

with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            record = json.loads(line)
            idx = record.get("index")

            if idx in target_ids:
                found_ids.add(idx)
        except json.JSONDecodeError:
            continue

print(f"Found IDs: {found_ids}")
print(f"Missing IDs: {target_ids - found_ids}")
        