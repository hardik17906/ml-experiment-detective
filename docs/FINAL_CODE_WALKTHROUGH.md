# Final Code Walkthrough

Open a source file beside this reference. Line numbers and excerpts are generated from the actual final files; they are not invented examples. The learning guide explains the concepts; this document explains responsibilities and control flow. Static call names below are syntactic references, not proof that every branch ran in the real trace.

## simple_agent.py

**Absolute path:** `D:\Agentic_ai_rag projects\simple_agent.py`

**Purpose:** Original native tool-using educational reference.

Shows the original bounded native-tool loop and its smaller allowed menu. Its semantic search reuses the shared encoder and its exact reads use experiment_data. It remains a reference CLI mode; the final primary application adds stronger scope, memory, graph/persistence and model-failure handling.

**Dependencies:** `import argparse`; `import json`; `import math`; `import re`; `from urllib.request import Request, urlopen`; `from experiment_data import PROJECT_DIR, compare_experiments, get_experiment, search_runs`; `from note_retrieval import MODEL_ID, encode_queries_and_notes, load_notes, semantic_rank`.

**Main symbols and input contracts:**

- `search_notes(query: str, top_k: int=2)` — source line 80.
- `execute_tool(name: str, arguments: dict)` — source line 114.
- `explicit_run_filters(question: str)` — source line 144.
- `ask_ollama(messages: list[dict], available_tools: list[dict])` — source line 159.
- `render_answer(tool_results: list[tuple[str, dict]])` — source line 181.
- `answer_question(question: str, *, trace: bool=True)` — source line 300.

**Who references this selected routine:** legacy_ui.py.

**What the selected routine calls:** `', '.join`, `(PROJECT_DIR / 'runs').glob`, `RuntimeError`, `ValueError`, `any`, `ask_ollama`, `bool`, `dict.fromkeys`, `execute_tool`, `explicit_run_filters`, `json.dumps`, `len`, `list`, `message.get`, `messages.append`, `next`, `print`, `question.lower`, `question.strip`, `range`, `re.findall`, `re.search`, `render_answer`, `reversed`, `str`, `tool_results.append`.

**Error/control boundaries:** `RuntimeError('Agent did not produce a final answer within the step limit')`; `RuntimeError('Agent reached its tool-call limit')`; `RuntimeError('Ollama did not complete its response')`; `RuntimeError('The model stopped without collecting experiment evidence')`; `ValueError('Question must not be empty')`; `ValueError('Run IDs must be strings')`; `ValueError('Search query must be nonempty text')`; `ValueError('Search query must not be empty')`; `ValueError('top_k must be an integer from 1 to 5')`; `ValueError('train_size must be a positive integer')`; `ValueError(f'Tool is not allowed: {name}')`; `ValueError(f'{key} must be a finite number')`; `ValueError(f'{name} requires {sorted(required)}; optional: {sorted(optional)}')`.

Actual source: `simple_agent.py:300`–`339`; excerpt of `answer_question` (remaining lines, if any, are not reproduced here).

```python
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
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## legacy_ui.py

**Absolute path:** `D:\Agentic_ai_rag projects\legacy_ui.py`

**Purpose:** Earlier educational UI and compatibility checks.

Keeps the older chat/run view and manual/graph/simple selection used by historical UI checks. It is not the recommended entry point. The current ui.py replaces its navigation with one coherent application while reusing the actual tools and investigation workspace.

**Dependencies:** `import re`; `import pandas as pd`; `import streamlit as st`; `from experiment_data import RUNS_DIR, get_experiment`; `from v2_agent import run_manual`; `from v2_analysis import plot_run_metrics`; `from v2_state import SessionState`.

**Main symbols and input contracts:**

- `display_answer(text: str)` — source line 17.
- `render_v2()` — source line 22.

**Who references this selected routine:** Entry-point/framework callbacks or method dispatch; inspect the runtime trace for the actual caller.

**What the selected routine calls:** `RUNS_DIR.glob`, `SessionState`, `answer_question`, `chosen['config'].get`, `display_answer`, `get_experiment`, `len`, `pd.DataFrame`, `plot_run_metrics`, `run_graph`, `run_ids.index`, `run_manual`, `sorted`, `st.button`, `st.caption`, `st.chat_input`, `st.chat_message`, `st.checkbox`, `st.columns`, `st.dataframe`, `st.divider`, `st.error`, `st.expander`, `st.json`, `st.line_chart`, `st.markdown`, `st.metric`, `st.radio`, `st.rerun`, `st.selectbox`, `st.session_state.chat_entries.append`, `st.session_state.detective_session.clear`, `st.session_state.detective_session.snapshot`, `st.spinner`, `st.subheader`, `st.tabs`, `st.title`, `st.write`.

**Error/control boundaries:** Delegated exceptions propagate to the service/UI/CLI boundaries described above; absence of an explicit raise is not absence of failure.

Actual source: `legacy_ui.py:22`–`61`; excerpt of `render_v2` (remaining lines, if any, are not reproduced here).

```python
def render_v2():
    if "detective_session" not in st.session_state:
        st.session_state.detective_session = SessionState()
    if "chat_entries" not in st.session_state:
        st.session_state.chat_entries = []

    run_ids = sorted(path.stem for path in RUNS_DIR.glob("*.json"))
    with st.sidebar:
        st.title("Experiment Detective")
        st.caption("Local learning interface")
        st.metric("Saved run records", len(run_ids))
        mode = st.radio("Agent", ("manual", "graph", "simple"), help="Both modes use the same Python tools.")
        rerank = st.checkbox("Optional cross-encoder reranking", value=False,
                            help="Hybrid order is the default. The reranker can make some searches worse.")
        selected = st.selectbox("Inspect a saved run", run_ids, index=run_ids.index("lr_01_seed3") if "lr_01_seed3" in run_ids else 0)
        chosen = get_experiment(selected)
        st.caption("Selected run settings")
        st.json({key: chosen["config"].get(key) for key in
                 ("learning_rate", "train_size", "epochs", "batch_size", "dropout", "split_seed", "shuffle_seed", "model_seed")})
        st.markdown("**Try asking**")
        st.caption("Have we seen unstable validation behavior before?\n\nCompare that run with lr_005_seed3.\n\nWhy might a high learning rate create unstable training?")
        if st.button("Clear conversation", width="stretch"):
            st.session_state.detective_session.clear()
            st.session_state.chat_entries = []
            st.rerun()

    st.title("ML Experiment Detective")
    st.caption("Ask about saved runs and general ML ideas. Expand a response to see memory, tool calls, retrieval stages, and sources.")

    for entry in st.session_state.chat_entries:
        with st.chat_message("user"):
            st.write(entry["question"])
        with st.chat_message("assistant"):
            st.markdown(display_answer(entry["answer"]))
            with st.expander("How did the agent answer this?"):
                for event in entry["trace"]:
                    if event["kind"] == "FINAL":
                        continue
                    st.markdown(f"**{event['kind']}**")
                    st.json(event["data"])
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## assistant.py

**Absolute path:** `D:\Agentic_ai_rag projects\assistant.py`

**Purpose:** Primary facade and shared conversation entry.

Captures the original/resolved question, checks ambiguous/unknown IDs, calls the durable investigator, records actual results in bounded conversation memory, and returns answer/trace/status. Inputs are text and SessionState; outputs are a result dictionary. Invalid references return helpful clarification/alternatives before evidence calls.

**Dependencies:** `from difflib import get_close_matches`; `from experiment_data import RUNS_DIR`; `from v2_state import SessionState, mentioned_run_ids`; `from v3.planner import unknown_run_ids`; `from v3.service import Investigator`.

**Main symbols and input contracts:**

- `ResearchAssistant` — source line 11.

**Who references this selected routine:** app.py, demonstrate_final.py, tests/test_final.py, ui.py.

**What the selected routine calls:** `', '.join`, `RUNS_DIR.glob`, `SessionState`, `e['data'].get`, `get_close_matches`, `isinstance`, `mentioned_run_ids`, `self.investigator.start`, `self.investigator.store.save`, `session.remember`, `session.resolve`, `session.snapshot`, `sorted`, `state.get`, `state.get('analysis', {}).get`, `state['trace'].append`, `str`, `unknown_run_ids`.

**Error/control boundaries:** Delegated exceptions propagate to the service/UI/CLI boundaries described above; absence of an explicit raise is not absence of failure.

Actual source: `assistant.py:15`–`48`; excerpt of `ask` (remaining lines, if any, are not reproduced here).

```python
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
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## ui.py

**Absolute path:** `D:\Agentic_ai_rag projects\ui.py`

**Purpose:** Recommended four-area Streamlit interface.

Reads exact run data into tables/charts, displays local status and examples, retains chat state, and delegates research controls to v3.ui. Streamlit reruns the script on interaction; session state persists objects. UI errors become readable messages; API results remain inspectable in expanders.

**Dependencies:** `import re`; `from urllib.request import urlopen`; `import json`; `import pandas as pd`; `import streamlit as st`; `from assistant import ResearchAssistant`; `from experiment_data import RUNS_DIR, PROJECT_DIR, load_run`; `from v2_analysis import rank_experiments, plot_run_metrics`; `from v2_state import SessionState`; `from v3.analysis import compare_records`.

**Main symbols and input contracts:**

- `display_answer(text)` — source line 18.
- `model_status()` — source line 23.
- `draw_run(run_id)` — source line 53.

**Who references this selected routine:** Entry-point/framework callbacks or method dispatch; inspect the runtime trace for the actual caller.

**What the selected routine calls:** `left.metric`, `load_run`, `pd.DataFrame`, `plot_run_metrics`, `right.metric`, `st.caption`, `st.columns`, `st.dataframe`, `st.expander`, `st.json`, `st.line_chart`.

**Error/control boundaries:** Delegated exceptions propagate to the service/UI/CLI boundaries described above; absence of an explicit raise is not absence of failure.

Actual source: `ui.py:53`–`66`; excerpt of `draw_run` (remaining lines, if any, are not reproduced here).

```python
def draw_run(run_id):
    record = load_run(run_id)
    st.caption(f"Exact source: runs/{run_id}.json")
    last = record["metrics"][-1]
    left, right = st.columns(2)
    left.metric("Final validation accuracy", f"{100*last['val_accuracy']:.2f}%")
    right.metric("Final validation loss", f"{last['val_loss']:.4f}")
    points = pd.DataFrame(plot_run_metrics(run_id)["points"])
    st.line_chart(points, x="epoch", y=["train_loss", "validation_loss"])
    st.line_chart(points, x="epoch", y="validation_accuracy_percent")
    with st.expander("Configuration and epoch measurements"):
        st.json(record["config"])
        st.dataframe(pd.DataFrame(record["metrics"]), hide_index=True, width="stretch")
    st.caption("Training loss is measured after each epoch when available; missing historical metrics remain blank.")
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## investigate.py

**Absolute path:** `D:\Agentic_ai_rag projects\investigate.py`

**Purpose:** Persistent investigation CLI entry point.

Delegates start/list/show/resume/decide/modify/export/cancel to the tested research CLI. It preserves exact proposal hash/mode checks and existing stored investigations.

**Dependencies:** `from v3.cli import main as research_cli`.

**Main symbols and input contracts:**

- `main(argv=None)` — source line 4.

**Who references this selected routine:** app.py, demonstrate_final.py, evaluate_final.py, evaluate_final_retrieval.py, phase0.py, tests/test_final.py, tests/test_v3.py, v3/cli.py, v3/training_worker.py, validate_final_ui.py, verify_final.py.

**What the selected routine calls:** `research_cli`.

**Error/control boundaries:** Delegated exceptions propagate to the service/UI/CLI boundaries described above; absence of an explicit raise is not absence of failure.

Actual source: `investigate.py:4`–`5`; excerpt of `main` (remaining lines, if any, are not reproduced here).

```python
def main(argv=None):
    return research_cli(argv)
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## app.py

**Absolute path:** `D:\Agentic_ai_rag projects\app.py`

**Purpose:** Primary interactive/single-question CLI and educational mode switches.

Argparse selects the integrated assistant by default; manual/graph/simple/research aliases remain. Interactive clear resets only conversation memory. --offline and --lexical bound dependencies for the primary assistant. Errors print an evidence/application limitation.

**Dependencies:** `import argparse`; `from simple_agent import answer_question as answer_simple`; `from v2_agent import print_trace, run_manual`; `from v2_state import SessionState`.

**Main symbols and input contracts:**

- `main()` — source line 10.

**Who references this selected routine:** demonstrate_final.py, evaluate_final.py, evaluate_final_retrieval.py, investigate.py, phase0.py, tests/test_final.py, tests/test_v3.py, v3/cli.py, v3/training_worker.py, validate_final_ui.py, verify_final.py.

**What the selected routine calls:** `ResearchAssistant`, `ResearchAssistant().ask`, `SessionState`, `answer_simple`, `argparse.ArgumentParser`, `input`, `input('\n> ').strip`, `parser.add_argument`, `parser.parse_args`, `print`, `print_trace`, `question.lower`, `research_cli`, `run_graph`, `run_manual`, `session.clear`.

**Error/control boundaries:** Delegated exceptions propagate to the service/UI/CLI boundaries described above; absence of an explicit raise is not absence of failure.

Actual source: `app.py:10`–`49`; excerpt of `main` (remaining lines, if any, are not reproduced here).

```python
def main() -> None:
    parser = argparse.ArgumentParser(description="Ask questions about saved ML experiments")
    parser.add_argument("--question", help="ask one question and exit")
    parser.add_argument("--no-trace", action="store_true", help="hide tool requests and results")
    parser.add_argument("--agent", choices=("assistant", "manual", "graph", "simple", "research"), default="assistant")
    parser.add_argument("--offline", action="store_true", help="primary assistant uses visible Python fallbacks without Ollama")
    parser.add_argument("--lexical", action="store_true", help="primary assistant searches without embedding imports")
    parser.add_argument("--rerank", action="store_true", help="opt in to the cached cross-encoder reranker")
    args = parser.parse_args()

    if args.agent == "research":
        from v3.cli import main as research_cli
        if args.question:
            research_cli(["start", args.question])
        else:
            print('Use: python investigate.py start "Investigate ..."; list/show/resume/decide/export manage saved work.')
        return

    print(f"ML Experiment Detective ({args.agent} agent, local evidence)")
    if args.question is None:
        print("Ask about runs, observations, or ML knowledge. Type clear to reset memory; exit to quit.")
    session = SessionState()

    while True:
        if args.question is not None:
            question = args.question
        else:
            try:
                question = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye.")
                return
            if question.lower() in {"exit", "quit"}:
                print("Goodbye.")
                return
            if question.lower() == "clear":
                session.clear()
                print("Session memory cleared.")
                continue
            if not question:
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## experiment_data.py

