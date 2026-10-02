"""Verify model-selected measurements against their cited run records."""

import json
import re
from pathlib import Path


METRICS = {
    "train_loss_after_epoch": ("Post-epoch training loss", "loss"),
    "val_loss": ("Validation loss", "loss"),
    "train_accuracy_after_epoch": ("Post-epoch training accuracy", "accuracy"),
    "val_accuracy": ("Validation accuracy", "accuracy"),
}
RUN_ID = re.compile(r"[a-z0-9_-]+")


def display_value(metric: str, recorded_value: float) -> str:
    """Use the same precision and units as the evidence packet."""
    kind = METRICS[metric][1]
    return f"{recorded_value:.4f}" if kind == "loss" else f"{recorded_value * 100:.2f}%"


def check_observations(observations: list[dict], runs_dir: Path) -> list[dict]:
    """Require each run, epoch, metric, and displayed value to match the JSON."""
    if not observations:
        raise ValueError("Answer has no observations to verify")

    checked = []
    records = {}
    for item in observations:
        if not isinstance(item, dict) or set(item) != {"run_id", "epoch", "metric", "value"}:
            raise ValueError(f"Invalid observation fields: {item!r}")
        run_id, epoch, metric, value = (
            item["run_id"], item["epoch"], item["metric"], item["value"]
        )
        if not isinstance(run_id, str) or not RUN_ID.fullmatch(run_id):
            raise ValueError(f"Unsafe run ID: {run_id!r}")
        if not isinstance(epoch, int) or isinstance(epoch, bool) or epoch < 1:
            raise ValueError(f"Invalid epoch: {epoch!r}")
        if metric not in METRICS or not isinstance(value, str):
            raise ValueError(f"Invalid metric or value: {metric!r}, {value!r}")

        if run_id not in records:
            record = json.loads((runs_dir / f"{run_id}.json").read_text(encoding="utf-8"))
            if record["config"]["run_id"] != run_id:
                raise ValueError(f"Run ID does not match record: {run_id}")
            records[run_id] = {row["epoch"]: row for row in record["metrics"]}

        row = records[run_id].get(epoch)
        if row is None or row.get(metric) is None:
            raise ValueError(f"{run_id}: {metric} at epoch {epoch} is not recorded")
        expected = display_value(metric, row[metric])
        if value != expected:
            raise ValueError(
                f"{run_id}: {metric} at epoch {epoch} is {expected}, not {value}"
            )
        checked.append(dict(item))
    return checked


def rise_then_fall_patterns(verified_observations: list[dict]) -> list[dict]:
    """Find three consecutive displayed validation losses that rise, then fall."""
    by_run = {}
    for item in verified_observations:
        if item["metric"] == "val_loss":
            by_run.setdefault(item["run_id"], {})[item["epoch"]] = float(item["value"])

    patterns = []
    for run_id, losses in by_run.items():
        for first_epoch in sorted(losses):
            middle_epoch, last_epoch = first_epoch + 1, first_epoch + 2
            if (
                middle_epoch in losses
                and last_epoch in losses
                and losses[first_epoch] < losses[middle_epoch]
                and losses[last_epoch] < losses[middle_epoch]
            ):
                patterns.append(
                    {
                        "run_id": run_id,
                        "epochs": [first_epoch, middle_epoch, last_epoch],
                        "values": [
                            f"{losses[first_epoch]:.4f}",
                            f"{losses[middle_epoch]:.4f}",
                            f"{losses[last_epoch]:.4f}",
                        ],
                    }
                )
    return patterns


def require_complete_val_loss_history(
    verified_observations: list[dict], run_ids: list[str], runs_dir: Path
) -> None:
    """A no-pattern answer needs every validation-loss epoch from each cited run."""
    supplied = {run_id: set() for run_id in run_ids}
    for item in verified_observations:
        if item["metric"] == "val_loss" and item["run_id"] in supplied:
            supplied[item["run_id"]].add(item["epoch"])

    for run_id in run_ids:
        record = json.loads((runs_dir / f"{run_id}.json").read_text(encoding="utf-8"))
        expected = {row["epoch"] for row in record["metrics"] if row.get("val_loss") is not None}
        missing = sorted(expected - supplied[run_id])
        if missing:
            raise ValueError(
                f"{run_id}: cannot verify no pattern; validation loss missing for epochs {missing}"
            )
