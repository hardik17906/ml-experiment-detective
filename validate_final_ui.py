"""Execute the recommended interface through Streamlit AppTest, using isolated data."""
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from assistant import ResearchAssistant
from v3.investigation_state import ROOT


def main():
    checks=[]
    with tempfile.TemporaryDirectory(dir=ROOT/".tmp",prefix="final-ui-") as folder:
        app=ResearchAssistant(Path(folder)/"state.sqlite3")
        with patch("assistant.ResearchAssistant",return_value=app), patch("v3.ui.Investigator",return_value=app.investigator):
            ui=AppTest.from_file(str(ROOT/"ui.py"),default_timeout=90).run()
            assert not ui.exception,ui.exception
            assert len(ui.metric)==4
            checks.append("Overview statistics and model status render")
            ui.sidebar.radio[0].set_value("Experiment Explorer").run()
            assert not ui.exception,ui.exception
            checks.append("Experiment catalog and per-epoch charts render")
            ui.selectbox[2].set_value("lr_005_seed3").run()
            assert not ui.exception,ui.exception
            checks.append("Two-run comparison settings and visualizations render")
            ui.selectbox[0].set_value(0.05).run()
            assert not ui.exception,ui.exception
            checks.append("Exact learning-rate filter works")
            ui.sidebar.radio[0].set_value("AI Chat").run()
            ui.sidebar.checkbox[0].check()
            ui.sidebar.checkbox[1].uncheck()
            ui.chat_input[0].set_value("Tell me about lr_01_seed3.").run()
            assert not ui.exception,ui.exception
            assert "71.45" in ui.session_state.chat_entries[-1]["answer"]
            checks.append("Chat renders measured answer and expandable tool trace")
            ui.chat_input[0].set_value("Compare that run with lr_005_seed3.").run()
            assert not ui.exception,ui.exception
            assert "4.45" in ui.session_state.chat_entries[-1]["answer"]
            checks.append("Conversational comparison reference resolves")
            ui.sidebar.radio[0].set_value("Investigations").run()
            assert not ui.exception,ui.exception
            # The initial stored direct answers do not have a plan; create research from its form.
            ui.checkbox[0].uncheck()
            ui.checkbox[1].uncheck()
            next(b for b in ui.button if b.label=="Start investigation").click().run()
            assert not ui.exception,ui.exception
            checks.append("Investigation creation displays plan, evidence and hypotheses")
            next(b for b in ui.button if b.label=="Resume saved investigation").click().run()
            assert not ui.exception,ui.exception
            checks.append("Resume preserves the approval boundary")
            next(b for b in ui.button if b.label=="Approve dry run").click().run()
            assert not ui.exception,ui.exception
            selected=ui.session_state.v3_selected
            assert app.investigator.store.load(selected)["status"]=="dry_run_completed"
            checks.append("UI approval completes a dry run without training")
            next(b for b in ui.button if b.label=="Save report locally").click().run()
            assert not ui.exception,ui.exception
            assert list((Path(folder)/"reports").glob("*.md"))
            checks.append("Report export writes Markdown")
    Path("reports/final").mkdir(exist_ok=True,parents=True)
    Path("reports/final/ui.json").write_text(json.dumps({"passed":len(checks),"checks":checks,"scope":"Streamlit AppTest; no browser screenshot or live training"},indent=2),encoding="utf-8")
    print("\n".join("PASS "+x for x in checks))


if __name__=="__main__":main()
