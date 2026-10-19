# ML Experiment Detective V2 — complete implementation context

Technical snapshot of the repository at `D:\Agentic_ai_rag projects`, inspected on 2026-10-04. This file is intended to stand alone for an AI tutor. It describes implemented behavior and the saved validation evidence, rather than an intended architecture. File paths below are relative to that project root unless an absolute installation path is given.

## 1. Current project architecture

```text
USER
  |
  +--> app.py (CLI: manual default / graph / simple V1)
  |       owns one process-local SessionState for V2 turns
  |
  +--> ui.py (Streamlit: manual / graph)
          owns SessionState and chat entries in st.session_state
                  |
                  v
     V2 prepare_turn: resolve simple references; assemble system,
     bounded prior user/assistant messages, current user message;
     select a small initial tool menu
                  |
          +-------+-------+
          |               |
     v2_agent.py      graph_agent.py
     explicit for      START -> agent -> tools -> agent
     loop              or agent -> final -> END
          |               |
          +-------+-------+
                  |
                  v
     ask_ollama -> local Ollama /api/chat -> qwen3:1.7b
     model can return a tool_calls array; app policy can fill required
     steps if it returns no call
                  |
                  v
     execute_call -> v2_tools.execute_tool: menu check, argument
     correction/validation, one Python handler
          |                |                     |
          v                v                     v
     experiment_data   v2_retrieval          v2_analysis
     runs/*.json       notes/*.md ->         runs/*.json ->
     exact lookup      keyword + MiniLM      curve/group/chart
     and filters       -> RRF -> optional    calculations
                      CrossEncoder
                      knowledge/*.md -> separate ML-knowledge retrieval
                  |
                  v
     tool result + synthetic assistant/tool messages -> next Ollama call
                  |
                  v
     v2_answers.render_answer: deterministic Markdown from successful
     Python results -> observed facts / general ML knowledge /
     possible interpretation / limitations / source paths and URLs
                  |
                  v
     SessionState.remember -> trace MEMORY AFTER and FINAL -> CLI or UI
```

**Three modes:** `simple_agent.py` is the preserved V1 agent. Its four tools include semantic-only `search_notes`; it has its own explicit loop and no V2 session state. `v2_agent.py` is the new *manual* V2 loop with nine shared tools. `graph_agent.py` expresses that same V2 policy and handlers as LangGraph nodes and edges. The graph is orchestration, not a different model or evidence source. The CLI exposes all three; the UI exposes manual and graph.

**Trust boundaries:** `runs/*.json` supplies measured numbers. `notes/*.md` are search clues tied to run IDs, not independent logs. `knowledge/*.md` supplies general, attributed ML explanations, not evidence of a particular run's cause. Python validates arguments, computes arithmetic, and renders the final answer. The local LLM's returned prose is *not* used as the final factual answer; its useful output is a selected tool call. A visible `APP POLICY` can call a required tool when the small model stops early.

## 2. File map and call relationships

| Actual path | Purpose and important names | Calls / reads | Called by |
| --- | --- | --- | --- |
| `app.py` | CLI `main`; `--agent manual/graph/simple`, `--question`, `--no-trace`, `--rerank`, `clear` | `run_manual`, `run_graph`, V1 `answer_question`, `SessionState` | User's Python command |
| `ui.py` | Streamlit chat, sidebar, run detail, chart, expandable trace | `run_manual`/`run_graph`, `SessionState`, `get_experiment`, `plot_run_metrics` | Streamlit server |
| `v2_agent.py` | `prepare_turn`, `available_tool_names`, `ask_ollama`, `policy_call`, `execute_call`, `finish_turn`, `run_manual`, `print_trace` | state, shared tool registry, renderer, V1's `explicit_run_filters`, local Ollama HTTP API | CLI, UI, `graph_agent.py`, validation |
| `v2_state.py` | `SessionState`, `mentioned_run_ids`, `MAX_TURNS=4` | `RUNS_DIR` to recognize IDs | V2 agent, CLI, UI, graph, validation |
| `v2_tools.py` | Nine Ollama tool schemas, `HANDLERS`, `execute_tool`, `tool_menu` | exact data, retrieval, analysis functions | Both V2 agents through `v2_agent.py` |
| `v2_retrieval.py` | `hybrid_search_notes`, `_reranker`, `_knowledge_chunks`, `search_ml_knowledge` | `note_retrieval.py`, `notes/*.md`, `knowledge/*.md`, D: model cache | `v2_tools.py`, retrieval evaluation |
| `v2_analysis.py` | `summarize_run_curve`, `find_overfitting_candidates`, `compare_run_group`, `plot_run_metrics` | `experiment_data.load_run` and `RUNS_DIR` | `v2_tools.py`; UI directly calls plot data |
| `v2_answers.py` | `render_answer` builds source-aware Markdown from successful tool results | Result dictionaries; no LLM or filesystem reads | `v2_agent.finish_turn`, therefore both V2 modes |
| `graph_agent.py` | `GraphState`, `agent_node`, `route_after_agent`, `tools_node`, `final_node`, `build_graph`, `run_graph` | Reuses `v2_agent.py` helpers and `tool_menu` | CLI, UI, validation |
| `experiment_data.py` | `load_run`, `get_experiment`, `compare_experiments`, `search_runs`, `largest_rise`, `loss_recoveries` | `runs/*.json` | tools, analysis, UI, validation |
| `note_retrieval.py` | `load_notes`, `words`, `keyword_rank`, cached `_embedding_model`, `encode_queries_and_notes`, `cosine_similarity`, `semantic_rank` | `notes/*.md`, local MiniLM cache | V2 retrieval, V1 agent, evaluation |
| `simple_agent.py` | Independent preserved V1 loop, semantic-only note search, `explicit_run_filters` | exact data, note retrieval, Ollama | `app.py`; filter helper reused by V2 |
| `requirements.txt` | Pinned direct Python dependencies | sentence-transformers 6.1.0, Streamlit 1.65.0, LangGraph 1.2.12 | Environment setup |
| `knowledge/*.md` | Five local, attributed general ML chunks | Official source URLs recorded in each file | `_knowledge_chunks` |
| `runs/*.json` | Eleven saved Fashion-MNIST experiment records: config and epoch metrics | No application imports; read as data | `experiment_data.py`; analysis indirectly |
| `notes/*.md` | Five run-linked observation notes | Each note has an `Observation: ` field | `note_retrieval.load_notes` |
| `evaluate_retrieval.py` + `retrieval_eval_cases.json` | Five labeled note-search cases, Recall@2 and MRR@2 for four rankings | V2 retrieval | Manual evaluation command |
| `validate_v2.py` + `reports/v2_validation_traces.json` | Seventeen saved integration cases and full events | Both V2 agents, exact data | Manual validation command |
| `docs/V2_ARCHITECTURE.md`, `MEMORY.md`, `HYBRID_RAG.md`, `EXTERNAL_KNOWLEDGE_RAG.md`, `MANUAL_VS_LANGGRAPH.md`, `V2_COMPLETE_TRACE.md`, `STUDY_V2.md` | Focused V2 explanations; this document consolidates their technical context | Current code and trace | Reader |
| `README.md`, `OLLAMA_SETUP.md` | Entry commands and local Ollama setup | Project configuration | Reader |

The eleven run IDs are `baseline_001`, `baseline_gap_001`, `lr_001`, `lr_005_gap_001`, `lr_005_seed2`, `lr_005_seed3`, `lr_01_seed2`, `lr_01_seed3`, `lr_gap_001`, `small_dropout_05_001`, and `small_no_dropout_001`. Only five have observation notes: `baseline_gap_001`, `lr_005_gap_001`, `lr_01_seed2`, `small_dropout_05_001`, and `small_no_dropout_001`. A note search cannot retrieve a note for every saved run.

## 3. Important real code excerpts

Each excerpt below is from the named current source file. Some functions have separate excerpts; omitted surrounding lines are explained in prose rather than represented as executable code.

### 3.1 CLI entry and agent selection — `app.py`

```python
parser.add_argument("--question", help="ask one question and exit")
parser.add_argument("--no-trace", action="store_true", help="hide tool requests and results")
parser.add_argument("--agent", choices=("manual", "graph", "simple"), default="manual")
parser.add_argument("--rerank", action="store_true", help="opt in to the cached cross-encoder reranker")
args = parser.parse_args()

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
            continue
```

**What it does:** The parser selects V2 manual by default and creates one session for the interactive process. **Why it exists:** Several user turns can share a focused run ID; a one-question `--question` invocation exits after one answer. **How it connects:** Later in `main`, `simple` calls `answer_simple(question, trace=...)`; `manual` calls `run_manual(question, session, rerank=...)`; `graph` imports and calls `run_graph`. `print_trace` displays V2 events unless `--no-trace` was given.

### 3.2 Session structure and reference resolution — `v2_state.py`

```python
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
```

