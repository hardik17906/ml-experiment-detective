"""Restricted subprocess execution with an atomic, exact-configuration approval claim."""

import json
import os
from pathlib import Path
import subprocess
import sys
import time

from v3.analysis import check_record, compare_records
from v3.experiment_designer import validate_proposal
from v3.investigation_state import ROOT, digest, now


def ingest_record(record, config, *, investigation_id, proposal_id, fixture=False):
    """Validate real output or labeled fixtures without silently publishing fixture data."""
    if record.get("config") != config or check_record(record):
        raise ValueError("Training output is incomplete or does not match the approved configuration")
    if fixture and not record.get("provenance", {}).get("test_fixture"):
        raise ValueError("Fixture ingestion requires an explicit test_fixture provenance label")
    return {"run_id": config["run_id"], "source_type": "TEST_FIXTURE" if fixture else "EXPERIMENT_JSON",
            "investigation_id": investigation_id, "proposal_id": proposal_id, "record": record}


def evaluate_outcomes(records):
    if len(records) != 2:
        return {"status": "incomplete", "interpretation": "Both approved arms must finish before comparison."}
    comparison = compare_records(records[0], records[1])
    rise = comparison.get("rise_delta")
    outcome = "inconclusive" if rise is None or rise == 0 else "consistent" if rise > 0 else "opposing"
    return {"status": outcome, "predefined_primary_metric": "largest_positive_consecutive_epoch_validation_loss_rise",
            "comparison": comparison,
            "interpretation": {"consistent": "The new loss-rise ordering is consistent with the instability hypothesis; one block cannot prove causation.",
                               "opposing": "This block opposes the expected loss-rise ordering; it does not conclusively disprove the mechanism.",
                               "inconclusive": "The primary metric does not distinguish the proposed explanation in this block."}[outcome],
            "competing_explanations": "Seed variability, short horizons, unmeasured optimization details, and shared-split limits remain possible."}


def execute(store, proposal_id, expected_hash, mode):
    row = store.proposal(proposal_id)
    proposal = row["payload"]
    if digest(proposal) != expected_hash or row["hash"] != expected_hash:
        raise PermissionError("Proposal hash mismatch")
    validate_proposal(proposal)
    store.claim_execution(proposal_id, expected_hash, mode)
    result = {"status": "running", "mode": mode, "started": now(), "run_ids": [], "logs": [], "ingested": []}
    store.execution_result(proposal_id, result)
    try:
        if mode == "dry_run":
            result.update(status="dry_run_completed", planned_configs=proposal["runs"],
                          message="Approval and resource checks passed. No trainer was launched; no metrics or run files were created.")
        elif mode == "live":
            data = ROOT / "data" / "FashionMNIST" / "raw"
            if not all((data / name).is_file() for name in ("train-images-idx3-ubyte", "train-labels-idx1-ubyte")):
                raise FileNotFoundError("Cached Fashion-MNIST training partition is unavailable; downloads are disabled")
            folder = store.path.parent / "executions" / proposal_id
            folder.mkdir(parents=True, exist_ok=True)
            started = time.monotonic()
            for config in proposal["runs"]:
                remaining = proposal["limits"]["max_total_seconds"] - (time.monotonic() - started)
                if remaining <= 0:
                    raise TimeoutError("Total approved execution time exhausted")
                output = ROOT / "runs" / f"{config['run_id']}.json"
                if output.exists():
                    raise FileExistsError("Existing experiment cannot be overwritten")
                payload_path = folder / f"{config['run_id']}.input.json"
                payload_path.write_text(json.dumps({"config": config, "output_path": str(output),
                    "provenance": {"investigation_id": proposal["investigation_id"], "proposal_id": proposal_id,
                                   "approved_sha256": expected_hash, "created_at": now(), "executor": "v3"}}), encoding="utf-8")
                log = folder / f"{config['run_id']}.log"
                result["logs"].append(str(log))
                environment = dict(os.environ, OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", PYTHONUTF8="1",
                                   HF_HOME=str(ROOT / ".model_cache" / "hub"), HF_HUB_OFFLINE="1")
                with log.open("x", encoding="utf-8") as stream:
                    # Fixed executable/module + data path; no shell and no LLM-written command.
                    subprocess.run([sys.executable, "-u", "-m", "v3.training_worker", str(payload_path)],
                                   cwd=ROOT, env=environment, shell=False, stdout=stream,
                                   stderr=subprocess.STDOUT, timeout=remaining, check=True)
                record = json.loads(output.read_text(encoding="utf-8"))
                result["ingested"].append(ingest_record(record, config,
                    investigation_id=proposal["investigation_id"], proposal_id=proposal_id))
                result["run_ids"].append(config["run_id"])
                store.execution_result(proposal_id, result)
            result["status"] = "completed"
        else:
            raise ValueError("Unknown execution mode")
    except Exception as exc:
        result.update(status="failed", error=f"{type(exc).__name__}: {exc}")
    result["finished"] = now()
    store.execution_result(proposal_id, result)
    return result
