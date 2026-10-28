"""Integrated final-application scenarios. No live training is permitted here."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from assistant import ResearchAssistant
from experiment_data import RUNS_DIR, load_run
from v2_state import SessionState
from v2_tools import execute_tool
from v3.experiment_executor import execute
from v3.investigation_state import ROOT
from v3.retrieval import knowledge, search_notes


class FinalApplicationTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(dir=ROOT / ".tmp", prefix="final-tests-")
        self.addCleanup(self.folder.cleanup)
        self.app = ResearchAssistant(Path(self.folder.name) / "state.sqlite3")
        self.session = SessionState()

    def ask(self, question):
        return self.app.ask(question, self.session, offline=True, semantic=False)

    def test_catalog_discovery_without_ids(self):
        r = self.ask("What experiments do we have?")
        self.assertEqual(len(r["tool_results"][0][1]["matches"]), len(list(RUNS_DIR.glob("*.json"))))

    def test_best_then_curve_journey(self):
        r = self.ask("Which had the best final validation accuracy?")
        best = max((load_run(p.stem) for p in RUNS_DIR.glob("*.json")), key=lambda x:x["metrics"][-1]["val_accuracy"])
        self.assertEqual(self.session.focused_run_id, best["config"]["run_id"])
        r = self.ask("Show its training and validation curves.")
        self.assertEqual(r["tool_results"][0][0], "plot_run_metrics")
        self.assertEqual(len(r["tool_results"][0][1]["points"]), len(best["metrics"]))

    def test_pair_reference_and_mechanism_journey(self):
        self.ask("Tell me about lr_01_seed3.")
        self.ask("Compare that run with lr_005_seed3.")
        r = self.ask("Why might the difference exist?")
        self.assertIn("lr_01_seed3", r["resolved_question"])
        self.assertIn("lr_005_seed3", r["resolved_question"])
        self.assertIn("Relevant ML knowledge", r["answer"])
        self.assertIn("4.45 percentage points", r["answer"])

    def test_corresponding_rate_uses_recorded_controls(self):
        self.ask("Show me the best learning-rate-0.1 experiment.")
        anchor = self.session.focused_run_id
        r = self.ask("Compare it with the corresponding learning-rate-0.05 experiment.")
        p = r["tool_results"][0][1]
        self.assertEqual(load_run(p["target_run_id"])["config"]["learning_rate"],0.05)
        self.assertEqual(set(p["changed_settings"]), {"learning_rate"})
        self.assertIn(anchor, r["resolved_question"])

    def test_ambiguous_pair_pronoun_is_not_guessed(self):
        self.ask("Compare lr_01_seed3 with lr_005_seed3.")
        self.assertEqual(self.ask("Plot it.")["status"], "clarification_needed")

    def test_reset_clears_reference(self):
        self.ask("Tell me about lr_01_seed3.")
        self.session.clear()
        self.assertEqual(self.ask("Plot its curve.")["status"], "clarification_needed")

    def test_wrong_id_offers_saved_alternatives(self):
        r = self.ask("Show lr_01_seed33")
        self.assertEqual(r["status"], "invalid_request")
        self.assertIn("lr_01_seed3", r["answer"])

    def test_unrelated_question_never_searches(self):
        with patch("v3.investigation_graph.search_notes") as search:
            r = self.ask("Who won the football World Cup?")
        search.assert_not_called()
        self.assertIn("appropriate tool", r["answer"])

    def test_single_run_investigation_finds_control(self):
        r = self.ask("Investigate why lr_01_seed3 underperformed.")
        self.assertEqual(r["status"], "awaiting_approval", r.get("last_error"))
        self.assertTrue(r["analysis"]["comparisons"][0]["controlled_learning_rate_pair"])
        self.assertEqual(r["analysis"]["comparisons"][0]["accuracy_delta_pp"], -4.45)

    def test_no_id_experiment_design_finds_complete_pair(self):
        r = self.ask("Design a controlled experiment to test learning rate instability with fresh seeds")
        self.assertEqual(r["status"], "awaiting_approval", r.get("last_error"))

    def test_invalid_native_tool_uses_visible_fallback(self):
        with patch("v2_agent.ask_ollama", return_value={"tool_calls":[{"function":{"name":"shell","arguments":{}}}]}):
            r = self.app.ask("Tell me about lr_01_seed3", self.session, semantic=False)
        self.assertEqual(r["status"], "completed")
        self.assertIn("71.45%", r["answer"])
        self.assertTrue(any(e["kind"] == "APP POLICY" for e in r["trace"]))

    def test_ollama_transport_failure_recovers(self):
        with patch("v2_agent.ask_ollama", side_effect=OSError("fixture server unavailable")):
            r = self.app.ask("Tell me about lr_01_seed3", semantic=False)
        self.assertIn("71.45%", r["answer"])

    def test_invalid_rank_enum_rejected(self):
        with self.assertRaises(ValueError):
            execute_tool("rank_experiments", {"sort_by":"made_up"})

    def test_spike_ranking_is_measured(self):
        r = self.ask("Which experiments have the largest validation-loss spikes?")
        values=[x["largest_loss_rise"] for x in r["tool_results"][0][1]["matches"]]
        self.assertEqual(values,sorted(values,reverse=True))

    def test_stale_proposal_can_be_rejected(self):
        r = self.ask("Investigate why lr_01_seed3 underperformed.")
        app=self.app.investigator
        p=app.store.proposal(r["proposal_id"])
        with patch("v3.experiment_designer.trainer_hash", return_value="fixture changed code"):
            result=app.decide(r["investigation_id"],p["hash"],"rejected")
        self.assertEqual(result["status"],"rejected")

    def test_cancellation_prevents_trainer_launch(self):
        r=self.ask("Investigate why lr_01_seed3 underperformed.")
        app=self.app.investigator
        p=app.store.proposal(r["proposal_id"])
        app.store.decide(p["id"],p["hash"],"approved","live")
        app.cancel(r["investigation_id"])
        with patch("v3.experiment_executor.subprocess.run") as trainer:
            outcome=execute(app.store,p["id"],p["hash"],"live")
        trainer.assert_not_called()
        self.assertEqual(outcome["status"],"cancelled")

    def test_global_live_execution_limit(self):
        app=self.app.investigator
        proposals=[]
        for _ in range(2):
            d=self.ask("Investigate why lr_01_seed3 underperformed.")
            p=app.store.proposal(d["proposal_id"])
            app.store.decide(p["id"],p["hash"],"approved","live")
            proposals.append(p)
        app.store.claim_execution(proposals[0]["id"],proposals[0]["hash"],"live")
        with self.assertRaises(PermissionError):
            app.store.claim_execution(proposals[1]["id"],proposals[1]["hash"],"live")

    def test_separate_seed_knowledge_exists(self):
        self.assertTrue(knowledge("random seeds reproducibility",semantic=False)["matches"])

    def test_unsupported_ml_topic_has_no_generated_answer(self):
        r=self.ask("Explain transformer attention models")
        self.assertIn("not covered",r["answer"])

    def test_retrieval_ranks_scores_and_sources_visible(self):
        r=self.ask("Have we seen unstable validation behavior before?")
        search=r["tool_results"][0][1]
        self.assertIn("stage_details",search)
        self.assertIn("rrf_score",search["matches"][0])
        self.assertIn("Sources",r["answer"])

    def test_next_experiment_without_any_run_reference(self):
        r=self.ask("What should we test next?")
        self.assertEqual(r["status"],"awaiting_approval",r.get("last_error"))

    def test_seed_question_uses_covered_knowledge(self):
        r=self.ask("Explain random seeds and reproducibility")
        self.assertIn("Relevant ML knowledge",r["answer"])

    def test_generalization_problem_query_uses_measured_rule(self):
        r=self.ask("Which runs appear to have generalization problems?")
        self.assertEqual(r["tool_results"][0][0],"find_overfitting_candidates")

    def test_saved_research_list_excludes_plain_lookup_turns(self):
        self.ask("Tell me about lr_01_seed3")
        self.assertEqual(self.app.investigator.store.list(research_only=True),[])
        self.ask("Investigate why lr_01_seed3 underperformed")
        self.assertEqual(len(self.app.investigator.store.list(research_only=True)),1)

    def test_running_progress_visible_before_worker_returns(self):
        d=self.ask("Investigate why lr_01_seed3 underperformed")
        app=self.app.investigator
        p=app.store.proposal(d["proposal_id"])
        app.store.decide(p["id"],p["hash"],"approved","live")
        observed=[]
        def fixture_worker(*args,**kwargs):
            progress=app.store.proposal(p["id"])["execution"]
            observed.append(progress["current_run_id"])
            self.assertTrue(Path(progress["logs"][0]).exists())
            app.cancel(d["investigation_id"])
            raise subprocess.CalledProcessError(1,"CANCEL_FIXTURE")
        with patch("v3.experiment_executor.subprocess.run",side_effect=fixture_worker):
            outcome=execute(app.store,p["id"],p["hash"],"live")
        self.assertEqual(len(observed),1)
        self.assertEqual(outcome["status"],"cancelled")


if __name__=="__main__":
    unittest.main(verbosity=2)
