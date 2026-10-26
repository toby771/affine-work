import json
import os

total_keys = []
available_keys = []
available_keys_level_2 = []

available_data = []
available_data_level_2 = []

folder_index = 12

# save_path1 = f"./log_mimo_{folder_index}/available_keys.jsonl"
# save_path2 = f"./log_mimo_{folder_index}/available_keys_level_2.jsonl"
save_path1 = f"./available_keys.jsonl"
save_path2 = f"./available_keys_level_2.jsonl"



for i in range(25):
    # log_path = f"./log_mimo_12/miner_eval_log_{i + 1}.json"
    log_path = f"./miner_eval_log_{i + 1}.json"

    if not os.path.exists(log_path):
        print(f"Warning: File not found: {log_path}")
        continue

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            log_data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: Could not read {log_path}: {e}")
        continue

    for entry, data in log_data.items():
        try:
            prob_index = int(entry.split(":")[1])

            required_fields = [
                "positive", "negative", "neutral",
                "positive_lengths", "negative_lengths",
                "neutral_lengths"
            ]

            missing = [k for k in required_fields if k not in data]
            # if missing:
            #     print(f"Warning: {entry} missing fields: {missing}")
            #     continue

            pos = data["positive"]
            neg = data["negative"]

            # Preserve the complete original information
            record = {
                "entry": entry,
                "prob_index": prob_index,
                "source_file": log_path,
                "data": data
            }

            total_keys.append(prob_index)

            if neg > 0 and pos > 0:
                available_keys.append(prob_index)
                available_data.append(record)

            if neg > 1 and pos > 1:
                available_keys_level_2.append(prob_index)
                available_data_level_2.append(record)

        except (ValueError, IndexError, TypeError) as e:
            print(f"Warning: Invalid entry '{entry}' in {log_path}: {e}")
            continue


def save_jsonl(filename, records):
    with open(filename, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Saved {len(records)} records to {filename}")


save_jsonl(save_path1, available_data)
save_jsonl(save_path2, available_data_level_2)

print("\nAvailable keys:")
print(available_keys)
print("Available keys count:", len(available_keys))

print("\nAvailable level-2 keys:")
print(available_keys_level_2)
print("Available level-2 count:", len(available_keys_level_2))

print("Total keys count:", len(total_keys))


