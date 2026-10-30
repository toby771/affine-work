import json
import time
import signal
import sys
import requests
from datetime import datetime, timezone

URL = "https://affine.io/scores.json"

# Enter the UIDs or hotkeys you want to look up
TARGET_IDS = {
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

SNAPSHOT_FILE = "results/default_miners3.jsonl"         # overwritten each cycle
HISTORY_FILE  = "results/default_miners3_history.jsonl"  # appended each cycle
POLL_INTERVAL_SEC = 300
REQUEST_TIMEOUT_SEC = 30


def fetch_miners():
    """One HTTP fetch of scores.json. Returns the miners list."""
    response = requests.get(URL, timeout=REQUEST_TIMEOUT_SEC)
    response.raise_for_status()
    data = response.json()
    return data.get("miners", [])


def filter_matched(miners):
    """Return only miners whose uid or hotkey is in TARGET_IDS."""
    return [
        m for m in miners
        if m.get("uid") in TARGET_IDS or m.get("hotkey") in TARGET_IDS
    ]


def print_matched(matched, cycle_started_at):
    print(f"\n=== {cycle_started_at} | matched: {len(matched)} ===")
    for miner in matched:
        print(
            f"UID: {miner.get('uid', 'N/A')}, "
            f"Hotkey: {miner.get('hotkey', 'N/A')}, "
            f"flip_score: {miner.get('flip_score', 0)}, "
            f"share_now: {miner.get('share_now', 0)}, "
            f"n_events: {miner.get('n_events', 0)}, "
            f"n_fail_to_pass: {miner.get('n_fail_to_pass', 0)}, "
            f"n_pass_to_fail: {miner.get('n_pass_to_fail', 0)}, "
            f"ban_epoch: {miner.get('ban_epoch', 'N/A')}, "
            f"banned: {miner.get('banned', False)}"
        )

    found_ids = {
        value
        for miner in matched
        for value in (miner.get("uid"), miner.get("hotkey"))
        if value in TARGET_IDS
    }
    missing = TARGET_IDS - found_ids
    if missing:
        print("IDs not found:")
        for item in sorted(missing):
            print(f"  {item}")


def to_record(miner, timestamp):
    return {
        "ts": timestamp,
        "uid": miner.get("uid", "null"),
        "hotkey": miner.get("hotkey", "null"),
        "share_now": miner.get("share_now", 0),
        "flip_score": miner.get("flip_score", 0),
        "n_events": miner.get("n_events", 0),
        "n_fail_to_pass": miner.get("n_fail_to_pass", 0),
        "n_pass_to_fail": miner.get("n_pass_to_fail", 0),
        "ban_epoch": miner.get("ban_epoch", "null"),
        "banned": miner.get("banned", False),
    }


def save_snapshot(matched, timestamp):
    """Overwrite snapshot file with the current cycle."""
    import os
    os.makedirs(os.path.dirname(SNAPSHOT_FILE), exist_ok=True)
    with open(SNAPSHOT_FILE, "w", encoding="utf-8") as f:
        for miner in matched:
            f.write(f"{to_record(miner, timestamp)}\n")


def append_history(matched, timestamp):
    """Append this cycle to the history file for time-series tracking."""
    import os
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        for miner in matched:
            f.write(f"{to_record(miner, timestamp)}\n")


def run_once():
    """One full fetch → print → save cycle. Returns True on success."""
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    try:
        miners = fetch_miners()
    except requests.RequestException as exc:
        print(f"[{timestamp}] fetch failed: {type(exc).__name__}: {exc}")
        return False

    matched = filter_matched(miners)
    print_matched(matched, timestamp)

    try:
        save_snapshot(matched, timestamp)
        append_history(matched, timestamp)
    except OSError as exc:
        print(f"[{timestamp}] save failed: {exc}")
        return False

    print(f"[{timestamp}] snapshot -> {SNAPSHOT_FILE} | history -> {HISTORY_FILE}")
    return True


def _handle_sigint(_signum, _frame):
    print("\nInterrupted, exiting cleanly.")
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, _handle_sigint)

    print(f"Polling {URL} every {POLL_INTERVAL_SEC}s "
          f"(snapshot={SNAPSHOT_FILE}, history={HISTORY_FILE})")

    while True:
        cycle_start = time.time()
        run_once()

        # Sleep so that the *start-to-start* interval is POLL_INTERVAL_SEC,
        # even if the fetch/save took a couple of seconds.
        elapsed = time.time() - cycle_start
        sleep_for = max(0.0, POLL_INTERVAL_SEC - elapsed)
        print(f"Sleeping {sleep_for:.1f}s ...")
        time.sleep(sleep_for)


if __name__ == "__main__":
    main()