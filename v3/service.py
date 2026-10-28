"""CLI/UI operations; human approval is deliberately absent from the LLM tool menu."""

import json
from pathlib import Path

from langgraph.types import Command

from v3.experiment_designer import validate_proposal
from v3.investigation_graph import investigation_graph
from v3.investigation_state import InvestigationStore, event
from v3.report import render_report


class Investigator:
    def __init__(self, db=None):
        self.store = InvestigationStore(db) if db else InvestigationStore()

    def _config(self, identifier):
        return {"configurable": {"thread_id": identifier}, "recursion_limit": 24}

    def start(self, objective, *, model_enabled=True, semantic=True, direct_mode=None, context=None, rerank=False):
        d = self.store.create(objective, model_enabled)
        d["semantic"] = semantic
        d["direct_mode"] = direct_mode
        d["rerank"] = rerank
        if context:
            d.update(context)
            event(d, "STATE UPDATE", context)
        try:
            with investigation_graph(self.store) as graph:
                graph.invoke({"doc": d}, self._config(d["investigation_id"]))
        except Exception as exc:
            d = self.store.load(d["investigation_id"])
            d.update(status="failed", last_error=f"{type(exc).__name__}: {exc}")
            event(d, "WORKFLOW ERROR", d["last_error"])
            self.store.save(d)
        return self.store.load(d["investigation_id"])

    def resume(self, identifier):
        d = self.store.load(identifier)
        with investigation_graph(self.store) as graph:
            snapshot = graph.get_state(self._config(identifier))
            if not snapshot.next:
                return d
            interrupted = any(t.interrupts for t in snapshot.tasks)
            if interrupted:
                p = self.store.proposal(d["proposal_id"])
                if p["status"] not in {"approved", "rejected", "deferred"}:
                    return d  # Loading/resuming does not imply approval.
                graph.invoke(Command(resume={"proposal_id": p["id"], "hash": p["hash"]}), self._config(identifier))
            else:
                graph.invoke(None, self._config(identifier))
        return self.store.load(identifier)

    def decide(self, identifier, expected_hash, decision, *, mode="dry_run", reason="", actor="user"):
        d = self.store.load(identifier)
        p = self.store.proposal(d["proposal_id"])
        if decision == "approved":
            validate_proposal(p["payload"])
        if p["investigation_id"] != identifier:
            raise PermissionError("Proposal does not belong to this investigation")
        with investigation_graph(self.store) as graph:
            if not graph.get_state(self._config(identifier)).next:
                graph.update_state(self._config(identifier), {"doc": d}, as_node="design")
                graph.invoke(None, self._config(identifier))
        self.store.decide(p["id"], expected_hash, decision, mode, reason, actor)
        return self.resume(identifier)

    def modify(self, identifier, payload):
        d = self.store.load(identifier)
        if payload.get("proposal_id") != d["proposal_id"] or payload.get("investigation_id") != identifier:
            raise ValueError("Cannot change investigation or proposal identity")
        validate_proposal(payload)
        self.store.put_proposal(identifier, payload)
        d["status"] = "awaiting_approval"
        event(d, "USER DECISION", {"decision": "modified", "approval": "invalidated"}, "USER")
        with investigation_graph(self.store) as graph:
            graph.update_state(self._config(identifier), {"doc": d}, as_node="design")
            graph.invoke(None, self._config(identifier))
        return self.store.load(identifier)

    def export(self, identifier, folder=None):
        d = self.store.load(identifier)
        p = self.store.proposal(d["proposal_id"]) if d.get("proposal_id") else None
        # Reflect current decisions even before graph resumption.
        d["report"] = render_report(d, p, self.store.decisions(p["id"]) if p else []) if d.get("plan") else d.get("answer", d.get("report", ""))
        self.store.save(d)
        out = Path(folder) if folder else self.store.path.parent / "reports"
        out.mkdir(parents=True, exist_ok=True)
        report = out / f"{identifier}.md"
        report.write_text(d["report"], encoding="utf-8")
        (out / f"{identifier}.json").write_text(json.dumps(d, indent=2), encoding="utf-8")
        return report

    def cancel(self, identifier):
        d = self.store.load(identifier)
        row = self.store.proposal(d["proposal_id"])
        if row["status"] not in {"running", "approved"}:
            raise ValueError("No active approved execution to cancel")
        folder = self.store.path.parent / "executions" / row["id"]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "cancel.requested").write_text("User requested cancellation", encoding="utf-8")
        return "Cancellation requested; the trainer checks between batches. Existing completed records are preserved."
