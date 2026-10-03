"""Small, process-local conversation state for V2.

The saved runs and notes are experiment knowledge. This object only remembers a
bounded number of user/assistant turns and run references within one session.
"""

from dataclasses import dataclass, field
import re

from experiment_data import RUNS_DIR


MAX_TURNS = 4


def mentioned_run_ids(text: str) -> list[str]:
    known = {path.stem for path in RUNS_DIR.glob("*.json")}
    return list(dict.fromkeys(token for token in re.findall(r"[A-Za-z0-9_-]+", text) if token in known))


@dataclass
class SessionState:
    turns: list[dict] = field(default_factory=list)
    focused_run_id: str | None = None
    referenced_run_ids: list[str] = field(default_factory=list)

    def resolve(self, question: str) -> tuple[str, dict]:
        """Resolve simple singular references using an explicit, visible focus ID."""
        found = mentioned_run_ids(question)
        resolved = question
        used = None
        if self.focused_run_id and re.search(r"\b(that run|this run|its|it)\b", question, re.I):
            resolved = re.sub(
                r"\b(that run|this run|its|it)\b",
                self.focused_run_id,
                question,
                count=1,
                flags=re.I,
            )
            used = self.focused_run_id
        return resolved, {
            "focused_run_id_before": self.focused_run_id,
            "explicit_run_ids": found,
            "resolved_reference": used,
            "resolved_question": resolved,
            "recent_turns": len(self.turns),
        }

    def history_messages(self) -> list[dict]:
        """Only compact summaries of the last four turns enter the next LLM call."""
        messages = []
        for turn in self.turns[-MAX_TURNS:]:
            messages.append({"role": "user", "content": turn["resolved_question"][:400]})
            decisions = ", ".join(
                f"{call['tool']}({call['arguments']})" for call in turn["tool_decisions"]
            )
            messages.append({
                "role": "assistant",
                "content": f"Tools used: {decisions[:300]}\n{turn['answer'][:700]}",
            })
        return messages

    def remember(self, question: str, resolved: str, answer: str, calls: list[dict], results: list[tuple[str, dict]]) -> None:
        ids = mentioned_run_ids(resolved)
        for name, result in results:
            if name == "search_runs" and "worst" in resolved.lower() and result.get("matches"):
                worst = min(result["matches"], key=lambda item: item["final_validation_accuracy_percent"])
                self.focused_run_id = worst["run_id"]
                ids.append(worst["run_id"])
            elif name == "get_experiment":
                ids.append(result["run_id"])
            elif name == "compare_experiments":
                ids.extend((result["baseline_run_id"], result["target_run_id"]))
            elif name == "plot_run_metrics":
                ids.append(result["run_id"])
        ids = list(dict.fromkeys(ids))
        if self.focused_run_id not in ids:
            if len(mentioned_run_ids(resolved)) == 1:
                self.focused_run_id = mentioned_run_ids(resolved)[0]
            elif len(ids) == 1:
                self.focused_run_id = ids[0]
        self.referenced_run_ids = list(dict.fromkeys((self.referenced_run_ids + ids)[-8:]))
        self.turns.append({
            "question": question,
            "resolved_question": resolved,
            "answer": answer,
            "tool_decisions": calls,
            "run_ids": ids,
        })
        del self.turns[:-MAX_TURNS]

    def snapshot(self) -> dict:
        return {
            "focused_run_id": self.focused_run_id,
            "referenced_run_ids": list(self.referenced_run_ids),
            "recent_turns": [
                {k: turn[k] for k in ("question", "resolved_question", "tool_decisions", "run_ids")}
                for turn in self.turns
            ],
            "history_bound": MAX_TURNS,
        }

    def clear(self) -> None:
        self.turns.clear()
        self.focused_run_id = None
        self.referenced_run_ids.clear()