**What it does:** Recognizes only IDs that correspond to saved JSON stems and replaces the first simple singular reference with the focused ID. **Why it exists:** “that run” can be used after a prior run question. **How it connects:** `prepare_turn` calls `resolve` before routing or sending the question to Ollama. This resolution is rule-based; the LLM does not perform it.

### 3.3 Bounded prior messages and memory update — `v2_state.py`

```python
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
```

**What it does:** At most four previous user/assistant pairs become eight Ollama messages, with per-field character limits. **Why it exists:** It retains useful context without sending the entire growing trace. **How it connects:** `prepare_turn` puts these messages between its system prompt and the current resolved user message. `remember` stores each turn's original and resolved question, answer, tool decisions, and run IDs; then truncates `turns` to four. It also tracks up to eight recent referenced IDs and updates `focused_run_id` from one explicit ID, one inspected ID, or a “worst” search result. `snapshot` exposes a compact debug view; `clear` empties all three fields.

The update rule itself is important:

```python
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
```

**What it does:** Selects a focused ID when there is a clear singular target and stores the turn while trimming old turns. **Why it exists:** A later “that run” needs a concrete reference; unlimited old turns would grow context. **How it connects:** `finish_turn` calls this after deterministic rendering. The “worst” branch deliberately changes focus; a comparison with two IDs can leave an existing focus unchanged.

### 3.4 Tool schema and dispatcher — `v2_tools.py`

```python
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
```

**What it does:** `TOOLS`, omitted here because the complete nine rows are in section 9, contains JSON-schema-like declarations offered to Ollama; `HANDLERS` maps the same names to Python functions. `execute_tool` enforces allowlisting, required/extra argument checks, and simple types. **Why it exists:** The model can suggest a function and arguments but cannot directly execute arbitrary Python. **How it connects:** `ask_ollama` receives `tool_menu(names)`; `v2_agent.execute_call` invokes `execute_tool` after its own menu and policy checks.

Examples of the real schema declarations show what the model is told:

```python
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
```

**What it does:** Each declaration names a tool, describes when to use it, lists JSON argument types and required keys. **Why it exists:** Ollama needs a machine-readable menu; ordinary prose alone cannot represent a validated function call. **How it connects:** `tool_menu` sends only currently offered declarations, while `HANDLERS` maps the returned name to an implementation. The excerpt ends after two entries; the other seven are named in `HANDLERS` above and specified in section 9.

### 3.5 Ollama request — `v2_agent.py`

```python
MODEL = "qwen3:1.7b"
MAX_TOOL_CALLS = 6

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
```

**What it does:** Sends the current messages and offered tool schemas to the local Ollama server with deterministic sampling settings and returns its message object. **Why it exists:** Qwen can propose a tool call within a bounded local context. **How it connects:** Both the manual loop and graph agent call this helper. The code checks completion but does not save the raw model response in the V2 trace.

### 3.6 Choosing a narrow menu and the application fallback — `v2_agent.py`

```python
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
```

**What it does:** The menu depends on accumulated successful tool results. When Ollama returns no call, `policy_call` can require a first evidence lookup, inspect the top note's run, or fetch general ML knowledge for a “why/might/explain” question. **Why it exists:** The 1.7B model sometimes stops before collecting enough evidence. **How it connects:** Both V2 agents use these helpers. The trace marks such a call `APP POLICY`, while a real model-selected call is `AGENT`. `_first_tool_names`, before these excerpts, routes by simple wording and known run IDs: overfitting → candidate tool; two rates → group; one run plus curve/plot → chart; “seen/similar/before” → note search; two IDs → compare; one ID → exact lookup; explicit settings → structured search; general “why/might/explain/what is” → knowledge search; otherwise notes. Branch order matters. Most menus contain one tool, so this is constrained tool choice rather than open selection across all nine.

### 3.7 Tool call, argument correction, trace, and observation — `v2_agent.py`

```python
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
```

**What it does:** Checks the current menu; adjusts model-suggested IDs/filters/rerank/top-k where the app has explicit constraints; runs validated Python; records `APP FILTER`, origin, full `TOOL RESULT` and retrieval stages; appends a compact observation to Ollama messages. **Why it exists:** The model must not invent run IDs, ignore explicit numeric filters, or supply arbitrary function arguments. **How it connects:** Both V2 orchestrators call this one function. A synthetic assistant tool-call message is appended **even for APP POLICY calls** to keep the Ollama conversation well formed. The origin stored in the trace and decisions is the authoritative distinction. Only successful results enter `tool_results`; tool errors become `{"error": "..."}` observations and consume one of six tool calls.

### 3.8 Explicit manual loop and stopping — `v2_agent.py`

```python
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
```

**What it does:** Repeatedly asks Ollama, executes at most the first returned tool call, then asks again with the observation. On an empty call list it uses policy if necessary, or finishes once successful evidence exists. **Why it exists:** This is the educational agent loop without framework machinery. **How it connects:** `finish_turn` calls `render_answer`, remembers the turn, and appends `MEMORY AFTER` and `FINAL` to the trace. Six tool executions are permitted, with at most seven loop iterations; runtime errors surface to the CLI/UI.

### 3.9 Original keyword and semantic rankers — `note_retrieval.py`

```python
def words(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))

def keyword_rank(query, notes):
    query_words = words(query)
    matches = []
    for path, observation in notes:
        shared_words = query_words & words(observation)
        if shared_words:
            matches.append((len(shared_words), path, sorted(shared_words), observation))
    return sorted(matches, key=lambda match: (-match[0], match[1].stem))

@lru_cache(maxsize=2)
def _embedding_model(local_only):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(
        MODEL_ID,
        revision=MODEL_REVISION,
        cache_folder=str(PROJECT_DIR / ".model_cache"),
        local_files_only=local_only,
    )

def cosine_similarity(first, second):
    import numpy as np

    return float(np.dot(first, second) / (np.linalg.norm(first) * np.linalg.norm(second)))

def semantic_rank(query_embedding, note_embeddings, notes):
    matches = [
        (cosine_similarity(query_embedding, embedding), path, observation)
        for (path, observation), embedding in zip(notes, note_embeddings)
    ]
    return sorted(matches, key=lambda match: (-match[0], match[1].stem))
```

**What it does:** Keyword ranking counts distinct shared lowercase alphanumeric tokens; semantic ranking computes cosine similarity between one query embedding and each note embedding. `MODEL_ID` is `sentence-transformers/all-MiniLM-L6-v2`. **Why it exists:** Exact vocabulary and paraphrase similarity are useful signals with different strengths. **How it connects:** `v2_retrieval.hybrid_search_notes` reuses both functions. `load_notes` extracts text after each note's `Observation: ` marker. The keyword code has no stopword removal or stemming; for some questions, “and” contributes to rank.

### 3.10 Hybrid fusion and optional reranking — `v2_retrieval.py`

```python
RRF_K = 60
RERANKER_ID = "cross-encoder/ms-marco-MiniLM-L2-v2"
RERANKER_DIR = PROJECT_DIR / ".model_cache" / "reranker-ms-marco-MiniLM-L2-v2"

@lru_cache(maxsize=1)
def _reranker():
    if not (RERANKER_DIR / "config.json").is_file():
        raise FileNotFoundError(f"Reranker is not cached at {RERANKER_DIR}")
    from sentence_transformers import CrossEncoder

    return CrossEncoder(
        str(RERANKER_DIR), local_files_only=True, device="cpu",
    )

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
    hybrid_order = [dict(row) for row in rows]

    status = "disabled"
    if rerank:
        try:
            scores = _reranker().predict([(query, row["observation"]) for row in rows])
            for row, score in zip(rows, scores):
                row["reranker_score"] = round(float(score), 4)
            rows.sort(key=lambda row: (-row["reranker_score"], row["hybrid_rank"]))
            status = f"{RERANKER_ID} (local cache)"
        except FileNotFoundError:
            status = "model not cached; hybrid order used"
    for rank, row in enumerate(rows, 1):
        row["final_rank"] = rank
```

**What it does:** All five notes are candidates because semantic rank covers every note. Each gets `1/(60+keyword_rank)` if keyword matched, plus `1/(60+semantic_rank)`. Ties break by run ID. The optional cross-encoder scores each `(query, observation)` pair and reorders *all five current notes*; it does not create new candidates. **Why it exists:** Reciprocal Rank Fusion (RRF) combines rank positions without treating shared-word counts and cosine values as directly comparable. A cross-encoder can spend more work evaluating pairs after the cheap rankers. **How it connects:** `search_notes` in the V2 registry points to this function. Its return has `matches[:top_k]` plus `KEYWORD RESULTS`, `SEMANTIC RESULTS`, `HYBRID RESULTS`, `RERANKED RESULTS`, model ID, RRF constant, and rerank status. If the reranker file is absent, it keeps hybrid order and reports that status.

### 3.11 Separate external knowledge search — `v2_retrieval.py`

