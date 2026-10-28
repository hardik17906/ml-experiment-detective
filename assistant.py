"""Primary application facade: bounded conversation plus the existing research graph."""

from difflib import get_close_matches

from experiment_data import RUNS_DIR
from v2_state import SessionState, mentioned_run_ids
from v3.planner import unknown_run_ids
from v3.service import Investigator


class ResearchAssistant:
    def __init__(self, db=None):
        self.investigator = Investigator(db)

    def ask(self, question, session=None, *, offline=False, semantic=True, rerank=False):
        session = session if session is not None else SessionState()
        before = session.snapshot()
        try:
            resolved, memory = session.resolve(question)
        except ValueError as exc:
            return {"answer": str(exc), "trace": [{"kind": "APP POLICY", "data": {"clarification": str(exc)}}],
                    "status": "clarification_needed", "tool_results": []}
        unknown = unknown_run_ids(resolved)
        if unknown:
            ids = sorted(p.stem for p in RUNS_DIR.glob("*.json"))
            alternatives = {x: get_close_matches(x, ids, n=3, cutoff=0.3) for x in unknown}
            answer = f"Unknown experiment ID(s): {', '.join(unknown)}. Available alternatives: {alternatives}. Browse Experiment Explorer to choose a saved run."
            return {"answer": answer, "status": "invalid_request", "tool_results": [],
                    "trace": [{"kind": "APP POLICY", "data": {"unknown_ids": unknown, "alternatives": alternatives}}]}
        context = {"original_question": question, "resolved_question": resolved,
                   "conversation_before": before, "reference_resolution": memory,
                   "explicit_run_ids": mentioned_run_ids(resolved)}
        state = self.investigator.start(resolved, model_enabled=not offline, semantic=semantic,
                                        direct_mode="policy" if offline else "graph", context=context, rerank=rerank)
        answer = state.get("answer") or state.get("report") or state.get("last_error", "No evidence was collected.")
        results = state.get("tool_results", [])
        calls = [{"tool": e["data"]["tool"], "arguments": e["data"].get("arguments", {}), "origin": e["kind"]}
                 for e in state["trace"] if e["kind"] in {"AGENT", "APP POLICY"}
                 and isinstance(e["data"], dict) and "tool" in e["data"]]
        session.remember(question, resolved, answer, calls, results)
        comparisons = state.get("analysis", {}).get("comparisons", [])
        if comparisons:
            session.comparison_run_ids = [comparisons[0]["baseline_run_id"], comparisons[0]["target_run_id"]]
        state["conversation_after"] = session.snapshot()
        state["answer"] = answer
        state["trace"].append({"kind": "STATE UPDATE", "origin": "PYTHON", "data": state["conversation_after"]})
        self.investigator.store.save(state)
        return state
