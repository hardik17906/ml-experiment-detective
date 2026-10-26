"""Deterministic scenarios. All training outcomes here are labeled in-memory fixtures."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from experiment_data import load_run
from langgraph.types import Command
from v2_state import SessionState
from v2_tools import execute_tool
from v3.analysis import check_record, compare_records
from v3.demo import QUESTION
from v3.experiment_designer import validate_config, validate_proposal
from v3.experiment_executor import evaluate_outcomes, execute, ingest_record
from v3.hypothesis import validate_evidence
from v3.investigation_graph import investigation_graph
from v3.investigation_state import ROOT, digest
from v3.planner import classify, make_plan
from v3.retrieval import knowledge, search_notes, tokens
from v3.service import Investigator


class InvestigatorTests(unittest.TestCase):
    def setUp(self):
        (ROOT / ".tmp").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="v3-tests-", dir=ROOT / ".tmp")
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "state.sqlite3"
        self.app = Investigator(self.db)

    def start(self):
        d = self.app.start(QUESTION, model_enabled=False, semantic=False)
        self.assertEqual(d["status"], "awaiting_approval", d.get("last_error"))
        return d

    def proposal(self):
        d = self.start()
        return d, self.app.store.proposal(d["proposal_id"])

    def test_01_exact_numeric_difference(self):
        pair = compare_records(load_run("lr_005_seed3"), load_run("lr_01_seed3"))
        self.assertEqual(pair["accuracy_delta_pp"], -4.45)
        self.assertEqual(round(pair["loss_delta"], 4), 0.1303)

    def test_02_controlled_pair_checks_every_field(self):
        pair = compare_records(load_run("lr_005_seed3"), load_run("lr_01_seed3"))
        self.assertTrue(pair["controlled_learning_rate_pair"])
        self.assertEqual(list(pair["changed_settings"]), ["learning_rate"])
        self.assertEqual(pair["missing_controls"], [])

    def test_03_missing_historical_controls_not_assumed(self):
        pair = compare_records(load_run("lr_005_seed2"), load_run("lr_01_seed2"))
        self.assertFalse(pair["controlled_learning_rate_pair"])
        self.assertIn("dropout", pair["missing_controls"])
        self.assertIn("validation_start", pair["missing_controls"])

    def test_04_confounded_comparison(self):
        a, b = load_run("lr_005_seed3"), load_run("lr_01_seed3")
        b["config"]["dropout"] = 0.5
        pair = compare_records(a, b)
        self.assertTrue(pair["confounded"])
        self.assertFalse(pair["controlled_learning_rate_pair"])

    def test_05_incomplete_metrics(self):
        record = load_run("lr_01_seed3")
        del record["metrics"][1]["val_loss"]
        self.assertTrue(check_record(record))
        pair = compare_records(load_run("lr_005_seed3"), record)
        self.assertNotIn("accuracy_delta_pp", pair)

    def test_06_unequal_epochs_do_not_compare_final(self):
        record = load_run("lr_01_seed3")
        record["metrics"].pop()
        record["config"]["epochs"] = 4
        self.assertNotIn("accuracy_delta_pp", compare_records(load_run("lr_005_seed3"), record))

    def test_07_pending_approval_blocks_execution(self):
        _, p = self.proposal()
        with self.assertRaises(PermissionError), patch("subprocess.run") as trainer:
            execute(self.app.store, p["id"], p["hash"], "dry_run")
        trainer.assert_not_called()

    def test_08_rejection_blocks_execution(self):
        _, p = self.proposal()
        self.app.store.decide(p["id"], p["hash"], "rejected")
        with self.assertRaises(PermissionError):
            execute(self.app.store, p["id"], p["hash"], "dry_run")

    def test_09_dry_run_cannot_authorize_live_training(self):
        _, p = self.proposal()
        self.app.store.decide(p["id"], p["hash"], "approved", "dry_run")
        with self.assertRaises(PermissionError):
            execute(self.app.store, p["id"], p["hash"], "live")

    def test_10_stale_hash_cannot_approve(self):
        _, p = self.proposal()
        with self.assertRaises(PermissionError):
            self.app.store.decide(p["id"], "wrong-hash", "approved")

    def test_11_modification_invalidates_approval(self):
        d, p = self.proposal()
        self.app.store.decide(p["id"], p["hash"], "approved")
        payload = p["payload"]
        for config in payload["runs"]:
            config["epochs"] = 4
        self.app.modify(d["investigation_id"], payload)
        updated = self.app.store.proposal(p["id"])
        self.assertEqual(updated["status"], "pending")
        self.assertNotEqual(updated["hash"], p["hash"])
        with self.assertRaises(PermissionError):
            execute(self.app.store, p["id"], updated["hash"], "dry_run")

    def test_12_arbitrary_command_field_rejected(self):
        _, p = self.proposal()
        p["payload"]["runs"][0]["shell_command"] = "echo forbidden"
        with self.assertRaises(ValueError):
            validate_proposal(p["payload"])
        with self.assertRaises(ValueError):
            execute_tool("execute_experiment", {"command": "anything"})

    def test_13_resource_limits_enforced(self):
        _, p = self.proposal()
        p["payload"]["runs"][0]["epochs"] = 1000
        with self.assertRaises(ValueError):
            validate_proposal(p["payload"])

    def test_14_changed_trainer_requires_new_proposal(self):
        _, p = self.proposal()
        p["payload"]["training_code_sha256"] = "old"
        with self.assertRaises(ValueError):
            validate_proposal(p["payload"])

    def test_15_duplicate_configuration_rejected(self):
        _, p = self.proposal()
        p["payload"]["runs"][0].update(model_seed=244, shuffle_seed=243)
        p["payload"]["runs"][1].update(model_seed=244, shuffle_seed=243)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validate_proposal(p["payload"])

    def test_16_new_seed_block_and_exact_shared_controls(self):
        _, p = self.proposal()
        a, b = p["payload"]["runs"]
        self.assertGreater(a["model_seed"], 344)
        self.assertEqual(a["model_seed"], b["model_seed"])
        self.assertEqual(a["shuffle_seed"], b["shuffle_seed"])
        self.assertEqual({k for k in a if a[k] != b[k]}, {"run_id", "learning_rate"})

    def test_17_structured_plan_dependencies(self):
        d = self.start()
        by_id = {p["id"]: p for p in d["plan"]}
        self.assertEqual(by_id["approval"]["status"], "waiting")
        self.assertEqual(by_id["analyze"]["depends_on"], ["collect"])
        self.assertEqual(by_id["execute"]["status"], "pending")

    def test_18_offline_trace_never_claims_model_decisions(self):
        d = self.start()
        self.assertFalse(any(x.get("origin") == "LLM" for x in d["trace"]))
        self.assertEqual(next(x for x in d["trace"] if x["kind"] == "PLANNER DECISION")["origin"], "APP POLICY")

    def test_19_hypothesis_grounding_and_competition(self):
        d = self.start()
        self.assertGreaterEqual(len(d["hypotheses"]), 2)
        self.assertTrue(validate_evidence(d))
        self.assertTrue(all(k in d["evidence"] for h in d["hypotheses"] for k in h["supporting_experiment_evidence"]))

    def test_20_forged_evidence_rejected(self):
        d = self.start()
        d["hypotheses"][0]["supporting_experiment_evidence"].append("RUN:invented")
        self.assertFalse(validate_evidence(d))

    def test_21_knowledge_cannot_prove_run_outcome(self):
        d = self.start()
        key = next(k for k in d["evidence"] if k.startswith("ML:"))
        d["hypotheses"][0]["supporting_experiment_evidence"].append(key)
        self.assertFalse(validate_evidence(d))

    def test_22_state_survives_new_store(self):
        d = self.start()
        reopened = Investigator(self.db)
        self.assertEqual(reopened.store.load(d["investigation_id"]), d)
        self.assertEqual(reopened.resume(d["investigation_id"])["status"], "awaiting_approval")

    def test_23_checkpoint_resume_dry_run_no_trainer(self):
        d, p = self.proposal()
        reopened = Investigator(self.db)
        with patch("subprocess.run") as trainer:
            result = reopened.decide(d["investigation_id"], p["hash"], "approved")
        trainer.assert_not_called()
        self.assertEqual(result["status"], "dry_run_completed")
        self.assertNotIn("outcome", result)
        self.assertEqual(result["execution"]["ingested"], [])

    def test_24_resume_token_does_not_grant_permission(self):
        d, p = self.proposal()
        with investigation_graph(self.app.store) as graph:
            with self.assertRaises(PermissionError):
                graph.invoke(Command(resume={"proposal_id": p["id"], "hash": p["hash"]}), self.app._config(d["investigation_id"]))

    def test_25_reject_routes_to_report(self):
        d, p = self.proposal()
        with patch("v3.investigation_graph.execute") as trainer:
            result = self.app.decide(d["investigation_id"], p["hash"], "rejected")
        trainer.assert_not_called()
        self.assertEqual(result["status"], "rejected")
        self.assertIn("## 15. Sources", result["report"])

    def test_26_wrong_model_tool_bounded_fallback(self):
        d = self.app.store.create(QUESTION, True)
        bad = {"tool_calls": [{"function": {"name": "train", "arguments": {}}}]}
        with patch("v3.planner.ask_decision", return_value=bad) as model:
            make_plan(d)
        self.assertEqual(model.call_count, 2)
        self.assertEqual(next(x for x in d["trace"] if x["kind"] == "PLANNER DECISION")["origin"], "APP POLICY")

    def test_27_no_model_tool_call_bounded_fallback(self):
        d = self.app.store.create(QUESTION, True)
        with patch("v3.planner.ask_decision", return_value={"content": "I think..."}) as model:
            make_plan(d)
        self.assertEqual(model.call_count, 2)

    def test_28_valid_model_decision_changes_plan(self):
        d = self.app.store.create(QUESTION, True)
        good = {"tool_calls": [{"function": {"name": "create_investigation_plan", "arguments": {
            "steps": ["retrieve_knowledge"], "knowledge_topic": "training validation loss curves"}}}]}
        with patch("v3.planner.ask_decision", return_value=good):
            make_plan(d)
        self.assertEqual(d["selected_steps"], ["retrieve_knowledge"])
        self.assertEqual(next(x for x in d["plan"] if x["id"] == "notes")["status"], "skipped")
        self.assertEqual(next(x for x in d["trace"] if x["kind"] == "PLANNER DECISION")["origin"], "LLM")

    def test_29_unrelated_question_never_searches(self):
        with patch("v3.investigation_graph.search_notes") as notes, patch("v2_agent.run_manual") as v2:
            d = self.app.start("Who won the football World Cup?", model_enabled=False, semantic=False)
        notes.assert_not_called()
        v2.assert_not_called()
        self.assertIn("appropriate tool", d["answer"])

    def test_30_uncovered_ml_question_explains_limit(self):
        d = self.app.start("Explain transformer attention models", model_enabled=False, semantic=False)
        self.assertIn("not covered", d["answer"])

    def test_31_wrong_run_id_fails_explicitly(self):
        d = self.app.start("Investigate lr_not_real compared with lr_005_seed3", model_enabled=False, semantic=False)
        self.assertEqual(d["status"], "failed")
        self.assertIn("Unknown run", d["last_error"])

    def test_32_training_failure_captured_without_training(self):
        _, p = self.proposal()
        self.app.store.decide(p["id"], p["hash"], "approved", "live")
        with patch("v3.experiment_executor.subprocess.run", side_effect=subprocess.CalledProcessError(1, "FIXTURE")):
            result = execute(self.app.store, p["id"], p["hash"], "live")
        self.assertEqual(result["status"], "failed")
        self.assertIn("CalledProcessError", result["error"])
        self.assertTrue(Path(result["logs"][0]).is_file())

    def test_33_fixture_ingestion_and_post_experiment_cycle(self):
        _, p = self.proposal()
        fixtures = []
        for original, config in zip(("lr_005_seed3", "lr_01_seed3"), p["payload"]["runs"]):
            r = load_run(original)
            r["config"] = config
            r["provenance"] = {"test_fixture": True, "original_source": original}
            ingested = ingest_record(r, config, investigation_id="TEST", proposal_id=p["id"], fixture=True)
            self.assertEqual(ingested["source_type"], "TEST_FIXTURE")
            fixtures.append(ingested["record"])
        result = evaluate_outcomes(fixtures)
        self.assertEqual(result["status"], "consistent")
        self.assertEqual(result["comparison"]["accuracy_delta_pp"], -4.45)

    def test_34_fixture_label_and_config_mandatory(self):
        r = load_run("lr_01_seed3")
        with self.assertRaises(ValueError):
            ingest_record(r, r["config"], investigation_id="TEST", proposal_id="TEST", fixture=True)
        r["provenance"] = {"test_fixture": True}
        wrong = dict(r["config"], learning_rate=0.15)
        with self.assertRaises(ValueError):
            ingest_record(r, wrong, investigation_id="TEST", proposal_id="TEST", fixture=True)

    def test_35_evidence_snapshot_tampering_detected(self):
        d = self.start()
        key = next(k for k in d["evidence"] if k.startswith("RUN:"))
        d["evidence"][key]["value"]["metrics"][0]["val_loss"] = 999
        self.assertFalse(validate_evidence(d))

    def test_36_memory_is_separate_from_persistence(self):
        session = SessionState(focused_run_id="lr_01_seed3")
        resolved, _ = session.resolve("Compare that run with lr_005_seed3")
        self.assertIn("lr_01_seed3", resolved)
        self.start()
        session.clear()
        self.assertEqual(len(self.app.store.list()), 1)

    def test_37_derived_summaries_include_unnoted_run(self):
        result = search_notes("lr_01_seed3", semantic=False)
        self.assertEqual(result["matches"][0]["run_id"], "lr_01_seed3")
        self.assertEqual(result["matches"][0]["source_type"], "DERIVED_ANALYSIS")
        self.assertIn("runs/lr_01_seed3.json", result["matches"][0]["observation"])

    def test_38_configuration_filter(self):
        result = search_notes("validation loss", filters={"learning_rate": 0.05}, semantic=False)
        self.assertTrue(result["matches"])
        self.assertTrue(all(load_run(x["run_id"])["config"]["learning_rate"] == 0.05 for x in result["matches"]))

    def test_39_stopwords_removed_negation_retained(self):
        self.assertNotIn("the", tokens("the validation loss did not fall"))
        self.assertIn("not", tokens("the validation loss did not fall"))
        self.assertIn("without", tokens("training without dropout"))

    def test_40_simple_question_uses_v2_without_full_plan(self):
        with patch("v2_agent.run_manual", return_value={"answer": "MEASURED FIXTURE", "trace": []}) as v2:
            d = self.app.start("What is the accuracy of lr_01_seed3?", model_enabled=False, semantic=False)
        v2.assert_called_once()
        self.assertEqual(d["plan"], [])
        self.assertEqual(d["answer"], "MEASURED FIXTURE")

    def test_41_approval_consumed_once(self):
        d, p = self.proposal()
        self.app.decide(d["investigation_id"], p["hash"], "approved")
        with self.assertRaises(PermissionError):
            execute(self.app.store, p["id"], p["hash"], "dry_run")

    def test_42_missing_file_reported(self):
        from v3.analysis import analyze
        with patch("v3.analysis.load_run", side_effect=ValueError("missing record fixture")):
            result = analyze(["lr_01_seed3"])
        self.assertTrue(result["incomplete_records"])
        self.assertEqual(result["comparisons"], [])

    def test_43_defer_preserves_proposal(self):
        d, p = self.proposal()
        result = self.app.decide(d["investigation_id"], p["hash"], "deferred")
        self.assertEqual(result["status"], "deferred")
        result = self.app.decide(d["investigation_id"], p["hash"], "approved")
        self.assertEqual(result["status"], "dry_run_completed")

    def test_44_retrieval_failure_falls_back_to_explicit_runs(self):
        with patch("v3.investigation_graph.search_notes", side_effect=OSError("weak/unavailable retrieval fixture")):
            d = self.start()
        self.assertEqual(len(d["analysis"]["comparisons"]), 1)
        self.assertTrue(any("retrieval failed" in x for x in d["uncertainties"]))

    def test_45_invalid_tool_arguments(self):
        for name, args in (("get_experiment", {"run_id": "../secret"}), ("search_runs", {"learning_rate": float('nan')}),
                           ("get_experiment", {}), ("search_notes", {"query": "x", "top_k": True})):
            with self.subTest(name=name, args=args), self.assertRaises(ValueError):
                execute_tool(name, args)

    def test_46_model_cannot_grant_live_permission(self):
        _, p = self.proposal()
        with self.assertRaises(PermissionError):
            self.app.store.decide(p["id"], p["hash"], "approved", "live", actor="LLM")

    def test_47_outcome_incomplete_opposing_and_equal(self):
        self.assertEqual(evaluate_outcomes([])["status"], "incomplete")
        low, high = load_run("lr_005_seed3"), load_run("lr_01_seed3")
        self.assertEqual(evaluate_outcomes([high, low])["status"], "opposing")
        self.assertEqual(evaluate_outcomes([low, deepcopy(low)])["status"], "inconclusive")

    def test_48_timeout_recorded_and_no_unbounded_retry(self):
        _, p = self.proposal()
        self.app.store.decide(p["id"], p["hash"], "approved", "live")
        with patch("v3.experiment_executor.subprocess.run", side_effect=subprocess.TimeoutExpired("FIXTURE", 600)) as runner:
            result = execute(self.app.store, p["id"], p["hash"], "live")
        self.assertEqual(runner.call_count, 1)
        self.assertEqual(result["status"], "failed")
        self.assertIn("TimeoutExpired", result["error"])

    def test_49_report_numbers_and_source_attribution(self):
        d = self.start()
        self.assertIn("75.90%", d["report"])
        self.assertIn("71.45%", d["report"])
        self.assertIn("-4.45 percentage points", d["report"])
        self.assertIn("+0.1303", d["report"])
        self.assertIn("runs/lr_01_seed3.json", d["report"])
        self.assertNotIn("confidence", d["report"].lower())

    def test_50_source_priority_protects_human_notes(self):
        result = search_notes("validation loss spike recover", semantic=False)
        self.assertTrue(all(x["source_type"] == "EXPERIMENT_NOTE" for x in result["matches"]))
        self.assertTrue(result["supplementary_derived_matches"])

    def test_51_no_run_id_discovers_and_inspects_sources(self):
        d = self.app.start("Investigate unstable validation behavior and possible hypotheses", model_enabled=False, semantic=False)
        self.assertNotEqual(d["status"], "failed", d.get("last_error"))
        self.assertTrue(d["records"])
        kinds = [e["kind"] for e in d["trace"]]
        self.assertLess(kinds.index("TOOL EXECUTION"), kinds.index("EXPERIMENT EVIDENCE"))
        self.assertIn("REPLANNING", kinds)

    def test_52_restart_during_execution_does_not_relaunch(self):
        d, p = self.proposal()
        self.app.store.decide(p["id"], p["hash"], "approved", "live")
        self.app.store.claim_execution(p["id"], p["hash"], "live")
        self.app.store.execution_result(p["id"], {"status": "running", "mode": "live", "run_ids": []})
        d["status"] = "approved"
        self.app.store.save(d)
        with investigation_graph(self.app.store) as graph:
            graph.update_state(self.app._config(d["investigation_id"]), {"doc": d}, as_node="approval")
        with patch("v3.investigation_graph.execute") as trainer:
            result = Investigator(self.db).resume(d["investigation_id"])
        trainer.assert_not_called()
        self.assertEqual(result["status"], "interrupted")

    def test_53_completed_execution_recovery_is_idempotent(self):
        d, p = self.proposal()
        result = self.app.decide(d["investigation_id"], p["hash"], "approved")
        with investigation_graph(self.app.store) as graph:
            replay = dict(result, status="approved")
            graph.update_state(self.app._config(d["investigation_id"]), {"doc": replay}, as_node="approval")
        with patch("v3.investigation_graph.execute") as trainer:
            result = Investigator(self.db).resume(d["investigation_id"])
        trainer.assert_not_called()
        self.assertEqual(result["status"], "dry_run_completed")

    def test_54_successful_fixture_execution_updates_report_and_hypothesis(self):
        d, p = self.proposal()
        ingested = []
        for original, config in zip(("lr_005_seed3", "lr_01_seed3"), p["payload"]["runs"]):
            r = load_run(original)
            r["config"] = config
            r["provenance"] = {"test_fixture": True}
            ingested.append(ingest_record(r, config, investigation_id=d["investigation_id"], proposal_id=p["id"], fixture=True))
        fixture_result = {"status": "completed", "mode": "fixture", "ingested": ingested, "run_ids": [], "logs": []}
        with patch("v3.investigation_graph.execute", return_value=fixture_result):
            result = self.app.decide(d["investigation_id"], p["hash"], "approved", mode="dry_run")
        self.assertEqual(result["outcome"]["status"], "consistent")
        self.assertEqual(next(h for h in result["hypotheses"] if h["hypothesis_id"] == "H1")["status"], "TEST_FIXTURE simulation: Supported by new controlled observations")
        self.assertIn("## 12. Follow-up results", result["report"])

    def test_55_wrong_run_in_simple_comparison_is_not_ignored(self):
        with patch("v2_agent.run_manual") as v2:
            d = self.app.start("Compare lr_missing with lr_005_seed3", model_enabled=False, semantic=False)
        self.assertEqual(d["status"], "failed")
        self.assertIn("Unknown run IDs", d["last_error"])
        v2.assert_not_called()

    def test_56_general_ml_mechanism_is_a_simple_question(self):
        self.assertEqual(classify("Why might a high learning rate create unstable training?"), "simple")


if __name__ == "__main__":
    unittest.main(verbosity=2)
