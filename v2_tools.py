"""The one tool registry used by both V2 manual and graph agents."""

import math

from experiment_data import compare_experiments, get_experiment, search_runs
from v2_analysis import (
    compare_run_group, find_overfitting_candidates, plot_run_metrics, summarize_run_curve,
)
from v2_retrieval import hybrid_search_notes, search_ml_knowledge


def _schema(name, description, properties, required=()):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": list(required),
                "additionalProperties": False,
            },
        },
    }


TEXT = {"type": "string"}
NUMBER = {"type": "number"}
INTEGER = {"type": "integer"}
TOOLS = [
    _schema("get_experiment", "Read one saved experiment. Use only for a question about one run; for two run IDs, use compare_experiments instead.",
            {"run_id": {"type": "string", "description": "Exact saved run ID"}}, ("run_id",)),
    _schema("compare_experiments", "Preferred tool whenever a question mentions two run IDs. Compare their recorded settings and final metrics. Use baseline_run_id for the reference and target_run_id for the run being explained; differences are target minus baseline.",
            {"baseline_run_id": {"type": "string", "description": "Reference run ID"},
             "target_run_id": {"type": "string", "description": "Run ID being compared with the reference"}},
            ("baseline_run_id", "target_run_id")),
    _schema("search_runs", "Filter saved JSON by exact learning_rate, train_size or dropout; do not use for behavior wording.",
            {"learning_rate": NUMBER, "train_size": INTEGER, "dropout": NUMBER}),
    _schema("search_notes", "Hybrid keyword and MiniLM search over experiment notes. Returns run IDs and visible ranking stages; inspect a returned run for exact metrics.",
            {"query": TEXT, "top_k": INTEGER, "rerank": {"type": "boolean"}}, ("query",)),
    _schema("summarize_run_curve", "Compute best validation accuracy, minimum loss, largest rise and recoveries for one run.",
            {"run_id": TEXT}, ("run_id",)),
    _schema("find_overfitting_candidates", "Flag saved intervals where post-epoch training loss fell while validation loss rose. This is only a candidate rule.", {}),
    _schema("compare_run_group", "Describe counts and accuracy statistics for two exact learning-rate groups; no causal claim.",
            {"learning_rate_a": NUMBER, "learning_rate_b": NUMBER}, ("learning_rate_a", "learning_rate_b")),
    _schema("plot_run_metrics", "Return epoch, post-epoch train loss, validation loss and validation accuracy for a chart.",
            {"run_id": TEXT}, ("run_id",)),
    _schema("search_ml_knowledge", "Search the separate offline corpus of general ML documentation. It cannot prove a specific run's cause.",
            {"query": TEXT, "top_k": INTEGER}, ("query",)),
]

HANDLERS = {
    "get_experiment": get_experiment,
    "compare_experiments": compare_experiments,
    "search_runs": search_runs,
    "search_notes": hybrid_search_notes,
    "summarize_run_curve": summarize_run_curve,
    "find_overfitting_candidates": find_overfitting_candidates,
    "compare_run_group": compare_run_group,
    "plot_run_metrics": plot_run_metrics,
    "search_ml_knowledge": search_ml_knowledge,
}
PARAMETERS = {x["function"]["name"]: x["function"]["parameters"] for x in TOOLS}


def execute_tool(name: str, arguments: dict) -> dict:
    if name not in HANDLERS:
        raise ValueError(f"Tool is not allowed: {name}")
    schema = PARAMETERS[name]
    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be an object")
    allowed, required = set(schema["properties"]), set(schema["required"])
    if not required <= set(arguments) or set(arguments) - allowed:
        raise ValueError(f"{name} requires {sorted(required)} and allows only {sorted(allowed)}")
    for key, value in arguments.items():
        kind = schema["properties"][key]["type"]
        if kind == "string" and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"{key} must be nonempty text")
        if kind == "integer" and (not isinstance(value, int) or isinstance(value, bool) or value < 1):
            raise ValueError(f"{key} must be a positive integer")
        if kind == "number" and (not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value)):
            raise ValueError(f"{key} must be a finite number")
        if kind == "boolean" and not isinstance(value, bool):
            raise ValueError(f"{key} must be true or false")
    return HANDLERS[name](**arguments)


def tool_menu(names: list[str]) -> list[dict]:
    return [schema for schema in TOOLS if schema["function"]["name"] in names]
