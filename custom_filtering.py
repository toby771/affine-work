import json
import random

input_file = "/mnt/d/Exercise/Affine_work/affine_work/dataset/available_keys_12.jsonl"
output_file = "/mnt/d/Exercise/Affine_work/affine_work/dataset/filtering_6_2_output.jsonl"

MAX_TOKENS = 6000
KEEP_FIRST = 2000
KEEP_LAST = 1000

# Customize the target counts here.
TARGET_PER_CLASS = {
    "positive": 6,
    "negative": 2,
}

random.seed(42)

stats = {
    "kept": 0,
    "skipped": 0,
    "invalid_json": 0,
    "long_repaired": 0,
    "long_unrepairable": 0,
    "class_conversions": 0,
    "neutral_conversions": 0,
}


def tokenize_rollout(rollout):
    if isinstance(rollout, list):
        return rollout
    if isinstance(rollout, str):
        return rollout.split()

    raise TypeError(
        f"Unsupported rollout type: {type(rollout).__name__}"
    )


def restore_format(tokens, original):
    if isinstance(original, str):
        return " ".join(tokens)
    return tokens


def rollout_length(rollout):
    return len(tokenize_rollout(rollout))


def get_rollouts(data, category):
    value = data.get(category, [])
    return value if isinstance(value, list) else []


def make_candidates(rollouts, label):
    result = []

    for rollout in rollouts:
        try:
            tokenize_rollout(rollout)
        except (TypeError, ValueError):
            continue

        result.append({
            "rollout": rollout,
            "label": label,
            "repaired": False,
            "converted": False,
        })

    return result


def make_candidate(
    rollout,
    label,
    repaired=False,
    converted=False,
):
    return {
        "rollout": rollout,
        "label": label,
        "repaired": repaired,
        "converted": converted,
    }


def repair_long_rollouts(positive, negative, neutral):
    """
    Repair rollouts longer than MAX_TOKENS:
      - Keep the first KEEP_FIRST tokens.
      - Append the last KEEP_LAST tokens of a donor rollout.
      - Inherit the donor's class.

    Donors must have at least KEEP_LAST tokens and fewer
    than MAX_TOKENS tokens.
    """
    all_candidates = positive + negative + neutral

    donors = [
        item for item in all_candidates
        if KEEP_LAST <= rollout_length(item["rollout"]) < MAX_TOKENS
    ]

    repaired_by_label = {
        "positive": [],
        "negative": [],
        "neutral": [],
    }

    random.shuffle(all_candidates)

    for candidate in all_candidates:
        rollout = candidate["rollout"]
        tokens = tokenize_rollout(rollout)

        if len(tokens) <= MAX_TOKENS:
            repaired_by_label[candidate["label"]].append(candidate)
            continue

        eligible = [
            donor for donor in donors
            if donor is not candidate
        ]

        if not eligible:
            stats["long_unrepairable"] += 1
            continue

        donor = random.choice(eligible)
        donor_tokens = tokenize_rollout(donor["rollout"])

        new_tokens = tokens[:KEEP_FIRST] + donor_tokens[-KEEP_LAST:]
        new_rollout = restore_format(new_tokens, rollout)

        repaired_by_label[donor["label"]].append(
            make_candidate(
                new_rollout,
                label=donor["label"],
                repaired=True,
            )
        )

        stats["long_repaired"] += 1

    return (
        repaired_by_label["positive"],
        repaired_by_label["negative"],
        repaired_by_label["neutral"],
    )


def convert_rollout(source, donor, target_label):
    """
    Replace the source rollout's final KEEP_LAST tokens with
    the donor rollout's final KEEP_LAST tokens.

    The converted rollout inherits target_label.
    """
    source_tokens = tokenize_rollout(source["rollout"])
    donor_tokens = tokenize_rollout(donor["rollout"])

    if len(donor_tokens) < KEEP_LAST:
        return None

    prefix = source_tokens[:-KEEP_LAST]
    new_tokens = prefix + donor_tokens[-KEEP_LAST:]

    if len(new_tokens) > MAX_TOKENS:
        return None

    new_rollout = restore_format(new_tokens, source["rollout"])

    return make_candidate(
        new_rollout,
        label=target_label,
        repaired=source["repaired"] or donor["repaired"],
        converted=True,
    )