```python
def _knowledge_chunks() -> list[dict]:
    chunks = []
    for path in sorted((PROJECT_DIR / "knowledge").glob("*.md")):
        metadata, text = path.read_text(encoding="utf-8").split("Text:\n", 1)
        fields = dict(line.split(": ", 1) for line in metadata.splitlines() if ": " in line)
        chunks.append({
            "id": path.stem,
            "path": f"knowledge/{path.name}",
            "source_title": fields["Title"],
            "source_url": fields["URL"],
            "topic": fields["Topic"],
            "source_type": fields["Source-Type"],
            "text": text.strip(),
        })
    return chunks

def search_ml_knowledge(query: str, top_k: int = 2) -> dict:
    """Only curated general ML documentation; never experiment notes or run facts."""
    if not query.strip():
        raise ValueError("Search query must not be empty")
    chunks = _knowledge_chunks()
    if not 1 <= top_k <= max(1, len(chunks)):
        raise ValueError(f"top_k must be from 1 to {len(chunks)}")
    if not chunks:
        return {"query": query, "matches": []}
    note_pairs = [(Path(item["path"]), item["text"]) for item in chunks]
    embeddings = encode_queries_and_notes([query], note_pairs, local_only=True)
    ranked = semantic_rank(embeddings[0], embeddings[1:], note_pairs)
    keyword = keyword_rank(query, note_pairs)
    keyword_ranks = {path.stem: rank for rank, (_, path, _, _) in enumerate(keyword, 1)}
    by_id = {item["id"]: item for item in chunks}
    candidates = []
    for semantic_rank_number, (score, path, _) in enumerate(ranked, 1):
        keyword_rank_number = keyword_ranks.get(path.stem)
        rrf = 1 / (RRF_K + semantic_rank_number)
        if keyword_rank_number is not None:
            rrf += 1 / (RRF_K + keyword_rank_number)
        candidates.append({
            **by_id[path.stem],
            "semantic_rank": semantic_rank_number,
            "keyword_rank": keyword_rank_number,
            "cosine_similarity": round(score, 4),
            "hybrid_score": round(rrf, 6),
        })
    candidates.sort(key=lambda item: (-item["hybrid_score"], item["id"]))
    for rank, item in enumerate(candidates, 1):
        item["rank"] = rank
```

**What it does:** Parses source metadata from local Markdown, then uses keyword/MiniLM RRF on the five *general ML* chunks. **Why it exists:** A run's metrics and a possible general mechanism require distinct evidence sources. **How it connects:** The function returns `source_category="general ML knowledge"`, `ranking_method="keyword + MiniLM reciprocal rank fusion"` and `matches[:top_k]` with title, URL, topic, source type, text, ranks, cosine, and RRF score. It never reads `notes/*.md` or `runs/*.json`. Unlike note retrieval, this search has no cross-encoder reranking.

### 3.12 Exact JSON and deterministic calculations — `experiment_data.py` and `v2_analysis.py`

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

def loss_recoveries(metrics: list[dict]) -> list[dict]:
    """List consecutive validation-loss rises followed by falls."""
    patterns = []
    for before, peak, after in zip(metrics, metrics[1:], metrics[2:]):
        if before["val_loss"] < peak["val_loss"] > after["val_loss"]:
            patterns.append({
                "epochs": [before["epoch"], peak["epoch"], after["epoch"]],
                "losses": [round(row["val_loss"], 4) for row in (before, peak, after)],
            })
    return patterns
```

```python
def find_overfitting_candidates() -> dict:
    """A transparent warning: a training-loss fall with a validation-loss rise."""
    matches = []
    for path in sorted(RUNS_DIR.glob("*.json")):
        rows = load_run(path.stem)["metrics"]
        intervals = []
        for before, after in zip(rows, rows[1:]):
            a, b = before.get("train_loss_after_epoch"), after.get("train_loss_after_epoch")
            if a is None or b is None:
                continue
            if b < a and after["val_loss"] > before["val_loss"]:
                intervals.append({
                    "epochs": [before["epoch"], after["epoch"]],
                    "train_loss": [round(a, 4), round(b, 4)],
                    "validation_loss": [round(before["val_loss"], 4), round(after["val_loss"], 4)],
                })
        if intervals:
            matches.append({"run_id": path.stem, "source": f"runs/{path.name}", "intervals": intervals})
    return {
        "label": "possible overfitting candidate",
        "rule": "post-epoch training loss falls while validation loss rises over the same saved interval",
        "scope": "descriptive flag, not a diagnosis",
        "matches": matches,
    }
