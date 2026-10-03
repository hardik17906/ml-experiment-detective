"""V2 manual agent. The choose -> execute -> observe loop stays explicit."""

import json
import re
from urllib.request import Request, urlopen

from simple_agent import explicit_run_filters
from v2_answers import render_answer
from v2_state import SessionState, mentioned_run_ids
from v2_tools import execute_tool, tool_menu


MODEL = "qwen3:1.7b"
MAX_TOOL_CALLS = 6
SYSTEM = (
    "You are ML Experiment Detective. Use a tool before answering a question about saved runs. "
    "For a behavior question without a run ID, search_notes first, then inspect one or "
    "more returned run IDs with get_experiment. Do not guess a run ID. "
    "For a question asking which runs match an exact learning rate, train size, or dropout value, "
    "use search_runs with that numeric filter. "
    "For a question about two runs, call compare_experiments first, with the reference as baseline "
    "and the run being explained as target. Example: 'Why was runB worse than runA?' requires "
    "compare_experiments(baseline_run_id='runA', target_run_id='runB'). "
    "Do not replace that call with two get_experiment calls. Use get_experiment for questions about one run. "
    "Use only measured facts returned by tools. Never call a changed setting the cause of a metric difference. "
    "For accuracy differences, say percentage points (pp), never percent. "
    "Use search_ml_knowledge for general mechanisms after collecting any relevant run evidence. "
    "Do not invent runs, measurements, filters, or citations. After enough evidence, answer briefly."
)


def _learning_rates(question: str) -> list[float]:
    return [float(value) for value in re.findall(
        r"learning[- ]rate\s*(?:-|=|:|of)?\s*(\d+(?:\.\d+)?)", question, flags=re.I
    )]


def _first_tool_names(question: str) -> list[str]:
    lower = question.lower()
    ids = mentioned_run_ids(question)
    rates = _learning_rates(question)
    if "overfit" in lower:
        return ["find_overfitting_candidates"]
    if len(rates) >= 2 and ("compare" in lower or "group" in lower):
        return ["compare_run_group"]
    if ("curve" in lower or "chart" in lower or "plot" in lower) and len(ids) == 1:
        return ["plot_run_metrics"]
    if len(ids) == 1 and any(term in lower for term in (
        "best validation", "minimum validation loss", "largest loss rise", "summarize the curve",
    )):
        return ["summarize_run_curve"]
    if "seen" in lower or "similar" in lower or "before" in lower:
        return ["search_notes"]
    if len(ids) >= 2:
        return ["compare_experiments"]
    if "worst" in lower and rates:
        return ["search_runs"]
    if len(ids) == 1:
        return ["get_experiment"]
    if re.search(r"\b(learning[- ]rate|train[- ]size|dropout)\b", lower) and not re.search(r"\b(why|might|explain)\b", lower):
        return ["search_runs"]
    if re.search(r"\b(why|might|explain|what is)\b", lower):
        return ["search_ml_knowledge"]
    return ["search_notes"]


def _fallback_arguments(name: str, state: dict) -> dict:
    question = state["resolved_question"]
    ids = mentioned_run_ids(question)
    if name == "compare_experiments":
        if len(ids) < 2:
            raise ValueError("Two saved run IDs are required for comparison")
        if "worse than" in question.lower() or "behaved worse than" in question.lower():
            return {"baseline_run_id": ids[1], "target_run_id": ids[0]}
        return {"baseline_run_id": ids[0], "target_run_id": ids[1]}
    if name in {"get_experiment", "summarize_run_curve", "plot_run_metrics"}:
        if not ids:
            raise ValueError("A saved run ID is required")
        return {"run_id": ids[0]}
    if name == "search_runs":
        filters = explicit_run_filters(question)
        if not filters:
            rates = _learning_rates(question)
            if rates:
                filters = {"learning_rate": rates[0]}
        return filters
    if name == "compare_run_group":
        rates = _learning_rates(question)
        if len(rates) < 2:
            raise ValueError("Two learning rates are required")
        return {"learning_rate_a": rates[0], "learning_rate_b": rates[1]}
    if name == "search_notes":
        return {"query": question, "top_k": 2, "rerank": state["rerank"]}
    if name == "search_ml_knowledge":
        comparisons = [result for tool, result in state["tool_results"] if tool == "compare_experiments"]
        if comparisons and "learning_rate" in comparisons[-1]["changed_settings"]:
            query = "high learning rate optimization instability"
        else:
            query = question
        return {"query": query, "top_k": 2}
    return {}


