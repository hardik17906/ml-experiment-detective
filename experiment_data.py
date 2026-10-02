"""Read and compare saved experiment records without an LLM."""

import json
import re
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
RUNS_DIR = PROJECT_DIR / "runs"
RUN_ID = re.compile(r"[a-z0-9_-]+")


def load_run(run_id: str) -> dict:
    if not isinstance(run_id, str) or not RUN_ID.fullmatch(run_id):
        raise ValueError(f"Invalid run ID: {run_id!r}")
    path = RUNS_DIR / f"{run_id}.json"
    if not path.is_file():
        raise ValueError(f"Unknown run ID: {run_id}")
    record = json.loads(path.read_text(encoding="utf-8"))
    if record["config"].get("run_id") != run_id:
        raise ValueError(f"Run ID does not match JSON record: {run_id}")
    epochs = [row["epoch"] for row in record["metrics"]]
    if not epochs or epochs != list(range(1, len(epochs) + 1)):
        raise ValueError(f"Epochs are missing or not consecutive in {run_id}")
    return record


def largest_rise(metrics: list[dict]) -> tuple[float, int | None, int | None]:
    rises = [
        (after["val_loss"] - before["val_loss"], before["epoch"], after["epoch"])
        for before, after in zip(metrics, metrics[1:])
        if after["val_loss"] > before["val_loss"]
    ]
    return max(rises) if rises else (0.0, None, None)


def loss_recoveries(metrics: list[dict]) -> list[dict]:
    """List consecutive validation-loss rises followed by falls."""
    patterns = []
    for before, peak, after in zip(metrics, metrics[1:], metrics[2:]):
        if before["val_loss"] < peak["val_loss"] > after["val_loss"]:
            patterns.append({
                "epochs": [before["epoch"], peak["epoch"], after["epoch"]],
                "losses": [round(row["val_loss"], 4) for row in (before, peak, after)],
            })
    return patterns


def get_experiment(run_id: str) -> dict:
    record = load_run(run_id)
    final = record["metrics"][-1]
    return {
        "run_id": run_id,
        "source": f"runs/{run_id}.json",
        "config": record["config"],
        "final_epoch": final["epoch"],
        "final_validation_loss": round(final["val_loss"], 4),
        "final_validation_accuracy_percent": round(100 * final["val_accuracy"], 2),
        "epoch_metrics": [
            {
                "epoch": row["epoch"],
                "validation_loss": round(row["val_loss"], 4),
                "validation_accuracy_percent": round(100 * row["val_accuracy"], 2),
            }
            for row in record["metrics"]
        ],
        "validation_loss_recoveries": loss_recoveries(record["metrics"]),
    }


def compare_experiments(baseline_run_id: str, target_run_id: str) -> dict:
    baseline, target = load_run(baseline_run_id), load_run(target_run_id)
    left, right = baseline["metrics"][-1], target["metrics"][-1]
    if left["epoch"] != right["epoch"]:
        raise ValueError("Cannot compare final metrics from different epochs")
    left_config, right_config = baseline["config"], target["config"]
    changes = {
        key: {"baseline": left_config.get(key), "target": right_config.get(key)}
        for key in sorted(set(left_config) | set(right_config))
        if key != "run_id" and left_config.get(key) != right_config.get(key)
    }
    return {
        "baseline_run_id": baseline_run_id,
        "target_run_id": target_run_id,
        "baseline_source": f"runs/{baseline_run_id}.json",
        "target_source": f"runs/{target_run_id}.json",
        "changed_settings": changes,
        "final_epoch": left["epoch"],
        "baseline_validation_accuracy_percent": round(100 * left["val_accuracy"], 2),
        "target_validation_accuracy_percent": round(100 * right["val_accuracy"], 2),
        "accuracy_change_target_minus_baseline_pp": round(
            100 * (right["val_accuracy"] - left["val_accuracy"]), 2
        ),
        "baseline_validation_loss": round(left["val_loss"], 4),
        "target_validation_loss": round(right["val_loss"], 4),
        "loss_change_target_minus_baseline": round(right["val_loss"] - left["val_loss"], 4),
        "largest_one_epoch_validation_loss_rise": {
            baseline_run_id: round(largest_rise(baseline["metrics"])[0], 4),
            target_run_id: round(largest_rise(target["metrics"])[0], 4),
        },
    }


def search_runs(learning_rate=None, train_size=None, dropout=None) -> dict:
    """Filter exact recorded configuration values; absent fields stay unknown."""
    filters = {
        key: value for key, value in {
            "learning_rate": learning_rate,
            "train_size": train_size,
            "dropout": dropout,
        }.items() if value is not None
    }
    matches = []
    for path in sorted(RUNS_DIR.glob("*.json")):
        record = load_run(path.stem)
        config = record["config"]
        if any(config.get(key) != wanted for key, wanted in filters.items()):
            continue
        final = record["metrics"][-1]
        matches.append({
            "run_id": path.stem,
            "source": f"runs/{path.name}",
            "learning_rate": config.get("learning_rate"),
            "train_size": config.get("train_size"),
            "dropout": config.get("dropout"),
            "final_epoch": final["epoch"],
            "final_validation_accuracy_percent": round(100 * final["val_accuracy"], 2),
            "final_validation_loss": round(final["val_loss"], 4),
        })
    return {"filters": filters, "matches": matches}
