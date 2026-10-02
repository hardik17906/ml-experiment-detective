# Learning guide

Read the working path in this order. Run the CLI once with its trace visible before opening the files:

```powershell
.\.venv\Scripts\python.exe app.py --question "Have we seen unstable validation behavior before?"
```

1. **`app.py` — entry point.** Find the interactive `input()` loop and the single call to `answer_question`. Notice that this file does not know how embeddings or tool calls work.
2. **`simple_agent.py` — tool calling and the agent loop.** Read `TOOLS`, `execute_tool`, `ask_ollama`, and `answer_question` in that order. Look for the assistant's `tool_calls`, the Python function call, the `role: tool` message, and the maximum-call limit. Notice the difference between `AGENT` and `APP POLICY` trace lines.
3. **`experiment_data.py` — exact evidence.** Read `load_run`, `get_experiment`, `compare_experiments`, and `search_runs`. Check how percentages and percentage-point differences are calculated from JSON. This is why an LLM does not need to perform arithmetic.
4. **`note_retrieval.py` and `simple_agent.search_notes` — RAG retrieval.** Follow `load_notes`, `encode_queries_and_notes`, and `semantic_rank`. The query and each observation become vectors; cosine similarity ranks the five current notes. Search returns candidate IDs, which are then used for exact JSON lookup.
5. **One note and its run.** Open `notes/lr_01_seed2.md` beside `runs/lr_01_seed2.json`. Compare the note's paraphrase with epoch 3, 4, and 5 validation losses in the JSON.
6. **`simple_agent.render_answer` — final presentation.** Trace how measured values and source paths become readable output. The local model's free-text reply determines that it has stopped, but its unverified numeric prose is not published.
7. **`docs/TRACE_EXAMPLE.md` — join the pieces.** Follow a real query through every component, then run the same question yourself. Tool choices can vary across runs even with a low temperature.

The earlier `phase0.py`, comparison, hypothesis, and evaluation scripts remain useful history. They are not required to start the final question-answering CLI. Read them later if you want to study how the evidence was produced.
