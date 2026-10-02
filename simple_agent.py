"""A small local tool-using agent for saved ML experiment runs."""

import argparse
import json
import math
import re
from urllib.request import Request, urlopen

from experiment_data import PROJECT_DIR, compare_experiments, get_experiment, search_runs
from note_retrieval import MODEL_ID, encode_queries_and_notes, load_notes, semantic_rank


MODEL = "qwen3:1.7b"
MAX_TOOL_CALLS = 5
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_experiment",
            "description": "Read one saved experiment. Use only for a question about one run; for two run IDs, use compare_experiments instead.",
            "parameters": {
                "type": "object",
                "properties": {"run_id": {"type": "string", "description": "Exact saved run ID"}},
                "required": ["run_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_experiments",
            "description": "Preferred tool whenever a question mentions two run IDs. Compare their recorded settings and final metrics. Use baseline_run_id for the reference and target_run_id for the run being explained; differences are target minus baseline.",
            "parameters": {
                "type": "object",
                "properties": {
                    "baseline_run_id": {"type": "string", "description": "Reference run ID"},
                    "target_run_id": {"type": "string", "description": "Run ID being compared with the reference"},
                },
                "required": ["baseline_run_id", "target_run_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_notes",
            "description": "Semantic search over experiment observation notes. Use for questions about behavior without a known run ID. Returns candidate primary run IDs, note excerpts, and similarity scores. Inspect returned runs with get_experiment for exact metrics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Observation question or search phrase"},
                    "top_k": {"type": "integer", "description": "Number of notes, 1 to 5; default 2"},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_runs",
            "description": "Find saved runs by exact structured configuration values, such as learning rate, train size, or dropout. Use this for 'which experiments used' questions; it does not use embeddings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "learning_rate": {"type": "number", "description": "Exact learning rate, e.g. 0.1"},
                    "train_size": {"type": "integer", "description": "Exact training image count"},
                    "dropout": {"type": "number", "description": "Exact recorded dropout value"},
                },
                "additionalProperties": False,
            },
        },
    },
]


def search_notes(query: str, top_k: int = 2) -> dict:
    if not query.strip():
        raise ValueError("Search query must not be empty")
    notes = load_notes()
    if not notes:
        return {"query": query, "embedding_model": MODEL_ID, "matches": []}
    embeddings = encode_queries_and_notes([query], notes, local_only=True)
    ranked = semantic_rank(embeddings[0], embeddings[1:], notes)
    return {
        "query": query,
        "embedding_model": MODEL_ID,
        "matches": [
            {
                "run_id": path.stem,
                "note_source": f"notes/{path.name}",
                "run_source": f"runs/{path.stem}.json",
                "similarity": round(score, 3),
                "observation": observation,
            }
            for score, path, observation in ranked[:top_k]
        ],
    }


HANDLERS = {
    "search_notes": (search_notes, {"query"}, {"top_k"}),
    "get_experiment": (get_experiment, {"run_id"}, set()),
    "compare_experiments": (
        compare_experiments, {"baseline_run_id", "target_run_id"}, set()
    ),
    "search_runs": (search_runs, set(), {"learning_rate", "train_size", "dropout"}),
}


def execute_tool(name: str, arguments: dict) -> dict:
    if name not in HANDLERS:
        raise ValueError(f"Tool is not allowed: {name}")
    function, required, optional = HANDLERS[name]
    if (
        not isinstance(arguments, dict)
        or not required <= set(arguments)
        or set(arguments) - required - optional
    ):
        raise ValueError(f"{name} requires {sorted(required)}; optional: {sorted(optional)}")
    if name in {"get_experiment", "compare_experiments"} and any(
        not isinstance(value, str) for value in arguments.values()
    ):
        raise ValueError("Run IDs must be strings")
    if name == "search_notes":
        if not isinstance(arguments["query"], str) or not arguments["query"].strip():
            raise ValueError("Search query must be nonempty text")
        top_k = arguments.get("top_k", 2)
        if not isinstance(top_k, int) or isinstance(top_k, bool) or not 1 <= top_k <= 5:
            raise ValueError("top_k must be an integer from 1 to 5")
    if name == "search_runs":
        for key, value in arguments.items():
            if key == "train_size":
                if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                    raise ValueError("train_size must be a positive integer")
            elif not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
                raise ValueError(f"{key} must be a finite number")
    return function(**arguments)