def prepare_turn(question: str, session: SessionState | None = None, *, rerank: bool = False) -> dict:
    session = session if session is not None else SessionState()
    if not question.strip():
        raise ValueError("Question must not be empty")
    resolved, memory = session.resolve(question)
    first_names = _first_tool_names(resolved)
    ids = mentioned_run_ids(resolved)
    id_context = ", ".join(ids) if ids else "none"
    messages = [{"role": "system", "content": SYSTEM + f" Exact saved run IDs in this question: {id_context}."}]
    messages.extend(session.history_messages())
    messages.append({"role": "user", "content": resolved})
    return {
        "question": question,
        "resolved_question": resolved,
        "session": session,
        "messages": messages,
        "first_names": first_names,
        "rerank": rerank,
        "tool_results": [],
        "decisions": [],
        "trace": [
            {"kind": "USER", "data": question},
            {"kind": "MEMORY BEFORE", "data": memory},
        ],
        "tool_count": 0,
        "pending_calls": [],
        "answer": None,
    }


def available_tool_names(state: dict) -> list[str]:
    results = state["tool_results"]
    names = [name for name, _ in results]
    if not results:
        return state["first_names"]
    if "search_notes" in names and "get_experiment" not in names:
        return ["get_experiment"]
    if re.search(r"\b(why|might|explain)\b", state["resolved_question"], re.I) and "search_ml_knowledge" not in names:
        return ["search_ml_knowledge"]
    return []


def ask_ollama(messages: list[dict], available_tools: list[dict]) -> dict:
    body = {
        "model": MODEL, "stream": False, "think": False,
        "messages": messages, "tools": available_tools,
        "options": {"temperature": 0, "num_ctx": 4096, "num_predict": 400},
    }
    request = Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urlopen(request, timeout=300) as response:
        result = json.load(response)
    if not result.get("done") or result.get("done_reason") != "stop":
        raise RuntimeError("Ollama did not complete its response")
    return result["message"]


def policy_call(state: dict) -> tuple[str, dict] | None:
    names = [name for name, _ in state["tool_results"]]
    if not names:
        name = state["first_names"][0]
        return name, _fallback_arguments(name, state)
    if "search_notes" in names and "get_experiment" not in names:
        search = next(result for name, result in reversed(state["tool_results"]) if name == "search_notes")
        if search["matches"]:
            return "get_experiment", {"run_id": search["matches"][0]["run_id"]}
    if re.search(r"\b(why|might|explain)\b", state["resolved_question"], re.I) and "search_ml_knowledge" not in names:
        return "search_ml_knowledge", _fallback_arguments("search_ml_knowledge", state)
    return None


