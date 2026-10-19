# Manual loop and LangGraph

Both V2 modes use `v2_state.py`, `v2_tools.py`, `v2_retrieval.py`, `v2_analysis.py`, and `v2_answers.py`. They call the same local Ollama model. The graph changes orchestration, not the source of facts or the model's intelligence.

| Manual V2 in `v2_agent.py` | LangGraph V2 in `graph_agent.py` |
| --- | --- |
| `state = prepare_turn(...)` creates messages, memory snapshot, and trace. | `GraphState` wraps the same payload as graph state. |
| A `for` loop asks Ollama, executes one tool, and repeats. | `agent` node asks Ollama; a conditional edge sends work to `tools` or `final`. |
| `available_tool_names()` produces the next menu. | The `agent` node calls the same function. |
| `execute_call()` validates and runs a selected tool. | The `tools` node calls the same function. |
| `policy_call()` fills a required evidence step if the small model stops. | The `agent` node calls the same policy. |
| `finish_turn()` renders the source-aware answer and saves memory. | The `final` node calls the same function, then reaches `END`. |

```text
START -> agent
          |-- tool pending -> tools -> agent
          |-- enough evidence -> final -> END
```

This graph is useful when a workflow gains branches, checkpoints, or long-running state. Here it makes transitions explicit and inspectable. The manual version remains the clearest place to learn the agent loop. `langgraph` does not itself retrieve notes, calculate metrics, or reason about the runs.

Try the same prompt in both modes:

```powershell
.\.venv\Scripts\python.exe app.py --agent manual --question "Have we seen unstable validation behavior before?"
.\.venv\Scripts\python.exe app.py --agent graph --question "Have we seen unstable validation behavior before?"
```

The exact `AGENT` versus `APP POLICY` decisions may vary with Ollama's output; both modes must still use the same evidence tools and source-aware renderer. The saved `reports/v2_validation_traces.json` contains successful graph and manual traces.