**Absolute path:** `D:\Agentic_ai_rag projects\experiment_data.py`

**Purpose:** Exact JSON read/filter/compare boundary.

Validates IDs and epoch ordering, reads source records, filters explicit settings and computes final deltas. Paths are derived under runs; source IDs and file metadata are never supplied by unvalidated generated prose.

**Dependencies:** `import json`; `import re`; `from pathlib import Path`.

**Main symbols and input contracts:**

- `load_run(run_id: str)` — source line 13.
- `largest_rise(metrics: list[dict])` — source line 28.
- `loss_recoveries(metrics: list[dict])` — source line 37.
- `get_experiment(run_id: str)` — source line 49.
- `compare_experiments(baseline_run_id: str, target_run_id: str)` — source line 71.
- `search_runs(learning_rate=None, train_size=None, dropout=None)` — source line 104.

**Who references this selected routine:** tests/test_final.py, tests/test_v3.py, ui.py, v2_analysis.py, v3/analysis.py, v3/experiment_designer.py, v3/investigation_graph.py, v3/retrieval.py.

**What the selected routine calls:** `RUN_ID.fullmatch`, `ValueError`, `isinstance`, `json.loads`, `len`, `list`, `path.is_file`, `path.read_text`, `range`, `record['config'].get`.

**Error/control boundaries:** `ValueError('Cannot compare final metrics from different epochs')`; `ValueError(f'Epochs are missing or not consecutive in {run_id}')`; `ValueError(f'Invalid run ID: {run_id!r}')`; `ValueError(f'Run ID does not match JSON record: {run_id}')`; `ValueError(f'Unknown run ID: {run_id}')`.

Actual source: `experiment_data.py:13`–`25`; excerpt of `load_run` (remaining lines, if any, are not reproduced here).

```python
def load_run(run_id: str) -> dict:
    if not isinstance(run_id, str) or not RUN_ID.fullmatch(run_id):
        raise ValueError(f"Invalid run ID: {run_id!r}")
    path = RUNS_DIR / f"{run_id}.json"
    if not path.is_file():
        raise ValueError(f"Unknown run ID: {run_id}")
    record = json.loads(path.read_text(encoding="utf-8"))
    if record["config"].get("run_id") != run_id:
        raise ValueError(f"Run ID does not match JSON record: {run_id}")
    epochs = [row["epoch"] for row in record["metrics"]]
    if not epochs or epochs != list(range(1, len(epochs) + 1)):
        raise ValueError(f"Epochs are missing or not consecutive in {run_id}")
    return record
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## note_retrieval.py

**Absolute path:** `D:\Agentic_ai_rag projects\note_retrieval.py`

**Purpose:** Shared MiniLM encoding and baseline text/vector operations.

Loads original observations, tokenizes baseline words, caches the installed encoder object and computes cosine ranking. Encoder arrays stay associated with document paths during sorting. Model revision/cache location are explicit; current queries use local-only weights.

**Dependencies:** `import json`; `import re`; `from functools import lru_cache`; `from pathlib import Path`.

**Main symbols and input contracts:**

- `words(text)` — source line 12.
- `load_notes()` — source line 16.
- `filter_notes(notes, *, dropout=None, train_size=None, run_id=None)` — source line 25.
- `keyword_rank(query, notes)` — source line 43.
- `_embedding_model(local_only)` — source line 54.
- `encode_queries_and_notes(queries, notes, *, local_only=False)` — source line 65.
- `cosine_similarity(first, second)` — source line 71.
- `semantic_rank(query_embedding, note_embeddings, notes)` — source line 77.

**Who references this selected routine:** Entry-point/framework callbacks or method dispatch; inspect the runtime trace for the actual caller.

**What the selected routine calls:** `float`, `np.dot`, `np.linalg.norm`.

**Error/control boundaries:** Delegated exceptions propagate to the service/UI/CLI boundaries described above; absence of an explicit raise is not absence of failure.

Actual source: `note_retrieval.py:71`–`74`; excerpt of `cosine_similarity` (remaining lines, if any, are not reproduced here).

```python
def cosine_similarity(first, second):
    import numpy as np

    return float(np.dot(first, second) / (np.linalg.norm(first) * np.linalg.norm(second)))
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## v2_retrieval.py

**Absolute path:** `D:\Agentic_ai_rag projects\v2_retrieval.py`

**Purpose:** Preserved baseline hybrid/reranker and local knowledge corpus loader.

Loads note/knowledge metadata, applies historical ranking for baseline comparisons and supplies the cached optional cross-encoder. New primary note policy reuses its encoder/reranker rather than introducing another embedding implementation.

**Dependencies:** `from functools import lru_cache`; `from pathlib import Path`; `from note_retrieval import PROJECT_DIR, MODEL_ID, encode_queries_and_notes, keyword_rank, load_notes, semantic_rank`.

**Main symbols and input contracts:**

- `_reranker()` — source line 18.
- `hybrid_search_notes(query: str, top_k: int=2, rerank: bool=False)` — source line 28.
- `_knowledge_chunks()` — source line 109.
- `search_ml_knowledge(query: str, top_k: int=2)` — source line 126.

**Who references this selected routine:** Entry-point/framework callbacks or method dispatch; inspect the runtime trace for the actual caller.

**What the selected routine calls:** `ValueError`, `_reranker`, `_reranker().predict`, `dict`, `encode_queries_and_notes`, `enumerate`, `float`, `keyword_by_id.get`, `keyword_rank`, `load_notes`, `query.strip`, `round`, `row.get`, `rows.append`, `rows.sort`, `semantic_rank`, `status.startswith`, `zip`.

**Error/control boundaries:** `FileNotFoundError(f'Reranker is not cached at {RERANKER_DIR}')`; `ValueError('Search query must not be empty')`; `ValueError('top_k must be from 1 to 5')`; `ValueError(f'top_k must be from 1 to {len(chunks)}')`.

Actual source: `v2_retrieval.py:28`–`67`; excerpt of `hybrid_search_notes` (remaining lines, if any, are not reproduced here).

```python
def hybrid_search_notes(query: str, top_k: int = 2, rerank: bool = False) -> dict:
    if not query.strip():
        raise ValueError("Search query must not be empty")
    if not 1 <= top_k <= 5:
        raise ValueError("top_k must be from 1 to 5")
    notes = load_notes()
    if not notes:
        return {"query": query, "matches": [], "stages": {}, "rerank_status": "no notes"}

    keyword = keyword_rank(query, notes)
    embeddings = encode_queries_and_notes([query], notes, local_only=True)
    semantic = semantic_rank(embeddings[0], embeddings[1:], notes)
    keyword_by_id = {
        path.stem: {"rank": rank, "score": score, "shared_words": shared}
        for rank, (score, path, shared, _) in enumerate(keyword, 1)
    }
    semantic_by_id = {
        path.stem: {"rank": rank, "cosine": round(score, 4)}
        for rank, (score, path, _) in enumerate(semantic, 1)
    }
    rows = []
    for path, observation in notes:
        kw = keyword_by_id.get(path.stem)
        sem = semantic_by_id[path.stem]
        score = (1 / (RRF_K + kw["rank"]) if kw else 0) + 1 / (RRF_K + sem["rank"])
        rows.append({
            "run_id": path.stem,
            "note_source": f"notes/{path.name}",
            "run_source": f"runs/{path.stem}.json",
            "observation": observation,
            "keyword_rank": kw["rank"] if kw else None,
            "keyword_score": kw["score"] if kw else 0,
            "keyword_shared_words": kw["shared_words"] if kw else [],
            "semantic_rank": sem["rank"],
            "cosine_similarity": sem["cosine"],
            "hybrid_score": round(score, 6),
        })
    rows.sort(key=lambda row: (-row["hybrid_score"], row["run_id"]))
    for rank, row in enumerate(rows, 1):
        row["hybrid_rank"] = rank
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## v2_tools.py

**Absolute path:** `D:\Agentic_ai_rag projects\v2_tools.py`

**Purpose:** Shared allowlisted tool schemas and dispatcher.

Checks names, required/extra fields, types, enum membership, finite numeric values and booleans before calling a handler. The registry includes ranking and existing read/search/analysis tools; it offers no approval or arbitrary execution tool to the model.

**Dependencies:** `import math`; `from experiment_data import compare_experiments, get_experiment, search_runs`; `from v2_analysis import compare_run_group, find_overfitting_candidates, plot_run_metrics, summarize_run_curve, rank_experiments`; `from v2_retrieval import hybrid_search_notes, search_ml_knowledge`.

**Main symbols and input contracts:**

- `_schema(name, description, properties, required=())` — source line 12.
- `execute_tool(name: str, arguments: dict)` — source line 71.
- `tool_menu(names: list[str])` — source line 95.

**Who references this selected routine:** simple_agent.py, tests/test_final.py, tests/test_v3.py, v2_agent.py.

**What the selected routine calls:** `HANDLERS[name]`, `ValueError`, `arguments.items`, `isinstance`, `math.isfinite`, `set`, `sorted`, `value.strip`.

**Error/control boundaries:** `ValueError('Tool arguments must be an object')`; `ValueError(f'Tool is not allowed: {name}')`; `ValueError(f'Unsupported {key}: {value}')`; `ValueError(f'{key} must be a finite number')`; `ValueError(f'{key} must be a positive integer')`; `ValueError(f'{key} must be nonempty text')`; `ValueError(f'{key} must be true or false')`; `ValueError(f'{name} requires {sorted(required)} and allows only {sorted(allowed)}')`.

Actual source: `v2_tools.py:71`–`92`; excerpt of `execute_tool` (remaining lines, if any, are not reproduced here).

```python
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
        if "enum" in schema["properties"][key] and value not in schema["properties"][key]["enum"]:
            raise ValueError(f"Unsupported {key}: {value}")
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
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## v2_agent.py

**Absolute path:** `D:\Agentic_ai_rag projects\v2_agent.py`

**Purpose:** Shared turn preparation, policy, tool observation and manual reference loop.

The primary graph uses choose_next for one bounded model choice and transparent fallback. execute_call applies explicit user constraints, dispatches allowed tools, records full trace and feeds compact tool messages to the next model choice. run_manual retains the educational while-loop implementation.

**Dependencies:** `import json`; `import re`; `from urllib.request import Request, urlopen`; `from simple_agent import explicit_run_filters`; `from v2_answers import render_answer`; `from v2_state import SessionState, mentioned_run_ids`; `from v2_tools import execute_tool, tool_menu`.

**Main symbols and input contracts:**

- `_learning_rates(question: str)` — source line 32.
- `_first_tool_names(question: str)` — source line 38.
- `_fallback_arguments(name: str, state: dict)` — source line 73.
- `prepare_turn(question: str, session: SessionState | None=None, *, rerank: bool=False)` — source line 117.
- `available_tool_names(state: dict)` — source line 147.
- `ask_ollama(messages: list[dict], available_tools: list[dict])` — source line 159.
- `policy_call(state: dict)` — source line 177.
- `execute_call(state: dict, name: str, arguments: dict, *, origin: str)` — source line 191.
- `choose_next(state)` — source line 261.
- `finish_turn(state: dict)` — source line 286.
- `run_manual(question: str, session: SessionState | None=None, *, rerank: bool=False)` — source line 298.
- `print_trace(events: list[dict])` — source line 324.

**Who references this selected routine:** graph_agent.py.

**What the selected routine calls:** `ValueError`, `ask_ollama`, `available_tool_names`, `isinstance`, `json.loads`, `message.get`, `policy_call`, `state.get`, `state['trace'].append`, `str`, `tool_menu`.

**Error/control boundaries:** `RuntimeError('Ollama did not complete its response')`; `RuntimeError('The model stopped before evidence was collected')`; `RuntimeError('Tool agent did not stop within its step limit')`; `RuntimeError('Tool agent reached its tool-call limit')`; `ValueError('A saved run ID is required')`; `ValueError('Question must not be empty')`; `ValueError('Tool not offered or arguments not an object')`; `ValueError('Two learning rates are required')`; `ValueError('Two saved run IDs are required for comparison')`; `ValueError(f'{name} was not in the offered tool menu: {available}')`.

Actual source: `v2_agent.py:261`–`283`; excerpt of `choose_next` (remaining lines, if any, are not reproduced here).