def execute_call(state: dict, name: str, arguments: dict, *, origin: str) -> None:
    available = available_tool_names(state)
    if name not in available:
        raise ValueError(f"{name} was not in the offered tool menu: {available}")
    corrected = dict(arguments)
    if name in {"get_experiment", "compare_experiments", "search_runs", "compare_run_group", "plot_run_metrics", "summarize_run_curve"}:
        if name == "get_experiment" and any(tool == "search_notes" for tool, _ in state["tool_results"]):
            search = next(result for tool, result in reversed(state["tool_results"]) if tool == "search_notes")
            returned_ids = [item["run_id"] for item in search["matches"]]
            expected = {"run_id": returned_ids[0]} if returned_ids and corrected.get("run_id") not in returned_ids else {}
        else:
            expected = _fallback_arguments(name, state)
        # Match only constraints/IDs explicitly present in the question.
        if expected and corrected != expected:
            corrected = expected
    if name == "search_notes":
        corrected["rerank"] = state["rerank"]
    if name == "find_overfitting_candidates":
        corrected = {}
    if name in {"search_notes", "search_ml_knowledge"} and not re.search(r"\btop\s*[1-5]\b", state["question"], re.I):
        if corrected.get("top_k", 2) > 2:
            corrected["top_k"] = 2
    if name == "search_ml_knowledge" and any(
        run_id in str(corrected.get("query", "")) for run_id in mentioned_run_ids(state["resolved_question"])
    ):
        corrected = _fallback_arguments(name, state)
    if corrected != arguments:
        state["trace"].append({"kind": "APP FILTER", "data": {"from": arguments, "to": corrected}})
    state["trace"].append({"kind": origin, "data": {"tool": name, "arguments": corrected}})
    state["decisions"].append({"origin": origin, "tool": name, "arguments": corrected})
    try:
        result = execute_tool(name, corrected)
    except (ValueError, KeyError, TypeError, FileNotFoundError) as exc:
        result = {"error": str(exc)}
    state["trace"].append({"kind": "TOOL RESULT", "data": {"tool": name, "result": result}})
    if "stages" in result:
        for stage, rows in result["stages"].items():
            state["trace"].append({"kind": stage, "data": rows})
    if "error" not in result:
        state["tool_results"].append((name, result))
    state["messages"].append({
        "role": "assistant", "content": "",
        "tool_calls": [{"function": {"name": name, "arguments": corrected}}],
    })
    # Keep the model's context compact; the full result remains in the visible trace.
    model_result = result
    if name == "search_notes" and "matches" in result:
        model_result = {"matches": [
            {key: match[key] for key in ("run_id", "observation", "hybrid_rank", "final_rank", "cosine_similarity")}
            for match in result["matches"]
        ]}
    elif name == "find_overfitting_candidates" and "matches" in result:
        model_result = {"rule": result["rule"], "candidate_ids": [x["run_id"] for x in result["matches"]]}
    state["messages"].append({"role": "tool", "tool_name": name, "content": json.dumps(model_result)})
    state["tool_count"] += 1


def finish_turn(state: dict) -> dict:
    answer = render_answer(state["resolved_question"], state["tool_results"])
    state["session"].remember(
        state["question"], state["resolved_question"], answer,
        state["decisions"], state["tool_results"],
    )
    state["trace"].append({"kind": "MEMORY AFTER", "data": state["session"].snapshot()})
    state["trace"].append({"kind": "FINAL", "data": answer})
    state["answer"] = answer
    return {"answer": answer, "trace": state["trace"], "session": state["session"], "tool_results": state["tool_results"]}


def run_manual(question: str, session: SessionState | None = None, *, rerank: bool = False) -> dict:
    state = prepare_turn(question, session, rerank=rerank)

    # The educational manual loop: decide -> execute -> observe -> decide again.
    for _ in range(MAX_TOOL_CALLS + 1):
        names = available_tool_names(state)
        state["trace"].append({"kind": "TOOL MENU", "data": names})
        message = ask_ollama(state["messages"], tool_menu(names))
        calls = message.get("tool_calls") or []
        if not calls:
            needed = policy_call(state)
            if needed and state["tool_count"] < MAX_TOOL_CALLS:
                execute_call(state, needed[0], needed[1], origin="APP POLICY")
                continue
            if not state["tool_results"]:
                raise RuntimeError("The model stopped before evidence was collected")
            return finish_turn(state)
        if state["tool_count"] >= MAX_TOOL_CALLS:
            raise RuntimeError("V2 agent reached its tool-call limit")
        # Reconsider the menu after each observation; a multi-call model response
        # cannot assume that later calls still belong to the next menu.
        function = calls[0]["function"]
        execute_call(state, function["name"], function["arguments"], origin="AGENT")
    raise RuntimeError("V2 agent did not stop within its step limit")


def print_trace(events: list[dict]) -> None:
    for event in events:
        if event["kind"] == "FINAL":
            continue
        print(f"{event['kind']} -> {json.dumps(event['data'], ensure_ascii=False, sort_keys=True)}")