```

**What it does:** `load_run` checks ID syntax, file existence, embedded ID, and consecutive epochs before returning JSON. `loss_recoveries` identifies local validation-loss rise-then-fall triples. The candidate tool flags intervals where saved post-epoch training loss decreases and validation loss increases. **Why it exists:** The LLM should receive computed evidence rather than inventing trends. **How it connects:** `get_experiment` computes final percentage as `round(100 * val_accuracy, 2)`; `compare_experiments` calculates target-minus-baseline percentage points and loss deltas, and rejects different final epochs. `search_runs` filters exact config values. `summarize_run_curve` uses max/min and largest rise; `compare_run_group` uses Python `mean`/`median` and count; `plot_run_metrics` returns rows with epoch, post-epoch train loss, validation loss, and validation accuracy percent. All operate on `runs/*.json`. A flagged interval is not a diagnosis of overfitting.

The remaining analysis functions use these actual calculation lines:

```python
best_accuracy = max(rows, key=lambda row: row["val_accuracy"])
lowest_loss = min(rows, key=lambda row: row["val_loss"])
rise, from_epoch, to_epoch = largest_rise(rows)

values = [row["validation_accuracy_percent"] for row in rows]
groups[str(rate)] = {
    "count": len(rows),
    "mean_validation_accuracy_percent": round(mean(values), 2) if values else None,
    "median_validation_accuracy_percent": round(median(values), 2) if values else None,
    "runs": rows,
}

"train_loss": round(row["train_loss_after_epoch"], 4) if row.get("train_loss_after_epoch") is not None else None,
"validation_loss": round(row["val_loss"], 4),
"validation_accuracy_percent": round(100 * row["val_accuracy"], 2),
```

**What it does:** Selects best/worst curve points, aggregates group values, and converts saved fractions to percent for plot rows. **Why it exists:** These summaries must follow saved numbers, not the LLM's arithmetic. **How it connects:** The relevant V2 tool returns each calculated value and source path to the renderer or UI. These are selected lines from three functions, not one runnable function.

### 3.13 Source-aware answer rendering — `v2_answers.py`

```python
def render_answer(question: str, tool_results: list[tuple[str, dict]]) -> str:
    by_name = {}
    for name, result in tool_results:
        by_name.setdefault(name, []).append(result)
    observations = []
    experiment_sources = set()
    knowledge_sources = {}

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
```

```python
knowledge = []
for result in by_name.get("search_ml_knowledge", []):
    for match in result["matches"]:
        if match["source_url"] in knowledge_sources:
            continue
        knowledge.append(
            f"- **{match['source_title']}** ({match['topic']}): {match['text']}"
        )
        knowledge_sources[match["source_url"]] = match["source_title"]

sections = []
if observations:
    sections.append("### Observed experiment facts\n" + "\n".join(observations))
if knowledge:
    sections.append("### Relevant ML knowledge\n" + "\n".join(knowledge))
if observations and knowledge:
    sections.append(
        "### Possible interpretation\nThe observed pattern is compatible with one or more general "
        "mechanisms described above. The saved runs do not establish which mechanism, if any, caused it."
    )
```

**What it does:** Groups successful Python tool results by name and formats measured comparison numbers, inspected run facts, note-linked recovered loss values, filtered runs, curve summaries, candidate intervals, group statistics, chart availability, and general knowledge. **Why it exists:** Earlier model prose could fabricate or misstate measurements; deterministic rendering keeps figures and provenance tied to tool results. **How it connects:** `finish_turn` calls this function and then saves its text in memory. The remaining real code adds conditional limitations and separate `Experiment records and notes` file paths versus `General ML references` URLs. Note text may appear as a retrieval clue only after a corresponding run was inspected. The possible-interpretation sentence is fixed Python text, not a fresh LLM explanation; Ollama's prose is not inserted. An answer with only knowledge results has no observed-run section or possible-interpretation section.

The note-inspection gate and source split are visible in the current renderer:

```python
inspections = {item["run_id"]: item for item in by_name.get("get_experiment", [])}
for search in by_name.get("search_notes", []):
    for match in search["matches"]:
        record = inspections.get(match["run_id"])
        if record is None:
            continue
        observations.append(
            f"- **{match['run_id']}** (note rank {match['final_rank']}, "
            f"cosine {match['cosine_similarity']:.4f}): {match['observation']}"
        )
        for pattern in record["validation_loss_recoveries"]:
            epochs, losses = pattern["epochs"], pattern["losses"]
            observations.append(
                f"  - Saved validation loss, epochs {epochs[0]}->{epochs[1]}->{epochs[2]}: "
                f"{losses[0]:.4f} -> {losses[1]:.4f} -> {losses[2]:.4f}."
            )
        experiment_sources.update((match["note_source"], record["source"]))
```

**What it does:** Requires inspection of a returned run ID before showing its note, then shows JSON-derived recovery values and both file paths. **Why it exists:** A note alone should not stand in for a saved run record. **How it connects:** The agent offers `get_experiment` after `search_notes`. **Important precision:** The renderer does not independently check every numeric phrase in the note's `observation` against JSON; it checks the run ID through inspection and computes the displayed recovery subsection from JSON. A stale or mistaken note could still put a wrong sentence in the observed-facts section. Exact metrics should be read from the JSON result.

### 3.14 LangGraph state, nodes, and edges — `graph_agent.py`

```python
class GraphState(TypedDict):
    payload: dict

def agent_node(state: GraphState) -> GraphState:
    payload = state["payload"]
    names = available_tool_names(payload)
    payload["trace"].append({"kind": "TOOL MENU", "data": names})
    message = ask_ollama(payload["messages"], tool_menu(names))
    calls = message.get("tool_calls") or []
    if calls:
        if payload["tool_count"] >= MAX_TOOL_CALLS:
            raise RuntimeError("V2 graph agent reached its tool-call limit")
        payload["pending_calls"] = [
            {"name": calls[0]["function"]["name"], "arguments": calls[0]["function"]["arguments"], "origin": "AGENT"}
        ]
    else:
        needed = policy_call(payload)
        if needed and payload["tool_count"] < MAX_TOOL_CALLS:
            payload["pending_calls"] = [{"name": needed[0], "arguments": needed[1], "origin": "APP POLICY"}]
        else:
            if not payload["tool_results"]:
                raise RuntimeError("The graph model stopped before evidence was collected")
            payload["pending_calls"] = []
    return {"payload": payload}

def route_after_agent(state: GraphState) -> str:
    return "tools" if state["payload"]["pending_calls"] else "final"

def tools_node(state: GraphState) -> GraphState:
    payload = state["payload"]
    calls = payload["pending_calls"]
    payload["pending_calls"] = []
    for call in calls:
        execute_call(payload, call["name"], call["arguments"], origin=call["origin"])
    return {"payload": payload}

def final_node(state: GraphState) -> GraphState:
    payload = state["payload"]
    finish_turn(payload)
    return {"payload": payload}

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

**What it does:** Wraps the same mutable V2 payload in a `GraphState` and replaces the manual loop with `agent → tools → agent` or `agent → final → END` transitions. **Why it exists:** It teaches explicit state and edges using the same case. **How it connects:** `run_graph` calls `prepare_turn` and `GRAPH.invoke` with recursion limit `2 * MAX_TOOL_CALLS + 5`, then returns the same answer/trace/session/result shape as `run_manual`. LangGraph supplies orchestration; the app's shared helpers still make decisions and execute tools.

### 3.15 Streamlit state, trace, and charts — `ui.py`

```python
if "detective_session" not in st.session_state:
    st.session_state.detective_session = SessionState()
if "chat_entries" not in st.session_state:
    st.session_state.chat_entries = []

run_ids = sorted(path.stem for path in RUNS_DIR.glob("*.json"))
with st.sidebar:
    st.metric("Saved run records", len(run_ids))
    mode = st.radio("Agent", ("manual", "graph"), help="Both modes use the same Python tools.")
    rerank = st.checkbox("Optional cross-encoder reranking", value=False,
                        help="Hybrid order is the default. The reranker can make some searches worse.")
    selected = st.selectbox("Inspect a saved run", run_ids, index=run_ids.index("lr_01_seed3") if "lr_01_seed3" in run_ids else 0)
    chosen = get_experiment(selected)
```

```python
question = st.chat_input("Ask about an experiment or a possible ML mechanism")
if question:
    try:
        with st.spinner("Inspecting saved evidence..."):
            if mode == "manual":
                result = run_manual(question, st.session_state.detective_session, rerank=rerank)
            else:
                from graph_agent import run_graph

                result = run_graph(question, st.session_state.detective_session, rerank=rerank)
        st.session_state.chat_entries.append({
            "question": question, "answer": result["answer"], "trace": result["trace"],
        })
        st.rerun()
    except (OSError, ValueError, RuntimeError) as exc:
        st.error(f"Could not answer: {exc}")

points = pd.DataFrame(plot_run_metrics(selected)["points"])
tab_curve, tab_table, tab_memory = st.tabs(("Training and validation curves", "Epoch table", "Current session memory"))
with tab_curve:
    st.line_chart(points, x="epoch", y=["train_loss", "validation_loss"])
    st.line_chart(points, x="epoch", y="validation_accuracy_percent")
```

**What it does:** Keeps one session and displayed chat entries per browser session, switches between the same V2 runners, plots saved run metrics, and displays memory. **Why it exists:** The UI is a teaching surface for state, sources, run data, and trace inspection. **How it connects:** An expander iterates each saved trace event and calls `st.json(event["data"])`. `display_answer` converts local `runs/...` and `notes/...` Markdown links to literal paths because Streamlit does not serve those files; external URLs remain links. The sidebar's reset button calls `SessionState.clear()`, empties chat entries, and reruns. The two charts come from `plot_run_metrics` directly for the selected run, even if no chat question used the chart tool.

```python
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

**What it does:** Replays each stored answer and every non-duplicate trace event in the chat UI. **Why it exists:** The user can inspect tool origins, arguments, scores, and results rather than treating the answer as a black box. **How it connects:** `run_manual` and `run_graph` both return the same event-list shape consumed here.

## 4. Session memory and state, exactly

The state is a Python `SessionState` instance with `turns`, `focused_run_id`, and `referenced_run_ids`. Each stored turn has original `question`, `resolved_question`, full deterministic `answer`, `tool_decisions` (including `AGENT` or `APP POLICY` origin and arguments), and `run_ids`. The history used in the next model request contains at most four prior user messages and four assistant summaries, plus one system and one current user message. Each prior question is cut to 400 characters; the tool-decision text to 300; the prior answer to 700. The saved in-process answer itself is not cut. Recent referenced IDs are deduplicated after limiting the latest ID list to eight entries; the focused ID is separate. This is short-term conversation state, not a vector index or persistent user profile.

The actual `resolve` regex handles the first occurrence of `that run`, `this run`, `its`, or `it` if a focus exists, case-insensitively. It does not understand plural references or determine which of two recently compared runs “that one” means. The focus can persist through a comparison: if the previous focus is among the current referenced IDs, `remember` leaves it unchanged. For a question about the “worst” exact-filtered run, `remember` deliberately focuses the lowest-final-accuracy match so “Show me its loss curve” can work.

**Actual validated two-turn case (`E_memory_first` and `E_memory_reference`):**

| Step | Recorded value |
| --- | --- |
| Turn 1 user | `Tell me about lr_01_seed3.` |
| Turn 1 tool origin and call | `AGENT get_experiment({"run_id": "lr_01_seed3"})` |
| Turn 1 JSON result | Final validation accuracy 71.45%, loss 0.8109, epoch 5 |
| Memory after turn 1 | `focused_run_id="lr_01_seed3"`, `referenced_run_ids=["lr_01_seed3"]` |
| Turn 2 user | `Compare that run with lr_005_seed3.` |
| `MEMORY BEFORE` turn 2 | `focused_run_id_before="lr_01_seed3"`, explicit IDs `["lr_005_seed3"]`, resolved reference `"lr_01_seed3"` |
| Resolved turn 2 text | `Compare lr_01_seed3 with lr_005_seed3.` |
| Turn 2 tool origin and call | `AGENT compare_experiments({"baseline_run_id":"lr_01_seed3","target_run_id":"lr_005_seed3"})` |
| Python result | Accuracy 71.45% → 75.90%, **+4.45 percentage points**; validation loss 0.8109 → 0.6806, **−0.1303** |

The resolution is **rule-based before** Ollama sees the current turn. Ollama receives bounded prior messages and the resolved current question. The CLI keeps one `SessionState` for its process until `clear` or exit; `--question` is one turn per process. Streamlit keeps one state in `st.session_state.detective_session` and a separate UI-only `chat_entries` list; its **Clear conversation** button resets both. The V1 `simple` mode does not consume V2 memory even though the CLI created a session variable.

## 5. Hybrid experiment-note retrieval

The V2 `search_notes` tool maps to `v2_retrieval.hybrid_search_notes(query, top_k=2, rerank=False)`. It reads the `Observation: ` portion of each of five notes. `keyword_rank` tokenizes to lowercase alphanumeric *sets* and counts shared words; a nonmatching note gets no keyword rank. `encode_queries_and_notes([query], notes, local_only=True)` uses cached `sentence-transformers/all-MiniLM-L6-v2` embeddings, pinned to revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. `semantic_rank` computes cosine as the vector dot product divided by the product of their norms and ranks *every* note. Cosine is similarity, not a probability of relevance or a confidence in a conclusion.

For note `d` with keyword rank `r_k` (if any) and semantic rank `r_s`:

```text
RRF(d) = [1 / (60 + r_k) if keyword matched, else 0]
       +  1 / (60 + r_s)
```

The code sorts descending by this score, breaks ties by run ID, optionally reranks, and returns the first `top_k`. The public function permits `top_k=1..5`. The agent's fallback requests two, and the execution filter clamps model requests above two unless the user's question explicitly says `top1` through `top5`. The result includes each note's `run_id`, `note_source`, `run_source`, observation, keyword rank/score/shared words, semantic rank/cosine, hybrid score/rank, optional reranker score, and final rank. Four stage arrays make every ranking visible. A note result is only a candidate until `get_experiment` opens its JSON.

**Real saved query:** `Have we seen unstable validation behavior like lr_01_seed3, and why might it happen?` from the two-turn `L_full_trace` case, with reranking off:

| Keyword rank | Note ID | Shared-word count and words |
| ---: | --- | --- |
| 1 | `baseline_gap_001` | 2: `and`, `validation` |
| 2 | `lr_005_gap_001` | 2: `and`, `validation` |
| 3 | `lr_01_seed2` | 2: `and`, `validation` |
| 4 | `small_dropout_05_001` | 2: `and`, `validation` |
| 5 | `small_no_dropout_001` | 2: `and`, `validation` |

| Semantic rank | Note ID | Cosine |
| ---: | --- | ---: |
| 1 | `lr_01_seed2` | 0.5027 |
| 2 | `baseline_gap_001` | 0.4119 |
| 3 | `small_no_dropout_001` | 0.3362 |
| 4 | `lr_005_gap_001` | 0.3297 |
| 5 | `small_dropout_05_001` | 0.2949 |

| Hybrid rank | Note ID | RRF |
| ---: | --- | ---: |
| 1 | `baseline_gap_001` | 0.032522 |
| 2 | `lr_01_seed2` | 0.032266 |
| 3 | `lr_005_gap_001` | 0.031754 |
| 4 | `small_no_dropout_001` | 0.031258 |
| 5 | `small_dropout_05_001` | 0.031010 |

For the first note, `1/61 + 1/62 = 0.032522` after rounding. The word `and` affected every keyword match, showing the limitation of this unfiltered tokenizer. `search_runs(learning_rate=0.1)` is different: it does *exact* JSON config filtering without embeddings. The routing offers it for “Which experiments used learning rate 0.1?”, whereas behavioral wording such as “Have we seen unstable validation behavior?” offers note retrieval.

## 6. Optional cross-encoder reranking

The reranker is `cross-encoder/ms-marco-MiniLM-L2-v2`, locally stored at `D:\Agentic_ai_rag projects\.model_cache\reranker-ms-marco-MiniLM-L2-v2`. Its `model.safetensors` is 62,471,772 bytes (about 62.5 MB decimal). `_reranker` loads it from that local path on CPU, with `local_files_only=True`, and caches the Python model object. It is off by default in both CLI and UI. `app.py --rerank` or the UI checkbox enables it for *experiment note search*; `search_ml_knowledge` does not use it.

When enabled, `CrossEncoder.predict([(query, observation), ...])` scores each of the five candidate notes. The code stores rounded `reranker_score`, sorts descending by that score (using hybrid rank as a tie-breaker), and sets `final_rank`. This score ranks a query/document pair; it is not a probability, citation quality measure, or proof of a factual claim. If the local model's `config.json` is absent, the function reports `model not cached; hybrid order used`. Other model failures are not silently swallowed by that fallback.

The five-case evaluation in section 15 measured mean Recall@2/MRR@2 of **0.80/0.70** after reranking versus **0.90/0.90** for hybrid. In the held-out spike-and-recover case, the reranker placed neither labeled relevant note in its top two, while semantic search placed both. That observed weakness explains the default `rerank=False`; the sample is too small to prove that reranking is generally worse.

## 7. Experiment RAG versus knowledge RAG

```text
Experiment RAG:
user behavior question -> search_notes -> notes/*.md observations
  -> keyword + MiniLM + RRF -> candidate run IDs and note paths
  -> get_experiment(candidate ID) -> exact runs/*.json metrics
  -> observed-facts section with run and note source paths

Knowledge RAG:
user mechanism question, often after run evidence
  -> search_ml_knowledge -> knowledge/*.md local chunks
  -> keyword + MiniLM + RRF -> titles, topics, source URLs, text
  -> relevant-ML-knowledge section; possible interpretation only
```

`search_notes` finds *our* observations; `search_ml_knowledge` finds *general* reference material. The tools have different handlers and different file collections. For example, a note can point to `baseline_gap_001`, whose JSON shows a validation-loss rise and recovery. A learning-rate lesson can explain that large gradient steps may bounce around a minimum generally, but it does not show that this mechanism caused the saved run's pattern. A final answer may contain both source types in separate sections.

One actual knowledge chunk's format, from `knowledge/learning_rates.md`:

```text
Title: Linear regression: Hyperparameters
URL: https://developers.google.com/machine-learning/crash-course/linear-regression/hyperparameters
Topic: learning rates and optimization
Source-Type: official educational material (Google Machine Learning Crash Course)
Text:
The learning rate controls the size of a gradient-descent parameter update. A rate that is too high can make optimization bounce around a minimum or fail to converge; a rate that is too low can make progress slow. The useful rate depends on the model and data. This general mechanism does not establish why any specific Fashion-MNIST run changed.
```

The `Text:` separator and four metadata keys are parsed by `_knowledge_chunks`. A malformed chunk can raise while parsing; there is no document ingestion service or web request during a user question.

## 8. Current external knowledge base

The five files are local, short, attributed **paraphrases** of official sources. They were curated into `knowledge/` with title, URL, topic, source type, and retrieval text; the app retrieves the local text offline after the MiniLM cache exists. This is a small starter corpus, not a comprehensive ML textbook.

| File | Topic | Recorded source and URL | Questions it can support |
| --- | --- | --- | --- |
| `knowledge/dropout.md` | Dropout regularization | PyTorch, `torch.nn.Dropout`: https://docs.pytorch.org/docs/stable/generated/torch.nn.Dropout | What dropout does during training and evaluation |
| `knowledge/learning_rates.md` | Learning rates and optimization | Google ML Crash Course, `Linear regression: Hyperparameters`: https://developers.google.com/machine-learning/crash-course/linear-regression/hyperparameters | Why a rate may make gradient steps too large or too small |
| `knowledge/optimization.md` | SGD, loss, and weight updates | PyTorch, `Optimizing Model Parameters`: https://docs.pytorch.org/tutorials/beginner/basics/optimization_tutorial.html | What zeroing gradients, backpropagation, and optimizer steps mean |
| `knowledge/overfitting.md` | Overfitting and validation behavior | scikit-learn, `Validation curves: plotting scores to evaluate models`: https://scikit-learn.org/stable/modules/learning_curve.html | What a train/validation gap may suggest |
| `knowledge/validation.md` | Training and validation loss curves | Google ML Crash Course, `Overfitting: Interpreting loss curves`: https://developers.google.com/machine-learning/crash-course/overfitting/interpreting-loss-curves | How to read oscillating or diverging loss curves cautiously |

`_knowledge_chunks` rereads these Markdown files on each search and preserves their source URLs in results. The current app does not fetch live pages, update the corpus automatically, embed a large document collection, or attach publication excerpts beyond these local paraphrases.

## 9. Complete V2 tool inventory

These are the **nine** `TOOLS` entries in `v2_tools.py`. A schema is sent to Ollama only when the current menu offers that name; `execute_tool` dispatches the selected name to exactly the Python function shown. “Deterministic” means the same saved files and arguments yield the same computation; semantic and cross-encoder rankings are model-computed but have no text generation and use fixed local model files.

| Offered tool and arguments | Exact handler | Purpose and when offered/used | Main return and evidence source |
| --- | --- | --- | --- |
| `get_experiment(run_id: str)` | `experiment_data.get_experiment` | One known run, or inspect a run ID returned by note search | Config, final epoch/accuracy/loss, epoch metrics, rise/fall patterns, `runs/<id>.json`; deterministic JSON calculation |
| `compare_experiments(baseline_run_id: str, target_run_id: str)` | `experiment_data.compare_experiments` | Two named runs; “worse than” routes reference second ID as baseline | Changed recorded settings, final values, target-minus-baseline percentage points and loss, source paths; deterministic JSON calculation |
| `search_runs(learning_rate?: number, train_size?: int, dropout?: number)` | `experiment_data.search_runs` | Exact configuration/filter question such as “which used 0.1” | Filters and matching run rows with final metrics and sources; deterministic JSON filter |
| `search_notes(query: str, top_k?: int, rerank?: bool)` | `v2_retrieval.hybrid_search_notes` | Behavior/similarity question, especially without a named run | Candidate note/run IDs, raw ranks/scores, stage arrays; `notes/*.md` plus local MiniLM and optional CrossEncoder; ranked, not a measurement |
| `summarize_run_curve(run_id: str)` | `v2_analysis.summarize_run_curve` | Best accuracy, minimum loss, largest rise, recoveries | Computed curve summary and `runs/<id>.json`; deterministic |
| `find_overfitting_candidates()` | `v2_analysis.find_overfitting_candidates` | “Possible overfitting candidates” wording | Intervals where train loss fell and validation loss rose, with measurements and source paths; deterministic heuristic over JSON |
| `compare_run_group(learning_rate_a: number, learning_rate_b: number)` | `v2_analysis.compare_run_group` | Compare two exact learning-rate groups | Counts, per-run values, mean/median accuracy, caveat; deterministic descriptive JSON aggregation |
| `plot_run_metrics(run_id: str)` | `v2_analysis.plot_run_metrics` | One run's curve/chart request | Epoch rows: train loss, validation loss, validation accuracy percent and JSON source; deterministic |
| `search_ml_knowledge(query: str, top_k?: int)` | `v2_retrieval.search_ml_knowledge` | General ML mechanism, often after run evidence | Ranked local chunks with title, URL, topic, text, cosine, RRF; `knowledge/*.md`, not run evidence |

Schema-required keys: `run_id` for one-run tools; both IDs for comparison; `query` for both retrieval tools; both rates for group comparison; none for `search_runs` and `find_overfitting_candidates`. `top_k` is optional in schemas, default two in Python. `find_overfitting_candidates` accepts no arguments. The tool registry does **not** expose filesystem writes, shell commands, web search, experiment training, or arbitrary Python execution.

## 10. Manual V2 agent loop, including policy and errors

The exact `run_manual` excerpt is in section 3.8. `prepare_turn` (before the loop) creates one state payload containing original/resolved question, session object, Ollama messages, first tool names, rerank setting, successful `tool_results`, `decisions`, `trace`, `tool_count`, `pending_calls`, and `answer`. The trace begins with `USER` and `MEMORY BEFORE`. The system prompt instructs tool use for saved runs, note search then JSON inspection for behavior questions, exact search for configuration questions, comparison for two IDs, separate knowledge lookup for mechanisms, and no invented measurements or causal claims.

At each iteration:

1. `available_tool_names` reads successful results to build the next *narrow* menu. A `TOOL MENU` event records it.
2. `ask_ollama` sends system, bounded history, resolved current user question, and all current-turn assistant/tool messages to `qwen3:1.7b` through local Ollama.
3. If `message["tool_calls"]` has entries, only the first is attempted. `execute_call(..., origin="AGENT")` checks the menu, corrects constrained arguments if needed, validates against the shared registry, executes Python, and records an observation. A later tool is considered after another model request.
4. If there is no tool call, `policy_call` may choose the first required evidence tool, a retrieved run's exact JSON, or ML knowledge for a “why” question. `execute_call(..., origin="APP POLICY")` records the actual origin. If policy has nothing else to require and at least one tool succeeded, `finish_turn` renders and remembers the answer.
5. `MAX_TOOL_CALLS=6` limits executions. No successful evidence when the model stops yields `RuntimeError`. An unsupported or currently unoffered tool yields `ValueError` from the menu check; it is not executed. Validation/data errors from an allowed tool are caught into `{"error": ...}`, placed in the trace and model observation, but not accepted as successful `tool_results`. Network/other unhandled errors propagate to the CLI/UI error handler where covered.

`_fallback_arguments` derives exact run IDs and explicit filters from the resolved question, requests `top_k=2`, and, after a comparison where learning rate changed, uses `"high learning rate optimization instability"` as a general-knowledge search query. `execute_call` may record `APP FILTER` if it replaces model arguments: for example, it can force a retrieved run ID to one of the returned candidates, override the rerank flag with the user's switch, or cap oversized top-k. Thus **AGENT** means Ollama supplied the tool request; it does not mean every final argument was accepted unchanged. `APP POLICY` means Python initiated that call after an empty tool-call response. The synthetic assistant tool message appended for either origin is an Ollama protocol detail, not evidence that Ollama made the fallback choice.

The message construction and final state update are short enough to show directly:

```python
resolved, memory = session.resolve(question)
first_names = _first_tool_names(resolved)
ids = mentioned_run_ids(resolved)
id_context = ", ".join(ids) if ids else "none"
messages = [{"role": "system", "content": SYSTEM + f" Exact saved run IDs in this question: {id_context}."}]
messages.extend(session.history_messages())
messages.append({"role": "user", "content": resolved})
```

**What it does:** Resolves a reference, routes the first tool menu, and sends bounded prior turns plus the current resolved question. **Why it exists:** It makes context and routing visible. **How it connects:** `run_manual` and `run_graph` both start with `prepare_turn`.

## 11. LangGraph agent

The actual graph in section 3.14 is:

```text
START -> agent -- pending_calls? --> tools -> agent
                  |
                  +-- none --> final -> END
```

`GraphState` is a `TypedDict` with one `payload: dict` field. The payload is the very same structure returned by `prepare_turn`. `agent_node` appends a menu event, asks Ollama, and places either the first real model call (`origin="AGENT"`), a needed fallback (`origin="APP POLICY"`), or no call into `pending_calls`. `route_after_agent` chooses `tools` or `final`. `tools_node` clears the pending list and calls shared `execute_call`. `final_node` calls shared `finish_turn`. `run_graph` invokes the compiled graph with `recursion_limit=17`, because `2 * MAX_TOOL_CALLS + 5 = 17`.

| Manual V2 concept | Graph V2 counterpart |
| --- | --- |
| State dict from `prepare_turn` | `GraphState["payload"]` |
| Manual `for` loop | Repeated `agent -> tools -> agent` edges |
| `ask_ollama` inside loop | `ask_ollama` inside `agent_node` |
| `if calls ... else policy` | Same branching inside `agent_node`; then conditional `route_after_agent` |
| `execute_call` directly | `tools_node` calls the *same* `execute_call` |
| `finish_turn` and return | `final_node` calls the *same* `finish_turn`, then `END` |

LangGraph makes workflow transitions explicit and offers a foundation for more complex orchestration, but this implementation has no multi-agent network, persisted checkpoint, LangGraph-specific retrieval, or new reasoning engine. The graph and manual modes can produce different *origins* if Ollama's response differs between calls, but both use the same allowed tools, policy, data, and renderer. `reports/v2_validation_traces.json` contains successful single-run, combined, and note-search graph cases.

## 12. Source-aware answer rendering and factual grounding

`finish_turn` calls `v2_answers.render_answer(resolved_question, successful_tool_results)`. This is **deterministic Python**, not a final prose completion from Qwen. It groups results by tool name:

- `get_experiment` and `compare_experiments` supply final accuracy/loss, epoch and setting differences from JSON. `compare_experiments` computes percentage points rather than a percent-relative change.
- `search_notes` supplies a ranked observation and note path, but `render_answer` only emits that observation when `get_experiment` also inspected the same run ID. For a rise/fall pattern it renders the checked JSON-derived `validation_loss_recoveries` values.
- `search_runs`, `summarize_run_curve`, `find_overfitting_candidates`, `compare_run_group`, and `plot_run_metrics` supply other Python-computed observations and run paths.
- `search_ml_knowledge` supplies attributed text and source URLs under `Relevant ML knowledge`. Duplicate URLs are suppressed.
- Only when both an observed experiment section and a knowledge section exist does Python add its fixed cautious `Possible interpretation` sentence. Conditional `Limitations` warn about ranking scores, heuristic flags, or causal overreach. `Sources` separates local run/note paths from external reference URLs.

```python
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
```

**What it does:** Renders from successful evidence, persists session context, and appends final trace events. **Why it exists:** The displayed metrics and citations remain inspectable and traceable to tool results. **How it connects:** Both V2 agents end here. The LLM influences which tool is called when it actually emits one; it does not write the final V2 answer. Its general pretrained knowledge is not treated as a cited source. This architecture can still produce a weak interpretation if retrieval selected weak evidence; deterministic formatting is not a guarantee of retrieval quality.

## 13. Streamlit UI architecture

`ui.py` runs as a normal Streamlit script and is rerun after widget interactions. `st.session_state.detective_session` keeps the agent's `SessionState` for that browser session. `st.session_state.chat_entries` stores visible user questions, answers, and event lists; it is separate from the bounded agent-memory turns and can grow until cleared. A radio selects `manual` or `graph`; a checkbox opts into reranking, default false. The UI passes the same session object to `run_manual` or `run_graph`, then appends the returned answer/trace and calls `st.rerun()`. No retrieval, comparison, or agent loop is reimplemented in Streamlit.

The sidebar counts the eleven run JSON files, selects a run (initially `lr_01_seed3` if present), shows selected config fields and example questions, and offers **Clear conversation**. The main chat shows deterministic answers. The `How did the agent answer this?` expander shows every trace event except the duplicate `FINAL` event as a labeled JSON block, including `MEMORY BEFORE`, `TOOL MENU`, `AGENT` or `APP POLICY`, `APP FILTER` when needed, `TOOL RESULT`, and retrieval-stage arrays. Thus scores and tool arguments remain visible.

The run-detail area reads `get_experiment(selected)` for config and final metrics, then directly calls `plot_run_metrics(selected)` to build a Pandas DataFrame. One line chart shows post-epoch training and validation loss; another shows validation accuracy percent; a table shows epoch rows. A third tab shows `SessionState.snapshot()`. Local source paths in chat are rendered as literal paths because Streamlit cannot serve project files via those relative Markdown links; external URLs remain clickable. Clearing resets both memory and displayed chat but never changes saved run, note, or knowledge files. Streamlit's automated UI check observed no exceptions, two rendered chart elements, one run table, and a graph-mode chat answer containing the JSON measurement and source.

## 14. Complete real V2 multi-turn trace

Source: saved `reports/v2_validation_traces.json`, cases `L_full_trace_memory_seed` and `L_full_trace`, produced by `validate_v2.py`. The second turn has **18 events**. This is the actual successful case that combines short-term memory, experiment note retrieval, exact run evidence, and external ML knowledge. The trace does **not** save raw Ollama response text; `APP POLICY` after an offered menu establishes that Ollama supplied no usable `tool_calls` in that step. The raw response body itself cannot be reconstructed from the saved events. `LLM` below therefore refers only to the observable tool-call condition, not imagined model wording.

**Turn 1: `Tell me about lr_01_seed3.`**

1. **PYTHON memory before:** No focus, no recent turns, explicit ID `lr_01_seed3`.
2. **Tool menu:** `["get_experiment"]`.
3. **AGENT CHOICE:** Ollama supplied `get_experiment({"run_id":"lr_01_seed3"})`.
4. **PYTHON result:** `runs/lr_01_seed3.json` gave final validation accuracy **71.45%**, loss **0.8109**, epoch **5**.
5. **Memory after:** `focused_run_id="lr_01_seed3"` and `referenced_run_ids=["lr_01_seed3"]`. Python rendered an observed-fact answer with that run source.

**Turn 2: `Have we seen unstable validation behavior like that run, and why might it happen?`**

| Event order | Label and actual content | What it establishes |
| ---: | --- | --- |
| 1 | `USER`: original second question | The user did not type a run ID in this turn. |
| 2 | `MEMORY BEFORE`: focus `lr_01_seed3`, no explicit IDs, `resolved_reference="lr_01_seed3"`, resolved text `Have we seen unstable validation behavior like lr_01_seed3, and why might it happen?`, one recent turn | **PYTHON** resolved the reference before routing and sent bounded prior history to Ollama. |
| 3 | `TOOL MENU ["search_notes"]` | **PYTHON** route offered experiment-note search for “seen”. |
| 4 | `APP POLICY search_notes` with resolved query, `top_k=2`, `rerank=False` | **LLM** provided no usable tool call; **PYTHON** initiated this fallback. |
| 5 | `TOOL RESULT search_notes` | **RETRIEVAL** returned two note candidates and four stage arrays. |
| 6 | `KEYWORD RESULTS`: `baseline_gap_001` rank 1, `lr_005_gap_001` rank 2, `lr_01_seed2` rank 3, both remaining notes ranks 4–5 | Shared-word counts were 2 for each; `and` and `validation` matched. |
| 7 | `SEMANTIC RESULTS`: `lr_01_seed2` rank 1, cosine 0.5027; `baseline_gap_001` rank 2, 0.4119; remaining cosines 0.3362, 0.3297, 0.2949 | MiniLM provided a different ordering from keyword matching. |
| 8 | `HYBRID RESULTS`: `baseline_gap_001` rank 1/RRF 0.032522; `lr_01_seed2` rank 2/0.032266; remaining 0.031754, 0.031258, 0.031010 | RRF fused rank positions. |
| 9 | `RERANKED RESULTS []` | Reranking was disabled. |
| 10 | `TOOL MENU ["get_experiment"]` | **PYTHON** required exact inspection after note search. |
| 11 | `APP POLICY get_experiment({"run_id":"baseline_gap_001"})` | **LLM** again provided no usable tool call; **PYTHON** chose the top returned note ID. |
| 12 | `TOOL RESULT get_experiment` | **PYTHON** loaded the saved JSON. Validation loss: epoch 1 **0.8696**, epoch 2 **1.4186**, epoch 3 **0.6663**. Final epoch 5: accuracy **71.25%**, loss **0.8208**. |
| 13 | `TOOL MENU ["search_ml_knowledge"]` | Because the question asked “why”, a general reference search was offered after experiment evidence. |
| 14 | `APP POLICY search_ml_knowledge`, resolved question, `top_k=2` | **LLM** again supplied no usable tool call; **PYTHON** initiated the general-knowledge lookup. |
| 15 | `TOOL RESULT search_ml_knowledge` | **RETRIEVAL** ranked `optimization.md` first (RRF 0.032018, cosine 0.3013) and `learning_rates.md` second (RRF 0.032002, cosine 0.3041). |
| 16 | `TOOL MENU []` | No further tool was offered; the following model response produced no tool call. |
| 17 | `MEMORY AFTER` | Focus remained `lr_01_seed3`; referenced IDs included `baseline_gap_001`. The original and resolved questions and all three APP POLICY decisions were stored. |
| 18 | `FINAL` | **PYTHON** rendered the source-aware answer from the three successful tool results. |

The final answer's **Observed experiment facts** section cited the retrieved `baseline_gap_001` note but confirmed the loss rise/fall against `runs/baseline_gap_001.json`. **Relevant ML knowledge** used the local PyTorch optimization chunk and Google learning-rate chunk. **Possible interpretation** said the pattern is compatible with general mechanisms but did not identify a proven cause. **Limitations** said similarity/reranker scores only rank text. **Sources** contained `notes/baseline_gap_001.md`, `runs/baseline_gap_001.json`, https://docs.pytorch.org/tutorials/beginner/basics/optimization_tutorial.html, and https://developers.google.com/machine-learning/crash-course/linear-regression/hyperparameters. The final answer does not assert that `lr_01_seed3` itself showed the retrieved rise/fall; it reports a *similar retrieved* run. The prior focused ID provided context for the question.

For contrast, saved case `H_combined` shows a true **AGENT CHOICE** for `compare_experiments(baseline=lr_005_seed3, target=lr_01_seed3)`, followed by **APP POLICY** `search_ml_knowledge("high learning rate optimization instability", top_k=2)`. Python measured accuracy **75.90% → 71.45%**, **−4.45 percentage points**, and loss **0.6806 → 0.8109**, **+0.1303**; the retrieved general mechanism remained a possible interpretation. This is another actual tool origin pattern, not a claim that Ollama chose the knowledge lookup.

## 15. Retrieval evaluation and its limits

`evaluate_retrieval.py` reads five hand-labeled entries from `retrieval_eval_cases.json`, ranks the same five notes four ways, and prints per-case and mean Recall@2 and MRR@2. For each case, Recall@2 is the fraction of labeled relevant notes present in the first two. MRR@2 is the reciprocal of the first relevant rank (1, 1/2, or 0 if absent). The recorded run completed with the local reranker available:

| Method | Mean Recall@2 | Mean MRR@2 |
| --- | ---: | ---: |
| Keyword | 0.90 | 0.80 |
| Semantic MiniLM | 1.00 | 0.90 |
| Hybrid RRF | 0.90 | 0.90 |
| Hybrid then cross-encoder reranking | 0.80 | 0.70 |

Hybrid beat keyword on MRR here because it moved a relevant note to rank 1 in the held-out spike query; it did **not** beat semantic on recall. Semantic put both relevant notes in the top two for that case, while hybrid put only one, so hybrid's aggregate recall is lower than semantic's. The reranker put neither in its top two for that case. Other cases often tied. With five queries and five notes, these values are a local teaching check, not a reliable estimate for new datasets or an argument that one method always wins. More stages can worsen ranking.

## 16. Exact current limitations

- **Collection size:** Eleven run JSON records, only five note files, and five general-knowledge chunks. Note search misses saved runs without notes; the knowledge corpus covers only a few ML ideas.
- **Note fidelity:** The renderer requires an exact run inspection before displaying a retrieved observation and computes recovery values from JSON, but it does not verify every number inside the note's free-text observation. A stale note can still contain a mistaken detail.
- **Evaluation size and labels:** Five project-specific retrieval questions. The aggregate differences are sensitive to one case and label choices.
- **Keyword weakness:** It counts raw shared tokens, including stopwords such as `and`, without stemming or field weighting. RRF can promote such weak keyword matches above stronger semantic matches.
- **Reranker weakness:** The chosen cross-encoder degraded the measured five-case score and is opt-in. A reranker score is merely an ordering signal. CPU reranking adds latency.
- **Small local model:** `qwen3:1.7b` chooses some tools but often emits no call for note/knowledge/analysis menus. `APP POLICY` then enforces a visible next evidence step. The menus are intentionally narrow and route partly by wording, so this is a constrained agent rather than unrestricted planning.
- **Trace observability:** It records menus, selected calls, corrected arguments, full Python results, retrieval stages, memory snapshots, and final output. It does **not** record raw Ollama response text or token-level reasoning; an empty tool-call list is inferred from the fallback path. `APP FILTER` events appear only when arguments change.
- **Memory:** Four prior turns, simple singular regex, no persistence between CLI processes, no plural/general coreference, and up to eight recent referenced IDs. Streamlit's displayed chat list is not bounded until reset, while the agent's model history is bounded. A previously focused ID can remain the focus after comparing two runs.
- **Context and runtime:** Ollama request uses `num_ctx=4096` and `num_predict=400`, with a 300-second HTTP timeout. Current-turn tool results may still be large; only note and overfitting results are compressed before insertion into Ollama messages. Local Ollama must be running, and cached models must exist for offline retrieval. The Windows `.venv` was created with `include-system-site-packages=true`; it is not a fully isolated environment and relies on installed packages visible to that Python process. `requirements.txt` pins direct V2 packages, not the whole transitive environment or Ollama.
- **External source verification:** The knowledge files and their recorded official URLs were inspected locally for this snapshot. The live pages were not refetched during this documentation task; the app itself always uses the saved paraphrases at query time.
- **Graph/manual behavior:** Both share handlers and renderer, but separate Ollama calls can yield differing `AGENT` versus `APP POLICY` origins. Graph state is one mutable payload; no checkpointing is configured.
- **Inference limits:** The overfitting candidate rule and group means are descriptive. Runs may repeat configs or differ in other settings. A matched pair and a relevant ML reference are compatible with a mechanism, but do not prove what caused the measured difference. General document text cannot validate a specific experimental cause.

## 17. Models, dependencies, and storage

| Component | Purpose | Current path and approximate size |
| --- | --- | --- |
| Ollama application | Local server exposing `/api/chat`; loads and runs generation model | `D:\Ollama\ollama.exe`; service on `127.0.0.1:11434` |
| `qwen3:1.7b` | Local text/tool-call model used by both V2 agents | Ollama model files under `D:\Ollama\models`; `ollama list` reported **1.4 GB** |
| `sentence-transformers/all-MiniLM-L6-v2` | Encodes queries, notes, and knowledge chunks for semantic cosine ranking | `D:\Agentic_ai_rag projects\.model_cache\models--sentence-transformers--all-MiniLM-L6-v2`; `model.safetensors` **90,868,376 bytes** (about 90.9 MB decimal) |
| `cross-encoder/ms-marco-MiniLM-L2-v2` | Optional query-note reranker | `D:\Agentic_ai_rag projects\.model_cache\reranker-ms-marco-MiniLM-L2-v2`; `model.safetensors` **62,471,772 bytes** (about 62.5 MB decimal) |

**Do not conflate them:** Ollama is the local serving program, while Qwen is the model it runs. MiniLM produces numerical embeddings and does not compose answers. The cross-encoder jointly scores a query/note pair and is a different model from the MiniLM embedding model. `v2_answers.py`, not any model, produces the final V2 wording from tool results.

`requirements.txt` declares `sentence-transformers==6.1.0`, `streamlit==1.65.0`, and `langgraph==1.2.12`; Ollama is installed separately. The Python environment is `D:\Agentic_ai_rag projects\.venv` using Python 3.12 with system site packages enabled. The user-level `OLLAMA_MODELS` value was verified as `D:\Ollama\models`; the default `C:\Users\ASUS\.ollama\models` folder was absent at verification. Project embedding/reranking caches are on D:. Ollama may still keep small logs/configuration under the Windows user profile. The model-weight sizes above were checked locally; they do not include every tokenizer/config/cache file.

## 18. Verified commands

Open PowerShell in the project directory:

```powershell
Set-Location -LiteralPath 'D:\Agentic_ai_rag projects'
.\.venv\Scripts\python.exe app.py
.\.venv\Scripts\python.exe app.py --agent manual
.\.venv\Scripts\python.exe app.py --agent graph
.\.venv\Scripts\python.exe app.py --agent simple
.\.venv\Scripts\streamlit.exe run ui.py
.\.venv\Scripts\python.exe evaluate_retrieval.py
.\.venv\Scripts\python.exe validate_v2.py
```

The CLI modes accept `--question "What is the final validation accuracy of lr_01_seed3?"` to run once, `--no-trace` to hide events, and `--rerank` to opt into note reranking. Without `--question`, type `clear` to reset memory and `exit` to quit. For a trace-rich one-shot question:

```powershell
.\.venv\Scripts\python.exe app.py --agent manual --question "Have we seen unstable validation behavior before?"
```

The local Ollama service must already be available with `qwen3:1.7b`. `validate_v2.py` tests 17 category/mode cases and writes `reports/v2_validation_traces.json`; `evaluate_retrieval.py` runs the five-case local retrieval check. These commands and the Streamlit manual/graph chat and two charts were verified in the V2 build session. Re-running them later may vary in latency and in model-selected versus fallback origin, though the exact JSON measurements should stay the same unless the saved files change.

## 19. Exact study order

1. **V1 recap:** Read `simple_agent.py` and run `app.py --agent simple`. Before moving on, identify its explicit Ollama → tool → observation loop and semantic-only note retrieval.
2. **State:** Read `v2_state.py`, then `app.py`. Before moving on, explain why `Compare that run...` becomes a resolved run ID and what four-turn history actually sends to Ollama.
3. **Retrieval:** Read `note_retrieval.py` and `v2_retrieval.py`. Before moving on, compute `1/61 + 1/62` and explain why cosine and keyword counts are not added directly; inspect `KEYWORD/SEMANTIC/HYBRID` stage arrays.
4. **Tool boundary:** Read `v2_tools.py`. Before moving on, locate the JSON-like schema, name-to-function handler, allowed argument checks, and menu filtering.
5. **Exact analysis:** Read `experiment_data.py` and `v2_analysis.py`. Before moving on, trace one percentage-point difference and one overfitting candidate back to JSON fields.
6. **Manual agent:** Read `v2_agent.py` and `v2_answers.py`. Before moving on, distinguish `AGENT` from `APP POLICY` and `APP FILTER`, and explain why the final numbers and prose are Python-rendered.
7. **Knowledge RAG:** Read all five `knowledge/*.md` chunks and `search_ml_knowledge`. Before moving on, separate “what this run measured” from “what an official ML source says can happen generally.”
8. **Full trace:** Walk through section 14 event by event, optionally comparing `reports/v2_validation_traces.json`. Before moving on, account for the memory reference, every menu, each fallback, both RAG paths, JSON source, and final sources.
9. **LangGraph:** Read `graph_agent.py`. Before moving on, map its payload, agent/tools/final nodes and edges to the manual `for` loop, and state what LangGraph does not calculate.
10. **UI:** Read `ui.py` and run Streamlit. Before moving on, find where browser-session state, chat entries, mode switch, reranker switch, charts, trace expander, and reset connect to the same V2 agent functions.

## 20. Final mental model

```text
User question -> short-term SessionState and reference resolution
              -> narrow tool menu -> local Qwen through Ollama
              -> AGENT tool call or visible APP POLICY fallback
              -> validated Python tool:
                   exact runs JSON / hybrid experiment notes /
                   local general ML knowledge / deterministic analysis
              -> tool observation appended to model messages
              -> repeat or stop -> Python-rendered source-aware answer
              -> bounded memory update and visible trace
```

In this project, **RAG** is retrieving note or knowledge text as context for a question. **Agentic AI** is the repeated model/tool/observation loop, with explicit application routing and fallbacks. **Hybrid RAG** fuses keyword and MiniLM semantic ranks using RRF. **Reranking** optionally applies a separate cross-encoder to reorder experiment-note candidates; it is off by default based on the five-case check. **Memory** is a bounded in-process/browser-session record of recent turns and focused run IDs, not the experiment database. **Tools** are allowlisted Python functions with schemas that expose exact records, retrieval, and calculations to the loop. **LangGraph** packages the same steps as state, nodes, conditional edges, and termination. **Knowledge RAG** searches local attributed ML reference chunks to support cautious general interpretation while JSON remains the source of measured experiment facts.