```python
def choose_next(state):
    """One bounded model choice; malformed/offline requests have visible policy recovery."""
    names = available_tool_names(state)
    state["trace"].append({"kind": "TOOL MENU", "data": tool_menu(names)})
    if not names or state["tool_count"] >= MAX_TOOL_CALLS or state.get("last_tool_error"):
        return []
    if state.get("model_enabled", True):
        try:
            message = ask_ollama(state["messages"], tool_menu(names))
            state["trace"].append({"kind": "AGENT CHOICE", "origin": "LLM", "data": message})
            calls = message.get("tool_calls") or []
            if calls:
                function = calls[0]["function"]
                args = function["arguments"]
                if isinstance(args, str):
                    args = json.loads(args)
                if function["name"] not in names or not isinstance(args, dict):
                    raise ValueError("Tool not offered or arguments not an object")
                return [{"name": function["name"], "arguments": args, "origin": "AGENT"}]
        except (OSError, RuntimeError, ValueError, TypeError, KeyError, IndexError) as exc:
            state["trace"].append({"kind": "APP POLICY", "data": {"model_failure": str(exc), "action": "bounded deterministic recovery"}})
    needed = policy_call(state)
    return [{"name": needed[0], "arguments": needed[1], "origin": "APP POLICY"}] if needed else []
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## v2_state.py

**Absolute path:** `D:\Agentic_ai_rag projects\v2_state.py`

**Purpose:** Bounded conversation and reference resolution.

Uses explicit focused IDs and comparison pairs, not embeddings. Resolves corresponding-rate partners using recorded controls, tracks ranking focus, retains four turns and asks for clarification when a singular reference has no unique focus. clear resets every conversation reference.

**Dependencies:** `from dataclasses import dataclass, field`; `import re`; `from experiment_data import RUNS_DIR`.

**Main symbols and input contracts:**

- `mentioned_run_ids(text: str)` — source line 16.
- `SessionState` — source line 22.

**Who references this selected routine:** assistant.py, experiment_data.py, note_retrieval.py, phase0.py, tests/test_v3.py, v2_agent.py, v3/investigation_state.py, v3/training_worker.py, verify_final.py.

**What the selected routine calls:** `ValueError`, `float`, `len`, `list`, `matched_runs`, `mentioned_run_ids`, `re.search`, `re.sub`.

**Error/control boundaries:** `ValueError('Which run do you mean? Select a run or name one; the current conversation has no unambiguous single-run focus.')`; `ValueError(f'The corresponding run is ambiguous or unavailable. Candidates: {matches or 'none'}')`.

Actual source: `v2_state.py:28`–`63`; excerpt of `resolve` (remaining lines, if any, are not reproduced here).

```python
    def resolve(self, question: str) -> tuple[str, dict]:
        """Resolve simple singular references using an explicit, visible focus ID."""
        found = mentioned_run_ids(question)
        resolved = question
        used = None
        if not found and self.comparison_run_ids and re.search(r"\b(difference|comparison|those runs|these runs|explanations|additional evidence|test next|hypothesis)\b", question, re.I):
            resolved = f"Compare {self.comparison_run_ids[0]} with {self.comparison_run_ids[1]}. {question}"
            return resolved, {"resolved_question": resolved, "resolved_reference": list(self.comparison_run_ids),
                              "recent_turns": len(self.turns), "explicit_run_ids": found}
        if re.search(r"\b(that run|this run|its|it)\b", question, re.I) and not self.focused_run_id:
            raise ValueError("Which run do you mean? Select a run or name one; the current conversation has no unambiguous single-run focus.")
        if self.focused_run_id and re.search(r"\b(that run|this run|its|it)\b", question, re.I):
            resolved = re.sub(
                r"\b(that run|this run|its|it)\b",
                self.focused_run_id,
                question,
                count=1,
                flags=re.I,
            )
            used = self.focused_run_id
        if self.focused_run_id and re.search(r"corresponding|matched", question, re.I):
            rate = re.search(r"learning[- ]rate\s*[-=:]?\s*(\d+(?:\.\d+)?)", question, re.I)
            if rate:
                from v3.analysis import matched_runs
                matches = matched_runs(self.focused_run_id, float(rate[1]))
                if len(matches) != 1:
                    raise ValueError(f"The corresponding run is ambiguous or unavailable. Candidates: {matches or 'none'}")
                resolved = f"Compare {self.focused_run_id} with {matches[0]}."
                used = self.focused_run_id
        return resolved, {
            "focused_run_id_before": self.focused_run_id,
            "explicit_run_ids": found,
            "resolved_reference": used,
            "resolved_question": resolved,
            "recent_turns": len(self.turns),
        }
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## v2_answers.py

**Absolute path:** `D:\Agentic_ai_rag projects\v2_answers.py`

**Purpose:** Deterministic source-aware conversational answer renderer.

Groups successful Python results into observations, reference knowledge, interpretations, uncertainty and sources. Numeric formatting is downstream of tool calculations; no LLM arithmetic or invented source URL is required.

**Dependencies:** .

**Main symbols and input contracts:**

- `render_answer(question: str, tool_results: list[tuple[str, dict]])` — source line 4.

**Who references this selected routine:** simple_agent.py, v2_agent.py.

**What the selected routine calls:** `', '.join`, `'\n'.join`, `'\n\n'.join`, `any`, `by_name.get`, `by_name.setdefault`, `by_name.setdefault(name, []).append`, `experiment_sources.add`, `experiment_sources.update`, `inspections.get`, `inspections.items`, `knowledge.append`, `knowledge_sources.items`, `len`, `limits.append`, `min`, `observations.append`, `question.lower`, `result['changed_settings'].items`, `result['filters'].items`, `result['groups'].items`, `sections.append`, `sections.insert`, `set`, `sorted`, `source_lines.append`, `source_lines.extend`, `str`.

**Error/control boundaries:** Delegated exceptions propagate to the service/UI/CLI boundaries described above; absence of an explicit raise is not absence of failure.

Actual source: `v2_answers.py:4`–`43`; excerpt of `render_answer` (remaining lines, if any, are not reproduced here).

```python
def render_answer(question: str, tool_results: list[tuple[str, dict]]) -> str:
    by_name = {}
    for name, result in tool_results:
        by_name.setdefault(name, []).append(result)
    observations = []
    experiment_sources = set()
    knowledge_sources = {}

    for result in by_name.get("rank_experiments", []):
        observations.append(f"- Saved experiments ranked by **{result['sort_by']}** ({result['total_matches']} matching records).")
        for row in result["matches"]:
            observations.append(f"  - **{row['run_id']}**: accuracy {row['final_validation_accuracy_percent']:.2f}%; loss {row['final_validation_loss']:.4f}; largest validation-loss rise {row['largest_loss_rise']:.6f}.")
            experiment_sources.add(row["source"])

    for result in by_name.get("compare_experiments", []):
        changes = ", ".join(
            f"{key}: {values['baseline']} -> {values['target']}"
            for key, values in result["changed_settings"].items()
        ) or "none recorded"
        observations.append(
            f"- **{result['baseline_run_id']} -> {result['target_run_id']}** at epoch {result['final_epoch']}: "
            f"validation accuracy {result['baseline_validation_accuracy_percent']:.2f}% -> "
            f"{result['target_validation_accuracy_percent']:.2f}% "
            f"({result['accuracy_change_target_minus_baseline_pp']:+.2f} percentage points); "
            f"validation loss {result['baseline_validation_loss']:.4f} -> "
            f"{result['target_validation_loss']:.4f} "
            f"({result['loss_change_target_minus_baseline']:+.4f}). "
            f"Changed recorded settings: {changes}."
        )
        experiment_sources.update((result["baseline_source"], result["target_source"]))

    inspections = {item["run_id"]: item for item in by_name.get("get_experiment", [])}
    for search in by_name.get("search_notes", []):
        for match in search["matches"]:
            record = inspections.get(match["run_id"])
            if record is None:
                continue
            observations.append(
                f"- **{match['run_id']}** (note rank {match['final_rank']}, "
                f"cosine {str(match['cosine_similarity'])}): {match['observation']}"
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## v2_analysis.py

**Absolute path:** `D:\Agentic_ai_rag projects\v2_analysis.py`

**Purpose:** Reusable measured ranking, curve summaries and descriptive heuristics.

Reads saved metrics, supports exact configuration filters, ranks accuracy/loss/spikes, returns chart points, and flags possible generalization intervals. Descriptive ranking is not statistical inference and does not silently match confounded records.

**Dependencies:** `from statistics import mean, median`; `from experiment_data import RUNS_DIR, largest_rise, load_run, loss_recoveries`.

**Main symbols and input contracts:**

- `rank_experiments(sort_by='accuracy', learning_rate=None, train_size=None, dropout=None, top_k=11)` — source line 8.
- `summarize_run_curve(run_id: str)` — source line 24.
- `find_overfitting_candidates()` — source line 47.
- `compare_run_group(learning_rate_a: float, learning_rate_b: float)` — source line 73.
- `plot_run_metrics(run_id: str)` — source line 103.

**Who references this selected routine:** ui.py.

**What the selected routine calls:** `ValueError`, `largest_rise`, `len`, `load_run`, `result.update`, `result['matches'].sort`, `round`, `search_runs`, `type`.

**Error/control boundaries:** `ValueError('Choose accuracy/loss/spike and top_k between 1 and 20')`; `ValueError('Choose two distinct learning rates')`.

Actual source: `v2_analysis.py:8`–`21`; excerpt of `rank_experiments` (remaining lines, if any, are not reproduced here).

```python
def rank_experiments(sort_by="accuracy", learning_rate=None, train_size=None, dropout=None, top_k=11):
    """Rank saved results; a spike is a measured positive epoch-to-epoch loss rise."""
    from experiment_data import search_runs
    if sort_by not in {"accuracy", "loss", "spike"} or type(top_k) is not int or not 1 <= top_k <= 20:
        raise ValueError("Choose accuracy/loss/spike and top_k between 1 and 20")
    result = search_runs(learning_rate, train_size, dropout)
    for row in result["matches"]:
        row["largest_loss_rise"] = round(largest_rise(load_run(row["run_id"])["metrics"])[0], 6)
    key = {"accuracy": "final_validation_accuracy_percent", "loss": "final_validation_loss", "spike": "largest_loss_rise"}[sort_by]
    result["matches"].sort(key=lambda r: ((r[key] if sort_by == "loss" else -r[key]), r["run_id"]))
    result.update(sort_by=sort_by, total_matches=len(result["matches"]),
                  limit="Ranking saved records is descriptive; configurations and horizons can differ. A loss rise is not a diagnosis.")
    result["matches"] = result["matches"][:top_k]
    return result
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## graph_agent.py

**Absolute path:** `D:\Agentic_ai_rag projects\graph_agent.py`

**Purpose:** Compact reactive graph reused for simple questions.

agent_node calls shared choose_next, tools_node dispatches the pending allowed request, and final_node renders successful evidence. Conditional routing stops when the menu is empty, a tool fails, or the bounded call budget is exhausted.

**Dependencies:** `from typing import TypedDict`; `from langgraph.graph import END, START, StateGraph`; `from v2_agent import MAX_TOOL_CALLS, execute_call, finish_turn, prepare_turn, choose_next`; `from v2_state import SessionState`.

**Main symbols and input contracts:**

- `GraphState` — source line 18.
- `agent_node(state: GraphState)` — source line 22.
- `route_after_agent(state: GraphState)` — source line 28.
- `tools_node(state: GraphState)` — source line 32.
- `final_node(state: GraphState)` — source line 41.
- `build_graph()` — source line 47.
- `run_graph(question: str, session: SessionState | None=None, *, rerank: bool=False, model_enabled: bool=True, final_tools: bool=False, semantic: bool=True)` — source line 62.

**Who references this selected routine:** Entry-point/framework callbacks or method dispatch; inspect the runtime trace for the actual caller.

**What the selected routine calls:** `StateGraph`, `builder.add_conditional_edges`, `builder.add_edge`, `builder.add_node`, `builder.compile`.

**Error/control boundaries:** Delegated exceptions propagate to the service/UI/CLI boundaries described above; absence of an explicit raise is not absence of failure.

Actual source: `graph_agent.py:47`–`56`; excerpt of `build_graph` (remaining lines, if any, are not reproduced here).

```python
def build_graph():
    builder = StateGraph(GraphState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", tools_node)
    builder.add_node("final", final_node)
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", route_after_agent, {"tools": "tools", "final": "final"})
    builder.add_edge("tools", "agent")
    builder.add_edge("final", END)
    return builder.compile()
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## v3/planner.py

**Absolute path:** `D:\Agentic_ai_rag projects\v3\planner.py`

**Purpose:** Request classification and bounded model planning/hypothesis choices.

Classifies local scope and complexity, requests schema-constrained planning or a native hypothesis tool call, validates choices, bounds attempts at two and records policy fallbacks. make_plan records step dependencies/status/origin and required user-requested additions.

**Dependencies:** `import json`; `import re`; `from urllib.request import Request, urlopen`; `from experiment_data import RUNS_DIR`; `from v2_agent import ask_ollama`; `from v2_state import mentioned_run_ids`; `from v3.investigation_state import event`.

**Main symbols and input contracts:**

- `ask_decision(messages, schema)` — source line 15.
- `classify(question)` — source line 31.
- `unknown_run_ids(question)` — source line 45.
- `select(state, name, description, properties, fallback, validator)` — source line 50.
- `make_plan(state)` — source line 77.
- `mark(state, step_id, status='completed', detail=None)` — source line 136.

**Who references this selected routine:** v3/hypothesis.py.

**What the selected routine calls:** `ValueError`, `ask_decision`, `event`, `isinstance`, `json.loads`, `list`, `message.get`, `range`, `set`, `str`, `validator`.

**Error/control boundaries:** `RuntimeError('Planner did not complete its structured response')`; `ValueError('Invalid or repeated plan steps')`; `ValueError('Question must not be empty')`; `ValueError('Unknown knowledge topic')`; `ValueError('Wrong tool, absent call, or invalid fields')`; `ValueError(f'Unknown run IDs: {unknown}')`.

Actual source: `v3/planner.py:50`–`74`; excerpt of `select` (remaining lines, if any, are not reproduced here).

```python
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
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## v3/investigation_state.py

**Absolute path:** `D:\Agentic_ai_rag projects\v3\investigation_state.py`

**Purpose:** SQLite snapshots, proposals, audit history and atomic execution permission.

Stores application JSON separately from framework checkpoints in one local database. Connection contexts close handles explicitly. Canonical hashes bind approval to configuration. claim_execution serializes permission consumption and limits active live work; actor labels are local audit fields, not authentication.

**Dependencies:** `from contextlib import contextmanager`; `from datetime import datetime, timezone`; `import hashlib`; `import json`; `from pathlib import Path`; `import sqlite3`; `import uuid`.

**Main symbols and input contracts:**

- `now()` — source line 15.
- `digest(value)` — source line 19.
- `event(state, kind, data, origin='PYTHON')` — source line 23.
- `InvestigationStore` — source line 27.

**Who references this selected routine:** tests/test_final.py, tests/test_v3.py, v3/experiment_executor.py.

**What the selected routine calls:** `PermissionError`, `db.execute`, `db.execute("SELECT id FROM proposals WHERE status='running' AND mode='live' AND id<>?", (proposal_id,)).fetchone`, `db.execute('SELECT * FROM proposals WHERE id=?', (proposal_id,)).fetchone`, `self.connection`.

**Error/control boundaries:** `PermissionError('Another live experiment is already active; inspect it before starting another')`; `PermissionError('Execution requires unused approval for this exact proposal hash and mode')`; `PermissionError('Only the user can approve live training')`; `PermissionError('Stale proposal: inspect the exact current configuration again')`; `PermissionError('This permission has already been consumed')`; `ValueError('Create a new investigation to replace an executed proposal')`; `ValueError('Invalid decision or execution mode')`; `ValueError('Proposal belongs to another investigation')`; `ValueError('Unknown proposal')`; `ValueError(f'Unknown investigation: {identifier}')`.

Actual source: `v3/investigation_state.py:130`–`138`; excerpt of `claim_execution` (remaining lines, if any, are not reproduced here).

