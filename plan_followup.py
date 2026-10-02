"""Prepare one matched seed-block plan without training either model."""

import argparse
import hashlib
import json
import re
from pathlib import Path

from build_hypothesis_worksheet import analyze_pair, build_worksheet, load_run


PROJECT_DIR = Path(__file__).resolve().parent
ID = re.compile(r"[a-z0-9_-]+")
FIXED_KEYS = ("dataset", "source_partition", "preprocessing", "train_size", "val_size", "split_seed")
OLDER_MISSING_DEFAULTS = {"validation_start": 10000, "dropout": 0.0}


def build_plan(recipe: dict, hypothesis_case: dict) -> dict:
    build_worksheet(hypothesis_case)  # Recheck the source pairs before extending them.
    source_outcomes = []
    for item in hypothesis_case["pairs"]:
        pair = analyze_pair(item["low"], item["high"])
        source_outcomes.append({
            "low_run_id": pair["low_id"],
            "high_run_id": pair["high_id"],
            "model_seed": pair["low_config"]["model_seed"],
            "shuffle_seed": pair["low_config"]["shuffle_seed"],
            "accuracy_delta_pp": round(100 * (pair["high_accuracy"] - pair["low_accuracy"]), 2),
            "larger_loss_rise_at_high": pair["high_rise"][0] > pair["low_rise"][0],
        })
    low_id, high_id = recipe["low_run_id"], recipe["high_run_id"]
    if not all(ID.fullmatch(run_id) for run_id in (low_id, high_id)) or low_id == high_id:
        raise ValueError("New run IDs must be distinct, safe names")
    for run_id in (low_id, high_id):
        if (PROJECT_DIR / "runs" / f"{run_id}.json").exists():
            raise ValueError(f"Proposed run ID already exists: {run_id}")

    model_seed, shuffle_seed = recipe["model_seed"], recipe["shuffle_seed"]
    if any(not isinstance(seed, int) or isinstance(seed, bool) or seed < 0 for seed in (model_seed, shuffle_seed)):
        raise ValueError("Proposed seeds must be nonnegative integers")

    source_records = [
        load_run(run_id)
        for pair in hypothesis_case["pairs"]
        for run_id in (pair["low"], pair["high"])
    ]
    used_seed_blocks = set()
    for path in (PROJECT_DIR / "runs").glob("*.json"):
        config = json.loads(path.read_text(encoding="utf-8"))["config"]
        if "model_seed" in config and "shuffle_seed" in config:
            used_seed_blocks.add((config["model_seed"], config["shuffle_seed"]))
    if (model_seed, shuffle_seed) in used_seed_blocks:
        raise ValueError("Proposed model/shuffle seed block already appears in a saved run")

    first_low = source_records[0]["config"]
    first_high = source_records[1]["config"]
    for record in source_records:
        config = record["config"]
        if any(config.get(key) != first_low.get(key) for key in FIXED_KEYS):
            raise ValueError("Source runs disagree on data or validation-split settings")
    shared = {
        key: value for key, value in first_low.items()
        if key not in {"run_id", "learning_rate", "model_seed", "shuffle_seed"}
    }
    missing_from_old = sorted(
        key for key in OLDER_MISSING_DEFAULTS
        if any(key not in record["config"] for record in source_records)
    )
    for key, default in OLDER_MISSING_DEFAULTS.items():
        if key in shared and shared[key] != default:
            raise ValueError(f"Existing {key} does not match the current training default")
        shared[key] = default

    planned = []
    for run_id, learning_rate in (
        (low_id, first_low["learning_rate"]),
        (high_id, first_high["learning_rate"]),
    ):
        config = {
            "run_id": run_id,
            **shared,
            "model_seed": model_seed,
            "shuffle_seed": shuffle_seed,
            "learning_rate": learning_rate,
        }
        command = (
            f"python phase0.py --run-id {run_id} --learning-rate {learning_rate:g} "
            f"--model-seed {model_seed} --shuffle-seed {shuffle_seed} "
            f"--train-size {config['train_size']} --epochs {config['epochs']} "
            f"--dropout {config['dropout']:g}"
        )
        planned.append({"config": config, "command": command})

    left, right = planned[0]["config"], planned[1]["config"]
    changed = sorted(
        key for key in set(left) | set(right)
        if key != "run_id" and left.get(key) != right.get(key)
    )
    if changed != ["learning_rate"]:
        raise ValueError(f"Planned pair changes unexpected settings: {changed}")
    phase0_path = PROJECT_DIR / "phase0.py"
    return {
        "plan_id": recipe["id"],
        "hypothesis_case_id": hypothesis_case["id"],
        "phase0_sha256": hashlib.sha256(phase0_path.read_bytes()).hexdigest(),
        "changed_setting": "learning_rate",
        "older_record_fields_not_explicit": missing_from_old,
        "source_outcomes": source_outcomes,
        "planned_runs": planned,
    }


