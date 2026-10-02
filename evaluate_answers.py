"""Evaluate saved factual answers without calling the language model again."""

import json
import re
from pathlib import Path

from answer_checks import check_observations, require_complete_val_loss_history, rise_then_fall_patterns


PROJECT_DIR = Path(__file__).resolve().parent
CASES = PROJECT_DIR / "answer_eval_cases.json"
RUN_LINK = re.compile(r"\]\(\.\./runs/([a-z0-9_-]+)\.json\)")
ID = re.compile(r"[a-z0-9_-]+")


def raw_pattern_count(run_id: str) -> int:
    """Calculate the reference label from saved, unrounded validation losses."""
    run = json.loads((PROJECT_DIR / "runs" / f"{run_id}.json").read_text(encoding="utf-8"))
    rows = run["metrics"]
    return sum(
        before["val_loss"] < peak["val_loss"] > after["val_loss"]
        for before, peak, after in zip(rows, rows[1:], rows[2:])
    )


def evaluate_case(case: dict) -> dict:
    answer_id = case["answer_id"]
    expected_runs = set(case["expected_runs"])
    if not ID.fullmatch(answer_id) or not expected_runs or any(
        not ID.fullmatch(run_id) for run_id in expected_runs
    ):
        raise ValueError(f"Invalid case IDs: {case['id']}")
    if case["expected_answer"] not in {"yes", "no"}:
        raise ValueError(f"Invalid expected answer: {case['id']}")

    answer = (PROJECT_DIR / "answers" / f"{answer_id}.md").read_text(encoding="utf-8")
    metadata = json.loads(
        (PROJECT_DIR / "answers" / f"{answer_id}.json").read_text(encoding="utf-8")
    )
    prompt = (PROJECT_DIR / "prompts" / f"{answer_id}.md").read_text(encoding="utf-8")
    found_runs = set(RUN_LINK.findall(prompt))
    retrieval_ok = found_runs == expected_runs

    raw_positive_runs = {run_id for run_id in expected_runs if raw_pattern_count(run_id)}
    source_answer = "yes" if raw_positive_runs else "no"
    label_ok = source_answer == case["expected_answer"]

    answer_lines = answer.splitlines()
    direct_answer = next((line.strip() for line in answer_lines[1:] if line.strip()), "")
    match = re.match(r"^(yes|no)\b", direct_answer, re.IGNORECASE)
    answer_ok = bool(match and match.group(1).lower() == case["expected_answer"])

    observations = metadata["model_response"]["observations"]
    evidence_error = None
    try:
        verified = check_observations(observations, PROJECT_DIR / "runs")
        unexpected_runs = {item["run_id"] for item in verified} - expected_runs
        if unexpected_runs:
            raise ValueError(f"observations cite unexpected runs: {sorted(unexpected_runs)}")
        if metadata.get("verified_observations") != verified:
            raise ValueError("saved verification record differs from model observations")
        patterns = rise_then_fall_patterns(verified)
        found_pattern_runs = {pattern["run_id"] for pattern in patterns}
        if source_answer == "yes":
            evidence_ok = raw_positive_runs <= found_pattern_runs
        else:
            require_complete_val_loss_history(
                verified, sorted(expected_runs), PROJECT_DIR / "runs"
            )
            evidence_ok = not patterns
        if not evidence_ok:
            evidence_error = "verified observations do not cover the reference pattern"
    except (ValueError, KeyError, TypeError) as exc:
        verified, patterns, evidence_ok = [], [], False
        evidence_error = str(exc)

    citations_ok = all(f"[source](../runs/{run_id}.json)" in answer for run_id in expected_runs)
    checks = {
        "source_label": label_ok,
        "retrieval": retrieval_ok,
        "answer": answer_ok,
        "evidence": evidence_ok,
        "citations": citations_ok,
    }
    return {
        "checks": checks,
        "source_answer": source_answer,
        "found_runs": sorted(found_runs),
        "verified_measurements": len(verified),
        "verified_patterns": len(patterns),
        "evidence_error": evidence_error,
    }


def main() -> None:
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    print(f"Saved answer cases: {len(cases)}")
    passed = 0
    for case in cases:
        result = evaluate_case(case)
        checks = result["checks"]
        passed += all(checks.values())
        print(f"\n{case['id']}: {case['reason']}")
        print(f"  expected answer: {case['expected_answer']} | source record: {result['source_answer']}")
        print(f"  prompt runs: {', '.join(result['found_runs'])}")
        print(
            f"  verified measurements: {result['verified_measurements']} | "
            f"rise-then-fall patterns: {result['verified_patterns']}"
        )
        for name, okay in checks.items():
            print(f"  {name}: {'PASS' if okay else 'FAIL'}")
        if result["evidence_error"]:
            print(f"  evidence detail: {result['evidence_error']}")
        if not checks["retrieval"]:
            print("  failure stage: retrieval or packet assembly")
        elif not all(checks.values()):
            print("  failure stage: answer generation, evidence, or saved output")

    print(f"\nOverall: {passed}/{len(cases)} saved answers passed every check")
    if passed != len(cases):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
