import requests

url = "https://affine.io/scores.json"

# Enter the UIDs or hotkeys you want to look up
target_ids = {
    "5C4hvCUvqe8MdawADYmc66t6j967u5qtsnm42Ho66Qeup8Xn",
    "5GcvUzSSjsjTMvGbwbjc4Qrm9qcPyX4W3dpCb4Txpf4Egg5L",
    "5C4hx6fDcShomugnuLdRuQKWgMRJZpyxBJHQby6NzMfGFgbn",
    "5C4hvA2raFNJFo37vzfWDJEohpMDzgP8UszcDjNezJYMRokF",
    # "5C4htAPa3RNhqxLWjkmXTpeoq84PmwpjNud3pcMHSZ5jKs6L",
    "5C4hw8JS3viwDTNR6vVf7ZXgn3GQd2GFJwdWJRcWYXCenx7R",
    "5C4huX9WzRNEXjpkrKSFwbLhxfy63eTJWgmX9LkzVPA8aB5z",
    "5C4hwyBiuRNwVkxCppMAs49Xp3st5DGTyjFjNnhPfVFkEBHH",
    "5C4hu3embtQVmYjFex3yhb2TMM8rmpkscEsP7nwiWv8payMV",
    "5C4ht51skzw9KVVo3dKeFLfQ8j6LCuoUy3FdXJJBPJ6A9zQf",
    "5C4hsAn4h9Vrou8MsfDorAWaEtKaXpMm4gsh7y5Wngsiagex",
    "5C4hxs4qcPCRKAGDXdZVuRphHcfuSQ8aTsrhdQWG6Y1CZR4a",
    "5C4hzM3JF2JpPi5dxMpksP4Ap8xZ6DV6uTTkbqCB3zBd1uXz",
    "5C4hytx5XFNz4mNhuogwfp62tjeS4m2t5L1Y4tuLX9C2RbtW",
    "5C4hzf4t3AKxsLfnvyP3hCdSHwxSrnSy6UNu4jJbzpHuR7jQ",
    "5C4hxgQwM2Q9g7N8vtkRWdfzLdYRLoWehVDfTtcV6ips5xUq",
    "5C4hy7uR3EbyCLmAS4DYD3i4AKQ47pSfcQdBZYw5hErEP43J",
}

file_path = "results/default_miners3.jsonl"

response = requests.get(url, timeout=30)
response.raise_for_status()
data = response.json()

# Match against either UID or hotkey
matched_miners = [
    miner
    for miner in data.get("miners", [])
    if miner.get("uid") in target_ids
    or miner.get("hotkey") in target_ids
]

for miner in matched_miners:
    print(
        f"UID: {miner.get('uid', 'N/A')}, "
        f"Hotkey: {miner.get('hotkey', 'N/A')}, "
        f"flip_score: {miner.get('flip_score', 0)}, "
        f"share_now: {miner.get('share_now', 0)}"
    )


with open(file_path, "w", encoding="utf-8") as f:
    for miner in matched_miners:
        record = {"uid": miner.get("uid", "null"), "hotkey": miner.get("hotkey", "null"), "share_now": miner.get("share_now", 0), "flip_score": miner.get("flip_score", 0), "n_fail_to_pass": miner.get("n_fail_to_pass", 0), "n_pass_to_fail": miner.get("n_pass_to_fail", 0)}
        f.write(f"{record}\n")

print(f"\nTotal matched miners: {len(matched_miners)}")

# Show IDs that were not found
found_ids = {
    value
    for miner in matched_miners
    for value in (miner.get("uid"), miner.get("hotkey"))
    if value in target_ids
}

missing_ids = target_ids - found_ids

if missing_ids:
    print("\nIDs not found:")
    for item in sorted(missing_ids):
        print(item)