def explicit_run_filters(question: str) -> dict:
    """Read simple exact filters stated by the user, not inferred by the model."""
    patterns = {
        "learning_rate": r"learning[- ]rate\s*(?:=|of|:)?\s*(\d+(?:\.\d+)?)",
        "train_size": r"train(?:ing)?[- ]size\s*(?:=|of|:)?\s*(\d+)",
        "dropout": r"dropout\s*(?:=|of|:)?\s*(\d+(?:\.\d+)?)",
    }
    filters = {}
    for key, pattern in patterns.items():
        found = re.search(pattern, question, re.IGNORECASE)
        if found:
            filters[key] = int(found[1]) if key == "train_size" else float(found[1])
    return filters


def ask_ollama(messages: list[dict], available_tools: list[dict]) -> dict:
    body = {
        "model": MODEL,
        "stream": False,
        "think": False,
        "messages": messages,
        "tools": available_tools,
        "options": {"temperature": 0, "num_ctx": 4096, "num_predict": 500},
    }
    request = Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=300) as response:
        result = json.load(response)
    if not result.get("done") or result.get("done_reason") != "stop":
        raise RuntimeError("Ollama did not complete its response")
    return result["message"]


def render_answer(tool_results: list[tuple[str, dict]]) -> str:
    """Render only retrieved notes and calculated run facts, with linked sources."""
    comparisons = [item for name, item in tool_results if name == "compare_experiments"]
    note_searches = [item for name, item in tool_results if name == "search_notes"]
    run_searches = [item for name, item in tool_results if name == "search_runs"]
    inspections = [item for name, item in tool_results if name == "get_experiment"]
    sources = set()
    lines = []

    if comparisons:
        lines.append("Observed differences:")
        for result in comparisons:
            changes = result["changed_settings"]
            settings = ", ".join(
                f"{key} {values['baseline']} -> {values['target']}"
                for key, values in changes.items()
            ) or "none recorded"
            lines.extend([
                f"- {result['baseline_run_id']} -> {result['target_run_id']} at epoch {result['final_epoch']}:",
                f"  validation accuracy {result['baseline_validation_accuracy_percent']:.2f}% -> "
                f"{result['target_validation_accuracy_percent']:.2f}% "
                f"({result['accuracy_change_target_minus_baseline_pp']:+.2f} percentage points); "
                f"validation loss {result['baseline_validation_loss']:.4f} -> "
                f"{result['target_validation_loss']:.4f} "
                f"({result['loss_change_target_minus_baseline']:+.4f}).",
                f"  Changed recorded settings: {settings}.",
            ])
            sources.update((result["baseline_source"], result["target_source"]))
        lines.extend(["", "Interpretation: These comparisons show measured differences. "
                      "A changed setting is worth investigating, but these runs do not prove a cause."])

    elif note_searches:
        matches = note_searches[-1]["matches"]
        by_id = {item["run_id"]: item for item in inspections}
        lines.append("Retrieved observations and inspected metrics:")
        for match in matches:
            run = by_id.get(match["run_id"])
            if run is None:
                continue
            sources.update((match["note_source"], run["source"]))
            lines.append(
                f"- {match['run_id']} (note similarity {match['similarity']:.3f}): "
                f"{match['observation']}"
            )
            patterns = run["validation_loss_recoveries"]
            if patterns:
                for pattern in patterns:
                    epochs = pattern["epochs"]
                    values = pattern["losses"]
                    lines.append(
                        f"  Saved validation loss, epochs {epochs[0]}->{epochs[1]}->{epochs[2]}: "
                        f"{values[0]:.4f} -> {values[1]:.4f} -> {values[2]:.4f}."
                    )
            else:
                lines.append("  No consecutive rise-then-fall pattern in this run's saved epochs.")
        if len(lines) == 1:
            lines.append("Search returned candidate notes; no matching run metrics were inspected.")
            for match in matches:
                lines.append(f"- {match['run_id']}: similarity {match['similarity']:.3f}.")
                sources.add(match["note_source"])
        lines.append("Similarity ranks notes; it is not a probability or diagnosis.")

    elif run_searches:
        for search in run_searches:
            filters = search["filters"]
            filter_text = ", ".join(f"{key}={value}" for key, value in filters.items()) or "none"
            lines.append(f"Saved runs matching {filter_text}: {len(search['matches'])}")
            if filters:
                for item in search["matches"]:
                    lines.append(
                        f"- {item['run_id']}: learning rate {item['learning_rate']}, "
                        f"train size {item['train_size']}, final validation accuracy "
                        f"{item['final_validation_accuracy_percent']:.2f}% "
                        f"at epoch {item['final_epoch']}."
                    )
                    sources.add(item["source"])
                lines.append("These are saved records; repeated configurations are not independent experiments.")
            else:
                rates = sorted({item["learning_rate"] for item in search["matches"]})
                for rate in rates:
                    group = [item for item in search["matches"] if item["learning_rate"] == rate]
                    lines.append(f"Learning rate {rate:g}: {len(group)} saved records")
                    for item in group:
                        lines.append(
                            f"- {item['run_id']}: {item['final_validation_accuracy_percent']:.2f}% "
                            f"validation accuracy, train size {item['train_size']}, "
                            f"epoch {item['final_epoch']}."
                        )
                        sources.add(item["source"])
                lines.append("These records can repeat configurations and use different training sizes or epochs; "
                             "this grouping alone is not a controlled comparison.")
        if inspections:
            lines.append("Inspected runs:")
            for run in inspections:
                lines.append(
                    f"- {run['run_id']}: final validation accuracy "
                    f"{run['final_validation_accuracy_percent']:.2f}%, "
                    f"validation loss {run['final_validation_loss']:.4f}."
                )
                sources.add(run["source"])

    elif inspections:
        lines.append("Observed run metrics:")
        for run in inspections:
            lines.append(
                f"- {run['run_id']}: final validation accuracy "
                f"{run['final_validation_accuracy_percent']:.2f}%, validation loss "
                f"{run['final_validation_loss']:.4f} at epoch {run['final_epoch']}."
            )
            sources.add(run["source"])
    else:
        lines.append("No experiment evidence was collected.")

    if sources:
        lines.extend(["", "Sources:"])
        lines.extend(f"- [{path}]({path})" for path in sorted(sources))
    return "\n".join(lines)


