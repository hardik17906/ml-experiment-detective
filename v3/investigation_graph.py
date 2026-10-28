"""Durable LangGraph nodes. Only the approval branch reaches the executor."""

from contextlib import contextmanager
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from experiment_data import load_run
from v3.analysis import analyze, matched_runs, compare_records
from v3.experiment_designer import design, validate_proposal
from v3.experiment_executor import evaluate_outcomes, execute
from v3.hypothesis import build_evidence, generate, validate_evidence
from v3.investigation_state import event
from v3.planner import classify, make_plan, mark, unknown_run_ids, UNSUPPORTED
from v3.report import render_report
from v3.retrieval import knowledge, search_notes


class ResearchState(TypedDict):
    doc: dict


@contextmanager
def investigation_graph(store):
    def save(d):
        store.save(d)
        return {"doc": d}

    def classify_node(s):
        d = s["doc"]
        unknown = unknown_run_ids(d["objective"])
        if unknown:
            raise ValueError(f"Unknown run IDs: {unknown}")
        d["route"] = classify(d["objective"])
        event(d, "APP POLICY", {"classification": d["route"]})
        return save(d)

    def direct_node(s):
        d = s["doc"]
        if d["route"] == "unsupported":
            d["answer"] = UNSUPPORTED
        else:
            # Uncovered general ML questions should not be redirected to unrelated notes.
            from v2_state import mentioned_run_ids
            from v3.retrieval import knowledge
            import re
            if not mentioned_run_ids(d["objective"]) and re.search(r"\b(why|explain|how|what is)\b", d["objective"], re.I) and not re.search(r"\b(best|available|experiments|runs|spikes)\b", d["objective"], re.I):
                covered = knowledge(d["objective"], semantic=False)
                if not covered["matches"]:
                    d["answer"] = "This ML topic is not covered by the small local knowledge base. I cannot provide a grounded answer from the available sources."
                    d["status"] = "completed"
                    return save(d)
            if d.get("direct_mode") in {"graph", "policy"}:
                from graph_agent import run_graph
                result = run_graph(d["objective"], model_enabled=d["direct_mode"] == "graph",
                                   final_tools=True, semantic=d.get("semantic", True), rerank=d.get("rerank", False))
            else:
                from v2_agent import run_manual
                result = run_manual(d["objective"])
            d["answer"] = result["answer"]
            d["tool_results"] = result.get("tool_results", [])
            d["trace"].extend(result["trace"])
        d["status"] = "completed"
        d["report"] = d["answer"]
        return save(d)

    def plan_node(s):
        d = s["doc"]
        make_plan(d)
        d["status"] = "investigating"
        return save(d)

    def collect_node(s):
        d = s["doc"]
        if "search_notes" in d["selected_steps"]:
            try:
                d["notes"] = search_notes(d["objective"], semantic=d.get("semantic", True))
                event(d, "TOOL EXECUTION", {"tool": "search_notes", "result": d["notes"]})
                mark(d, "notes")
                if not d["run_ids"]:
                    candidates = d["notes"]["matches"][:2] + d["notes"].get("supplementary_derived_matches", [])[:1]
                    d["run_ids"] = list(dict.fromkeys(x["run_id"] for x in candidates))
                    event(d, "REPLANNING", {"reason": "Run IDs discovered through retrieval", "run_ids": d["run_ids"]}, "APP POLICY")
            except (ValueError, OSError, RuntimeError) as exc:
                mark(d, "notes", "failed", str(exc))
                d["uncertainties"].append(f"Note retrieval failed: {exc}")
        d["records"] = {}
        if len(d["run_ids"]) == 1:
            anchor = d["run_ids"][0]
            matches = matched_runs(anchor)
            if len(matches) == 1:
                d["run_ids"] = [matches[0], anchor]
                event(d, "REPLANNING", {"reason": "Found a counterpart with only the recorded learning rate changed",
                                         "run_ids": d["run_ids"]}, "APP POLICY")
        elif not d.get("explicit_run_ids") and d.get("direct_mode"):
            from experiment_data import RUNS_DIR
            from itertools import combinations
            pairs = []
            for a, b in combinations(sorted(p.stem for p in RUNS_DIR.glob("*.json")), 2):
                pair = compare_records(load_run(a), load_run(b))
                if pair["controlled_learning_rate_pair"]:
                    pairs.append((len(set((a,b)) & set(d["run_ids"])), a, b))
            if pairs:
                _, a, b = max(pairs)
                d["run_ids"] = sorted((a,b), key=lambda rid: load_run(rid)["config"]["learning_rate"])
                event(d, "REPLANNING", {"reason": "Selected a fully recorded controlled pair from discovered candidates", "run_ids": d["run_ids"]}, "APP POLICY")
        for rid in d["run_ids"]:
            try:
                record = load_run(rid)
                d["records"][rid] = record
                event(d, "EXPERIMENT EVIDENCE", {"tool": "get_experiment", "run_id": rid, "record": record})
            except (ValueError, KeyError, TypeError) as exc:
                d["uncertainties"].append(f"Missing experiment evidence {rid}: {exc}")
        mark(d, "collect", "completed" if d["records"] else "failed")
        return save(d)

    def analysis_node(s):
        d = s["doc"]
        d["analysis"] = analyze(list(d["records"]), include_seed_pairs="compare_seed_pairs" in d["selected_steps"])
        event(d, "TOOL EXECUTION", {"tool": "analyze_experiments", "result": d["analysis"]})
        # Include the exact source snapshots of all compared historical runs.
        for pair in d["analysis"]["seed_pairs"]:
            for rid in (pair["baseline_run_id"], pair["target_run_id"]):
                if rid not in d["records"]:
                    d["records"][rid] = load_run(rid)
        mark(d, "analyze")
        return save(d)

    def knowledge_node(s):
        d = s["doc"]
        if "retrieve_knowledge" in d["selected_steps"]:
            d["knowledge"] = knowledge(d["knowledge_topic"], semantic=d.get("semantic", True))
            mark(d, "knowledge", "completed" if d["knowledge"]["matches"] else "failed", None if d["knowledge"]["matches"] else "No covered local knowledge returned")
            event(d, "KNOWLEDGE RETRIEVAL", d["knowledge"])
        return save(d)

    def hypotheses_node(s):
        d = s["doc"]
        build_evidence(d)
        generate(d)
        mark(d, "hypotheses")
        return save(d)

    def validation_node(s):
        d = s["doc"]
        validate_evidence(d)
        mark(d, "validate", "completed" if d["evidence_validation"]["valid"] else "failed")
        return save(d)

    def design_node(s):
        d = s["doc"]
        proposal, limit = design(d)
        if proposal:
            store.put_proposal(d["investigation_id"], proposal)
            d["proposal_id"] = proposal["proposal_id"]
            d["status"] = "awaiting_approval"
            mark(d, "design")
        else:
            d["proposal_limitation"] = limit
            d["status"] = "evidence_collected"
            mark(d, "design", "skipped", limit)
            for key in ("approval", "execute", "outcome"):
                mark(d, key, "skipped", "No validated executable proposal")
        return save(d)

    def approval_node(s):
        d = s["doc"]
        p = store.proposal(d["proposal_id"])
        try:
            validate_proposal(p["payload"])
        except ValueError as exc:
            event(d, "APP POLICY", {"proposal_ineligible_for_approval": str(exc), "reject_or_modify": True})
        d["status"] = "awaiting_approval"
        mark(d, "approval", "waiting")
        event(d, "APPROVAL REQUEST", {"proposal_id": p["id"], "hash": p["hash"], "payload": p["payload"]}, "APP POLICY")
        d["report"] = render_report(d, p, store.decisions(p["id"]))
        store.save(d)
        # LangGraph persists this suspension. A resume token alone cannot grant permission.
        token = interrupt({"proposal_id": p["id"], "hash": p["hash"], "message": "Inspect the proposal and explicitly approve dry_run/live, reject, modify, or defer."})
        p = store.proposal(d["proposal_id"])
        if not isinstance(token, dict) or token.get("proposal_id") != p["id"] or token.get("hash") != p["hash"]:
            raise PermissionError("Resume token does not match the current proposal")
        if p["status"] not in {"approved", "rejected", "deferred"}:
            raise PermissionError("No persisted human decision is available")
        d["status"] = p["status"]
        if p["status"] == "approved":
            validate_proposal(p["payload"])
        decision = store.decisions(p["id"])[-1]
        event(d, "USER DECISION", decision, "USER" if decision["actor"] == "user" else "DEVELOPMENT_DRY_RUN")
        mark(d, "approval")
        if p["status"] != "approved":
            mark(d, "execute", "skipped", f"User decision: {p['status']}")
            mark(d, "outcome", "skipped", "No training executed")
        return save(d)

    def execute_node(s):
        d = s["doc"]
        p = store.proposal(d["proposal_id"])
        if p["status"] == "approved":
            result = execute(store, p["id"], p["hash"], p["mode"])
        elif p["execution"] and p["status"] != "running":
            result = p["execution"]  # A finished execution is never launched twice after a crash.
        elif p["status"] == "running":
            # A process may still exist after an app crash. Do not start another trainer.
            result = dict(p["execution"] or {}, status="interrupted",
                          error="Application restarted during execution. Inspect existing logs/processes; automatic training retry is forbidden.")
            store.execution_result(p["id"], result)
        else:
            raise PermissionError("The execution branch has no usable approval")
        d["execution"] = result
        d["status"] = result["status"]
        mark(d, "execute", "completed" if result["status"] in {"completed", "dry_run_completed"} else "failed")
        event(d, "EXECUTION RESULT", result, "USER_AUTHORIZED")
        return save(d)

    def outcome_node(s):
        d = s["doc"]
        if d["execution"]["status"] == "completed":
            records = [x["record"] for x in d["execution"].get("ingested", [])]
            d["outcome"] = evaluate_outcomes(records)
            is_fixture = any(x.get("source_type") == "TEST_FIXTURE" for x in d["execution"].get("ingested", []))
            if is_fixture:
                d["outcome"]["test_fixture"] = True
                d["outcome"]["interpretation"] = "TEST_FIXTURE simulation only: " + d["outcome"]["interpretation"]
            for item in d["execution"].get("ingested", []):
                rid, record = item["run_id"], item["record"]
                d["records"][rid] = record
                from v3.investigation_state import digest
                d["evidence"][f"FOLLOWUP:{rid}"] = {"source_type": item["source_type"], "source": "in-memory TEST_FIXTURE" if is_fixture else f"runs/{rid}.json", "sha256": digest(record), "value": record}
            for h in d["hypotheses"]:
                if h["hypothesis_id"] == "H1":
                    h["status"] = "Supported by new controlled observations" if d["outcome"]["status"] == "consistent" else "Inconclusive"
                    if is_fixture:
                        h["status"] = "TEST_FIXTURE simulation: " + h["status"]
            mark(d, "outcome")
            event(d, "POST-EXPERIMENT ANALYSIS", d["outcome"])
        else:
            mark(d, "outcome", "skipped", "No complete new measured pair; dry runs contain no measurements")
        return save(d)

    def report_node(s):
        d = s["doc"]
        p = store.proposal(d["proposal_id"]) if d.get("proposal_id") else None
        mark(d, "report")
        d["report"] = render_report(d, p, store.decisions(p["id"]) if p else [])
        event(d, "FINAL REPORT", {"status": d["status"], "sources": list(d.get("evidence", {}))})
        return save(d)

    builder = StateGraph(ResearchState)
    for name, node in (("classify", classify_node), ("direct", direct_node), ("plan", plan_node),
                       ("collect", collect_node), ("analyze", analysis_node), ("knowledge", knowledge_node),
                       ("hypotheses", hypotheses_node), ("validate", validation_node), ("design", design_node),
                       ("approval", approval_node), ("execute", execute_node), ("outcome", outcome_node), ("report", report_node)):
        builder.add_node(name, node)
    builder.add_edge(START, "classify")
    builder.add_conditional_edges("classify", lambda s: "plan" if s["doc"]["route"] == "investigation" else "direct")
    builder.add_edge("direct", END)
    for a, b in (("plan", "collect"), ("collect", "analyze"), ("analyze", "knowledge"),
                 ("knowledge", "hypotheses"), ("hypotheses", "validate"), ("validate", "design")):
        builder.add_edge(a, b)
    builder.add_conditional_edges("design", lambda s: "approval" if s["doc"].get("proposal_id") else "report")
    builder.add_conditional_edges("approval", lambda s: "execute" if s["doc"]["status"] == "approved" else "report")
    builder.add_edge("execute", "outcome")
    builder.add_edge("outcome", "report")
    builder.add_edge("report", END)
    with SqliteSaver.from_conn_string(str(store.path)) as checkpoints:
        yield builder.compile(checkpointer=checkpoints)
