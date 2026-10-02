# Real tool trace: unstable validation behavior

This trace came from the local CLI using the existing Ollama `qwen3:1.7b` model and cached MiniLM embedding model:

```powershell
.\.venv\Scripts\python.exe app.py --question "Have we seen unstable validation behavior before?"
```

## 1. User question and Ollama's first decision

The user supplied no run ID. `app.py` passed the question to `simple_agent.answer_question`. Python offered semantic note search as the first tool. Ollama requested a shorter search phrase:

```text
USER -> Have we seen unstable validation behavior before?
AGENT -> search_notes({"query": "unstable validation behavior"})
```

## 2. Search becomes RAG context

`search_notes` called the existing `note_retrieval.py` functions. MiniLM encoded the phrase and all five note observations; cosine similarity ranked the note embeddings. The top two results were:

| Rank | Note's primary run | Similarity | Note describes |
| ---: | --- | ---: | --- |
| 1 | `lr_01_seed2` | 0.468 | validation loss rose at epoch 4 and fell at epoch 5 |
| 2 | `baseline_gap_001` | 0.415 | validation loss rose at epoch 2 and fell at epoch 3 |

Each result included a note source path, the primary run ID, a run JSON path, and the note's observation text. The scores rank notes for this phrase; 0.468 is not a 46.8% probability that the note is correct.

## 3. Ollama requested exact run records

Python appended the search result as a `tool` message and asked Ollama for its next action. In this real run, Ollama chose to inspect both retrieved IDs:

```text
AGENT -> get_experiment({"run_id": "lr_01_seed2"})
TOOL RESULT -> final validation accuracy 76.35%; loss epochs 3,4,5: 0.7136,0.8142,0.6793
AGENT -> get_experiment({"run_id": "baseline_gap_001"})
TOOL RESULT -> final validation accuracy 71.25%; loss epochs 1,2,3: 0.8696,1.4186,0.6663
AGENT -> final answer after 3 tool call(s)
```

`get_experiment` read the two saved JSON files. Python calculated the consecutive rise-then-fall patterns from their saved epoch metrics. The exact source records are [`runs/lr_01_seed2.json`](../runs/lr_01_seed2.json) and [`runs/baseline_gap_001.json`](../runs/baseline_gap_001.json); the retrieved notes are [`notes/lr_01_seed2.md`](../notes/lr_01_seed2.md) and [`notes/baseline_gap_001.md`](../notes/baseline_gap_001.md).

## 4. Final response

After Ollama stopped, Python rendered the inspected evidence:

```text
lr_01_seed2: validation loss 0.7136 -> 0.8142 -> 0.6793 (epochs 3->4->5)
baseline_gap_001: validation loss 0.8696 -> 1.4186 -> 0.6663 (epochs 1->2->3)
```

The answer showed the two note observations, these measured patterns, and links to both notes and both run records. It did not claim a cause. In this run, Ollama selected all three tool calls. In another run, if Ollama stops directly after note search, the CLI visibly labels its one-run inspection as `APP POLICY` so the final answer still includes saved metrics.

This is RAG plus an agent loop: retrieval found candidates from language, Ollama chose follow-up inspections, Python computed the numbers, and the final response used those sources. A fixed RAG script would have inspected a predetermined number of results regardless of Ollama's next decision.
