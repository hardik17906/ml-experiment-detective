"""Real saved-data demonstration. The only execution permission granted is dry_run."""

import argparse
import json

from v3.investigation_state import ROOT
from v3.service import Investigator

QUESTION = "Investigate why lr_01_seed3 had worse final validation accuracy than lr_005_seed3. Examine the curves, retrieve relevant ML knowledge, compare possible explanations, and propose a controlled follow-up."


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    app = Investigator()
    state = app.start(QUESTION, model_enabled=not args.offline)
    print(state["investigation_id"], state["status"], flush=True)
    if state["status"] != "awaiting_approval":
        raise RuntimeError(state.get("last_error", "Demonstration did not reach the approval gate"))
    row = app.store.proposal(state["proposal_id"])
    # The development request explicitly authorizes demonstrating dry execution only.
    state = app.decide(state["investigation_id"], row["hash"], "approved", mode="dry_run",
                       actor="development_dry_run", reason="V3 development demonstration; no live training permission")
    folder = ROOT / "reports" / "v3_demo"
    path = app.export(state["investigation_id"], folder)
    (folder / "latest.json").write_text(json.dumps({"investigation_id": state["investigation_id"],
        "report": path.name, "state": path.with_suffix(".json").name}, indent=2), encoding="utf-8")
    for event in state["trace"]:
        print(f"{event['kind']} [{event.get('origin', 'PYTHON')}]", flush=True)
    print("FINAL", state["status"], "| REPORT", path, flush=True)


if __name__ == "__main__":
    main()
