import requests

url = "https://affine.io/scores.json"

file_path = "results/positive_miners5.jsonl"

response = requests.get(url, timeout=30)
response.raise_for_status()
data = response.json()

# positive_miners = [miner for miner in data["miners"] if miner.get("share_now", 0) > 0]


positive_miners = [miner for miner in data.get("miners", []) if miner.get("flip_score", 0) > 0 and miner.get("share_now", 0) == 0]

with open(file_path, "w", encoding="utf-8") as f:
    for miner in positive_miners:
        record = {"uid": miner.get("uid", "null"), "hotkey": miner.get("hotkey", "null"), "share_now": miner.get("share_now", 0), "flip_score": miner.get("flip_score", 0), "n_fail_to_pass": miner.get("n_fail_to_pass", 0), "n_pass_to_fail": miner.get("n_pass_to_fail", 0)}
        f.write(f"{record}\n")

for miner in positive_miners:
    print(f'UID: {miner["uid"]}, Hotkey: {miner["hotkey"]}, share_now: {miner["share_now"]}, flip_score: {miner.get("flip_score", "N/A")}, n_fail_to_pass: {miner.get("n_fail_to_pass", "N/A")}, n_pass_to_fail: {miner.get("n_pass_to_fail", "N/A")}')

print(f"\nTotal miners with flip_score > 0 and share_now == 0: {len(positive_miners)}")