# ML Experiment Detective V3

V3 adds a persistent **Agentic Research Investigator** alongside the preserved V1/V2 agents. It plans investigations, checks exact run metrics and controls, considers competing hypotheses, proposes a controlled experiment, and pauses for an explicit human decision. SQLite/LangGraph checkpoints let an investigation survive application restarts.

## Use V3

```powershell
cd "D:\Agentic_ai_rag projects"
.\.venv\Scripts\streamlit.exe run ui.py
```

Open the displayed local address and use **Investigations (V3)**. Start a question, inspect the plan/evidence/hypotheses, and review the proposed settings. **Approve dry run** exercises the workflow without training. Live training requires selecting the explicit live-training checkbox and approving that exact proposal. Editing invalidates earlier approval. **Chat and runs (V1/V2)** retains the existing agents and run charts.

```powershell
.\.venv\Scripts\python.exe app.py --agent research --question "Investigate why lr_01_seed3 performed worse than lr_005_seed3."
.\.venv\Scripts\python.exe -m v3.cli list
.\.venv\Scripts\python.exe -m v3.cli resume "INV-ID-FROM-START"
.\.venv\Scripts\python.exe -m v3.cli show "INV-ID-FROM-START"
.\.venv\Scripts\python.exe -m v3.cli export "INV-ID-FROM-START"
```

Replace the quoted investigation-ID placeholder with the ID printed by `start`/`list`. Reopening/resuming does not approve training. The CLI also supports `decide` and `modify`; see [the complete V3 reference](docs/V3_COMPLETE_IMPLEMENTATION_CONTEXT.md) for exact commands and permissions.

```powershell
.\.venv\Scripts\python.exe evaluate_v3.py
.\.venv\Scripts\python.exe evaluate_v3_retrieval.py
.\.venv\Scripts\python.exe validate_v3_ui.py
.\.venv\Scripts\python.exe validate_v3_live.py
.\.venv\Scripts\python.exe -m v3.demo
```

The demo reads real saved data and grants **development dry-run permission only**. It creates no training measurements. Test fixtures are explicitly labeled. Live end-to-end training has not been performed during V3 development; fixture ingestion, failures/timeouts, approval enforcement, persistence and UI behavior have been exercised separately. The executor supports the existing bounded Fashion-MNIST MLP learning-rate intervention, rather than arbitrary training jobs.

Runtime investigation state/logs/exports are stored under ignored `investigations/` on D:. Reviewable demonstrations and evaluation results are under `reports/v3_*`. Human notes, original run JSON and ML-knowledge files are preserved. The original V2 retrieval benchmark remains available; V3's measured source-priority policy keeps generated summaries supplementary because flat mixing degraded those labels. Reranking remains off by default.

Study [V3 architecture](docs/V3_ARCHITECTURE.md), [the learning order](docs/STUDY_V3.md), [the verified trace](docs/V3_COMPLETE_TRACE.md), [evaluation and limitations](docs/V3_EVALUATION.md), and the single uploadable [complete implementation context](docs/V3_COMPLETE_IMPLEMENTATION_CONTEXT.md).

## Preserved V1/V2 project

A local learning project for RAG and tool-using agents over saved Fashion-MNIST experiments. It keeps the original explicit agent loop and adds bounded conversation memory, hybrid note retrieval, optional reranking, deterministic analysis tools, separate ML-knowledge retrieval, a Streamlit UI, and a LangGraph version.

The included `runs/*.json` files contain the measured results. `notes/*.md` help find relevant runs; `knowledge/*.md` contains attributed general ML explanations. The app reads exact numbers from run JSON and keeps possible explanations separate from observations. No experiment retraining is required to explore V2.

## Requirements

- Windows with Python 3.12 and a local [Ollama](https://ollama.com/) server running `qwen3:1.7b`.
- Enough disk space for the Python environment, Ollama model, MiniLM embedding model, and optional reranker. Model weights and the Fashion-MNIST download are excluded from Git.

The original machine keeps Ollama and downloaded models on D:. See [OLLAMA_SETUP.md](OLLAMA_SETUP.md) for that setup; adapt its paths to your computer. Configure `OLLAMA_MODELS` before pulling a model if you need to keep its files off your system drive.

## Start on Windows

From the cloned project directory in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
ollama pull qwen3:1.7b
.\.venv\Scripts\python.exe semantic_search_notes.py "unstable validation behavior" --top-k 1
.\.venv\Scripts\python.exe app.py --agent manual
```

The semantic-search command downloads `sentence-transformers/all-MiniLM-L6-v2` once into the project-local `.model_cache/`. Later V2 searches load it locally. Ollama must be running before starting the app. The optional reranker is a separate download of roughly 62.5 MB of model weights:

```powershell
.\.venv\Scripts\python.exe download_reranker.py
.\.venv\Scripts\python.exe app.py --agent manual --rerank
```

Reranking is off by default because it lowered scores on this project's five retrieval evaluation cases.

## Choose an interface

```powershell
.\.venv\Scripts\python.exe app.py --agent manual
.\.venv\Scripts\python.exe app.py --agent graph
.\.venv\Scripts\python.exe app.py --agent simple
.\.venv\Scripts\streamlit.exe run ui.py
```

The CLI shows the tool trace by default. Type `clear` to reset session memory or `exit` to quit. Pass `--question "..."` for one question and `--no-trace` to hide the trace. The Streamlit UI has agent and reranker switches, run charts, and an expandable trace.

Try:

- `What is the final validation accuracy of lr_01_seed3?`
- `Have we seen unstable validation behavior before?`
- `Tell me about lr_01_seed3.` followed by `Compare that run with lr_005_seed3.`
- `Why might lr_01_seed3 have behaved worse than lr_005_seed3?`

## Verification and study

```powershell
.\.venv\Scripts\python.exe validate_v2.py
.\.venv\Scripts\python.exe evaluate_retrieval.py
```

The first command asks 17 manual/graph questions and saves full traces to `reports/v2_validation_traces.json`; it requires Ollama and the MiniLM cache. The second compares keyword, semantic, hybrid, and reranked results across five labeled queries; it also requires the optional reranker cache.

Start with [the architecture](docs/V2_ARCHITECTURE.md), then use [the study order](docs/STUDY_V2.md) and [the complete implementation context](docs/V2_COMPLETE_IMPLEMENTATION_CONTEXT.md). The [real V2 trace](docs/V2_COMPLETE_TRACE.md) shows how memory, experiment RAG, exact JSON, and general ML knowledge interact.

The repository includes saved metrics, examples, and documentation. It excludes downloaded datasets, model weights, virtual environments, and local caches. Retrieved similarity scores are ranking signals; observed run differences do not prove a cause.

## Development history

The project files were built locally during October 2–4, 2026 and published as milestone commits on October 19. The feature commits' author dates follow the original local artifacts; their committer dates show when this Git history was assembled and published.
