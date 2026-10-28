"""One independently validated, bounded, two-run learning-rate intervention."""

from pathlib import Path
import hashlib
import json
import math
import re

from experiment_data import RUNS_DIR, load_run
from v3.analysis import CONTROLS
from v3.investigation_state import ROOT

FIXED = {"dataset": "FashionMNIST", "source_partition": "train", "preprocessing": "ToTensor",
         "val_size": 2000, "validation_start": 10000, "split_seed": 42, "batch_size": 128,
         "hidden_units": 128, "optimizer": "SGD"}


def trainer_hash():
    paths = [ROOT / "phase0.py", ROOT / "v3" / "training_worker.py"]
    return hashlib.sha256(b"".join(p.read_bytes() for p in paths)).hexdigest()


def validate_config(config):
    expected = set(FIXED) | {"run_id", "learning_rate", "train_size", "epochs", "dropout", "model_seed", "shuffle_seed"}
    if not isinstance(config, dict) or set(config) != expected:
        raise ValueError("Configuration has missing or unsupported fields")
    if not isinstance(config["run_id"], str) or not re.fullmatch(r"v3_[a-z0-9_-]{1,80}", config["run_id"]):
        raise ValueError("Run ID must be a safe, unique v3_ identifier")
    for key, val in FIXED.items():
        if config[key] != val or type(config[key]) is not type(val):
            raise ValueError(f"Unsupported fixed training control: {key}")
    for key, low, high in (("train_size", 1, 10000), ("epochs", 1, 5), ("model_seed", 0, 2**31-1), ("shuffle_seed", 0, 2**31-1)):
        if type(config[key]) is not int or not low <= config[key] <= high:
            raise ValueError(f"Invalid or over-budget {key}")
    for key, low, high in (("learning_rate", 0.0001, 0.2), ("dropout", 0, 0.5)):
        v = config[key]
        if type(v) not in (float, int) or not math.isfinite(v) or not low <= v <= high:
            raise ValueError(f"Invalid or over-budget {key}")


def saved_configs():
    configs = [load_run(p.stem)["config"] for p in RUNS_DIR.glob("*.json")]
    # Existing unexecuted plans reserve seeds too; The investigator does not resume the old seed-four branch.
    for path in (ROOT / "plans").glob("*.json"):
        configs.extend(x["config"] for x in json.loads(path.read_text(encoding="utf-8")).get("planned_runs", []) if "config" in x)
    return configs


def validate_proposal(proposal, *, check_duplicates=True):
    if proposal.get("changed_variable") != "learning_rate" or len(proposal.get("runs", [])) != 2:
        raise ValueError("Only a two-run, single learning-rate intervention is supported")
    if proposal.get("training_code_sha256") != trainer_hash():
        raise ValueError("Training code changed; regenerate and approve the proposal again")
    if proposal.get("limits") != {"max_total_seconds": 600, "max_runs": 2, "cpu_threads": 2}:
        raise ValueError("Execution resource limits cannot be increased")
    a, b = proposal["runs"]
    for config in (a, b):
        validate_config(config)
    if a["run_id"] == b["run_id"] or not a["learning_rate"] < b["learning_rate"]:
        raise ValueError("Require distinct IDs and lower-rate control followed by higher-rate intervention")
    if any(a[k] != b[k] for k in CONTROLS):
        raise ValueError("All recorded controls, including both seeds, must match")
    existing = saved_configs()
    for config in (a, b):
        if (RUNS_DIR / f"{config['run_id']}.json").exists():
            raise ValueError("A proposed run ID already exists; overwriting is forbidden")
        if check_duplicates and any(all(old.get(k) == v for k, v in config.items() if k != "run_id") for old in existing):
            raise ValueError("Duplicate recorded/planned configuration")
    return {"valid": True, "checks": ["single_variable", "matched_controls", "new_configurations", "resource_limits", "trainer_hash", "unique_run_ids"]}


def design(state):
    comparisons = state.get("analysis", {}).get("comparisons", [])
    if not comparisons or not state.get("evidence_validation", {}).get("valid"):
        return None, "A valid comparison and grounded hypotheses are required before proposing training."
    pair = comparisons[0]
    if "learning_rate" not in pair["changed_settings"]:
        return None, "The first executor supports learning-rate interventions; this investigation needs another design."
    base = state["records"][pair["baseline_run_id"]]["config"]
    if any(key not in base for key in (*CONTROLS, "learning_rate")):
        return None, "Missing baseline controls must be resolved before an executable proposal can be created."
    rates = sorted([base["learning_rate"], state["records"][pair["target_run_id"]]["config"]["learning_rate"]])
    existing = saved_configs()
    model_seed = max(c.get("model_seed", 0) for c in existing) + 100
    shuffle_seed = max(c.get("shuffle_seed", 0) for c in existing) + 100
    prefix = state["investigation_id"].lower().replace("-", "_")
    runs = [dict(base, run_id=f"v3_{prefix}_{label}", learning_rate=rate,
                 model_seed=model_seed, shuffle_seed=shuffle_seed) for label, rate in zip(("control", "target"), rates)]
    p = {"proposal_id": f"{state['investigation_id']}-P1", "investigation_id": state["investigation_id"],
         "hypothesis_ids": [h["hypothesis_id"] for h in state["hypotheses"] if h["hypothesis_id"] in {"H1", "H2"}],
         "changed_variable": "learning_rate", "controlled_variables": list(CONTROLS), "runs": runs,
         "rationale": "A new shared seed block tests whether the observed loss-rise ordering replicates while all other recorded controls are matched.",
         "seed_rationale": "Seeds exceed recorded runs and reserved legacy plans. The same fresh seeds are used by both arms.",
         "primary_metric": "largest_positive_consecutive_epoch_validation_loss_rise",
         "secondary_metrics": ["final_validation_accuracy_percent", "final_validation_loss"],
         "supported_if": "The higher-rate arm has a strictly larger maximum validation-loss rise.",
         "contradicted_if": "The higher-rate arm has a smaller maximum rise; equality is inconclusive.",
         "limitations": ["One new seed block does not establish general causation.", "The same fixed validation split is reused; the official test set is excluded.",
                         "Validation metrics do not directly measure overshooting.", "Other hypotheses may require separately approved designs."],
         "limits": {"max_total_seconds": 600, "max_runs": 2, "cpu_threads": 2},
         "training_code_sha256": trainer_hash()}
    validate_proposal(p)
    return p, None