def balance_rollouts(data):
    """
    First repair long rollouts, then balance to the configured
    positive and negative targets.

    Excess candidates can be converted to the underrepresented
    class by replacing their final KEEP_LAST tokens with the
    ending of a rollout from the target class.

    Neutral candidates can fill remaining shortages by receiving
    an ending from a rollout in the target class.
    """
    positive = make_candidates(
        get_rollouts(data, "positive_rollouts"),
        "positive",
    )
    negative = make_candidates(
        get_rollouts(data, "negative_rollouts"),
        "negative",
    )
    neutral = make_candidates(
        get_rollouts(data, "neutral_rollouts"),
        "neutral",
    )

    positive_target = TARGET_PER_CLASS["positive"]
    negative_target = TARGET_PER_CLASS["negative"]

    # STEP 1: Repair long rollouts.
    positive, negative, neutral = repair_long_rollouts(
        positive, negative, neutral
    )

    random.shuffle(positive)
    random.shuffle(negative)
    random.shuffle(neutral)

    # Donors must have at least KEEP_LAST tokens.
    positive_donors = [
        c for c in positive
        if rollout_length(c["rollout"]) >= KEEP_LAST
    ]
    negative_donors = [
        c for c in negative
        if rollout_length(c["rollout"]) >= KEEP_LAST
    ]

    # STEP 2: Convert excess positive candidates to negative
    # if negative is short.
    while (
        len(negative) < negative_target
        and len(positive) > positive_target
    ):
        source = positive[-1]

        donors = [
            d for d in negative_donors
            if d is not source
        ]

        if not donors:
            break

        donor = random.choice(donors)
        converted = convert_rollout(source, donor, "negative")

        if converted is None:
            break

        positive.pop()
        negative.append(converted)
        negative_donors.append(converted)
        stats["class_conversions"] += 1

    # STEP 3: Convert excess negative candidates to positive
    # if positive is short.
    while (
        len(positive) < positive_target
        and len(negative) > negative_target
    ):
        source = negative[-1]

        donors = [
            d for d in positive_donors
            if d is not source
        ]

        if not donors:
            break

        donor = random.choice(donors)
        converted = convert_rollout(source, donor, "positive")

        if converted is None:
            break

        negative.pop()
        positive.append(converted)
        positive_donors.append(converted)
        stats["class_conversions"] += 1

    # STEP 4: Use neutral candidates to fill positive shortages.
    while (
        len(positive) < positive_target
        and neutral
        and positive_donors
    ):
        source = neutral[-1]
        donor = random.choice(positive_donors)

        converted = convert_rollout(source, donor, "positive")

        neutral.pop()

        if converted is None:
            continue

        positive.append(converted)
        positive_donors.append(converted)
        stats["neutral_conversions"] += 1

    # STEP 5: Use neutral candidates to fill negative shortages.
    while (
        len(negative) < negative_target
        and neutral
        and negative_donors
    ):
        source = neutral[-1]
        donor = random.choice(negative_donors)

        converted = convert_rollout(source, donor, "negative")

        neutral.pop()

        if converted is None:
            continue

        negative.append(converted)
        negative_donors.append(converted)
        stats["neutral_conversions"] += 1

    # STEP 6: Verify enough candidates remain.
    if (
        len(positive) < positive_target
        or len(negative) < negative_target
    ):
        return None

    # Select exactly the configured number of candidates.
    random.shuffle(positive)
    random.shuffle(negative)

    selected_positive = positive[:positive_target]
    selected_negative = negative[:negative_target]

    # STEP 7: Validate labels and lengths.
    for candidate in selected_positive:
        if candidate["label"] != "positive":
            return None
        if rollout_length(candidate["rollout"]) > MAX_TOKENS:
            return None

    for candidate in selected_negative:
        if candidate["label"] != "negative":
            return None
        if rollout_length(candidate["rollout"]) > MAX_TOKENS:
            return None

    return selected_positive, selected_negative


with (
    open(input_file, "r", encoding="utf-8") as fin,
    open(output_file, "w", encoding="utf-8") as fout,
):
    for line_number, line in enumerate(fin, start=1):
        line = line.strip()

        if not line:
            continue

        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            print(f"Invalid JSON on line {line_number}: {exc}")
            stats["invalid_json"] += 1
            stats["skipped"] += 1
            continue

        data = record.get("data", record)

        if not isinstance(data, dict):
            print(f"Skipping line {line_number}: data is not a dict")
            stats["skipped"] += 1
            continue

        try:
            balanced = balance_rollouts(data)
        except (TypeError, ValueError) as exc:
            print(f"Skipping line {line_number}: {exc}")
            stats["skipped"] += 1
            continue

        if balanced is None:
            print(
                f"Skipping line {line_number}: cannot balance to "
                f"{TARGET_PER_CLASS['positive']} positive and "
                f"{TARGET_PER_CLASS['negative']} negative rollouts"
            )
            stats["skipped"] += 1
            continue

        selected_positive, selected_negative = balanced

        positive_rollouts = [
            item["rollout"] for item in selected_positive
        ]
        negative_rollouts = [
            item["rollout"] for item in selected_negative
        ]

        # Final assertions before writing.
        assert len(positive_rollouts) == TARGET_PER_CLASS["positive"]
        assert len(negative_rollouts) == TARGET_PER_CLASS["negative"]

        assert all(
            rollout_length(r) <= MAX_TOKENS
            for r in positive_rollouts + negative_rollouts
        )

        selected = selected_positive + selected_negative

        output_record = {
            "index": data.get(
                "prob_index",
                data.get(
                    "index",
                    record.get(
                        "prob_index",
                        record.get("index"),
                    ),
                ),
            ),
            "positive_rollouts": positive_rollouts,
            "negative_rollouts": negative_rollouts,
            "rollouts": positive_rollouts + negative_rollouts,
            "needs_label_review": any(
                item["repaired"] or item["converted"]
                for item in selected
            ),
        }

        fout.write(
            json.dumps(output_record, ensure_ascii=False) + "\n"
        )

        stats["kept"] += 1

        print(
            f"Line {line_number}: saved; "
            f"positive={len(positive_rollouts)}, "
            f"negative={len(negative_rollouts)}"
        )


print("\n========== SUMMARY ==========")
print(f"Kept prompts: {stats['kept']}")
print(f"Prompts skipped: {stats['skipped']}")
print(f"Invalid JSON lines: {stats['invalid_json']}")
print(f"Long rollouts repaired: {stats['long_repaired']}")
print(f"Long rollouts without donors: {stats['long_unrepairable']}")
print(f"Positive/negative conversions: {stats['class_conversions']}")
print(f"Neutral conversions: {stats['neutral_conversions']}")
print(f"Saved to: {output_file}")
