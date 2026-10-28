# ML Experiment Detective — Agentic AI Research Assistant

A local RAG and tool-using application for exploring saved Fashion-MNIST experiments, investigating unexpected behavior, and reviewing controlled follow-up experiments before authorizing training. It combines experiment exploration, grounded chat and persistent investigations in one Streamlit interface.

## Run the installed project

In PowerShell:

```powershell
cd "D:\Agentic_ai_rag projects"
.\.venv\Scripts\streamlit.exe run ui.py
```

Open the local address printed by Streamlit (normally http://127.0.0.1:8501). Navigation offers **Overview**, **Experiment Explorer**, **AI Chat**, and **Investigations**. No run-ID knowledge is required to browse the table or start asking questions.

If Ollama is stopped, open a second PowerShell window:

```powershell
& "D:\Ollama\ollama.exe" serve
```

The installed user configuration keeps model files in `D:\Ollama\models`. The required local model is `qwen3:1.7b`. The existing MiniLM and optional reranker are under project `.model_cache/`; Fashion-MNIST is under `data/`. No additional model is required.

## Try these workflows

| Workflow | Example |
|---|---|
| Discover | What experiments do we have? |
| Rank | Which had the best final validation accuracy? |
| Follow up | Show its training and validation curves. |
| Compare | Tell me about lr_01_seed3. Then: Compare that run with lr_005_seed3. |
| Explain | Why might the difference exist? |
| RAG | Have we seen unstable validation-loss behavior before? |
| Investigate | Investigate why lr_01_seed3 underperformed. |
| Design | What should we test next? |

Every chat response has an expandable explanation of tools, model choices, Python policy, retrieval and sources. The Explorer displays exact settings and curve comparisons. The Investigation Workspace saves plans, evidence, hypotheses, proposals, decisions, execution information and reports.

## Approval and execution

Questions and proposals do not authorize training. Review the entire proposal in Investigations, then approve a **dry run**, reject, defer, modify, or explicitly authorize **live training**. Permission is tied to the exact configuration hash and mode; editing invalidates it. A dry run creates no training measurements.

The restricted executor reuses the original Fashion-MNIST MLP and training-partition split. It supports a two-run learning-rate intervention, shared fresh seeds, maximum five epochs per arm, two CPU threads and a 600-second total budget. It rejects duplicate IDs/configurations and preserves original files. Live work runs in the background; refresh its saved status or request cooperative cancellation. The CLI can also request cancellation. No arbitrary shell command is accepted from an LLM.

**Full live training was not performed during final development.** Approval, dry-run execution, failures, cancellation boundaries, ingestion and post-experiment reporting are tested through dry runs, mocks and labeled fixtures. This is a trusted single-user local application, not a production job scheduler or multi-user permission system.

## CLI

```powershell
.\.venv\Scripts\python.exe app.py --question "What experiments do we have?"
.\.venv\Scripts\python.exe app.py
.\.venv\Scripts\python.exe app.py --offline --lexical --question "Investigate why lr_01_seed3 underperformed."
.\.venv\Scripts\python.exe investigate.py list
.\.venv\Scripts\python.exe investigate.py show "INV-ID-FROM-LIST"
.\.venv\Scripts\python.exe investigate.py resume "INV-ID-FROM-LIST"
.\.venv\Scripts\python.exe investigate.py export "INV-ID-FROM-LIST"
.\.venv\Scripts\python.exe investigate.py cancel "INV-ID-FROM-LIST"
```

Replace quoted ID placeholders with an actual saved investigation ID. `app.py` uses the integrated assistant by default; `clear` resets chat memory and `exit` quits. `--offline` uses visibly labeled Python choices without Ollama; `--lexical` additionally avoids embedding imports. These primary-assistant options work without internet after Python dependencies are installed. `investigate.py` retains explicit research operations, including `decide`/`modify`; its research `--offline` flag disables research model decisions. Normal operation uses only localhost and cached files.

The manual loop and historical agents remain educational references:

```powershell
.\.venv\Scripts\python.exe app.py --agent manual
.\.venv\Scripts\python.exe app.py --agent graph
.\.venv\Scripts\python.exe app.py --agent simple
```

## Fresh setup and downloads

The original machine already has the environment and caches. On a new Windows/Python 3.12 installation, initial package and model setup needs internet and disk space. Put the clone/environment on the intended drive and set caches before downloading:

```powershell
py -3.12 -m venv .venv
$env:PIP_CACHE_DIR = Join-Path (Get-Location) '.pip_cache'
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:OLLAMA_MODELS = 'D:\Ollama\models'
ollama pull qwen3:1.7b
.\.venv\Scripts\python.exe semantic_search_notes.py "unstable validation behavior" --top-k 1
```

Install Ollama itself using [the existing D: setup notes](OLLAMA_SETUP.md), adapting paths to the new machine. Persist `OLLAMA_MODELS` before launching its server if needed. The semantic command populates project `.model_cache/`; subsequent normal retrieval uses local-only weights. Reranking is optional and off by default; `download_reranker.py` is the explicit initial download command if desired. Fresh training-data setup is separate; the approved executor refuses to download a missing dataset. The original `phase0.py` remains the user-operated dataset/training entry point; its `--dry-run` validates a configuration without training or downloading data.

## Reproduce checks

```powershell
.\.venv\Scripts\python.exe evaluate_final.py
.\.venv\Scripts\python.exe validate_final_ui.py
.\.venv\Scripts\python.exe evaluate_final_retrieval.py
.\.venv\Scripts\python.exe demonstrate_final.py --live
.\.venv\Scripts\python.exe docs\build_final_docs.py
```

Deterministic checks do not train models. Retrieval evaluation needs cached MiniLM and, for actual reranking scores, the cached optional cross-encoder. `demonstrate_final.py --live` uses real local language/embedding models but grants only development **dry-run** experiment permission. Final executed artifacts are under `reports/final/`; historical evaluations are preserved separately. A small local benchmark is not a general scientific or model-quality guarantee.

## Learn the finished implementation

1. [Complete learning guide: 30 beginner-first chapters](docs/FINAL_COMPLETE_LEARNING_GUIDE.md).
2. [Code walkthrough with actual line references](docs/FINAL_CODE_WALKTHROUGH.md).
3. [Actual end-to-end investigation trace](docs/FINAL_END_TO_END_TRACE.md).
4. [Single self-contained master context for an AI tutor](docs/FINAL_PROJECT_MASTER_CONTEXT.md).
5. [Audit and final scope](docs/FINAL_AUDIT.md).

The guide derives cosine similarity, RRF, evaluation metrics and experiment calculations, then connects each concept to actual code and outputs. The master reference begins with the architecture and includes schemas, state, evidence, evaluation, limitations and source excerpts. Earlier learning guides remain available; the linked guides describe the complete application.

## Data, models and limits

`runs/*.json` holds measured experiment records; `notes/*.md` holds the five original observation notes; `knowledge/*.md` holds attributed local ML references. Clearly labeled derived summaries expand discovery to runs without notes. Knowledge can suggest mechanisms but cannot prove a particular run's cause. Numerical answers come from Python and saved data.

Runtime SQLite checkpoints, investigation state, execution logs and exports live under ignored `investigations/`. Model weights, datasets, virtual environments, secrets and local caches are excluded from Git. Current package versions and D: locations are recorded in `reports/final/environment.json`.

The model selects bounded tools and hypotheses; Python prescribes scope checks, measurements, validation and permission. Missing historical architecture/software provenance, one reused validation split, a small corpus, imperfect retrieval and a restricted executable intervention family limit conclusions. Scores rank documents; they are not hypothesis probabilities. Interrupted live execution is not automatically retried or reattached.

## Development history

The original project files were built locally during October 2–4, 2026 and published as milestone commits on October 19. Their author dates follow the original local artifacts; committer dates show when that Git history was assembled and published. The persistent investigator extends the original tool workflow; the final integration completes its local user workflows and learning package. This concludes the planned development scope.