```python
    def claim_execution(self, proposal_id, expected_hash, mode):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
            if not row or row["hash"] != expected_hash or row["status"] != "approved" or row["mode"] != mode:
                raise PermissionError("Execution requires unused approval for this exact proposal hash and mode")
            if mode == "live" and db.execute("SELECT id FROM proposals WHERE status='running' AND mode='live' AND id<>?", (proposal_id,)).fetchone():
                raise PermissionError("Another live experiment is already active; inspect it before starting another")
            db.execute("UPDATE proposals SET status='running' WHERE id=?", (proposal_id,))
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## v3/analysis.py

**Absolute path:** `D:\Agentic_ai_rag projects\v3\analysis.py`

**Purpose:** Investigation-specific validation, controlled comparisons and seed blocks.

Checks metric completeness, compares the union of configuration keys, reports absent controls/provenance, computes curve statistics and deduplicates seed groups. matched_runs finds recorded partners. Missing required evidence suppresses deltas or executable proposals rather than filling defaults.

**Dependencies:** `from itertools import combinations`; `import math`; `from statistics import mean, pstdev`; `from experiment_data import RUNS_DIR, load_run, largest_rise, loss_recoveries`.

**Main symbols and input contracts:**

- `matched_runs(run_id, learning_rate=None)` — source line 14.
- `check_record(record)` — source line 29.
- `curve(record)` — source line 46.
- `compare_records(baseline, target)` — source line 68.
- `analyze(run_ids, *, include_seed_pairs=True)` — source line 92.

**Who references this selected routine:** tests/test_v3.py, ui.py, v3/experiment_executor.py, v3/investigation_graph.py.

**What the selected routine calls:** `a.get`, `any`, `b.get`, `curve`, `largest_rise`, `result.update`, `round`, `set`, `sorted`.

**Error/control boundaries:** Delegated exceptions propagate to the service/UI/CLI boundaries described above; absence of an explicit raise is not absence of failure.

Actual source: `v3/analysis.py:68`–`89`; excerpt of `compare_records` (remaining lines, if any, are not reproduced here).

```python
def compare_records(baseline, target):
    a, b = baseline["config"], target["config"]
    differences = {k: {"baseline": a.get(k), "target": b.get(k)}
                   for k in sorted(set(a) | set(b)) if k != "run_id" and a.get(k) != b.get(k)}
    unknown = [k for k in (*CONTROLS, "learning_rate") if k not in a or k not in b]
    ca, cb = curve(baseline), curve(target)
    result = {"baseline_run_id": a["run_id"], "target_run_id": b["run_id"],
              "sources": [f"runs/{a['run_id']}.json", f"runs/{b['run_id']}.json"],
              "source_type": "DERIVED_ANALYSIS", "changed_settings": differences,
              "missing_controls": unknown, "curves": {a["run_id"]: ca, b["run_id"]: cb},
              "matching_scope": "All recorded configuration fields; hidden_units and dropout describe architecture settings, not complete architecture provenance.",
              "missing_provenance": ["Exact model-class/trainer revision was not recorded in historical JSON.",
                                     "Hardware and software versions were not recorded in historical JSON."],
              "controlled_learning_rate_pair": not unknown and set(differences) == {"learning_rate"},
              "confounded": any(k != "learning_rate" for k in differences)}
    if "incomplete" not in ca and "incomplete" not in cb and ca["final_epoch"] == cb["final_epoch"]:
        result.update(accuracy_delta_pp=round(100 * (target["metrics"][-1]["val_accuracy"] - baseline["metrics"][-1]["val_accuracy"]), 2),
                      loss_delta=round(target["metrics"][-1]["val_loss"] - baseline["metrics"][-1]["val_loss"], 6),
                      rise_delta=round(largest_rise(target["metrics"])[0] - largest_rise(baseline["metrics"])[0], 6))
    else:
        result["missing_metrics"] = "Final deltas unavailable: incomplete records or different final epochs"
    return result
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## v3/retrieval.py

**Absolute path:** `D:\Agentic_ai_rag projects\v3\retrieval.py`

**Purpose:** Primary source-aware note retrieval and guarded knowledge retrieval.

Builds human or clearly derived documents, filters exact configurations before matching, normalizes tokens, reuses MiniLM, fuses ranks and exposes all stages/scores. Exact-ID and human-source priorities are explicit. Knowledge remains a separate corpus with covered-topic and lexical fallback behavior.

**Dependencies:** `import re`; `from pathlib import Path`; `from experiment_data import RUNS_DIR, load_run`; `from note_retrieval import encode_queries_and_notes, keyword_rank, load_notes, semantic_rank, words`; `from v2_retrieval import RRF_K, search_ml_knowledge`; `from v3.analysis import curve`.

**Main symbols and input contracts:**

- `tokens(text)` — source line 15.
- `derived_summary(record)` — source line 20.
- `documents(include_derived=True, filters=None)` — source line 34.
- `search_notes(query, top_k=3, *, include_derived=True, normalized=True, filters=None, semantic=True, source_policy='human_first', rerank=False)` — source line 57.
- `knowledge(query, *, semantic=True)` — source line 130.

**Who references this selected routine:** evaluate_final_retrieval.py, tests/test_v3.py, v2_agent.py, v3/investigation_graph.py.

**What the selected routine calls:** `ValueError`, `_reranker`, `_reranker().predict`, `counts.get`, `documents`, `encode_queries_and_notes`, `enumerate`, `float`, `int`, `isinstance`, `keyword_rank`, `kr.get`, `len`, `list`, `query.strip`, `re.findall`, `round`, `rows.append`, `rows.sort`, `semantic_rank`, `set`, `sorted`, `sr.get`, `sum`, `tokens`, `type`, `within_source`, `zip`.

**Error/control boundaries:** `ValueError('Search needs a nonempty query and top_k between 1 and 11')`; `ValueError('Unknown source policy')`; `ValueError('Unsupported retrieval filter')`.

Actual source: `v3/retrieval.py:57`–`96`; excerpt of `search_notes` (remaining lines, if any, are not reproduced here).

```python
def search_notes(query, top_k=3, *, include_derived=True, normalized=True, filters=None, semantic=True, source_policy="human_first", rerank=False):
    if not isinstance(query, str) or not query.strip() or type(top_k) is not int or not 1 <= top_k <= 11:
        raise ValueError("Search needs a nonempty query and top_k between 1 and 11")
    docs = documents(include_derived, filters)
    pairs = [(x["path"], x["text"]) for x in docs]
    if not docs:
        return {"matches": [], "stages": {}, "mode": "empty"}
    if normalized:
        kw = [(len(tokens(query) & tokens(text)), path, [], text) for path, text in pairs]
        kw = sorted([x for x in kw if x[0]], key=lambda x: (-x[0], x[1].stem))
    else:
        kw = keyword_rank(query, pairs)
    mode = "keyword + cached MiniLM RRF"
    sem = []
    if semantic:
        try:
            embeddings = encode_queries_and_notes([query], pairs, local_only=True)
            sem = semantic_rank(embeddings[0], embeddings[1:], pairs)
        except (OSError, RuntimeError, ImportError) as exc:
            mode = f"APP POLICY: keyword fallback; MiniLM unavailable: {type(exc).__name__}"
    else:
        mode = "deterministic lexical fixture mode (no embeddings)"
    kr = {x[1].stem: i for i, x in enumerate(kw, 1)}
    sr = {x[1].stem: i for i, x in enumerate(sem, 1)}
    cos = {x[1].stem: float(x[0]) for x in sem}
    if source_policy not in {"human_first", "mixed"}:
        raise ValueError("Unknown source policy")
    if source_policy == "human_first":
        # Keep within-source ranks: adding derived documents must not perturb human-note order.
        groups = {d["run_id"]: d["source_type"] for d in docs}
        def within_source(ranks):
            counts, result = {}, {}
            for rid in sorted(ranks, key=ranks.get):
                source = groups[rid]
                counts[source] = counts.get(source, 0) + 1
                result[rid] = counts[source]
            return result
        kr, sr = within_source(kr), within_source(sr)
    exact = set(re.findall(r"[a-zA-Z0-9_-]+", query))
    rows = []
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## v3/hypothesis.py

**Absolute path:** `D:\Agentic_ai_rag projects\v3\hypothesis.py`

**Purpose:** Evidence registry, competing candidates and reference validation.

build_evidence assigns source IDs and snapshot hashes. generate constructs measurement-conditioned candidate mechanisms; the model selects at least two. Validation rejects nonexistent references, knowledge used as experiment support, changed snapshots and missing competition. Statuses remain descriptive.

**Dependencies:** `from v3.investigation_state import digest, event`; `from v3.planner import select`.

**Main symbols and input contracts:**

- `build_evidence(state)` — source line 7.
- `generate(state)` — source line 29.
- `validate_evidence(state)` — source line 93.

**Who references this selected routine:** tests/test_v3.py, v3/investigation_graph.py.

**What the selected routine calls:** `digest`, `errors.append`, `event`, `len`, `registry.items`.

**Error/control boundaries:** `ValueError('Choose at least two distinct measured candidate hypotheses')`.

Actual source: `v3/hypothesis.py:93`–`112`; excerpt of `validate_evidence` (remaining lines, if any, are not reproduced here).

```python
def validate_evidence(state):
    errors = []
    registry = state["evidence"]
    for h in state["hypotheses"]:
        for field in ("supporting_experiment_evidence", "contradicting_experiment_evidence", "relevant_ml_knowledge"):
            for key in h[field]:
                if key not in registry:
                    errors.append(f"Unknown citation {key}")
                elif field != "relevant_ml_knowledge" and registry[key]["source_type"] == "ML_KNOWLEDGE":
                    errors.append("General knowledge cannot establish an experiment observation")
    for key, evidence in registry.items():
        if evidence["source_type"] == "EXPERIMENT_JSON" and digest(evidence["value"]) != evidence["sha256"]:
            errors.append(f"Evidence changed after collection: {key}")
    if len(state["hypotheses"]) < 2:
        errors.append("Competing hypotheses missing")
    state["evidence_validation"] = {"valid": not errors, "errors": errors,
                                    "unsupported_structured_citations": len(errors),
                                    "scope": "Structured evidence links and recorded snapshots; not a proof of causal mechanisms."}
    event(state, "HYPOTHESIS VALIDATION", state["evidence_validation"])
    return not errors
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## v3/experiment_designer.py

**Absolute path:** `D:\Agentic_ai_rag projects\v3\experiment_designer.py`

**Purpose:** Machine-readable controlled learning-rate proposals and independent validator.

Creates two supported arms from a complete saved baseline, picks shared seeds beyond existing/reserved configurations and declares a primary metric. Validation enforces exact supported fields, unique IDs/configurations, matched controls, trainer hash and bounded resources.

**Dependencies:** `from pathlib import Path`; `import hashlib`; `import json`; `import math`; `import re`; `from experiment_data import RUNS_DIR, load_run`; `from v3.analysis import CONTROLS`; `from v3.investigation_state import ROOT`.

**Main symbols and input contracts:**

- `trainer_hash()` — source line 18.
- `validate_config(config)` — source line 23.
- `saved_configs()` — source line 41.
- `validate_proposal(proposal, *, check_duplicates=True)` — source line 49.
- `design(state)` — source line 72.

**Who references this selected routine:** tests/test_v3.py, v3/experiment_executor.py, v3/investigation_graph.py, v3/service.py.

**What the selected routine calls:** `(RUNS_DIR / f'{config['run_id']}.json').exists`, `ValueError`, `all`, `any`, `config.items`, `len`, `old.get`, `proposal.get`, `saved_configs`, `trainer_hash`, `validate_config`.

**Error/control boundaries:** `ValueError('A proposed run ID already exists; overwriting is forbidden')`; `ValueError('All recorded controls, including both seeds, must match')`; `ValueError('Configuration has missing or unsupported fields')`; `ValueError('Duplicate recorded/planned configuration')`; `ValueError('Execution resource limits cannot be increased')`; `ValueError('Only a two-run, single learning-rate intervention is supported')`; `ValueError('Require distinct IDs and lower-rate control followed by higher-rate intervention')`; `ValueError('Run ID must be a safe, unique v3_ identifier')`; `ValueError('Training code changed; regenerate and approve the proposal again')`; `ValueError(f'Invalid or over-budget {key}')`; `ValueError(f'Unsupported fixed training control: {key}')`.

Actual source: `v3/experiment_designer.py:49`–`69`; excerpt of `validate_proposal` (remaining lines, if any, are not reproduced here).

