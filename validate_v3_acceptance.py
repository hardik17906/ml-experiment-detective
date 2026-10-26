"""Record acceptance evidence without treating untested training as a success."""

import ast
import hashlib
import json
from pathlib import Path
import subprocess

from v3.investigation_state import ROOT


def main():
    manifest = json.loads((ROOT / "reports/v3_original_data_manifest.json").read_text())
    unchanged = all(hashlib.sha256((ROOT / x["path"]).read_bytes()).hexdigest() == x["sha256"] for x in manifest)
    deterministic = json.loads((ROOT / "reports/v3_evaluation.json").read_text())
    ui = json.loads((ROOT / "reports/v3_ui_validation.json").read_text())
    live = json.loads((ROOT / "reports/v3_live_validation.json").read_text())
    old = json.loads((ROOT / "reports/v3_v2_regression_traces.json").read_text())
    latest = json.loads((ROOT / "reports/v3_demo/latest.json").read_text())
    demo = json.loads((ROOT / "reports/v3_demo" / latest["state"]).read_text())
    original = subprocess.check_output(["git", "show", "HEAD:phase0.py"], cwd=ROOT).decode()
    current = (ROOT / "phase0.py").read_text()
    def syntax(source, name):
        return ast.dump(next(x for x in ast.parse(source).body if isinstance(x, (ast.ClassDef, ast.FunctionDef)) and x.name == name), include_attributes=False)
    preserved = all(syntax(original, n) == syntax(current, n) for n in ("SimpleMLP", "evaluate"))
    def test_passed(number):
        return any(f"test_{number:02d}_" in x["scenario"] and x["passed"] for x in deterministic["scenarios"])
    checks = [
        {"requirement": "V1/V2 still run", "verified": live["passed"] == live["total"] and len(old["cases"]) == 17},
        {"requirement": "Original data unchanged", "verified": unchanged, "original_files_checked": len(manifest)},
        {"requirement": "Persistent investigations survive restart", "verified": test_passed(22) and test_passed(23) and any("restart" in c["case"] for c in live["cases"])},
        {"requirement": "Plans structured and traceable", "verified": test_passed(17) and test_passed(18) and test_passed(28)},
        {"requirement": "Hypotheses cite real evidence", "verified": test_passed(19) and test_passed(20) and test_passed(21)},
        {"requirement": "Controlled proposals valid", "verified": test_passed(15) and test_passed(16)},
        {"requirement": "Approval mandatory", "verified": test_passed(7) and test_passed(9) and test_passed(24)},
        {"requirement": "Rejected proposals blocked", "verified": test_passed(8) and test_passed(25)},
        {"requirement": "Dry run", "verified": demo["status"] == "dry_run_completed" and not demo["execution"]["ingested"]},
        {"requirement": "New-result ingestion", "verified": test_passed(33) and test_passed(54), "scope": "Labeled fixtures; no actual new training output"},
        {"requirement": "Graph recovery", "verified": test_passed(52) and test_passed(53)},
        {"requirement": "UI investigation paths", "verified": ui["passed"] == 8, "scope": "Streamlit AppTest, not browser screenshots"},
        {"requirement": "Unsupported questions", "verified": test_passed(29) and test_passed(30) and test_passed(55)},
        {"requirement": "Numeric accuracy and source grounding", "verified": test_passed(1) and test_passed(35) and test_passed(49)},
        {"requirement": "V3 evaluation suite", "verified": deterministic["passed"] == deterministic["tests_run"] and deterministic["failed_or_errors"] == 0},
        {"requirement": "D: local model/cache locations", "verified": all(p.is_dir() for p in (ROOT / ".model_cache", ROOT / ".pip_cache", Path("D:/Ollama/models"))),
         "scope": "Existing D: folders and configured model path were inspected; no new models/datasets downloaded"},
        {"requirement": "Original model/evaluation algorithm preserved", "verified": preserved},
        {"requirement": "Full live training", "verified": False, "scope": "Not authorized or run; dry-run, failure mocks and fixture ingestion only"}]
    report = {"checks": checks, "required_checks_passed": sum(x["verified"] for x in checks),
              "live_training_verified": False, "no_new_training_runs_created": len(list((ROOT / "runs").glob("v3_*.json"))) == 0}
    (ROOT / "reports/v3_acceptance.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    assert all(x["verified"] for x in checks if x["requirement"] != "Full live training")
    assert report["no_new_training_runs_created"]


if __name__ == "__main__":
    main()