def render_plan(plan: dict) -> str:
    first, second = plan["planned_runs"]
    config = first["config"]
    lines = [
        f"# Controlled follow-up plan: {plan['plan_id']}",
        "",
        f"Source hypothesis case: [worksheet](../hypotheses/{plan['hypothesis_case_id']}.md)",
        "",
        "## Why another seed block?",
        "",
        f"Each row below compares learning rate {second['config']['learning_rate']:g} with {first['config']['learning_rate']:g} on the same saved validation split. A negative accuracy difference means the higher learning rate finished worse in that seed block.",
        "",
        "| Model/shuffle seeds | Source runs (low, high) | Final accuracy difference (high − low) | Larger loss rise at high rate? |",
        "| --- | --- | ---: | --- |",
    ]
    for outcome in plan["source_outcomes"]:
        low_id, high_id = outcome["low_run_id"], outcome["high_run_id"]
        lines.append(
            f"| {outcome['model_seed']}/{outcome['shuffle_seed']} | "
            f"[{low_id}](../runs/{low_id}.json), [{high_id}](../runs/{high_id}.json) | "
            f"{outcome['accuracy_delta_pp']:+.2f} pp | "
            f"{'yes' if outcome['larger_loss_rise_at_high'] else 'no'} |"
        )
    negative_count = sum(outcome["accuracy_delta_pp"] < 0 for outcome in plan["source_outcomes"])
    rise_count = sum(outcome["larger_loss_rise_at_high"] for outcome in plan["source_outcomes"])
    prior_count = len(plan["source_outcomes"])
    lines.extend([
        "",
        f"So far, final accuracy was lower at the higher rate in {negative_count}/{prior_count} blocks; its largest one-epoch validation-loss rise was larger in {rise_count}/{prior_count}.",
        f"If the new pair has lower final accuracy at the higher rate, the first count becomes {negative_count + 1}/{prior_count + 1}; otherwise it stays {negative_count}/{prior_count + 1}. Either result adds one observation, not a general rule.",
        "",
        "## Question this pair tests",
        "",
        "In one new seed block, does raising learning rate produce a larger temporary validation-loss rise or lower final validation accuracy? Does the final-accuracy difference point down, up, or stay level?",
        "",
        "## Controlled settings",
        "",
        f"Both runs use model seed {config['model_seed']} and shuffle seed {config['shuffle_seed']}. They differ only in `learning_rate` among planned settings.",
        f"Both use Fashion-MNIST, training size {config['train_size']}, split seed {config['split_seed']}, and the same validation indices selected from positions {config['validation_start']} through {config['validation_start'] + config['val_size'] - 1} of the seeded permutation.",
        f"Both train for {config['epochs']} epochs with dropout {config['dropout']:g}.",
        "",
        "## Planned runs",
        "",
        f"| Run ID | Learning rate | Model seed | Shuffle seed |",
        "| --- | ---: | ---: | ---: |",
    ])
    for item in (first, second):
        row = item["config"]
        lines.append(
            f"| {row['run_id']} | {row['learning_rate']:g} | {row['model_seed']} | {row['shuffle_seed']} |"
        )
    lines.extend(["", "Commands to execute after reviewing the plan:", "", "```powershell"])
    lines.extend(item["command"] for item in (first, second))
    lines.extend(["```", "", "## Verification boundary", ""])
    if plan["older_record_fields_not_explicit"]:
        lines.append(
            "Older source JSON does not explicitly record "
            + ", ".join(f"`{key}`" for key in plan["older_record_fields_not_explicit"])
            + ". The new runs will record those current-script settings; equality with older runs cannot be established from old JSON alone."
        )
    lines.extend(
        [
            "No training runs were launched while creating this plan. This file contains no new run metrics.",
            f"Training script SHA-256 at planning time: `{plan['phase0_sha256']}`.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Save a controlled follow-up experiment plan")
    parser.add_argument("plan_id", help="ID from followup_plan_cases.json")
    args = parser.parse_args()
    if not ID.fullmatch(args.plan_id):
        parser.error("plan_id must use lowercase letters, numbers, underscores, or hyphens")
    recipes = json.loads((PROJECT_DIR / "followup_plan_cases.json").read_text(encoding="utf-8"))
    recipe = next((item for item in recipes if item["id"] == args.plan_id), None)
    if recipe is None:
        parser.error(f"unknown plan ID: {args.plan_id}")
    cases = json.loads((PROJECT_DIR / "hypothesis_cases.json").read_text(encoding="utf-8"))
    hypothesis_case = next(
        (item for item in cases if item["id"] == recipe["hypothesis_case_id"]), None
    )
    if hypothesis_case is None:
        parser.error("source hypothesis case does not exist")
    json_path = PROJECT_DIR / "plans" / f"{args.plan_id}.json"
    markdown_path = PROJECT_DIR / "plans" / f"{args.plan_id}.md"
    if json_path.exists() or markdown_path.exists():
        parser.error("plan already exists; choose a new plan ID")
    plan = build_plan(recipe, hypothesis_case)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("x", encoding="utf-8") as file:
        json.dump(plan, file, indent=2)
        file.write("\n")
    with markdown_path.open("x", encoding="utf-8") as file:
        file.write(render_plan(plan))
    print(f"Saved plan: {markdown_path}")
    print(f"Saved configuration: {json_path}")
    print(f"New seed block: {recipe['model_seed']}/{recipe['shuffle_seed']}")
    print("Planned setting difference: learning_rate only")
    print("Training runs launched: 0")


if __name__ == "__main__":
    main()
