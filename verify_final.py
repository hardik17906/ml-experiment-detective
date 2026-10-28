"""Final artifact/data/document acceptance checks. Does not launch training."""
import hashlib
import json
from pathlib import Path
import re
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parent


def main():
    def load(path):return json.loads((ROOT/path).read_text(encoding="utf-8"))
    deterministic=load("reports/final/deterministic.json")
    ui=load("reports/final/ui.json")
    compatibility=load("reports/final/compatibility.json")
    journeys=load("reports/final/journeys.json")
    investigation=load("reports/final/investigation.json")
    manifest=load("reports/v3_original_data_manifest.json")
    unchanged=all(hashlib.sha256((ROOT/x["path"]).read_bytes()).hexdigest()==x["sha256"] for x in manifest)
    from docs.build_final_docs import COMPONENTS
    master=(ROOT/"docs/FINAL_PROJECT_MASTER_CONTEXT.md").read_text(encoding="utf-8")
    guide=(ROOT/"docs/FINAL_COMPLETE_LEARNING_GUIDE.md").read_text(encoding="utf-8")
    documents=["FINAL_COMPLETE_LEARNING_GUIDE.md","FINAL_CODE_WALKTHROUGH.md","FINAL_END_TO_END_TRACE.md","FINAL_PROJECT_MASTER_CONTEXT.md"]
    source_embedded=all((ROOT/p).read_text(encoding="utf-8").rstrip() in master for p in COMPONENTS)
    hash_embedded=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest() in master for p in COMPONENTS)
    with urlopen("http://127.0.0.1:8501/_stcore/health",timeout=5) as response:health=response.status==200
    checks={"original_data_unchanged":unchanged,"main_application_health":health,
            "deterministic_scenarios_pass":deterministic["passed"]==deterministic["tests_run"] and deterministic["failures"]==0,
            "unified_ui_checks_pass":ui["passed"]==10,
            "compatibility_and_process_restart_pass":compatibility["passed"]==compatibility["total"],
            "all_six_journeys_recorded":{r["journey"].split()[0] for r in journeys["results"]}==set("123456"),
            "real_local_model_trace":investigation["model_enabled"] and any(e.get("origin")=="LLM" for e in investigation["trace"]),
            "dry_run_completed":investigation["status"]=="dry_run_completed" and not investigation["execution"]["ingested"],
            "no_new_training_records":not list((ROOT/"runs").glob("v3_*.json")),
            "all_four_documents_exist":all((ROOT/"docs"/n).is_file() and (ROOT/"docs"/n).stat().st_size>10000 for n in documents),
            "thirty_learning_chapters":len(re.findall(r"^## Chapter \d+",guide,re.M))==30,
            "master_begins_with_architecture":master.startswith("# ML Experiment Detective") and "## Architecture and purpose" in master[:300],
            "actual_core_sources_embedded":source_embedded,
            "actual_core_source_hashes_match":hash_embedded,
            "no_unexpanded_code_placeholders":not re.search(r"^<!-- CODE [^\n]+ -->$",master,re.M)}
    report={"status":"COMPLETE" if all(checks.values()) else "PARTIAL","checks":checks,
            "scope":"Completed local application and learning package; live training explicitly unverified pending user approval.",
            "deterministic_passed":deterministic["passed"],"ui_checks_passed":ui["passed"],
            "live_training_verified":False,"browser_visual_inspection_performed":False,
            "master_bytes":(ROOT/"docs/FINAL_PROJECT_MASTER_CONTEXT.md").stat().st_size,
            "investigation_id":investigation["investigation_id"]}
    (ROOT/"reports/final/acceptance.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))
    assert all(checks.values()),checks


if __name__=="__main__":main()
