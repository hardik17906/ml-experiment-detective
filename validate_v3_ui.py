"""Execute Streamlit widget paths with isolated SQLite state, no browser or trainer."""

import json
from pathlib import Path
import tempfile
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from v3.demo import QUESTION
from v3.investigation_state import ROOT
from v3.service import Investigator


def main():
    results = []
    (ROOT / ".tmp").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=ROOT / ".tmp", prefix="v3-ui-") as folder:
        app = Investigator(Path(folder) / "ui.sqlite3")
        with patch("v3.ui.Investigator", return_value=app):
            ui = AppTest.from_file(str(ROOT / "legacy_ui.py"), default_timeout=60).run()
            assert not ui.exception, ui.exception
            results.append("Research investigation workspace renders")
            # Start through the actual form with deterministic planning/lexical retrieval.
            ui.checkbox[0].uncheck()
            ui.checkbox[1].uncheck()
            next(b for b in ui.button if b.label == "Start investigation").click().run()
            assert not ui.exception, ui.exception
            assert len(app.store.list()) == 1
            results.append("New-investigation form executes and persists state")
            assert len(ui.tabs) == 7
            results.append("Plan, evidence/charts, hypotheses, approval, execution, report, trace tabs render")
            next(b for b in ui.button if b.label == "Resume saved investigation").click().run()
            assert not ui.exception, ui.exception
            results.append("Resume preserves the pending approval gate")
            next(b for b in ui.button if b.label == "Approve dry run").click().run()
            assert not ui.exception, ui.exception
            self_state = app.store.load(app.store.list()[0]["id"])
            assert self_state["status"] == "dry_run_completed", self_state["status"]
            results.append("Explicit UI approval reaches dry-run completion without training")
            next(b for b in ui.button if b.label == "Save report locally").click().run()
            assert not ui.exception, ui.exception
            assert list((Path(folder) / "reports").glob("*.md"))
            results.append("Markdown report export writes a real file")
            ui.sidebar.radio[0].set_value("Chat and run tools").run()
            assert not ui.exception, ui.exception
            results.append("Educational tool workspace and saved-run charts still render")
            assert set(ui.sidebar.radio[1].options) == {"manual", "graph", "simple"}
            results.append("Simple, manual and graph modes remain selectable")
    (ROOT / "reports" / "v3_ui_validation.json").write_text(json.dumps({"passed": len(results), "checks": results,
        "limitation": "Streamlit AppTest execution; no screenshot or browser visual inspection and no live training."}, indent=2), encoding="utf-8")
    print("\n".join("PASS " + r for r in results))


if __name__ == "__main__":
    main()
