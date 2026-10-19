"""Run a compact, repeatable V2 smoke check and save the real agent traces."""

import json
from pathlib import Path

from experiment_data import get_experiment, load_run
from graph_agent import run_graph
from v2_agent import run_manual
from v2_analysis import plot_run_metrics
from v2_state import SessionState


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "reports" / "v2_validation_traces.json"
CASES = []


def check(label, question, expected, *, mode="manual", session=None, rerank=False):
    runner = run_manual if mode == "manual" else run_graph
    result = runner(question, session, rerank=rerank)
    sequence = [event["data"]["tool"] for event in result["trace"]
                if event["kind"] in ("AGENT", "APP POLICY")]
    assert all(tool in sequence for tool in expected), (label, sequence)
    assert result["answer"] and "### Sources" in result["answer"], label
    record = {"label": label, "mode": mode, "question": question,
              "tool_sequence": sequence, "answer": result["answer"],
              "trace": result["trace"]}
    CASES.append(record)
    print(f"{label}: {mode} | {' -> '.join(sequence)} | PASS", flush=True)
    return result


def main():
    manual = SessionState()
    check("A_single_run", "What is the final validation accuracy of lr_01_seed3?",
          ["get_experiment"], session=manual)
    check("B_two_runs", "Compare lr_01_seed3 with lr_005_seed3.",
          ["compare_experiments"], session=manual)
    check("C_note_RAG", "Have we seen unstable validation behavior before?",
          ["search_notes", "get_experiment"], session=manual)
    check("D_structured_search", "Which experiments used learning rate 0.1?",
          ["search_runs"], session=manual)

    memory = SessionState()
    check("E_memory_first", "Tell me about lr_01_seed3.", ["get_experiment"], session=memory)
    second = check("E_memory_reference", "Compare that run with lr_005_seed3.",
                   ["compare_experiments"], session=memory)
    assert second["trace"][1]["data"]["resolved_reference"] == "lr_01_seed3"
    check("F_overfitting_rule", "Which saved runs look like possible overfitting candidates?",
          ["find_overfitting_candidates"], session=manual)
    check("G_ML_knowledge", "Why might a high learning rate create unstable training?",
          ["search_ml_knowledge"], session=manual)
    combined = check("H_combined", "Why might lr_01_seed3 have behaved worse than lr_005_seed3?",
                     ["compare_experiments", "search_ml_knowledge"], session=manual)
    assert "75.90%" in combined["answer"] and "71.45%" in combined["answer"]
    check("I_visual_tool", "Show the training curve for lr_01_seed3.",
          ["plot_run_metrics"], session=manual)
    check("J_group", "Compare learning-rate-0.1 runs with learning-rate-0.05 runs.",
          ["compare_run_group"], session=manual)
    check("K_curve_summary", "What was the best validation accuracy of lr_01_seed3?",
          ["summarize_run_curve"], session=manual)

    full_session = SessionState()
    check("L_full_trace_memory_seed", "Tell me about lr_01_seed3.",
          ["get_experiment"], session=full_session)
    full = check("L_full_trace", "Have we seen unstable validation behavior like that run, and why might it happen?",
                 ["search_notes", "get_experiment", "search_ml_knowledge"], session=full_session)
    assert full["trace"][1]["data"]["resolved_reference"] == "lr_01_seed3"
    assert "### Observed experiment facts" in full["answer"]
    assert "### Relevant ML knowledge" in full["answer"]

    graph = SessionState()
    check("M_graph_single", "What is the final validation accuracy of lr_01_seed3?",
          ["get_experiment"], mode="graph", session=graph)
    check("M_graph_combined", "Why might lr_01_seed3 have behaved worse than lr_005_seed3?",
          ["compare_experiments", "search_ml_knowledge"], mode="graph", session=graph)
    check("M_graph_note_RAG", "Have we seen unstable validation behavior before?",
          ["search_notes", "get_experiment"], mode="graph", session=graph)

    expected = get_experiment("lr_01_seed3")
    raw = load_run("lr_01_seed3")["metrics"][-1]
    assert expected["final_validation_accuracy_percent"] == round(100 * raw["val_accuracy"], 2)
    assert expected["final_validation_loss"] == round(raw["val_loss"], 4)
    assert len(plot_run_metrics("lr_01_seed3")["points"]) == len(load_run("lr_01_seed3")["metrics"])
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"cases": CASES, "checked_json_run": "lr_01_seed3"}, indent=2), encoding="utf-8")
    print(f"Saved {len(CASES)} complete traces: {OUT}", flush=True)


if __name__ == "__main__":
    main()