```python
def validate_proposal(proposal, *, check_duplicates=True):
    if proposal.get("changed_variable") != "learning_rate" or len(proposal.get("runs", [])) != 2:
        raise ValueError("Only a two-run, single learning-rate intervention is supported")
    if proposal.get("training_code_sha256") != trainer_hash():
        raise ValueError("Training code changed; regenerate and approve the proposal again")
    if proposal.get("limits") != {"max_total_seconds": 600, "max_runs": 2, "cpu_threads": 2}:
        raise ValueError("Execution resource limits cannot be increased")
    a, b = proposal["runs"]
    for config in (a, b):
        validate_config(config)
    if a["run_id"] == b["run_id"] or not a["learning_rate"] < b["learning_rate"]:
        raise ValueError("Require distinct IDs and lower-rate control followed by higher-rate intervention")
    if any(a[k] != b[k] for k in CONTROLS):
        raise ValueError("All recorded controls, including both seeds, must match")
    existing = saved_configs()
    for config in (a, b):
        if (RUNS_DIR / f"{config['run_id']}.json").exists():
            raise ValueError("A proposed run ID already exists; overwriting is forbidden")
        if check_duplicates and any(all(old.get(k) == v for k, v in config.items() if k != "run_id") for old in existing):
            raise ValueError("Duplicate recorded/planned configuration")
    return {"valid": True, "checks": ["single_variable", "matched_controls", "new_configurations", "resource_limits", "trainer_hash", "unique_run_ids"]}
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## v3/experiment_executor.py

**Absolute path:** `D:\Agentic_ai_rag projects\v3\experiment_executor.py`

**Purpose:** Only approved bounded execution and measured result interpretation.

Rechecks hash/configuration, atomically claims permission, either completes a no-training dry run or launches a fixed subprocess. It writes logs/provenance, respects timeout/cancellation, validates output records and records failures. ingest_record and evaluate_outcomes support labeled fixture tests without creating real data.

**Dependencies:** `import json`; `import os`; `from pathlib import Path`; `import subprocess`; `import sys`; `import time`; `from v3.analysis import check_record, compare_records`; `from v3.experiment_designer import validate_proposal`; `from v3.investigation_state import ROOT, digest, now`.

**Main symbols and input contracts:**

- `ingest_record(record, config, *, investigation_id, proposal_id, fixture=False)` — source line 15.
- `evaluate_outcomes(records)` — source line 25.
- `execute(store, proposal_id, expected_hash, mode)` — source line 39.

**Who references this selected routine:** demonstrate_final.py, tests/test_final.py, tests/test_v3.py, v3/investigation_graph.py, v3/investigation_state.py.

**What the selected routine calls:** `(data / name).is_file`, `(store.path.parent / 'executions' / proposal_id / 'cancel.requested').exists`, `FileExistsError`, `FileNotFoundError`, `PermissionError`, `RuntimeError`, `TimeoutError`, `ValueError`, `all`, `cancel_path.exists`, `dict`, `digest`, `folder.mkdir`, `ingest_record`, `json.dumps`, `json.loads`, `log.open`, `now`, `output.exists`, `output.read_text`, `payload_path.write_text`, `result.update`, `result['ingested'].append`, `result['logs'].append`, `result['run_ids'].append`, `store.claim_execution`, `store.execution_result`, `store.proposal`, `str`, `subprocess.run`, `time.monotonic`, `type`, `validate_proposal`.

**Error/control boundaries:** `FileExistsError('Existing experiment cannot be overwritten')`; `FileNotFoundError('Cached Fashion-MNIST training partition is unavailable; downloads are disabled')`; `PermissionError('Proposal hash mismatch')`; `RuntimeError('Training cancelled by user')`; `TimeoutError('Total approved execution time exhausted')`; `ValueError('Fixture ingestion requires an explicit test_fixture provenance label')`; `ValueError('Training output is incomplete or does not match the approved configuration')`; `ValueError('Unknown execution mode')`.

Actual source: `v3/experiment_executor.py:39`–`78`; excerpt of `execute` (remaining lines, if any, are not reproduced here).

```python
def execute(store, proposal_id, expected_hash, mode):
    row = store.proposal(proposal_id)
    proposal = row["payload"]
    if digest(proposal) != expected_hash or row["hash"] != expected_hash:
        raise PermissionError("Proposal hash mismatch")
    validate_proposal(proposal)
    store.claim_execution(proposal_id, expected_hash, mode)
    result = {"status": "running", "mode": mode, "started": now(), "run_ids": [], "logs": [], "ingested": []}
    store.execution_result(proposal_id, result)
    try:
        if mode == "dry_run":
            result.update(status="dry_run_completed", planned_configs=proposal["runs"],
                          message="Approval and resource checks passed. No trainer was launched; no metrics or run files were created.")
        elif mode == "live":
            data = ROOT / "data" / "FashionMNIST" / "raw"
            if not all((data / name).is_file() for name in ("train-images-idx3-ubyte", "train-labels-idx1-ubyte")):
                raise FileNotFoundError("Cached Fashion-MNIST training partition is unavailable; downloads are disabled")
            folder = store.path.parent / "executions" / proposal_id
            folder.mkdir(parents=True, exist_ok=True)
            cancel_path = folder / "cancel.requested"
            started = time.monotonic()
            for config in proposal["runs"]:
                if cancel_path.exists():
                    raise RuntimeError("Training cancelled by user")
                remaining = proposal["limits"]["max_total_seconds"] - (time.monotonic() - started)
                if remaining <= 0:
                    raise TimeoutError("Total approved execution time exhausted")
                output = ROOT / "runs" / f"{config['run_id']}.json"
                if output.exists():
                    raise FileExistsError("Existing experiment cannot be overwritten")
                payload_path = folder / f"{config['run_id']}.input.json"
                payload_path.write_text(json.dumps({"config": config, "output_path": str(output), "cancel_path": str(cancel_path),
                    "provenance": {"investigation_id": proposal["investigation_id"], "proposal_id": proposal_id,
                                   "approved_sha256": expected_hash, "created_at": now(), "executor": "v3"}}), encoding="utf-8")
                log = folder / f"{config['run_id']}.log"
                result["logs"].append(str(log))
                result["current_run_id"] = config["run_id"]
                store.execution_result(proposal_id, result)
                environment = dict(os.environ, OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", PYTHONUTF8="1",
                                   HF_HOME=str(ROOT / ".model_cache" / "hub"), HF_HUB_OFFLINE="1")
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## v3/training_worker.py

**Absolute path:** `D:\Agentic_ai_rag projects\v3\training_worker.py`

**Purpose:** Fixed worker calling the original trainer.

Reads the application-produced input JSON, validates configuration and fixed output path, sets two torch threads, and calls phase0.run_training with download=False, provenance, timeout and cancellation marker. This module is not an LLM shell tool.

**Dependencies:** `import json`; `from pathlib import Path`; `import sys`; `from v3.experiment_designer import validate_config`; `from v3.investigation_state import ROOT`.

**Main symbols and input contracts:**

- `main()` — source line 11.

**Who references this selected routine:** app.py, demonstrate_final.py, evaluate_final.py, evaluate_final_retrieval.py, investigate.py, phase0.py, tests/test_final.py, tests/test_v3.py, v3/cli.py, validate_final_ui.py, verify_final.py.

**What the selected routine calls:** `Path`, `Path(payload['output_path']).resolve`, `Path(sys.argv[1]).read_text`, `ValueError`, `expected.resolve`, `json.loads`, `payload.get`, `run_training`, `torch.set_num_threads`, `validate_config`.

**Error/control boundaries:** `ValueError('Worker output must be the fixed run-ID-derived JSON path')`.

Actual source: `v3/training_worker.py:11`–`22`; excerpt of `main` (remaining lines, if any, are not reproduced here).

```python
def main():
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    config = payload["config"]
    validate_config(config)
    expected = ROOT / "runs" / f"{config['run_id']}.json"
    if Path(payload["output_path"]).resolve() != expected.resolve():
        raise ValueError("Worker output must be the fixed run-ID-derived JSON path")
    from phase0 import run_training
    import torch
    torch.set_num_threads(2)
    run_training(config, expected, download=False, provenance=payload["provenance"], max_seconds=600,
                 cancel_path=payload.get("cancel_path"))
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## phase0.py

**Absolute path:** `D:\Agentic_ai_rag projects\phase0.py`

**Purpose:** Original Fashion-MNIST model, evaluation and callable training implementation.

SimpleMLP and evaluate preserve the existing model/evaluation code. run_training takes explicit config/output/provenance and optional runtime/cancel limits. Its split/shuffle/model generators preserve recorded semantics; new output uses exclusive creation. main preserves user-operated CLI and dry-run configuration output.

**Dependencies:** `import argparse`; `import json`; `import math`; `import re`; `import time`; `from pathlib import Path`; `import torch`; `from torch import nn`; `from torchvision import datasets, transforms`; `from torch.utils.data import DataLoader, Subset`.

**Main symbols and input contracts:**

- `SimpleMLP` — source line 14.
- `evaluate(model, loader, loss_fn)` — source line 28.
- `run_training(config, output_path, *, download=True, provenance=None, max_seconds=None, cancel_path=None)` — source line 42.
- `main()` — source line 140.

**Who references this selected routine:** v3/training_worker.py.

**What the selected routine calls:** `DataLoader`, `Path`, `Path(__file__).resolve`, `Path(cancel_path).exists`, `RuntimeError`, `SimpleMLP`, `Subset`, `TimeoutError`, `datasets.FashionMNIST`, `evaluate`, `history.append`, `json.dump`, `len`, `loss.backward`, `loss.item`, `loss_fn`, `model`, `model.parameters`, `model.train`, `nn.CrossEntropyLoss`, `optimizer.step`, `optimizer.zero_grad`, `output.write`, `output_path.open`, `output_path.parent.mkdir`, `print`, `range`, `str`, `time.monotonic`, `torch.Generator`, `torch.Generator().manual_seed`, `torch.manual_seed`, `torch.optim.SGD`, `torch.randperm`, `train_indices[:5].tolist`, `transforms.ToTensor`.

**Error/control boundaries:** `RuntimeError('Training cancelled by user')`; `SystemExit(0)`; `TimeoutError('Approved training runtime exceeded')`.

Actual source: `phase0.py:42`–`81`; excerpt of `run_training` (remaining lines, if any, are not reproduced here).

```python
def run_training(config, output_path, *, download=True, provenance=None, max_seconds=None, cancel_path=None):
    started = time.monotonic()
    # Convert images into PyTorch tensors
    transform = transforms.ToTensor()

    # Download Fashion-MNIST training data
    dataset = datasets.FashionMNIST(
        root=str(Path(__file__).resolve().parent / "data"),
        train=True,
        download=download,
        transform=transform
    )

    # Make the random selection reproducible
    generator = torch.Generator().manual_seed(config["split_seed"])

    # Generate a random ordering of all 60,000 image indices
    indices = torch.randperm(len(dataset), generator=generator)

    # Use the requested number from the fixed training pool
    train_indices = indices[:config["train_size"]]

    # Keep validation images fixed when the training subset size changes
    val_indices = indices[
        config["validation_start"]:config["validation_start"] + config["val_size"]
    ]

    # Create subsets using those indices
    train_dataset = Subset(dataset, train_indices)
    val_dataset = Subset(dataset, val_indices)

    # Keep the training shuffle reproducible and separate from the data split
    shuffle_generator = torch.Generator().manual_seed(config["shuffle_seed"])
    train_loader = DataLoader(
        train_dataset, batch_size=config["batch_size"], shuffle=True,
        generator=shuffle_generator
    )
    train_eval_loader = DataLoader(
        train_dataset, batch_size=config["batch_size"], shuffle=False
    )
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## v3/investigation_graph.py

**Absolute path:** `D:\Agentic_ai_rag projects\v3\investigation_graph.py`

**Purpose:** Primary durable graph with explicit conditional scientific workflow.

Classifies, plans, collects, measures, retrieves knowledge, selects/validates hypotheses, designs, interrupts, executes and reports. Simple questions delegate to the compact graph. Approval checks persistent decisions; execution reuses completed results or marks uncertain work interrupted. Nodes save application snapshots at explicit boundaries.

**Dependencies:** `from contextlib import contextmanager`; `from typing import TypedDict`; `from langgraph.checkpoint.sqlite import SqliteSaver`; `from langgraph.graph import END, START, StateGraph`; `from langgraph.types import interrupt`; `from experiment_data import load_run`; `from v3.analysis import analyze, matched_runs, compare_records`; `from v3.experiment_designer import design, validate_proposal`; `from v3.experiment_executor import evaluate_outcomes, execute`; `from v3.hypothesis import build_evidence, generate, validate_evidence`; `from v3.investigation_state import event`; `from v3.planner import classify, make_plan, mark, unknown_run_ids, UNSUPPORTED`; `from v3.report import render_report`; `from v3.retrieval import knowledge, search_notes`.

**Main symbols and input contracts:**

- `ResearchState` — source line 21.
- `investigation_graph(store)` — source line 26.

**Who references this selected routine:** Entry-point/framework callbacks or method dispatch; inspect the runtime trace for the actual caller.

**What the selected routine calls:** `PermissionError`, `event`, `interrupt`, `isinstance`, `mark`, `render_report`, `save`, `store.decisions`, `store.proposal`, `store.save`, `str`, `token.get`, `validate_proposal`.

**Error/control boundaries:** `PermissionError('No persisted human decision is available')`; `PermissionError('Resume token does not match the current proposal')`; `PermissionError('The execution branch has no usable approval')`; `ValueError(f'Unknown run IDs: {unknown}')`.

Actual source: `v3/investigation_graph.py:168`–`196`; excerpt of `approval_node` (remaining lines, if any, are not reproduced here).

```python
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
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## v3/service.py

**Absolute path:** `D:\Agentic_ai_rag projects\v3\service.py`

**Purpose:** Shared UI/CLI lifecycle operations for saved investigations.

start creates a thread/document and records failures; resume distinguishes pending interrupts from runnable nodes and never treats opening as approval. decide stores exact human decisions; modify invalidates permission and re-schedules approval; export writes Markdown/JSON; cancel requests cooperative stop through a fixed marker.

**Dependencies:** `import json`; `from pathlib import Path`; `from langgraph.types import Command`; `from v3.experiment_designer import validate_proposal`; `from v3.investigation_graph import investigation_graph`; `from v3.investigation_state import InvestigationStore, event`; `from v3.report import render_report`.

**Main symbols and input contracts:**

- `Investigator` — source line 14.

**Who references this selected routine:** tests/test_v3.py, v3/cli.py, v3/ui.py.

**What the selected routine calls:** `Command`, `any`, `graph.get_state`, `graph.invoke`, `investigation_graph`, `self._config`, `self.store.load`, `self.store.proposal`.

**Error/control boundaries:** `PermissionError('Proposal does not belong to this investigation')`; `ValueError('Cannot change investigation or proposal identity')`; `ValueError('No active approved execution to cancel')`.

Actual source: `v3/service.py:39`–`53`; excerpt of `resume` (remaining lines, if any, are not reproduced here).

```python
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
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## v3/report.py

**Absolute path:** `D:\Agentic_ai_rag projects\v3\report.py`

**Purpose:** Grounded persistent research report renderer.

Renders the objective, exact observations, recorded controls, hypotheses and evidence registry, ML references, uncertainties, proposal hash, audit/execute status and outcomes. When no measured follow-up exists it says so explicitly.

**Dependencies:** `import json`.

**Main symbols and input contracts:**

- `render_report(state, proposal=None, decisions=None)` — source line 6.

**Who references this selected routine:** v3/investigation_graph.py, v3/service.py.

**What the selected routine calls:** `' '.join`, `', '.join`, `'\n'.join`, `e.get`, `json.dumps`, `lines.append`, `pair.get`, `state.get`, `state.get('analysis', {}).get`, `state.get('evidence', {}).items`, `state.get('knowledge', {}).get`, `state.get('outcome', {}).get`, `state.get('records', {}).items`.

**Error/control boundaries:** Delegated exceptions propagate to the service/UI/CLI boundaries described above; absence of an explicit raise is not absence of failure.

Actual source: `v3/report.py:6`–`45`; excerpt of `render_report` (remaining lines, if any, are not reproduced here).

