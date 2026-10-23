
import json

input_file = "/root/affine/assets/rollouts.jsonl"
output_file = "/root/affine/assets/complete_output.jsonl"

max_tokens = 6000
cut_tokens = 2500
append_tokens = 500
expected_rollouts = 8

kept = 0
trimmed = 0
skipped = 0


def get_tokens(rollout):
    """Convert a rollout into a token list."""
    if isinstance(rollout, list):
        return rollout
    if isinstance(rollout, str):
        return rollout.split()
    raise TypeError(f"Unsupported rollout type: {type(rollout)}")


def restore_format(tokens, original):
    """Preserve the original rollout representation."""
    if isinstance(original, str):
        return " ".join(tokens)
    return tokens


def rollout_length(rollout):
    return len(get_tokens(rollout))


def process_rollouts(rollouts):
    """Trim long rollouts and append tokens from a shorter rollout."""
    updated = list(rollouts)
    trimmed_count = 0

    for i, rollout in enumerate(rollouts):
        tokens = get_tokens(rollout)

        if len(tokens) <= max_tokens:
            continue

        # Remove the last 1500 tokens
        shortened = tokens[:-cut_tokens]

        # Find another original rollout under 6000 tokens
        donor = None

        for j, candidate in enumerate(rollouts):
            if i == j:
                continue

            candidate_tokens = get_tokens(candidate)

            if len(candidate_tokens) < max_tokens:
                donor = candidate_tokens
                break

        # Skip the entire prompt if no donor exists
        if donor is None:
            return None, 0

        # Append the last append_tokens from the donor
        suffix = donor[-append_tokens:]
        combined = shortened + suffix

        updated[i] = restore_format(combined, rollout)
        trimmed_count += 1

    return updated, trimmed_count



with open(input_file, "r", encoding="utf-8") as fin, \
     open(output_file, "w", encoding="utf-8") as fout:

    for line in fin:
        line = line.strip()
        if not line:
            continue

        record = json.loads(line)
        data = record.get("data", record)

        rollouts = (
            data.get("positive_rollouts", [])
            + data.get("negative_rollouts", [])
            + data.get("neutral_rollouts", [])
        )

        # Keep prompts with exactly 8 rollouts
        if len(rollouts) != expected_rollouts:
            skipped += 1
            continue

        updated_rollouts, num_trimmed = process_rollouts(rollouts)

        if updated_rollouts is None:
            skipped += 1
            continue

        trimmed += num_trimmed


        prompt_index = data.get(
            "prob_index",
            data.get(
                "index",
                record.get("prob_index", record.get("index"))
            )
        )

        output_record = {
            "index": prompt_index,
            "rollouts": updated_rollouts,
        }

        fout.write(
            json.dumps(output_record, ensure_ascii=False) + "\n"
        )
        kept += 1

print(f"Kept prompts: {kept}")
print(f"Rollouts modified: {trimmed}")
print(f"Prompts discarded (not exactly 8 rollouts): {skipped}")
print(f"Saved to: {output_file}")
