"""Bounded model choices plus explicit Python requirements and fallbacks."""

import json
import re
from urllib.request import Request, urlopen

from experiment_data import RUNS_DIR
from v2_agent import ask_ollama
from v2_state import mentioned_run_ids
from v3.investigation_state import event

UNSUPPORTED = "This assistant specializes in saved ML experiments and their analysis. I don't have an appropriate tool or source for that question."


def ask_decision(messages, schema):
    """Planning uses Ollama JSON-schema output; hypothesis selection uses native tool calls."""
    if schema["function"]["name"] != "create_investigation_plan":
        return ask_ollama(messages, [schema])
    body = {"model": "qwen3:1.7b", "stream": False, "think": False,
            "messages": messages, "format": schema["function"]["parameters"],
            "options": {"temperature": 0, "num_ctx": 4096, "num_predict": 400}}
    request = Request("http://127.0.0.1:11434/api/chat", data=json.dumps(body).encode(),
                      headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=180) as response:
        result = json.load(response)
    if not result.get("done") or result.get("done_reason") != "stop":
        raise RuntimeError("Planner did not complete its structured response")
    return {"structured_decision": json.loads(result["message"]["content"]), "format": "Ollama JSON schema"}


def classify(question):
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question must not be empty")
    q = question.lower()
    # Saved IDs and domain terms are the local scope. No retrieval for unrelated topics.
    domain = bool(mentioned_run_ids(question)) or bool(re.search(
        r"\b(experiment|experiments|validation|training|learning|dropout|overfitting|optimizer|sgd|ml|model|models|neural|gradient|transformer|transformers|accuracy|loss|run|runs|seed|seeds|reproducibility|generalization)\b|test next", q))
    if not domain:
        return "unsupported"
    if re.search(r"investigat|hypothes|follow.up|research|underperform|consistent evidence|test next|controlled experiment|design.*experiment|fresh.*seeds|why.*worse|why.*learning.rate.*saved.experiments", q):
        return "investigation"
    return "simple"


def unknown_run_ids(question):
    return [x for x in re.findall(r"\b(?:lr_|baseline_|small_)[a-zA-Z0-9_-]+", question)
            if not (RUNS_DIR / f"{x}.json").is_file()]


def select(state, name, description, properties, fallback, validator):
    schema = {"type": "function", "function": {"name": name, "description": description,
              "parameters": {"type": "object", "properties": properties,
                             "required": list(properties), "additionalProperties": False}}}
    event(state, "TOOL MENU", schema)
    if state["model_enabled"]:
        for attempt in range(2):
            try:
                message = ask_decision([
                    {"role": "system", "content": "Call the offered function once. Choose only from its enumerated values. Do not invent measurements or launch training."},
                    {"role": "user", "content": description}], schema)
                event(state, "AGENT REQUEST", {"attempt": attempt + 1, "response": message}, "LLM")
                function = (message.get("tool_calls") or [{"function": {"name": name, "arguments": message.get("structured_decision")}}])[0]["function"]
                args = function["arguments"]
                if isinstance(args, str):
                    args = json.loads(args)
                if function["name"] != name or not isinstance(args, dict) or set(args) != set(properties):
                    raise ValueError("Wrong tool, absent call, or invalid fields")
                validator(args)
                return args, "LLM"
            except (OSError, RuntimeError, ValueError, TypeError, KeyError, IndexError) as exc:
                event(state, "APP POLICY", {"model_failure": str(exc), "attempt": attempt + 1,
                                            "maximum_attempts": 2})
    event(state, "APP POLICY", {"fallback": fallback, "reason": "model disabled or exhausted bounded attempts"})
    return fallback, "APP POLICY"