```python
def render_report(state, proposal=None, decisions=None):
    lines = [f"# Investigation report: {state['investigation_id']}", "", "## 1. Research question", "", state["objective"], "",
             "## 2. Relevant experiments", "", *[f"- `EXPERIMENT_JSON` runs/{x}.json" for x in state.get("records", {})], "",
             "## 3. Measured observations", ""]
    for rid, r in state.get("records", {}).items():
        last = r["metrics"][-1]
        lines.append(f"- {rid}: final validation accuracy **{100 * last['val_accuracy']:.2f}%**, loss **{last['val_loss']:.4f}**, epoch {last['epoch']}. [EXPERIMENT_JSON](../runs/{rid}.json)")
    lines += ["", "## 4. Controlled comparisons", ""]
    for pair in state.get("analysis", {}).get("comparisons", []):
        lines += [f"### {pair['target_run_id']} minus {pair['baseline_run_id']}", "",
                  f"Controlled learning-rate pair: `{pair['controlled_learning_rate_pair']}`. Confounded: `{pair['confounded']}`. Missing controls: `{pair['missing_controls']}`.", ""]
        if "accuracy_delta_pp" in pair:
            lines.append(f"- Accuracy difference: **{pair['accuracy_delta_pp']:+.2f} percentage points**; validation-loss difference: **{pair['loss_delta']:+.4f}**.")
        lines += ["", "```json", json.dumps(pair, indent=2), "```", ""]
    lines += ["## 5. Competing hypotheses", ""]
    for h in state.get("hypotheses", []):
        lines += [f"### {h['hypothesis_id']} — {h['status']}", "", f"`HYPOTHESIS` {h['statement']}", "",
                  f"- Supporting experiment evidence: {', '.join(h['supporting_experiment_evidence']) or 'None found'}",
                  f"- Opposing experiment evidence: {', '.join(h['contradicting_experiment_evidence']) or 'None found; absence is not proof'}",
                  f"- General ML knowledge: {', '.join(h['relevant_ml_knowledge']) or 'Unavailable / not selected'}",
                  f"- Assumptions: {' '.join(h['assumptions'])}", f"- Missing evidence: {' '.join(h['missing_evidence'])}",
                  f"- Proposed test: {h['proposed_test']}", f"- Selected by: {h['selected_by']}; wording: {h['statement_origin']}", ""]
    lines += ["## 6. Supporting evidence", "", "Evidence identifiers resolve in the source registry below. Hypothesis status is descriptive, not a statistical proof.", "",
              "## 7. Contradicting evidence", ""]
    for pair in state.get("analysis", {}).get("seed_pairs", []):
        lines.append(f"- {pair['target_run_id']} minus {pair['baseline_run_id']}: accuracy {pair.get('accuracy_delta_pp')} pp; maximum validation-loss-rise difference {pair.get('rise_delta')}. Missing controls: {pair['missing_controls']}. `DERIVED_ANALYSIS`, sources: {', '.join(pair['sources'])}")
    lines += ["", "## 8. Relevant ML knowledge", ""]
    for k in state.get("knowledge", {}).get("matches", []):
        lines += [f"- `ML_KNOWLEDGE` [{k['source_title']}]({k['source_url']}), local `{k['path']}`: {k['text']}"]
    if not state.get("knowledge", {}).get("matches"):
        lines.append("Knowledge retrieval was skipped, unavailable, or returned no covered evidence.")
    lines += ["", "General documentation supports possible mechanisms; it cannot prove the cause of a saved run.", "",
              "## 9. Missing evidence", "", *[f"- {x}" for x in state.get("uncertainties", [])], "",
              "## 10. Proposed experiments", ""]
    if proposal:
        lines += ["```json", json.dumps(proposal["payload"], indent=2), "```", "", f"Exact proposal SHA-256: `{proposal['hash']}`."]
    else:
        lines.append(state.get("proposal_limitation", "No executable follow-up proposal is available."))
    lines += ["", "## 11. Approval/execution status", "", f"Investigation: **{state['status']}**."]
    if proposal:
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## v3/ui.py

**Absolute path:** `D:\Agentic_ai_rag projects\v3\ui.py`

**Purpose:** Investigation plan/evidence/hypothesis/approval/execution/report controls.

Uses the shared service and SQLite state. Human controls review exact JSON/hash, approve dry/live, reject/defer or modify. Live decisions run in a background thread so refresh/cancellation remain usable. UI traces expose model and policy origins; completed futures surface exceptions.

**Dependencies:** `import json`; `from pathlib import Path`; `import pandas as pd`; `import streamlit as st`; `from concurrent.futures import ThreadPoolExecutor`; `from v3.service import Investigator`.

**Main symbols and input contracts:**

- `render_investigations()` — source line 15.

**Who references this selected routine:** legacy_ui.py, ui.py.

**What the selected routine calls:** `(current_execution or state.get('execution', {})).get`, `Investigator`, `Path`, `ThreadPoolExecutor`, `app.cancel`, `app.decide`, `app.export`, `app.modify`, `app.resume`, `app.start`, `app.store.decisions`, `app.store.list`, `app.store.load`, `app.store.proposal`, `bool`, `column.button`, `e.get`, `enumerate`, `future.done`, `future.result`, `json.dumps`, `json.loads`, `path.is_file`, `path.read_text`, `pd.DataFrame`, `pool.submit`, `st.button`, `st.caption`, `st.checkbox`, `st.code`, `st.columns`, `st.dataframe`, `st.download_button`, `st.error`, `st.expander`, `st.form`, `st.form_submit_button`, `st.info`, `st.json`, `st.line_chart`, `st.markdown`, `st.rerun`, `st.selectbox`, `st.session_state.execution_pool.shutdown`, `st.session_state.get`, `st.spinner`, `st.subheader`, `st.success`, `st.tabs`, `st.text_area`, `st.title`, `st.write`, `state.get`, `state.get('execution', {}).get`, `state.get('records', {}).items`, `str`, `zip`.

**Error/control boundaries:** Delegated exceptions propagate to the service/UI/CLI boundaries described above; absence of an explicit raise is not absence of failure.

Actual source: `v3/ui.py:15`–`54`; excerpt of `render_investigations` (remaining lines, if any, are not reproduced here).

```python
def render_investigations():
    app = Investigator()
    future = st.session_state.get("execution_future")
    if future is not None and future.done():
        try:
            future.result()
        except Exception as exc:
            st.error(f"Execution stopped: {exc}")
        st.session_state.execution_pool.shutdown(wait=False)
        del st.session_state.execution_future
    st.title("Investigation Workspace")
    st.caption("Investigate saved evidence, compare explanations, and review controlled follow-ups. Training requires your explicit approval.")
    with st.expander("Start a new investigation", expanded=not bool(app.store.list(research_only=True))):
        with st.form("new_investigation"):
            question = st.text_area("Research question", value=EXAMPLE)
            model = st.checkbox("Use local Ollama for planning and hypothesis selection", value=True)
            semantic = st.checkbox("Use cached MiniLM semantic retrieval", value=True)
            start = st.form_submit_button("Start investigation")
        if start:
            try:
                with st.spinner("Collecting evidence and checking competing explanations..."):
                    state = app.start(question, model_enabled=model, semantic=semantic)
                st.session_state.v3_selected = state["investigation_id"]
                st.rerun()
            except (ValueError, RuntimeError, OSError) as exc:
                st.error(str(exc))
    items = app.store.list(research_only=True)
    if not items:
        st.info("Start an investigation to save its plan, evidence, proposals, and report locally.")
        return
    ids = [x["id"] for x in items]
    if st.session_state.get("v3_selected") not in ids:
        st.session_state.v3_selected = ids[0]
    labels = {x["id"]: f"{x['id']} — {x['status']} — {x['objective'][:70]}" for x in items}
    identifier = st.selectbox("Saved investigations", ids, format_func=lambda x: labels[x], key="v3_selected")
    state = app.store.load(identifier)
    st.write(state["objective"])
    st.write(f"Status: **{state['status']}**")
    if state.get("last_error"):
        st.error(state["last_error"])
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## v3/cli.py

**Absolute path:** `D:\Agentic_ai_rag projects\v3\cli.py`

**Purpose:** Explicit persistent research operation CLI.

Supports start/list/show/resume/decide/modify/export/cancel. Exact IDs and proposal hashes are required for sensitive operations. Its research offline/lexical flags are separate from the integrated app.py interface.

**Dependencies:** `import argparse`; `import json`; `from pathlib import Path`; `from v3.service import Investigator`.

**Main symbols and input contracts:**

- `main(argv=None)` — source line 10.

**Who references this selected routine:** app.py, demonstrate_final.py, evaluate_final.py, evaluate_final_retrieval.py, investigate.py, phase0.py, tests/test_final.py, tests/test_v3.py, v3/training_worker.py, validate_final_ui.py, verify_final.py.

**What the selected routine calls:** `Investigator`, `Path`, `Path(args.proposal_file).read_text`, `SystemExit`, `app.cancel`, `app.decide`, `app.export`, `app.modify`, `app.resume`, `app.start`, `app.store.list`, `app.store.load`, `app.store.proposal`, `argparse.ArgumentParser`, `dec.add_argument`, `json.dumps`, `json.loads`, `mod.add_argument`, `p.add_argument`, `p.add_subparsers`, `p.parse_args`, `print`, `s.add_argument`, `start.add_argument`, `state.get`, `sub.add_parser`.

**Error/control boundaries:** `SystemExit(1)`.

Actual source: `v3/cli.py:10`–`49`; excerpt of `main` (remaining lines, if any, are not reproduced here).

