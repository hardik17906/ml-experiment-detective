"""Deterministic descriptions and aggregates over saved run JSON."""

from statistics import mean, median

from experiment_data import RUNS_DIR, largest_rise, load_run, loss_recoveries


def rank_experiments(sort_by="accuracy", learning_rate=None, train_size=None, dropout=None, top_k=11):
    """Rank saved results; a spike is a measured positive epoch-to-epoch loss rise."""
    from experiment_data import search_runs
    if sort_by not in {"accuracy", "loss", "spike"} or type(top_k) is not int or not 1 <= top_k <= 20:
        raise ValueError("Choose accuracy/loss/spike and top_k between 1 and 20")
    result = search_runs(learning_rate, train_size, dropout)
    for row in result["matches"]:
        row["largest_loss_rise"] = round(largest_rise(load_run(row["run_id"])["metrics"])[0], 6)
    key = {"accuracy": "final_validation_accuracy_percent", "loss": "final_validation_loss", "spike": "largest_loss_rise"}[sort_by]
    result["matches"].sort(key=lambda r: ((r[key] if sort_by == "loss" else -r[key]), r["run_id"]))
    result.update(sort_by=sort_by, total_matches=len(result["matches"]),
                  limit="Ranking saved records is descriptive; configurations and horizons can differ. A loss rise is not a diagnosis.")
    result["matches"] = result["matches"][:top_k]
    return result


def summarize_run_curve(run_id: str) -> dict:
    record = load_run(run_id)
    rows = record["metrics"]
    best_accuracy = max(rows, key=lambda row: row["val_accuracy"])
    lowest_loss = min(rows, key=lambda row: row["val_loss"])
    rise, from_epoch, to_epoch = largest_rise(rows)
    last = rows[-1]
    return {
        "run_id": run_id,
        "source": f"runs/{run_id}.json",
        "final_epoch": last["epoch"],
        "final_validation_accuracy_percent": round(100 * last["val_accuracy"], 2),
        "final_validation_loss": round(last["val_loss"], 4),
        "best_validation_accuracy_percent": round(100 * best_accuracy["val_accuracy"], 2),
        "best_accuracy_epoch": best_accuracy["epoch"],
        "minimum_validation_loss": round(lowest_loss["val_loss"], 4),
        "minimum_loss_epoch": lowest_loss["epoch"],
        "largest_one_epoch_validation_loss_rise": round(rise, 4),
        "largest_rise_epochs": [from_epoch, to_epoch] if from_epoch is not None else [],
        "validation_loss_recoveries": loss_recoveries(rows),
    }


def find_overfitting_candidates() -> dict:
    """A transparent warning: a training-loss fall with a validation-loss rise."""
    matches = []
    for path in sorted(RUNS_DIR.glob("*.json")):
        rows = load_run(path.stem)["metrics"]
        intervals = []
        for before, after in zip(rows, rows[1:]):
            a, b = before.get("train_loss_after_epoch"), after.get("train_loss_after_epoch")
            if a is None or b is None:
                continue
            if b < a and after["val_loss"] > before["val_loss"]:
                intervals.append({
                    "epochs": [before["epoch"], after["epoch"]],
                    "train_loss": [round(a, 4), round(b, 4)],
                    "validation_loss": [round(before["val_loss"], 4), round(after["val_loss"], 4)],
                })
        if intervals:
            matches.append({"run_id": path.stem, "source": f"runs/{path.name}", "intervals": intervals})
    return {
        "label": "possible overfitting candidate",
        "rule": "post-epoch training loss falls while validation loss rises over the same saved interval",
        "scope": "descriptive flag, not a diagnosis",
        "matches": matches,
    }


def compare_run_group(learning_rate_a: float, learning_rate_b: float) -> dict:
    if learning_rate_a == learning_rate_b:
        raise ValueError("Choose two distinct learning rates")
    groups = {}
    for rate in (learning_rate_a, learning_rate_b):
        rows = []
        for path in sorted(RUNS_DIR.glob("*.json")):
            record = load_run(path.stem)
            if record["config"].get("learning_rate") == rate:
                last = record["metrics"][-1]
                rows.append({
                    "run_id": path.stem,
                    "source": f"runs/{path.name}",
                    "final_epoch": last["epoch"],
                    "train_size": record["config"].get("train_size"),
                    "validation_accuracy_percent": round(100 * last["val_accuracy"], 2),
                })
        values = [row["validation_accuracy_percent"] for row in rows]
        groups[str(rate)] = {
            "count": len(rows),
            "mean_validation_accuracy_percent": round(mean(values), 2) if values else None,
            "median_validation_accuracy_percent": round(median(values), 2) if values else None,
            "runs": rows,
        }
    return {
        "groups": groups,
        "limit": "Saved records may repeat configurations and differ in training size or epoch; this is descriptive, not a causal comparison.",
    }


def plot_run_metrics(run_id: str) -> dict:
    rows = load_run(run_id)["metrics"]
    return {
        "run_id": run_id,
        "source": f"runs/{run_id}.json",
        "points": [
            {
                "epoch": row["epoch"],
                "train_loss": round(row["train_loss_after_epoch"], 4) if row.get("train_loss_after_epoch") is not None else None,
                "validation_loss": round(row["val_loss"], 4),
                "validation_accuracy_percent": round(100 * row["val_accuracy"], 2),
            }
            for row in rows
        ],
    }
