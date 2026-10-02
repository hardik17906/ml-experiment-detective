"""Build one evidence-and-counterevidence worksheet for matched learning-rate pairs."""

import argparse
import json
import re
from pathlib import Path

from experiment_data import largest_rise, load_run


PROJECT_DIR = Path(__file__).resolve().parent
ID = re.compile(r"[a-z0-9_-]+")
BLOCK_KEYS = {"run_id", "learning_rate", "model_seed", "shuffle_seed"}


def analyze_pair(low_id: str, high_id: str) -> dict:
    low, high = load_run(low_id), load_run(high_id)
    low_config, high_config = low["config"], high["config"]
    changes = sorted(
        key
        for key in set(low_config) | set(high_config)
        if key != "run_id" and low_config.get(key) != high_config.get(key)
    )
    if changes != ["learning_rate"]:
        raise ValueError(
            f"{low_id} vs {high_id}: expected only learning_rate to differ; found {changes}"
        )
    if low_config["learning_rate"] >= high_config["learning_rate"]:
        raise ValueError(f"{low_id} vs {high_id}: low/high learning-rate order is wrong")
    if low["metrics"][-1]["epoch"] != high["metrics"][-1]["epoch"]:
        raise ValueError(f"{low_id} vs {high_id}: final epochs differ")

    low_final, high_final = low["metrics"][-1], high["metrics"][-1]
    return {
        "low_id": low_id,
        "high_id": high_id,
        "low_config": low_config,
        "high_config": high_config,
        "low_rise": largest_rise(low["metrics"]),
        "high_rise": largest_rise(high["metrics"]),
        "low_accuracy": low_final["val_accuracy"],
        "high_accuracy": high_final["val_accuracy"],
        "low_loss": low_final["val_loss"],
        "high_loss": high_final["val_loss"],
        "final_epoch": low_final["epoch"],
    }


def rise_text(rise: tuple[float, int | None, int | None]) -> str:
    amount, start, end = rise
    return f"+{amount:.4f} (epochs {start}→{end})" if start is not None else "none"