```python
def main(argv=None):
    p = argparse.ArgumentParser(description="ML Experiment Detective Research Investigator")
    p.add_argument("--db", help="optional local SQLite path")
    sub = p.add_subparsers(dest="command", required=True)
    start = sub.add_parser("start")
    start.add_argument("question")
    start.add_argument("--offline", action="store_true", help="use Python fallbacks for investigation planning and hypothesis selection")
    start.add_argument("--lexical", action="store_true", help="fixture/debug mode without embedding imports")
    sub.add_parser("list")
    for name in ("show", "resume", "export", "cancel"):
        s = sub.add_parser(name)
        s.add_argument("investigation_id")
    dec = sub.add_parser("decide")
    dec.add_argument("investigation_id")
    dec.add_argument("decision", choices=("approved", "rejected", "deferred"))
    dec.add_argument("--hash", required=True, help="exact displayed proposal hash")
    dec.add_argument("--mode", choices=("dry_run", "live"), default="dry_run")
    dec.add_argument("--reason", default="")
    mod = sub.add_parser("modify")
    mod.add_argument("investigation_id")
    mod.add_argument("proposal_file")
    args = p.parse_args(argv)
    app = Investigator(args.db)
    if args.command == "cancel":
        print(app.cancel(args.investigation_id))
        return
    if args.command == "list":
        print(json.dumps(app.store.list(research_only=True), indent=2))
        return
    if args.command == "start":
        state = app.start(args.question, model_enabled=not args.offline, semantic=not args.lexical)
    elif args.command == "decide":
        state = app.decide(args.investigation_id, args.hash, args.decision, mode=args.mode, reason=args.reason)
    elif args.command == "modify":
        state = app.modify(args.investigation_id, json.loads(Path(args.proposal_file).read_text(encoding="utf-8")))
    elif args.command == "resume":
        state = app.resume(args.investigation_id)
    else:
        state = app.store.load(args.investigation_id)
    print(f"{state['investigation_id']} | {state['status']}")
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## evaluate_final.py

**Absolute path:** `D:\Agentic_ai_rag projects\evaluate_final.py`

**Purpose:** Combined deterministic scenario runner.

Discovers retained core and integrated tests, records individual success/failure details and exits nonzero on failure. This suite contains mocks and fixtures; it does not claim live-model or live-training success.

**Dependencies:** `from pathlib import Path`; `import json`; `import unittest`; `from evaluate_v3 import ScenarioResult`.

**Main symbols and input contracts:**

- `main()` — source line 8.

**Who references this selected routine:** app.py, demonstrate_final.py, evaluate_final_retrieval.py, investigate.py, phase0.py, tests/test_final.py, tests/test_v3.py, v3/cli.py, v3/training_worker.py, validate_final_ui.py, verify_final.py.

**What the selected routine calls:** `Path`, `Path('reports/final').mkdir`, `Path('reports/final/deterministic.json').write_text`, `SystemExit`, `json.dumps`, `len`, `print`, `result.wasSuccessful`, `sum`, `unittest.TextTestRunner`, `unittest.TextTestRunner(verbosity=2, resultclass=ScenarioResult).run`, `unittest.defaultTestLoader.discover`.

**Error/control boundaries:** `SystemExit(0 if result.wasSuccessful() else 1)`.

Actual source: `evaluate_final.py:8`–`17`; excerpt of `main` (remaining lines, if any, are not reproduced here).

```python
def main():
    suite=unittest.defaultTestLoader.discover("tests",pattern="test_*.py")
    result=unittest.TextTestRunner(verbosity=2,resultclass=ScenarioResult).run(suite)
    report={"type":"deterministic scenarios and labeled mocks; no live training", "tests_run":result.testsRun,
            "passed":sum(r["passed"] for r in result.scenarios), "failures":len(result.failures)+len(result.errors),
            "scenarios":result.scenarios}
    Path("reports/final").mkdir(parents=True,exist_ok=True)
    Path("reports/final/deterministic.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(f"FINAL: {report['passed']}/{report['tests_run']} passed")
    raise SystemExit(0 if result.wasSuccessful() else 1)
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## evaluate_final_retrieval.py

**Absolute path:** `D:\Agentic_ai_rag projects\evaluate_final_retrieval.py`

**Purpose:** Frozen relevance labels and separate exact-ID coverage benchmark.

Runs original five plus twelve additional labeled queries across keyword, semantic, hybrid and reranked paths, then separately checks six unnoted IDs. Scores and actual top IDs are saved; new local judgments are not a hidden unbiased test set.

**Dependencies:** `import json`; `from statistics import mean`; `from pathlib import Path`; `from note_retrieval import load_notes, encode_queries_and_notes, keyword_rank, semantic_rank`; `from v3.retrieval import search_notes`.

**Main symbols and input contracts:**

- `score(ids, relevant)` — source line 23.
- `main()` — source line 28.

**Who references this selected routine:** app.py, demonstrate_final.py, evaluate_final.py, investigate.py, phase0.py, tests/test_final.py, tests/test_v3.py, v3/cli.py, v3/training_worker.py, validate_final_ui.py, verify_final.py.

**What the selected routine calls:** `Path`, `Path('reports/final').mkdir`, `Path('reports/final/retrieval.json').write_text`, `Path('retrieval_eval_cases.json').read_text`, `Path('runs').glob`, `aggregate`, `coverage.append`, `dict`, `encode_queries_and_notes`, `json.dumps`, `json.loads`, `keyword_rank`, `load_notes`, `mean`, `print`, `rankings.items`, `report.items`, `results.append`, `round`, `score`, `search_notes`, `semantic_rank`, `sorted`.

**Error/control boundaries:** Delegated exceptions propagate to the service/UI/CLI boundaries described above; absence of an explicit raise is not absence of failure.

Actual source: `evaluate_final_retrieval.py:28`–`57`; excerpt of `main` (remaining lines, if any, are not reproduced here).

```python
def main():
    old=json.loads(Path("retrieval_eval_cases.json").read_text())
    extra=[dict(id=i,query=q,relevant=r,reason=reason) for i,q,r,reason in NEW_CASES]
    cases=old+extra
    notes=load_notes()
    results=[]
    for c in cases:
        kw=keyword_rank(c["query"],notes)
        vectors=encode_queries_and_notes([c["query"]],notes,local_only=True)
        sem=semantic_rank(vectors[0],vectors[1:],notes)
        hybrid=search_notes(c["query"],top_k=2)
        reranked=search_notes(c["query"],top_k=2,rerank=True)
        rankings={"keyword":[p.stem for _,p,_,_ in kw],"semantic":[p.stem for _,p,_ in sem],
                  "hybrid":[r["run_id"] for r in hybrid["matches"]],"reranked":[r["run_id"] for r in reranked["matches"]]}
        results.append({**c,"methods":{m:dict(score(ids,c["relevant"]),top_ids=ids[:2]) for m,ids in rankings.items()},"reranker_status":reranked["reranker"]})
        print("CASE",c["id"],flush=True)
    def aggregate(rows):
        return {m:{k:round(mean(r["methods"][m][k] for r in rows),4) for k in ("recall_at_2","mrr_at_2")} for m in rankings}
    human={p.stem for p,_ in notes}
    coverage=[]
    for path in sorted(Path("runs").glob("*.json")):
        if path.stem not in human:
            result=search_notes(f"Show recorded behavior of {path.stem}")
            coverage.append({"run_id":path.stem,"found_first":result["matches"][0]["run_id"]==path.stem})
    report={"historical_five":aggregate(results[:5]),"additional_twelve":aggregate(results[5:]),"all_seventeen":aggregate(results),
            "cases":results,"exact_unnoted_coverage":coverage,
            "scope":"17 note-relevance labels plus 6 exact-ID coverage cases. New labels are explicit local judgments, not a blind external benchmark. No tuning after scoring."}
    Path("reports/final").mkdir(exist_ok=True,parents=True)
    Path("reports/final/retrieval.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="cases"},indent=2))
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## demonstrate_final.py

**Absolute path:** `D:\Agentic_ai_rag projects\demonstrate_final.py`

**Purpose:** Six requested user journeys and real investigation artifact producer.

Runs exploration, conversation, RAG, investigation, approval and error journeys; --live uses actual installed models. It explicitly proves pending/rejected execution rejection and grants only development dry-run permission. It saves the full investigation and timing/event data.

**Dependencies:** `import argparse`; `import json`; `from pathlib import Path`; `import time`; `from assistant import ResearchAssistant`; `from v2_state import SessionState`; `from v3.experiment_executor import execute`; `from v3.investigation_state import ROOT`.

**Main symbols and input contracts:**

- `main()` — source line 14.

**Who references this selected routine:** app.py, evaluate_final.py, evaluate_final_retrieval.py, investigate.py, phase0.py, tests/test_final.py, tests/test_v3.py, v3/cli.py, v3/training_worker.py, validate_final_ui.py, verify_final.py.

**What the selected routine calls:** `(out / 'investigation.json').write_text`, `(out / 'investigation.md').write_text`, `(out / 'journeys.json').write_text`, `AssertionError`, `ResearchAssistant`, `SessionState`, `app.ask`, `app.investigator.decide`, `argparse.ArgumentParser`, `ask`, `blocked.append`, `execute`, `investigation.get`, `json.dumps`, `out.mkdir`, `parser.add_argument`, `parser.parse_args`, `print`, `r.get`, `results.append`, `round`, `session.clear`, `store.decide`, `store.proposal`, `time.monotonic`.

**Error/control boundaries:** `AssertionError('Unapproved/rejected execution was not blocked')`.

Actual source: `demonstrate_final.py:14`–`53`; excerpt of `main` (remaining lines, if any, are not reproduced here).

```python
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--live",action="store_true",help="use installed Ollama and cached MiniLM; training still dry-run only")
    args=parser.parse_args()
    out=ROOT/"reports/final"
    out.mkdir(exist_ok=True,parents=True)
    app=ResearchAssistant()
    session=SessionState()
    results=[]
    def ask(journey,question):
        started=time.monotonic()
        r=app.ask(question,session,offline=not args.live,semantic=args.live)
        assert r["status"]!="failed",r.get("last_error")
        results.append({"journey":journey,"question":question,"status":r["status"],"answer":r["answer"],
                        "elapsed_seconds":round(time.monotonic()-started,3),"trace":r["trace"]})
        print("PASS",journey,question,r["status"],flush=True)
        return r
    ask("1 Exploration","What experiments do we have?")
    ask("1 Exploration","Which had the best final validation accuracy?")
    curves=ask("1 Exploration","Show its training and validation curves.")
    assert curves["tool_results"][0][0]=="plot_run_metrics"
    session.clear()
    ask("2 Conversation","Tell me about lr_01_seed3.")
    ask("2 Conversation","Compare that run with lr_005_seed3.")
    mechanism=ask("2 Conversation","Why might the difference exist?")
    assert "Relevant ML knowledge" in mechanism["answer"]
    session.clear()
    rag=ask("3 RAG","Have we seen unstable validation-loss behavior before?")
    assert {name for name,_ in rag["tool_results"]}>={"search_notes","get_experiment"}
    session.clear()
    investigation=ask("4 Investigation",INVESTIGATION)
    assert investigation["status"]=="awaiting_approval",investigation.get("last_error")
    store=app.investigator.store
    p=store.proposal(investigation["proposal_id"])
    blocked=[]
    for decision in ("pending","rejected"):
        if decision=="rejected":store.decide(p["id"],p["hash"],"rejected",actor="development_dry_run")
        try:execute(store,p["id"],p["hash"],"dry_run")
        except PermissionError:blocked.append(decision)
        else:raise AssertionError("Unapproved/rejected execution was not blocked")
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## validate_final_ui.py

**Absolute path:** `D:\Agentic_ai_rag projects\validate_final_ui.py`

**Purpose:** Integrated UI widget and result verification.

Uses Streamlit AppTest with isolated SQLite state, exercises all four navigation areas, comparison/filter/chat references, research creation/resume, dry-run approval and export. It does not inspect browser screenshots or start real training.

**Dependencies:** `import json`; `from pathlib import Path`; `import tempfile`; `from unittest.mock import patch`; `from streamlit.testing.v1 import AppTest`; `from assistant import ResearchAssistant`; `from v3.investigation_state import ROOT`.

**Main symbols and input contracts:**

- `main()` — source line 11.

**Who references this selected routine:** app.py, demonstrate_final.py, evaluate_final.py, evaluate_final_retrieval.py, investigate.py, phase0.py, tests/test_final.py, tests/test_v3.py, v3/cli.py, v3/training_worker.py, verify_final.py.

**What the selected routine calls:** `'\n'.join`, `(Path(folder) / 'reports').glob`, `AppTest.from_file`, `AppTest.from_file(str(ROOT / 'ui.py'), default_timeout=90).run`, `Path`, `Path('reports/final').mkdir`, `Path('reports/final/ui.json').write_text`, `ResearchAssistant`, `app.investigator.store.load`, `checks.append`, `json.dumps`, `len`, `list`, `next`, `next((b for b in ui.button if b.label == 'Approve dry run')).click`, `next((b for b in ui.button if b.label == 'Approve dry run')).click().run`, `next((b for b in ui.button if b.label == 'Resume saved investigation')).click`, `next((b for b in ui.button if b.label == 'Resume saved investigation')).click().run`, `next((b for b in ui.button if b.label == 'Save report locally')).click`, `next((b for b in ui.button if b.label == 'Save report locally')).click().run`, `next((b for b in ui.button if b.label == 'Start investigation')).click`, `next((b for b in ui.button if b.label == 'Start investigation')).click().run`, `patch`, `print`, `str`, `tempfile.TemporaryDirectory`, `ui.chat_input[0].set_value`, `ui.chat_input[0].set_value('Compare that run with lr_005_seed3.').run`, `ui.chat_input[0].set_value('Tell me about lr_01_seed3.').run`, `ui.checkbox[0].uncheck`, `ui.checkbox[1].uncheck`, `ui.selectbox[0].set_value`, `ui.selectbox[0].set_value(0.05).run`, `ui.selectbox[2].set_value`, `ui.selectbox[2].set_value('lr_005_seed3').run`, `ui.sidebar.checkbox[0].check`, `ui.sidebar.checkbox[1].uncheck`, `ui.sidebar.radio[0].set_value`, `ui.sidebar.radio[0].set_value('AI Chat').run`, `ui.sidebar.radio[0].set_value('Experiment Explorer').run`, `ui.sidebar.radio[0].set_value('Investigations').run`.

**Error/control boundaries:** Delegated exceptions propagate to the service/UI/CLI boundaries described above; absence of an explicit raise is not absence of failure.

Actual source: `validate_final_ui.py:11`–`50`; excerpt of `main` (remaining lines, if any, are not reproduced here).

```python
def main():
    checks=[]
    with tempfile.TemporaryDirectory(dir=ROOT/".tmp",prefix="final-ui-") as folder:
        app=ResearchAssistant(Path(folder)/"state.sqlite3")
        with patch("assistant.ResearchAssistant",return_value=app), patch("v3.ui.Investigator",return_value=app.investigator):
            ui=AppTest.from_file(str(ROOT/"ui.py"),default_timeout=90).run()
            assert not ui.exception,ui.exception
            assert len(ui.metric)==4
            checks.append("Overview statistics and model status render")
            ui.sidebar.radio[0].set_value("Experiment Explorer").run()
            assert not ui.exception,ui.exception
            checks.append("Experiment catalog and per-epoch charts render")
            ui.selectbox[2].set_value("lr_005_seed3").run()
            assert not ui.exception,ui.exception
            checks.append("Two-run comparison settings and visualizations render")
            ui.selectbox[0].set_value(0.05).run()
            assert not ui.exception,ui.exception
            checks.append("Exact learning-rate filter works")
            ui.sidebar.radio[0].set_value("AI Chat").run()
            ui.sidebar.checkbox[0].check()
            ui.sidebar.checkbox[1].uncheck()
            ui.chat_input[0].set_value("Tell me about lr_01_seed3.").run()
            assert not ui.exception,ui.exception
            assert "71.45" in ui.session_state.chat_entries[-1]["answer"]
            checks.append("Chat renders measured answer and expandable tool trace")
            ui.chat_input[0].set_value("Compare that run with lr_005_seed3.").run()
            assert not ui.exception,ui.exception
            assert "4.45" in ui.session_state.chat_entries[-1]["answer"]
            checks.append("Conversational comparison reference resolves")
            ui.sidebar.radio[0].set_value("Investigations").run()
            assert not ui.exception,ui.exception
            # The initial stored direct answers do not have a plan; create research from its form.
            ui.checkbox[0].uncheck()
            ui.checkbox[1].uncheck()
            next(b for b in ui.button if b.label=="Start investigation").click().run()
            assert not ui.exception,ui.exception
            checks.append("Investigation creation displays plan, evidence and hypotheses")
            next(b for b in ui.button if b.label=="Resume saved investigation").click().run()
            assert not ui.exception,ui.exception
            checks.append("Resume preserves the approval boundary")
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## tests/test_final.py

**Absolute path:** `D:\Agentic_ai_rag projects\tests\test_final.py`

**Purpose:** Integrated final user journeys and failure-boundary scenarios.

Isolates SQLite state for each scenario and exercises exact ranking, single/pair/corresponding references, ambiguity/reset, unknown IDs, local scope, single/no-ID proposal discovery, model failure, cancellation and active-execution limits. Live training is mocked or prevented.

**Dependencies:** `from pathlib import Path`; `import subprocess`; `import tempfile`; `import unittest`; `from unittest.mock import patch`; `from assistant import ResearchAssistant`; `from experiment_data import RUNS_DIR, load_run`; `from v2_state import SessionState`; `from v2_tools import execute_tool`; `from v3.experiment_executor import execute`; `from v3.investigation_state import ROOT`; `from v3.retrieval import knowledge, search_notes`.

**Main symbols and input contracts:**

- `FinalApplicationTests` — source line 17.

**Who references this selected routine:** Entry-point/framework callbacks or method dispatch; inspect the runtime trace for the actual caller.

**What the selected routine calls:** `OSError`, `Path`, `Path(progress['logs'][0]).exists`, `RUNS_DIR.glob`, `ResearchAssistant`, `SessionState`, `any`, `app.cancel`, `app.decide`, `app.store.claim_execution`, `app.store.decide`, `app.store.proposal`, `execute`, `execute_tool`, `knowledge`, `len`, `list`, `load_run`, `max`, `observed.append`, `patch`, `proposals.append`, `r.get`, `range`, `search.assert_not_called`, `self.addCleanup`, `self.app.ask`, `self.app.investigator.store.list`, `self.ask`, `self.assertEqual`, `self.assertIn`, `self.assertRaises`, `self.assertTrue`, `self.session.clear`, `set`, `sorted`, `subprocess.CalledProcessError`, `tempfile.TemporaryDirectory`, `trainer.assert_not_called`.

**Error/control boundaries:** `subprocess.CalledProcessError(1, 'CANCEL_FIXTURE')`.

Actual source: `tests/test_final.py:17`–`56`; excerpt of `FinalApplicationTests` (remaining lines, if any, are not reproduced here).

```python
class FinalApplicationTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(dir=ROOT / ".tmp", prefix="final-tests-")
        self.addCleanup(self.folder.cleanup)
        self.app = ResearchAssistant(Path(self.folder.name) / "state.sqlite3")
        self.session = SessionState()

    def ask(self, question):
        return self.app.ask(question, self.session, offline=True, semantic=False)

    def test_catalog_discovery_without_ids(self):
        r = self.ask("What experiments do we have?")
        self.assertEqual(len(r["tool_results"][0][1]["matches"]), len(list(RUNS_DIR.glob("*.json"))))

    def test_best_then_curve_journey(self):
        r = self.ask("Which had the best final validation accuracy?")
        best = max((load_run(p.stem) for p in RUNS_DIR.glob("*.json")), key=lambda x:x["metrics"][-1]["val_accuracy"])
        self.assertEqual(self.session.focused_run_id, best["config"]["run_id"])
        r = self.ask("Show its training and validation curves.")
        self.assertEqual(r["tool_results"][0][0], "plot_run_metrics")
        self.assertEqual(len(r["tool_results"][0][1]["points"]), len(best["metrics"]))

    def test_pair_reference_and_mechanism_journey(self):
        self.ask("Tell me about lr_01_seed3.")
        self.ask("Compare that run with lr_005_seed3.")
        r = self.ask("Why might the difference exist?")
        self.assertIn("lr_01_seed3", r["resolved_question"])
        self.assertIn("lr_005_seed3", r["resolved_question"])
        self.assertIn("Relevant ML knowledge", r["answer"])
        self.assertIn("4.45 percentage points", r["answer"])

    def test_corresponding_rate_uses_recorded_controls(self):
        self.ask("Show me the best learning-rate-0.1 experiment.")
        anchor = self.session.focused_run_id
        r = self.ask("Compare it with the corresponding learning-rate-0.05 experiment.")
        p = r["tool_results"][0][1]
        self.assertEqual(load_run(p["target_run_id"])["config"]["learning_rate"],0.05)
        self.assertEqual(set(p["changed_settings"]), {"learning_rate"})
        self.assertIn(anchor, r["resolved_question"])
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## tests/test_v3.py

**Absolute path:** `D:\Agentic_ai_rag projects\tests\test_v3.py`

**Purpose:** Preserved scientific workflow, approval, persistence and fixture scenarios.

Retains the original 56 checks over real saved data plus labeled in-memory fixtures. It verifies numerical comparison, missing controls, confounding, source grounding, proposal constraints, permission bypasses, resume/recovery, failure/timeout and post-experiment updates without publishing synthetic measurements.

**Dependencies:** `from copy import deepcopy`; `import json`; `from pathlib import Path`; `import subprocess`; `import tempfile`; `import unittest`; `from unittest.mock import patch`; `from experiment_data import load_run`; `from langgraph.types import Command`; `from v2_state import SessionState`; `from v2_tools import execute_tool`; `from v3.analysis import check_record, compare_records`; `from v3.demo import QUESTION`; `from v3.experiment_designer import validate_config, validate_proposal`; `from v3.experiment_executor import evaluate_outcomes, execute, ingest_record`; `from v3.hypothesis import validate_evidence`; `from v3.investigation_graph import investigation_graph`; `from v3.investigation_state import ROOT, digest`; `from v3.planner import classify, make_plan`; `from v3.retrieval import knowledge, search_notes, tokens`; `from v3.service import Investigator`.

**Main symbols and input contracts:**

- `InvestigatorTests` — source line 27.

**Who references this selected routine:** Entry-point/framework callbacks or method dispatch; inspect the runtime trace for the actual caller.

**What the selected routine calls:** `(ROOT / '.tmp').mkdir`, `Command`, `Investigator`, `Investigator(self.db).resume`, `OSError`, `Path`, `Path(result['logs'][0]).is_file`, `SessionState`, `ValueError`, `all`, `analyze`, `any`, `check_record`, `classify`, `compare_records`, `d.get`, `d['hypotheses'][0]['supporting_experiment_evidence'].append`, `d['report'].lower`, `deepcopy`, `dict`, `evaluate_outcomes`, `execute`, `execute_tool`, `fixtures.append`, `float`, `graph.invoke`, `graph.update_state`, `ingest_record`, `ingested.append`, `investigation_graph`, `k.startswith`, `kinds.index`, `len`, `list`, `load_run`, `make_plan`, `next`, `notes.assert_not_called`, `p['payload']['runs'][0].update`, `p['payload']['runs'][1].update`, `patch`, `record['metrics'].pop`, `reopened.decide`, `reopened.resume`, `reopened.store.load`, `round`, `search_notes`, `self.addCleanup`, `self.app._config`, `self.app.decide`, `self.app.modify`, `self.app.start`, `self.app.store.claim_execution`, `self.app.store.create`, `self.app.store.decide`, `self.app.store.execution_result`, `self.app.store.list`, `self.app.store.proposal`, `self.app.store.save`, `self.assertEqual`, `self.assertFalse`, `self.assertGreater`, `self.assertGreaterEqual`, `self.assertIn`, `self.assertLess`, `self.assertNotEqual`, `self.assertNotIn`, `self.assertRaises`, `self.assertRaisesRegex`, `self.assertTrue`, `self.proposal`, `self.start`, `self.subTest`, `session.clear`, `session.resolve`, `subprocess.CalledProcessError`, `subprocess.TimeoutExpired`, `tempfile.TemporaryDirectory`, `tokens`, `trainer.assert_not_called`, `v2.assert_called_once`, `v2.assert_not_called`, `validate_evidence`, `validate_proposal`, `x.get`, `zip`.

**Error/control boundaries:** Delegated exceptions propagate to the service/UI/CLI boundaries described above; absence of an explicit raise is not absence of failure.

Actual source: `tests/test_v3.py:27`–`66`; excerpt of `InvestigatorTests` (remaining lines, if any, are not reproduced here).

```python
class InvestigatorTests(unittest.TestCase):
    def setUp(self):
        (ROOT / ".tmp").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="v3-tests-", dir=ROOT / ".tmp")
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "state.sqlite3"
        self.app = Investigator(self.db)

    def start(self):
        d = self.app.start(QUESTION, model_enabled=False, semantic=False)
        self.assertEqual(d["status"], "awaiting_approval", d.get("last_error"))
        return d

    def proposal(self):
        d = self.start()
        return d, self.app.store.proposal(d["proposal_id"])

    def test_01_exact_numeric_difference(self):
        pair = compare_records(load_run("lr_005_seed3"), load_run("lr_01_seed3"))
        self.assertEqual(pair["accuracy_delta_pp"], -4.45)
        self.assertEqual(round(pair["loss_delta"], 4), 0.1303)

    def test_02_controlled_pair_checks_every_field(self):
        pair = compare_records(load_run("lr_005_seed3"), load_run("lr_01_seed3"))
        self.assertTrue(pair["controlled_learning_rate_pair"])
        self.assertEqual(list(pair["changed_settings"]), ["learning_rate"])
        self.assertEqual(pair["missing_controls"], [])

    def test_03_missing_historical_controls_not_assumed(self):
        pair = compare_records(load_run("lr_005_seed2"), load_run("lr_01_seed2"))
        self.assertFalse(pair["controlled_learning_rate_pair"])
        self.assertIn("dropout", pair["missing_controls"])
        self.assertIn("validation_start", pair["missing_controls"])

    def test_04_confounded_comparison(self):
        a, b = load_run("lr_005_seed3"), load_run("lr_01_seed3")
        b["config"]["dropout"] = 0.5
        pair = compare_records(a, b)
        self.assertTrue(pair["confounded"])
        self.assertFalse(pair["controlled_learning_rate_pair"])
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## verify_final.py

**Absolute path:** `D:\Agentic_ai_rag projects\verify_final.py`

**Purpose:** Final data, artifact, document and launch acceptance check.

Verifies original data hashes, recorded tests/UI/compatibility/journeys, actual model events, dry-run completion, absence of new training records, all four documents, thirty chapters and embedded source/hash integrity. It reads the local Streamlit health endpoint and records COMPLETE only if every supported-scope check passes.

**Dependencies:** `import hashlib`; `import json`; `from pathlib import Path`; `import re`; `from urllib.request import urlopen`.

**Main symbols and input contracts:**

- `main()` — source line 11.

**Who references this selected routine:** app.py, demonstrate_final.py, evaluate_final.py, evaluate_final_retrieval.py, investigate.py, phase0.py, tests/test_final.py, tests/test_v3.py, v3/cli.py, v3/training_worker.py, validate_final_ui.py.

**What the selected routine calls:** `(ROOT / 'docs' / n).is_file`, `(ROOT / 'docs' / n).stat`, `(ROOT / 'docs/FINAL_COMPLETE_LEARNING_GUIDE.md').read_text`, `(ROOT / 'docs/FINAL_PROJECT_MASTER_CONTEXT.md').read_text`, `(ROOT / 'docs/FINAL_PROJECT_MASTER_CONTEXT.md').stat`, `(ROOT / 'reports/final/acceptance.json').write_text`, `(ROOT / 'runs').glob`, `(ROOT / p).read_bytes`, `(ROOT / p).read_text`, `(ROOT / p).read_text(encoding='utf-8').rstrip`, `(ROOT / path).read_text`, `(ROOT / x['path']).read_bytes`, `all`, `any`, `checks.values`, `e.get`, `hashlib.sha256`, `hashlib.sha256((ROOT / p).read_bytes()).hexdigest`, `hashlib.sha256((ROOT / x['path']).read_bytes()).hexdigest`, `json.dumps`, `json.loads`, `len`, `list`, `load`, `master.startswith`, `print`, `r['journey'].split`, `re.findall`, `re.search`, `set`, `urlopen`.

**Error/control boundaries:** Delegated exceptions propagate to the service/UI/CLI boundaries described above; absence of an explicit raise is not absence of failure.

Actual source: `verify_final.py:11`–`49`; excerpt of `main` (remaining lines, if any, are not reproduced here).

```python
def main():
    def load(path):return json.loads((ROOT/path).read_text(encoding="utf-8"))
    deterministic=load("reports/final/deterministic.json")
    ui=load("reports/final/ui.json")
    compatibility=load("reports/final/compatibility.json")
    journeys=load("reports/final/journeys.json")
    investigation=load("reports/final/investigation.json")
    manifest=load("reports/v3_original_data_manifest.json")
    unchanged=all(hashlib.sha256((ROOT/x["path"]).read_bytes()).hexdigest()==x["sha256"] for x in manifest)
    from docs.build_final_docs import COMPONENTS
    master=(ROOT/"docs/FINAL_PROJECT_MASTER_CONTEXT.md").read_text(encoding="utf-8")
    guide=(ROOT/"docs/FINAL_COMPLETE_LEARNING_GUIDE.md").read_text(encoding="utf-8")
    documents=["FINAL_COMPLETE_LEARNING_GUIDE.md","FINAL_CODE_WALKTHROUGH.md","FINAL_END_TO_END_TRACE.md","FINAL_PROJECT_MASTER_CONTEXT.md"]
    source_embedded=all((ROOT/p).read_text(encoding="utf-8").rstrip() in master for p in COMPONENTS)
    hash_embedded=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest() in master for p in COMPONENTS)
    with urlopen("http://127.0.0.1:8501/_stcore/health",timeout=5) as response:health=response.status==200
    checks={"original_data_unchanged":unchanged,"main_application_health":health,
            "deterministic_scenarios_pass":deterministic["passed"]==deterministic["tests_run"] and deterministic["failures"]==0,
            "unified_ui_checks_pass":ui["passed"]==10,
            "compatibility_and_process_restart_pass":compatibility["passed"]==compatibility["total"],
            "all_six_journeys_recorded":{r["journey"].split()[0] for r in journeys["results"]}==set("123456"),
            "real_local_model_trace":investigation["model_enabled"] and any(e.get("origin")=="LLM" for e in investigation["trace"]),
            "dry_run_completed":investigation["status"]=="dry_run_completed" and not investigation["execution"]["ingested"],
            "no_new_training_records":not list((ROOT/"runs").glob("v3_*.json")),
            "all_four_documents_exist":all((ROOT/"docs"/n).is_file() and (ROOT/"docs"/n).stat().st_size>10000 for n in documents),
            "thirty_learning_chapters":len(re.findall(r"^## Chapter \d+",guide,re.M))==30,
            "master_begins_with_architecture":master.startswith("# ML Experiment Detective") and "## Architecture and purpose" in master[:300],
            "actual_core_sources_embedded":source_embedded,
            "actual_core_source_hashes_match":hash_embedded,
            "no_unexpanded_code_placeholders":not re.search(r"^<!-- CODE [^\n]+ -->$",master,re.M)}
    report={"status":"COMPLETE" if all(checks.values()) else "PARTIAL","checks":checks,
            "scope":"Completed local application and learning package; live training explicitly unverified pending user approval.",
            "deterministic_passed":deterministic["passed"],"ui_checks_passed":ui["passed"],
            "live_training_verified":False,"browser_visual_inspection_performed":False,
            "master_bytes":(ROOT/"docs/FINAL_PROJECT_MASTER_CONTEXT.md").stat().st_size,
            "investigation_id":investigation["investigation_id"]}
    (ROOT/"reports/final/acceptance.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))
    assert all(checks.values()),checks
```

**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.

## Non-obvious implementation lines

### v2_tools.py:86

```python
if kind == "integer" and (not isinstance(value, int) or isinstance(value, bool) or value < 1):
```

Python booleans inherit from int, so explicit exclusion prevents True from being accepted as an integer count or seed.

### phase0.py:36

```python
total_loss += loss.item() * len(labels)
```

Weights each batch loss by its actual size, preserving the dataset mean when the last batch is short.

### v3/investigation_state.py:115

```python
db.execute("BEGIN IMMEDIATE")
```

Serializes the read/check/write permission transition so concurrent requests cannot both consume one approval.

### v3/investigation_graph.py:181

```python
token = interrupt({"proposal_id": p["id"], "hash": p["hash"], "message": "Inspect the proposal and explicitly approve dry_run/live, reject, modify, or defer."})
```

Durably suspends the graph. The node restarts when resumed; resource-consuming effects must occur after decision verification.

### v3/experiment_executor.py:82

```python
cwd=ROOT, env=environment, shell=False, stdout=stream,
```

Runs a fixed argument list instead of interpreting model text as shell code.

### v3/experiment_executor.py:79

```python
with log.open("x", encoding="utf-8") as stream:
```

Exclusive creation prevents overwriting an existing log from an earlier execution attempt.

### v3/experiment_designer.py:52

```python
if proposal.get("training_code_sha256") != trainer_hash():
```

Binds a proposal to the reviewed trainer implementation as well as parameter settings.

### v3/retrieval.py:87

```python
def within_source(ranks):
```

Adding derived summaries must not silently perturb human-note rank positions; source priority is part of the measured ranking policy.

### v3/ui.py:116

```python
st.session_state.execution_future = pool.submit(app.decide, identifier, row["hash"], decision, mode="live")
```

Runs only an explicitly approved live decision in the background so UI refresh/cancellation remain possible.

### phase0.py:99

```python
if cancel_path is not None and Path(cancel_path).exists():
```

Cancellation is checked between training batches; a marker does not interrupt every possible native operation instantly.

## Historical references and evaluations

`simple_agent.py` preserves the original native-tool reference; `legacy_ui.py` preserves the former UI; `validate_v2.py`, `evaluate_retrieval.py` and research validation scripts retain earlier checks. Old packet/prompt/hypothesis/planning scripts are educational standalone commands, not extra active services. Their presence is intentional preservation, not a requirement to execute all of them for one chat turn.

`tests/test_v3.py` contains retained core scenarios and `tests/test_final.py` adds integrated journeys and missing boundaries. `evaluate_final.py` records both. `validate_final_ui.py` drives real Streamlit widgets with isolated state. `evaluate_final_retrieval.py` contains actual relevance labels/reasons and scores. `demonstrate_final.py` records real-model journeys and dry-run proof.
