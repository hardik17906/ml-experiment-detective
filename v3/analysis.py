"""Scientific observations are computed here, never supplied by a language model."""

from itertools import combinations
import math
from statistics import mean, pstdev

from experiment_data import RUNS_DIR, load_run, largest_rise, loss_recoveries

CONTROLS = ("dataset", "source_partition", "preprocessing", "train_size", "val_size",
            "validation_start", "split_seed", "shuffle_seed", "model_seed", "batch_size",
            "hidden_units", "optimizer", "epochs", "dropout")


def matched_runs(run_id, learning_rate=None):
    """Find matches on all recorded controls, reporting absent metadata in comparisons."""
    anchor = load_run(run_id)
    result = []
    for path in sorted(RUNS_DIR.glob("*.json")):
        if path.stem == run_id:
            continue
        record = load_run(path.stem)
        if learning_rate is not None and record["config"].get("learning_rate") != learning_rate:
            continue
        if set(compare_records(anchor, record)["changed_settings"]) == {"learning_rate"}:
            result.append(path.stem)
    return result


def check_record(record):
    missing = []
    rows = record.get("metrics", [])
    if not rows or [x.get("epoch") for x in rows] != list(range(1, len(rows) + 1)):
        missing.append("nonempty consecutive epoch metrics")
    for row in rows:
        for key in ("val_loss", "val_accuracy"):
            v = row.get(key)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                missing.append(f"epoch {row.get('epoch')}: {key}")
            elif v < 0 or (key == "val_accuracy" and v > 1):
                missing.append(f"out-of-range {key}")
    if record.get("config", {}).get("epochs") != len(rows):
        missing.append("recorded epoch count does not match configuration")
    return missing


def curve(record):
    errors = check_record(record)
    if errors:
        return {"incomplete": errors}
    rows = record["metrics"]
    last = rows[-1]
    best = max(rows, key=lambda x: x["val_accuracy"])
    low = min(rows, key=lambda x: x["val_loss"])
    training = last.get("train_loss_after_epoch")
    return {"final_accuracy_percent": round(100 * last["val_accuracy"], 2),
            "final_loss": round(last["val_loss"], 6), "final_epoch": last["epoch"],
            "best_accuracy_percent": round(100 * best["val_accuracy"], 2), "best_epoch": best["epoch"],
            "minimum_loss": round(low["val_loss"], 6), "minimum_loss_epoch": low["epoch"],
            "largest_loss_rise": round(largest_rise(rows)[0], 6),
            "recoveries": loss_recoveries(rows),
            "final_loss_gap_val_minus_train": round(last["val_loss"] - training, 6) if training is not None else None,
            "candidate_generalization_intervals": [
                [a["epoch"], b["epoch"]] for a, b in zip(rows, rows[1:])
                if a.get("train_loss_after_epoch") is not None and b.get("train_loss_after_epoch") is not None
                and b["train_loss_after_epoch"] < a["train_loss_after_epoch"] and b["val_loss"] > a["val_loss"]]}


def compare_records(baseline, target):
    a, b = baseline["config"], target["config"]
    differences = {k: {"baseline": a.get(k), "target": b.get(k)}
                   for k in sorted(set(a) | set(b)) if k != "run_id" and a.get(k) != b.get(k)}
    unknown = [k for k in (*CONTROLS, "learning_rate") if k not in a or k not in b]
    ca, cb = curve(baseline), curve(target)
    result = {"baseline_run_id": a["run_id"], "target_run_id": b["run_id"],
              "sources": [f"runs/{a['run_id']}.json", f"runs/{b['run_id']}.json"],
              "source_type": "DERIVED_ANALYSIS", "changed_settings": differences,
              "missing_controls": unknown, "curves": {a["run_id"]: ca, b["run_id"]: cb},
              "matching_scope": "All recorded configuration fields; hidden_units and dropout describe architecture settings, not complete architecture provenance.",
              "missing_provenance": ["Exact model-class/trainer revision was not recorded in historical JSON.",
                                     "Hardware and software versions were not recorded in historical JSON."],
              "controlled_learning_rate_pair": not unknown and set(differences) == {"learning_rate"},
              "confounded": any(k != "learning_rate" for k in differences)}
    if "incomplete" not in ca and "incomplete" not in cb and ca["final_epoch"] == cb["final_epoch"]:
        result.update(accuracy_delta_pp=round(100 * (target["metrics"][-1]["val_accuracy"] - baseline["metrics"][-1]["val_accuracy"]), 2),
                      loss_delta=round(target["metrics"][-1]["val_loss"] - baseline["metrics"][-1]["val_loss"], 6),
                      rise_delta=round(largest_rise(target["metrics"])[0] - largest_rise(baseline["metrics"])[0], 6))
    else:
        result["missing_metrics"] = "Final deltas unavailable: incomplete records or different final epochs"
    return result


def analyze(run_ids, *, include_seed_pairs=True):
    records, errors = {}, []
    for path in sorted(RUNS_DIR.glob("*.json")):
        try:
            record = load_run(path.stem)
            if check_record(record):
                errors.append({"run_id": path.stem, "missing": check_record(record)})
            else:
                records[path.stem] = record
        except (ValueError, KeyError, TypeError) as exc:
            errors.append({"run_id": path.stem, "error": str(exc)})
    selected = [records[x] for x in run_ids if x in records]
    comparisons = [compare_records(a, b) for a, b in combinations(selected, 2)]
    pairs = []
    relevant_rates = {r["config"].get("learning_rate") for r in selected}
    if include_seed_pairs:
        for a, b in combinations(records.values(), 2):
            if a["config"].get("learning_rate", 0) > b["config"].get("learning_rate", 0):
                a, b = b, a
            comparison = compare_records(a, b)
            same_rate_question = len(relevant_rates) != 2 or {a["config"].get("learning_rate"), b["config"].get("learning_rate")} == relevant_rates
            if set(comparison["changed_settings"]) == {"learning_rate"} and same_rate_question:
                # Missing metadata remains unknown, even when both records omit it.
                pairs.append(comparison)
    # Repeated records with identical configurations are not independent seed blocks.
    blocks = {}
    for p in pairs:
        r = records[p["baseline_run_id"]]["config"]
        other = records[p["target_run_id"]]["config"]
        signature = tuple((k, r.get(k)) for k in CONTROLS) + (("rates", (r["learning_rate"], other["learning_rate"])),)
        blocks.setdefault(signature, p)
    deltas = [p["accuracy_delta_pp"] for p in blocks.values() if "accuracy_delta_pp" in p]
    return {"comparisons": comparisons, "seed_pairs": list(blocks.values()),
            "seed_summary": {"distinct_recorded_blocks": len(deltas),
                             "mean_accuracy_delta_pp": round(mean(deltas), 4) if deltas else None,
                             "population_sd_delta_pp": round(pstdev(deltas), 4) if deltas else None,
                             "limit": "Descriptive observed blocks; missing controls and reuse of one split limit causal interpretation."},
            "incomplete_records": errors, "selected_records": selected}
