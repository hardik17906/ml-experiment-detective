# Architecture

This is a local educational MVP. A single command starts the CLI; no database, cloud API, or agent framework is involved.

```text
                   User question in app.py
                            |
                            v
              simple_agent.py: agent loop
              | tool schemas | messages | trace |
                            |
                     Ollama /api/chat
                       qwen3:1.7b
                            |
               tool request or stop decision
                            |
          +-----------------+------------------+
          |                 |                  |
          v                 v                  v
   search_notes       get_experiment     compare_experiments
   MiniLM + cosine      run JSON           two run JSONs
   notes/*.md             |                  |
          |               +---------+--------+
          |                         |
          +----------> search_runs  |
                     exact JSON    |
                            |      |
                            v      v
                        tool result JSON
                            |
                     back to Ollama
                            |
                     next tool or stop
                            |
                 Python answer rendering
                            |
                 answer + sources + trace
```

## Main components

- `app.py` provides an interactive prompt and a `--question` option for one query. It prints the trace by default.
- `simple_agent.py` describes the allowed tools to Ollama, calls `http://127.0.0.1:11434/api/chat`, checks tool names and arguments, executes the functions, returns results as `tool` messages, and repeats up to five tool calls. The loop is in `answer_question`.
- `experiment_data.py` reads `runs/*.json` and calculates final metrics, per-epoch validation metrics, configuration changes, loss-rise patterns, and exact configuration filters. It does the arithmetic in Python.
- `note_retrieval.py` reads `notes/*.md`, encodes query plus note observations with the existing `sentence-transformers/all-MiniLM-L6-v2` model, and ranks them by cosine similarity. `simple_agent.search_notes` exposes this as an agent tool and loads the existing model cache in local-only mode. Notes are short, so a direct comparison of embeddings is enough; there is no vector database.
- `runs/` and `notes/` contain the evidence. A note's filename identifies its primary run. Notes paraphrase run metrics; they are not independent experiment logs.

## One loop turn

1. Python sends the current message history and available tool schemas to Ollama.
2. Ollama may return `tool_calls` with a function name and arguments.
3. Python validates the request and runs only an allowlisted function.
4. Python appends a `tool` message containing JSON results and asks Ollama again.
5. When Ollama stops, Python renders the final measured facts and source links from tool results.

The tool trace labels model-requested calls `AGENT`, their outputs `TOOL RESULT`, and an app-enforced inspection `APP POLICY`. If Ollama stops immediately after semantic search, the app opens the highest-ranked run before completing the answer. This policy makes the exact metrics available; the trace distinguishes it from a model choice.

For obvious questions, the first tool menu is narrowed: two named runs offer comparison, one named run offers inspection, an exact configuration question offers structured search, and a behavior question without an ID offers semantic note search. After the first call, the model can choose follow-up tools. This keeps the small local model from searching unrelated notes for a question that already names exact runs. When a structured question states a numeric filter, Python uses that stated filter even if the model adds an unsupported one; the trace labels the correction `APP FILTER`.

## Where RAG and LLM work happen

RAG begins in `search_notes`: the query becomes an embedding, notes are ranked, and candidate text plus run IDs enter the agent conversation. `get_experiment` can then supply the saved numbers. Ollama chooses tools and decides when to stop. The displayed final measurements come from deterministic Python rendering because this small model previously invented a baseline and made unsupported causal claims in free text. The fixed interpretation says what the records show without claiming proof of cause.

## Limits

- A similarity score is only a ranking signal. The selected note can be irrelevant.
- The rise-then-fall pattern means an increase in validation loss followed by a decrease in the next saved epoch; it is a descriptive pattern, not a diagnosis.
- A filtered run list can include repeated configurations. Older records can lack fields such as `dropout`; absent values are treated as unknown, not zero.
- Grouping runs by learning rate alone does not make them comparable when data size, training length, seeds, or other settings differ.
- Tool choices and arguments from `qwen3:1.7b` can be wrong. The visible tool menu and app policies cover the demonstrated question types, not arbitrary natural-language queries.
