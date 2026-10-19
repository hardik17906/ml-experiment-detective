# V2 architecture

## From V1 to V2

V1 remains in `simple_agent.py`: a visible Ollama tool loop can inspect saved JSON, search notes, and render a checked answer. V2 adds session context, additional tools, two retrieval collections, an optional second ranking stage, a local UI, and a LangGraph orchestration option. `app.py --agent simple` still runs V1.

```text
question
   -> SessionState.resolve (bounded recent turns; focused run ID)
   -> manual for-loop OR LangGraph agent node
   -> Ollama sees a small tool menu
   -> Python validates and executes one tool
       |-> runs/*.json: exact measurements / analysis
       |-> notes/*.md: keyword + MiniLM -> RRF -> optional CrossEncoder
       |-> knowledge/*.md: offline general ML references
   -> tool result appended to model messages; loop revisits decision
   -> Python renders separate facts, ML knowledge, interpretation, sources
   -> session remembers this turn
```

`runs/*.json` is the source of measurements. Notes help find run IDs. Knowledge files contain general ideas from linked official material. Neither notes nor retrieved documents override JSON. Python computes metrics and checks tool arguments; the LLM selects from offered tools. The app's visible `APP POLICY` fallback collects required evidence when the small model stops early. Trace labels `AGENT` and `APP POLICY` separately.

## Components

| File | Responsibility |
| --- | --- |
| `v2_state.py` | Four-turn session memory and reference resolution. |
| `v2_agent.py` | Explicit decide, execute, observe loop and Ollama request. |
| `v2_tools.py` | Shared nine-tool schema, validation, and dispatch. |
| `v2_retrieval.py` | Hybrid note search, optional local reranker, separate knowledge search. |
| `v2_analysis.py` | Deterministic curve, candidate, group, and plot data calculations. |
| `v2_answers.py` | Source-aware response assembled from successful tool results. |
| `graph_agent.py` | Same behavior expressed with graph nodes and edges. |
| `app.py`, `ui.py` | Interactive CLI and local Streamlit interface. |

## Nine tools

The four V1 capabilities are `get_experiment`, `compare_experiments`, `search_runs`, and `search_notes` (now hybrid in V2). V2 adds `summarize_run_curve`, `find_overfitting_candidates`, `compare_run_group`, `plot_run_metrics`, and `search_ml_knowledge`. Both agents call the same functions from `v2_tools.py`.

The overfitting rule flags an interval only when saved post-epoch training loss falls while validation loss rises. It is a descriptive candidate flag. Group statistics describe the saved records, which can repeat configurations or differ in other settings. The chart tool returns epoch data; Streamlit plots it.

## Run and inspect

From the project directory:

```powershell
.\.venv\Scripts\python.exe app.py --agent manual
.\.venv\Scripts\python.exe app.py --agent graph
.\.venv\Scripts\python.exe app.py --agent simple
.\.venv\Scripts\streamlit.exe run ui.py
.\.venv\Scripts\python.exe validate_v2.py
.\.venv\Scripts\python.exe evaluate_retrieval.py
```

The local Ollama service and `qwen3:1.7b` must be available. MiniLM and the optional reranker load from the D: project cache. General ML references are local files, so a user question does not require web access. `--rerank` opts into the extra model in the CLI; the UI has the same switch.

See [memory](MEMORY.md), [hybrid search](HYBRID_RAG.md), [external knowledge](EXTERNAL_KNOWLEDGE_RAG.md), [real trace](V2_COMPLETE_TRACE.md), and [manual versus graph](MANUAL_VS_LANGGRAPH.md).
