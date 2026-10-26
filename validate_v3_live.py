"""Small live-model sample plus an actual two-process checkpoint-resume check."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile

from simple_agent import answer_question
from v3.investigation_state import ROOT
from v3.service import Investigator


def main():
    results = []
    v1 = answer_question("What is the final validation accuracy of lr_01_seed3?", trace=False)
    assert "71.45" in v1, v1
    results.append({"case": "V1 simple agent live", "passed": True, "answer": v1})
    with tempfile.TemporaryDirectory(dir=ROOT / ".tmp", prefix="v3-live-") as folder:
        app = Investigator(Path(folder) / "live.sqlite3")
        simple = app.start("What is the final validation accuracy of lr_01_seed3?")
        assert simple["status"] == "completed" and "71.45" in simple["answer"], simple
        results.append({"case": "V3 simple route delegates to V2 live tools", "passed": True, "trace": simple["trace"]})
        discovery = app.start("Investigate whether we have seen unstable validation behavior before. Search notes, check previous experiments, and retrieve ML knowledge.")
        assert discovery["status"] != "failed", discovery.get("last_error")
        assert discovery["records"] and discovery["notes"]["matches"]
        kinds = [e["kind"] for e in discovery["trace"]]
        assert "REPLANNING" in kinds and "EXPERIMENT EVIDENCE" in kinds
        results.append({"case": "V3 no-ID live investigation discovers and inspects run IDs", "passed": True,
                        "status": discovery["status"], "trace": discovery["trace"]})
        # Close one Python process, then resume/approve in a completely new process.
        db = str(Path(folder) / "restart.sqlite3")
        create_code = "from v3.service import Investigator; import sys; a=Investigator(sys.argv[1]); d=a.start('Investigate why lr_01_seed3 was worse than lr_005_seed3',model_enabled=False,semantic=False); print(d['investigation_id']); assert d['status']=='awaiting_approval'"
        created = subprocess.run([sys.executable, "-X", "utf8", "-c", create_code, db], cwd=ROOT, capture_output=True, text=True, check=True)
        identifier = created.stdout.strip().splitlines()[-1]
        resume_code = "from v3.service import Investigator; import sys; a=Investigator(sys.argv[1]); d=a.store.load(sys.argv[2]); p=a.store.proposal(d['proposal_id']); d=a.decide(d['investigation_id'],p['hash'],'approved',mode='dry_run',actor='development_dry_run'); assert d['status']=='dry_run_completed'; print(d['status'])"
        resumed = subprocess.run([sys.executable, "-X", "utf8", "-c", resume_code, db, identifier], cwd=ROOT, capture_output=True, text=True, check=True)
        results.append({"case": "Actual app-process restart and SQLite interrupt resumption", "passed": True,
                        "result": resumed.stdout.strip(), "training": "not launched"})
    report = {"passed": len(results), "total": len(results), "scope": "Small live Ollama sample and one process-restart demonstration; not a general model success-rate estimate.", "cases": results}
    (ROOT / "reports" / "v3_live_validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("\n".join("PASS " + x["case"] for x in results))


if __name__ == "__main__":
    main()