def build_worksheet(case: dict) -> str:
    pairs = [analyze_pair(item["low"], item["high"]) for item in case["pairs"]]
    if len(pairs) < 2:
        raise ValueError("At least two matched seed blocks are needed for this worksheet")
    reference = pairs[0]
    low_configs = [pair["low_config"] for pair in pairs]
    setting_keys = set().union(*(set(config) for config in low_configs)) - BLOCK_KEYS
    missing_across_blocks = []
    for key in sorted(setting_keys):
        recorded_values = [config[key] for config in low_configs if key in config]
        if any(value != recorded_values[0] for value in recorded_values[1:]):
            raise ValueError(f"Recorded {key} differs across seed blocks")
        if len(recorded_values) != len(low_configs):
            missing_across_blocks.append(key)
    seed_blocks = set()
    for pair in pairs:
        if (
            pair["low_config"]["learning_rate"],
            pair["high_config"]["learning_rate"],
            pair["final_epoch"],
        ) != (
            reference["low_config"]["learning_rate"],
            reference["high_config"]["learning_rate"],
            reference["final_epoch"],
        ):
            raise ValueError("Learning rates or final epochs differ across seed blocks")
        seed_block = (
            pair["low_config"]["model_seed"], pair["low_config"]["shuffle_seed"]
        )
        if seed_block in seed_blocks:
            raise ValueError("Seed block repeated instead of replicated")
        seed_blocks.add(seed_block)

    low_lr = reference["low_config"]["learning_rate"]
    high_lr = reference["high_config"]["learning_rate"]
    lines = [
        f"# Hypothesis worksheet: {case['id']}",
        "",
        f"**Question:** {case['question']}",
        "",
        "## Candidate hypothesis",
        "",
        f"Raising the learning rate from {low_lr:g} to {high_lr:g} may contribute to lower final validation accuracy by producing larger temporary validation-loss increases. This is a testable possibility, not a causal finding.",
        "",
        "## Matched observations",
        "",
        "Within each seed block, the saved configurations differ only in `learning_rate`. Across blocks, settings recorded in every run agree; model and shuffle seeds change together.",
        f"All final measurements are from epoch {reference['final_epoch']}.",
    ]
    if missing_across_blocks:
        fields = ", ".join(f"`{key}`" for key in missing_across_blocks)
        lines.append(
            f"Metadata gap: {fields} are absent from some older run records. Their equality across all blocks cannot be verified from saved JSON."
        )
    lines.extend(
        [
            "",
            "| Seed block (model/shuffle) | Learning rates and source runs | Largest validation-loss rise (low → high) | Final validation accuracy (low → high; high − low) |",
            "| --- | --- | --- | --- |",
        ]
    )
    for pair in pairs:
        model_seed = pair["low_config"]["model_seed"]
        shuffle_seed = pair["low_config"]["shuffle_seed"]
        accuracy_change = 100 * (pair["high_accuracy"] - pair["low_accuracy"])
        lines.append(
            f"| {model_seed}/{shuffle_seed} | "
            f"{low_lr:g}: [{pair['low_id']}](../runs/{pair['low_id']}.json); "
            f"{high_lr:g}: [{pair['high_id']}](../runs/{pair['high_id']}.json) | "
            f"{rise_text(pair['low_rise'])} → {rise_text(pair['high_rise'])} | "
            f"{100 * pair['low_accuracy']:.2f}% → {100 * pair['high_accuracy']:.2f}% "
            f"({accuracy_change:+.2f} pp) |"
        )

    lines.extend(["", "## Evidence supporting the hypothesis", ""])
    for pair in pairs:
        label = f"seeds {pair['low_config']['model_seed']}/{pair['low_config']['shuffle_seed']}"
        if pair["high_rise"][0] > pair["low_rise"][0]:
            lines.append(
                f"- With {label}, the higher learning rate had a larger maximum one-epoch validation-loss increase: {rise_text(pair['high_rise'])} versus {rise_text(pair['low_rise'])}."
            )
        if pair["high_accuracy"] < pair["low_accuracy"]:
            difference = 100 * (pair["low_accuracy"] - pair["high_accuracy"])
            lines.append(
                f"- With {label}, final validation accuracy was {difference:.2f} percentage points lower at the higher learning rate."
            )

    lines.extend(["", "## Counterevidence and limits", ""])
    for pair in pairs:
        label = f"seeds {pair['low_config']['model_seed']}/{pair['low_config']['shuffle_seed']}"
        if pair["high_rise"][0] <= pair["low_rise"][0]:
            lines.append(f"- With {label}, the higher learning rate did not have a larger one-epoch validation-loss rise.")
        if pair["high_accuracy"] >= pair["low_accuracy"]:
            difference = 100 * (pair["high_accuracy"] - pair["low_accuracy"])
            lines.append(
                f"- With {label}, final validation accuracy was {difference:.2f} percentage points higher at the higher learning rate. A larger loss rise did not imply worse final accuracy in this block."
            )
    lines.extend(
        [
            f"- Only {len(pairs)} matched seed blocks are recorded here. A one-epoch validation-loss rise is a descriptive measure, not a direct measurement of the optimizer's mechanism.",
            "",
            "## Missing evidence and next controlled test",
            "",
            f"Run more matched seed blocks: train one model at learning rate {low_lr:g} and one at {high_lr:g} per block, keeping the same recorded settings and validation split within and across blocks. Compare per-block final validation accuracy and maximum one-epoch validation-loss rise before making a broader claim.",
            "",
            "The saved runs show an association in these blocks. They do not establish that the learning rate caused an accuracy change, and they do not estimate how often either outcome occurs across seeds.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a matched-run hypothesis worksheet")
    parser.add_argument("case_id", help="ID from hypothesis_cases.json")
    args = parser.parse_args()
    if not ID.fullmatch(args.case_id):
        parser.error("case_id must use lowercase letters, numbers, underscores, or hyphens")
    cases = json.loads((PROJECT_DIR / "hypothesis_cases.json").read_text(encoding="utf-8"))
    case = next((item for item in cases if item["id"] == args.case_id), None)
    if case is None:
        parser.error(f"unknown case ID: {args.case_id}")
    output = PROJECT_DIR / "hypotheses" / f"{args.case_id}.md"
    if output.exists():
        parser.error(f"worksheet already exists: {output}")
    worksheet = build_worksheet(case)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as file:
        file.write(worksheet)
    print(f"Saved: {output}")
    print(f"Matched seed blocks: {len(case['pairs'])}")
    print("Hypothesis status: tentative; review both support and counterevidence")


if __name__ == "__main__":
    main()