def answer_question(question: str, *, trace: bool = True) -> str:
    if not question.strip():
        raise ValueError("Question must not be empty")
    saved_ids = {path.stem for path in (PROJECT_DIR / "runs").glob("*.json")}
    mentioned_ids = list(dict.fromkeys(
        token for token in re.findall(r"[A-Za-z0-9_-]+", question) if token in saved_ids
    ))
    id_context = ", ".join(mentioned_ids) if mentioned_ids else "none"
    structured_question = not mentioned_ids and bool(
        re.search(r"\b(learning[- ]rate|train[- ]size|dropout)\b", question.lower())
    )
    if len(mentioned_ids) >= 2:
        first_tools = [tool for tool in TOOLS if tool["function"]["name"] == "compare_experiments"]
    elif len(mentioned_ids) == 1:
        first_tools = [tool for tool in TOOLS if tool["function"]["name"] == "get_experiment"]
    elif structured_question:
        first_tools = [tool for tool in TOOLS if tool["function"]["name"] == "search_runs"]
    else:
        first_tools = [tool for tool in TOOLS if tool["function"]["name"] == "search_notes"]
    messages = [
        {
            "role": "system",
            "content": (
                "You are ML Experiment Detective. Use a tool before answering a question about saved runs. "
                "For a behavior question without a run ID, search_notes first, then inspect one or "
                "more returned run IDs with get_experiment. Do not guess a run ID. "
                "For a question asking which runs match an exact learning rate, train size, or "
                "dropout value, use search_runs with that numeric filter. "
                "For a question about two runs, call compare_experiments first, with the reference "
                "as baseline and the run being explained as target. Example: 'Why was runB worse "
                "than runA?' requires compare_experiments(baseline_run_id='runA', "
                "target_run_id='runB'). Do not replace that call with two get_experiment calls. "
                "Use get_experiment for "
                "questions about one run. Use only measured facts returned by tools. "
                "Never call a changed setting the cause, explanation, primary factor, or reason "
                "for a metric difference. State only that it is the recorded setting that differs; "
                "these runs do not establish a cause. For accuracy differences, say percentage "
                "points (pp), never percent (%). In the final answer, report the final "
                "validation accuracy and loss of both runs, then the measured difference. "
                "Do not add general machine-learning theory. Cite source JSON paths from the tool result. "
                "After enough evidence, answer briefly instead of calling more tools. "
                f"Exact saved run IDs present in this question: {id_context}. "
                "If two are listed, compare them without searching notes; if one is listed, "
                "inspect it directly."
            ),
        },
        {"role": "user", "content": question},
    ]
    tool_count = 0
    tool_results = []
    for _ in range(MAX_TOOL_CALLS + 1):
        searched_notes = any(name == "search_notes" for name, _ in tool_results)
        inspected_run = any(name == "get_experiment" for name, _ in tool_results)
        if searched_notes and not inspected_run:
            available_tools = [tool for tool in TOOLS if tool["function"]["name"] == "get_experiment"]
        else:
            available_tools = first_tools if tool_count == 0 or len(mentioned_ids) >= 2 else TOOLS
        message = ask_ollama(messages, available_tools)
        calls = message.get("tool_calls") or []
        if not calls:
            if searched_notes and not inspected_run and tool_count < MAX_TOOL_CALLS:
                last_search = next(item for name, item in reversed(tool_results) if name == "search_notes")
                if last_search["matches"]:
                    run_id = last_search["matches"][0]["run_id"]
                    result = execute_tool("get_experiment", {"run_id": run_id})
                    if trace:
                        print(f"APP POLICY -> get_experiment({json.dumps({'run_id': run_id})})")
                        print("TOOL RESULT ->", json.dumps(result, sort_keys=True))
                    messages.append({
                        "role": "assistant", "content": "",
                        "tool_calls": [{"function": {
                            "name": "get_experiment", "arguments": {"run_id": run_id}
                        }}],
                    })
                    messages.append({
                        "role": "tool", "tool_name": "get_experiment",
                        "content": json.dumps(result),
                    })
                    tool_results.append(("get_experiment", result))
                    tool_count += 1
                    continue
            if not tool_results:
                raise RuntimeError("The model stopped without collecting experiment evidence")
            if trace:
                print(f"AGENT -> final answer after {tool_count} tool call(s)")
            return render_answer(tool_results)
        if tool_count + len(calls) > MAX_TOOL_CALLS:
            raise RuntimeError("Agent reached its tool-call limit")
        messages.append(message)  # Preserve the assistant's request for the next model turn.
        for call in calls:
            function = call["function"]
            name, arguments = function["name"], function["arguments"]
            if trace:
                print(f"AGENT -> {name}({json.dumps(arguments, sort_keys=True)})")
            if name == "search_runs" and structured_question:
                stated_filters = explicit_run_filters(question)
                if arguments != stated_filters:
                    arguments = stated_filters
                    if trace:
                        print("APP FILTER ->", json.dumps(arguments, sort_keys=True))
            try:
                result = execute_tool(name, arguments)
            except (ValueError, KeyError, TypeError) as exc:
                result = {"error": str(exc)}
            if trace:
                print("TOOL RESULT ->", json.dumps(result, sort_keys=True))
            if "error" not in result:
                tool_results.append((name, result))
            messages.append({
                "role": "tool", "tool_name": name,
                "content": json.dumps(result),
            })
            tool_count += 1
    raise RuntimeError("Agent did not produce a final answer within the step limit")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ask a local tool-using experiment agent")
    parser.add_argument("question", help="question about saved experiment runs")
    args = parser.parse_args()
    print(answer_question(args.question))