def make_plan(state):
    ids = mentioned_run_ids(state["objective"])
    unknown = unknown_run_ids(state["objective"])
    if unknown:
        raise ValueError(f"Unknown run IDs: {unknown}")
    optional = ["search_notes", "compare_seed_pairs", "retrieve_knowledge"]
    fallback = {"steps": optional, "knowledge_topic": "high learning rate optimization instability"}
    topics = ["high learning rate optimization instability", "dropout overfitting validation loss", "training validation loss curves"]
    def validate(args):
        if not isinstance(args["steps"], list) or len(args["steps"]) != len(set(args["steps"])) or set(args["steps"]) - set(optional):
            raise ValueError("Invalid or repeated plan steps")
        if args["knowledge_topic"] not in topics:
            raise ValueError("Unknown knowledge topic")
    choice, origin = select(state, "create_investigation_plan",
        f"Objective: {state['objective']}. Known mentioned runs: {ids}. Choose useful optional research tools. "
        "Choose compare_seed_pairs to check replication/counterevidence; search_notes to find previous observations; "
        "retrieve_knowledge for mechanisms. Return a topic from the menu.",
        {"steps": {"type": "array", "items": {"type": "string", "enum": optional}, "maxItems": 3},
         "knowledge_topic": {"type": "string", "enum": topics}}, fallback, validate)
    prescribed_steps = []
    if not ids and "search_notes" not in choice["steps"]:
        choice["steps"].insert(0, "search_notes")
        prescribed_steps.append("search_notes")
        event(state, "APP POLICY", "Search is required to discover run IDs absent from the question")
    for phrase, required in ((r"retrieve.*knowledge|ml knowledge", "retrieve_knowledge"),
                             (r"previous experiments|across seeds|seed blocks", "compare_seed_pairs"),
                             (r"search.*notes|retrieve.*notes", "search_notes")):
        if re.search(phrase, state["objective"], re.I) and required not in choice["steps"]:
            choice["steps"].append(required)
            prescribed_steps.append(required)
            event(state, "APP POLICY", {"required_by_objective": required})
    state["selected_steps"] = choice["steps"]
    state["knowledge_topic"] = choice["knowledge_topic"]
    state["optional_step_origins"] = {name: "APP POLICY" if name in prescribed_steps else origin for name in choice["steps"]}
    state["run_ids"] = ids[:4]
    # 'A worse than B' and 'A worse ... than B' orient differences as A minus B.
    if len(ids) >= 2 and re.search(r"worse|underperform", state["objective"], re.I):
        state["run_ids"] = [ids[1], ids[0], *ids[2:4]]
    definitions = [
        ("collect", "Read exact experiment evidence", "get_experiment", [], "PYTHON"),
        ("notes", "Find earlier experiment observations", "search_notes", [], state["optional_step_origins"].get("search_notes", origin)),
        ("analyze", "Compute curves, controls and seed comparisons", "analyze_experiments", ["collect"], "PYTHON"),
        ("knowledge", "Retrieve possible general mechanisms", "search_ml_knowledge", ["analyze"], state["optional_step_origins"].get("retrieve_knowledge", origin)),
        ("hypotheses", "Select competing evidence-backed hypotheses", "select_hypotheses", ["analyze"], "PYTHON"),
        ("validate", "Validate citations and hypothesis evidence", "validate_evidence", ["hypotheses"], "PYTHON"),
        ("design", "Design a new controlled experiment", "design_followup", ["validate"], "PYTHON"),
        ("approval", "Wait for an exact human decision", "human_approval", ["design"], "APP POLICY"),
        ("execute", "Execute only an approved configuration", "restricted_executor", ["approval"], "APP POLICY"),
        ("outcome", "Analyze new measured outcomes", "analyze_outcome", ["execute"], "PYTHON"),
        ("report", "Save sourced investigation report", "render_report", ["validate"], "PYTHON")]
    state["plan"] = [{"id": key, "description": desc, "tool": tool, "depends_on": deps,
                       "status": "pending", "proposed_by": proposed} for key, desc, tool, deps, proposed in definitions]
    for step in state["plan"]:
        if (step["id"] == "notes" and "search_notes" not in choice["steps"]) or (step["id"] == "knowledge" and "retrieve_knowledge" not in choice["steps"]):
            step["status"] = "skipped"
    event(state, "PLANNER DECISION", {"choice": choice, "plan": state["plan"],
          "distinction": "Model selects optional tools; Python prescribes scientific checks and the approval boundary."}, origin)


def mark(state, step_id, status="completed", detail=None):
    for step in state.get("plan", []):
        if step["id"] == step_id:
            step["status"] = status
            if detail:
                step["detail"] = detail
