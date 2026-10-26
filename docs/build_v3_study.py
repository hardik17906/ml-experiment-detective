"""Build the V3 study set from actual source files and executed validation artifacts."""

import ast
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from v2_tools import TOOLS


def fence(value, language="json"):
    text = value if isinstance(value, str) else json.dumps(value, indent=2, ensure_ascii=False)
    return f"\n```{language}\n{text.rstrip()}\n```\n"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def excerpt(path, name):
    source = read(path)
    node = next(n for n in ast.walk(ast.parse(source)) if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == name)
    return fence("\n".join(source.splitlines()[node.lineno - 1:node.end_lineno]), "python")


ARCH = r"""# V3 architecture — Agentic Research Investigator

V3 adds a persistent research workflow to the existing local experiment assistant. The user asks an investigation question; the model selects bounded planning options and competing hypotheses; Python retrieves and measures evidence, validates citations and proposals, then suspends at a human approval gate. An explicitly approved proposal can run as a dry run or a bounded live experiment. Live results can be ingested, compared, and included in the updated investigation.

The working implementation remains local: Windows, the existing Python environment, Ollama `qwen3:1.7b`, cached MiniLM, cached Fashion-MNIST, SQLite, and Streamlit. No paid API, new language model, vector database, cloud service, or multi-agent system is required. The small SQLite adapter has an unused sqlite-vec dependency; this project does not create a vector database or use that extension.

## End-to-end graph

```mermaid
flowchart TD
    A[CLI or Streamlit] --> B[Classify request in Python]
    B -->|outside scope| C[Explain source/tool limitation]
    B -->|simple| D[Existing V2 tool path]
    B -->|investigation| E[Model selects structured plan options]
    E --> F[Discover IDs if needed and read exact run JSON]
    F --> G[Python: controls, curves, matched seed comparisons]
    G --> H[Retrieve covered ML knowledge if selected]
    H --> I[Model selects competing evidence-conditioned hypotheses]
    I --> J[Python validates evidence references]
    J --> K[Python designs and independently validates a controlled pair]
    K -->|not executable| R[Save sourced report]
    K -->|valid| L[LangGraph interrupt and durable checkpoint]
    L -->|reject or defer| R
    L -->|exact approval| M[Atomically claim configuration and mode permission]
    M --> N[Dry run or fixed bounded training worker]
    N --> O[Ingest measured outcomes if both arms finish]
    O --> R
```

The graph arranges work. It does not calculate scientific evidence or supply an explanation by itself. There is no uncontrolled graph cycle: a run has a bounded sequence of nodes, a recursion limit of 24, and at most two model attempts for each decision. A user can deliberately resume an interrupt or revise a proposal. Model failures use visibly labeled Python fallbacks.

## Responsibility boundaries

| Operation | Responsible component | Decision source |
|---|---|---|
| Identify local scope and simple/investigation route | `planner.classify` | Python heuristic |
| Select optional note search, seed analysis, ML retrieval and topic | `planner.select` / `ask_decision` | Ollama structured schema, or APP POLICY fallback |
| Require discovery without a known ID or honor explicitly requested steps | `planner.make_plan` | APP POLICY, recorded separately |
| Read saved runs, calculate curves, check controls and seed blocks | `experiment_data`, `v3.analysis` | Deterministic Python |
| Embed text and rank notes/knowledge | Existing MiniLM functions plus `v3.retrieval` | Deterministic retrieval |
| Form evidence-conditioned candidate hypotheses | `hypothesis.generate` | Python templates conditioned on measurements |
| Select/order at least two competing candidates | `select_hypotheses` tool decision | Ollama native tool call, or fallback |
| Validate citations, configuration, new seeds and resource limits | Hypothesis/designer validators | Python |
| Suspend and resume work | LangGraph interrupt, `SqliteSaver` | Framework routing/checkpointing |
| Approve/reject/defer/modify the exact proposal | CLI/UI service methods | Human action; development demos explicitly labeled dry run |
| Launch the trainer and evaluate new results | Restricted executor and outcome node | User-authorized Python |
| Render measured numbers and source labels | `report.render_report` | Python |

The model can choose useful optional work and competing explanations within a bounded menu. It cannot invent arbitrary graph nodes, rewrite the trainer, issue shell commands, or approve an experiment. Hypothesis wording is deliberately supplied by Python, not unrestricted model prose; the trace labels model selection and wording origin separately.

## Source types

- `EXPERIMENT_JSON`: exact saved configuration and measurements.
- `EXPERIMENT_NOTE`: original human observation used for discovery.
- `DERIVED_ANALYSIS`: deterministic calculation or machine-generated summary, linked to its run JSON.
- `ML_KNOWLEDGE`: a curated attributed general explanation; never evidence that a mechanism caused a particular run.
- `HYPOTHESIS`: a possible explanation with explicit assumptions, missing evidence and a proposed test.
- `TEST_FIXTURE`: simulated outcomes in isolated tests; never saved as real experiment measurements.

## Runtime data and resource use

The default SQLite database is `D:\Agentic_ai_rag projects\investigations\investigations.sqlite3`. Application snapshots, approval audit events, proposals, and LangGraph checkpoints share the local database. Markdown/JSON exports live under `investigations/reports/`. That runtime folder is ignored by Git. The reproducible demonstration export under `reports/v3_demo/` is suitable for review.

Ollama remains in `D:\Ollama`, models in `D:\Ollama\models`, MiniLM/reranker in project `.model_cache`, pip downloads in project `.pip_cache`. No model or dataset was downloaded during V3 development. The new SQLite adapter and its small dependencies were installed into the existing D: environment. Python may still read pre-existing shared packages on C:; V3 does not relocate them.

Each proposed experiment has at most two runs, five epochs per run, 10,000 training images, 2,000 fixed validation images, hidden width 128, batch size 128, SGD, two CPU threads, and 600 seconds total parent-process timeout. The worker also checks elapsed time during training batches. Workload limits and timeout are enforced; there is no Windows OS memory quota. The optional reranker remains off by default. Cold model imports can take appreciably longer than warm requests on this machine; no general latency benchmark was measured.
"""

STATE = r"""# V3 planning, state and resumption

## Five kinds of information

1. **LLM context:** the current prompt/schema and compact candidate evidence sent to Ollama. It is a bounded request, not durable memory.
2. **Conversation memory:** V2 `SessionState` remembers up to four turns, focused run IDs and reference resolution inside the current chat. Clearing it does not delete investigations.
3. **Persistent workflow state:** SQLite stores the objective, plan, exact evidence snapshots, hypotheses, proposal IDs, trace, execution outcome and report. LangGraph checkpoints store where execution stopped.
4. **Experiment knowledge:** `runs/*.json`, original `notes/*.md` and deterministically derived summaries. These survive independently of chat and investigation state.
5. **Retrieved external knowledge:** the five local `knowledge/*.md` chunks contain attributed material from external ML documentation. They are curated offline sources, not live web browsing.

## What the plan really is

`make_plan` stores a list of objects. Every step has `id`, `description`, `tool`, `depends_on`, `status` and `proposed_by`. Statuses include pending, completed, skipped, failed and waiting. A trace records the raw model decision and any Python-required additions. `optional_step_origins` distinguishes a model-selected step from one inserted to satisfy the question.

The initial model decision selects from `search_notes`, `compare_seed_pairs`, and `retrieve_knowledge`, plus one covered knowledge topic. Exact reading, deterministic checks, hypothesis grounding, independent proposal validation, and the approval gate are Python requirements. With no run ID, a note search discovers IDs, then the collection node records a visible REPLANNING event before inspecting their JSON. This is bounded evidence-driven replanning, not an open-ended autonomous research planner.

Reactive calling chooses the next tool after an observation. Planning chooses useful work before collecting evidence. Replanning changes the concrete run references after search. A deterministic workflow prescribes scientific checks and their ordering. Genuine LLM decisions select optional tools and hypothesis candidates. V3 combines these explicitly instead of calling every operation an agent decision.

## Persistence mechanics

`InvestigationStore` creates `investigations`, `proposals` and append-only `decisions` audit rows. `SqliteSaver` creates its own checkpoint tables in the same database. The store always closes SQLite connections, including on Windows. Each node saves its application document; LangGraph commits a checkpoint at the node boundary. The investigation ID is also the LangGraph `thread_id`.

An application snapshot answers “What do we know?” A checkpoint answers “Which node is next, and are we interrupted?” These are separate writes, not one transaction. Important replay behavior is therefore explicit: unchanged proposals preserve approval; execution permission is consumed atomically; a finished execution result is reused; a running execution discovered after restart is marked interrupted rather than relaunched.

`resume` opens a fresh graph/checkpointer, reads the saved snapshot, and checks `snapshot.next` and task interrupts. Loading a pending investigation does not imply approval. A stored human decision is required before sending `Command(resume=...)`. A process-restart validation closes one Python process and resumes from a completely new process.

The interrupt node restarts from its beginning when resumed. Code before `interrupt` can run twice. It can render/save the request again, but cannot launch training. Side effects that spend resources occur only after a persisted exact decision and atomic execution claim.

## Recovery limits

A failed evidence/model node can be resumed from its checkpoint; each model decision still has at most two attempts. The graph does not retry training by itself. If an app crashes while a worker might still exist, inspect the saved logs and process before making a new proposal. Partial run records remain intact; both arms are needed for post-experiment interpretation. V3 does not automatically attach a surviving Windows process, cancel it, or reconstruct a partially completed pair. Those are deliberate limits of this local implementation.

Opening a deferred/rejected proposal and explicitly approving it schedules the approval gate again. Modifying a proposal validates it, invalidates its previous approval, updates the graph state as the design node, and suspends at a fresh gate. Completed proposals cannot be edited into new experiments; create a new investigation.
"""

HYP = r"""# V3 evidence-backed hypothesis engine

## Observation, hypothesis, experiment

An observation is a saved measurement or a Python calculation over measurements. A hypothesis is a possible explanation. An experiment changes a specified variable to obtain new evidence that can discriminate explanations. The report keeps these types separate.

For the real seed-three pair, the lower rate ends at 75.90% accuracy and loss 0.6806; the higher rate ends at 71.45% and loss 0.8109. Python computes higher minus lower: -4.45 percentage points and +0.1303 loss. The lower-rate maximum consecutive-epoch positive loss rise is zero; the higher-rate rise is about 0.138654. These observations support considering instability but cannot show optimizer overshooting directly.

`analysis.compare_records` compares the union of recorded settings, reports missing controls, detects multiple changed variables, and omits final deltas when horizons/metrics are not comparable. Its matching claim applies to recorded fields. Historical JSON records hidden width and dropout settings but lacks exact model-class/trainer revision and hardware/software provenance; those remain explicit limitations. Old missing dropout/validation-start fields are not filled with assumed defaults.

`analysis.analyze` finds comparable recorded pairs for the learning rates in the question, groups by recorded controls and seed block, and deduplicates repeated configurations. The independent experimental units are distinct seed blocks, not every JSON filename. Historical pairs with missing controls remain usable as qualified descriptive evidence, never as fully verified interventions.

## Evidence registry

Exact run snapshots receive `RUN:<id>` references and content hashes. Comparisons receive `PAIR:<index>` and list both source paths. Retrieved notes receive `NOTE:<index>`; knowledge receives `ML:<chunk-id>`. A hypothesis holds references into this registry. Its experiment-support/opposition fields cannot point to general ML knowledge. Snapshot integrity is checked before proposal design.

## Competing candidates

- H1 considers learning-rate instability when comparable rate changes exist. Larger higher-rate loss rises support it; equal or smaller rises oppose that specific directional prediction. The statement remains a mechanism hypothesis.
- H2 considers seed-dependent accuracy variability. Differently signed accuracy changes across observed blocks support considering it. One positive higher-rate seed block opposes a universal “higher learning rate always lowers accuracy” claim; it does not contradict the separate loss-rise prediction.
- H3 considers a limited training horizon and endpoint sensitivity. The saved short curves motivate an evidence limitation; they do not prove that longer training reverses the outcome.
- H4 is included only when saved intervals meet the explicit falling-training-loss/rising-validation-loss rule. That is a candidate generalization warning, not a diagnosis.

If there is no rate comparison, H1 becomes a qualified configuration/unrecorded-condition candidate rather than a learning-rate assertion. At least two candidates are required. Ollama selects/orders candidates with `select_hypotheses`; Python provides grounded wording, assumptions, support, opposition and tests. This scope avoids publishing arbitrary model-generated factual claims.

Every hypothesis has `hypothesis_id`, `statement`, supporting/opposing experiment references, relevant knowledge, assumptions, missing evidence, proposed test, descriptive status, selection origin and wording origin. There are no numerical confidence percentages. “Consistent with current evidence” and “Supported by new controlled observations” do not mean a causal or statistical proof.

## Follow-up design and evaluation

The executable designer currently handles a two-arm learning-rate experiment using the existing Fashion-MNIST MLP. It starts from a complete saved reference configuration; holds all other recorded controls fixed; picks shared new model/shuffle seeds beyond recorded and reserved legacy plans; checks duplicates and unique IDs; and records the trainer hash. It does not resume the paused legacy seed-four plan.

The primary metric is each arm's largest positive consecutive-epoch validation-loss rise. Secondary metrics are final validation accuracy and loss. A larger higher-rate rise is consistent with the directional prediction; a smaller one opposes it; equality is inconclusive. A single new block cannot establish general causation. H2/H3/H4 can need different separately approved follow-ups; the current executor does not silently claim one LR pair tests every mechanism.

After both approved arms complete, output configurations and metrics are validated, run JSONs enter the same backward-compatible format, predefined metrics are computed, H1's descriptive status can update, and a new report is saved. Errors and partial completion do not produce a causal conclusion. Fixture simulations are tagged `TEST_FIXTURE` throughout, including report status, and never become saved real measurements.
"""

APPROVAL = r"""# V3 human-in-the-loop execution

## The permission boundary

The LLM menu contains planning/hypothesis decisions and existing read/analysis tools. It contains no approve, subprocess, arbitrary Python, or shell tool. Human-facing `Investigator.decide` is called by CLI/Streamlit, not by model text.

The proposal payload includes both exact run configurations, hypotheses, primary/secondary metrics, expected observations, limitations, resource limits and training-code SHA-256. A canonical JSON hash binds approval to that complete payload. The mode is stored separately as dry_run or live. A dry-run decision cannot authorize live training.

## Exact sequence

1. Python creates and independently validates the proposal.
2. `approval_node` saves a report and invokes LangGraph `interrupt` with proposal ID/hash.
3. The UI displays the full configuration, resources and hash.
4. The user approves dry run, explicitly checks live training and approves it, rejects, defers, or edits.
5. SQLite records actor, decision, exact hash, mode, reason and timestamp.
6. Resumption checks its token against the current proposal and the persisted decision.
7. The executor revalidates configuration and trainer hash, then atomically changes approved to running using `BEGIN IMMEDIATE`.
8. Only that branch can reach the fixed training worker. Permission is consumed once.

Changing epochs, seeds, learning rates or any other payload field changes the hash and invalidates approval. Approving a stale hash fails. Rejected/pending/deferred proposals cannot execute. The resume token is a reference to the reviewed object, not a permission credential. Tests explicitly attempt bypasses at each boundary.

This is a trusted local application boundary, not multi-user authentication or an operating-system security sandbox. Someone who can edit the database or Python code already controls the local machine. The `actor` label is an audit field; the safety property is that LLM tool calls cannot reach the human decision API.

## Dry run versus live execution

A dry run passes proposal validation, approval verification and the atomic claim, then records planned configurations and a completion message. It launches no trainer, creates no run JSON, and invents no measurements. Development demonstrations use actor `development_dry_run`; they are not claims that the user clicked a live approval button.

Live execution invokes a fixed `[sys.executable, '-u', '-m', 'v3.training_worker', input_path]` argument list with `shell=False`. The worker reuses `phase0.run_training`, which retains the original model, loss, optimizer, shuffle/split generators and evaluation code. V3 passes `download=False`, fixed `train=True`, and the fixed training-partition validation slice. The official test set is never read for proposal evaluation.

The executor requires cached training-partition files, sets two CPU threads, enforces 600 seconds total, writes logs and provenance, and validates outputs. Output files use exclusive creation, so old runs are never overwritten. The original `phase0.py` CLI remains available and was verified with `--dry-run`.

## Interrupt and recovery

SQLite checkpoints allow a fresh app process to resume the suspended graph. Completed results are reused after node replay. A running execution found after restart is marked interrupted and is not retried automatically. No live training was performed during V3 development; subprocess failures/timeouts and successful result ingestion were checked with clearly labeled fixtures/mocks. End-to-end live training therefore remains an explicit unverified limitation.
"""

STUDY = r"""# Study V3 in this order

1. **Read the actual experiment data.** Open `runs/lr_005_seed3.json` and `runs/lr_01_seed3.json`. Identify configuration, epoch rows, fractions versus percent, and the fixed validation split. Read `experiment_data.py`.
2. **Review one V2 reactive loop.** Read `v2_tools.py`, `v2_agent.py`, `v2_state.py` and the preserved V2 trace. Follow model tool request → validation → Python execution → tool result → next request. Clearing a conversation does not delete any experiment.
3. **Review retrieval as a tool.** Read `note_retrieval.py`, `v2_retrieval.py`, then `v3/retrieval.py`. Compare keyword terms, cosine similarity, RRF rank, source priority and exact-ID handling. Similarity is not scientific confidence.
4. **Understand structured planning.** Read `v3/planner.py` and `V3_PLANNING_AND_STATE.md`. Identify what Ollama can select and what Python requires. The planner's JSON schema and hypothesis native-tool schema are different request formats.
5. **Understand persistent state.** Read `investigation_state.py` and `service.py`. Match a database snapshot to the investigation ID and proposal row. Learn why chat memory, evidence, database snapshots and graph checkpoints are separate.
6. **Recompute the observations.** Read `analysis.py`. Check the -4.45 pp delta, the maximum loss rises, missing old controls and the positive higher-rate accuracy delta in another seed block.
7. **Study competing hypotheses.** Read `hypothesis.py` and `V3_HYPOTHESIS_ENGINE.md`. Follow each evidence reference back to its exact source. Explain why documentation cannot prove a run's cause.
8. **Study controlled proposals.** Read `experiment_designer.py`. Identify changed variable, matched controls, shared fresh seeds, predefined primary metric, duplicate checks and limits. One seed block is not a universal conclusion.
9. **Study permission and interrupts.** Read `V3_HUMAN_IN_THE_LOOP.md`, then `approval_node` and `claim_execution`. Explain why model text or a resume token cannot approve a run. Use dry-run approval in the UI.
10. **Walk the graph and recovery paths.** Read `investigation_graph.py` and `service.resume`. Draw simple versus investigation routing, rejection, dry run, measured outcome and interrupted execution branches.
11. **Read the complete verified trace.** Use `V3_COMPLETE_TRACE.md`, its real report and exported state. Distinguish model requests, Python calculations, policy decisions and development dry-run authorization event by event.
12. **Study evaluation.** Read `tests/test_v3.py`, `evaluate_v3.py`, retrieval/UI/live validation artifacts and `V3_EVALUATION.md`. Explain what a mock proves, what a real local model sample proves, and what remains untested.

Use `V3_COMPLETE_IMPLEMENTATION_CONTEXT.md` as the single uploadable reference for a tutor. It includes architecture first, commands, schemas, real evidence, trace, evaluation, responsibilities and actual implementation source. No new development milestone is needed before studying this version.
"""

COMPARISON = r"""# V2 versus V3

| Capability | V2 | V3 |
|---|---|---|
| One/two-run questions | Existing simple/manual/graph tools | Preserved; V3 simple route delegates to V2 |
| Notes and knowledge | Hybrid RRF, optional reranking | Reuses encoder; source-aware expanded retrieval with measured source policy |
| Conversation memory | Four recent turns and run references | Preserved separately from research state |
| Investigation plan | Next reactive tool choice | Structured selected steps, status, dependencies and origin |
| Persistent workflow | Process-local conversation | SQLite document + durable LangGraph checkpoints |
| Explanation | Source-aware tool answer | Competing evidence-conditioned hypotheses with opposing evidence |
| Comparisons | Exact recorded changes and final metrics | Explicit missing controls/provenance, confounding, seed-block deduplication |
| Follow-up | Historical plan artifacts | Validated machine-readable bounded pair with fresh seeds |
| Human approval | No agent training tool | Exact proposal hash and dry/live mode, persistent audit, graph interrupt |
| Execution | User-run trainer | Restricted approved worker reusing that trainer |
| New outcomes | User inspects saved runs | Validate, ingest, compare predefined metrics and update report |
| Evaluation | Five retrieval queries and V2 checks | Deterministic agent scenarios, restart/UI/live sample, retrieval ablations |

V3 is intentionally a bounded investigator. It does not claim a general autonomous scientist, arbitrary hypothesis invention, statistical inference, multi-user security, broad ML knowledge or a production job runner. Model decisions, Python reasoning rules, framework routing and human permissions remain visible. Historical V2 artifacts and original experiment data are preserved.
"""


def main():
    docs = ROOT / "docs"
    latest = json.loads(read("reports/v3_demo/latest.json"))
    state = json.loads(read("reports/v3_demo/" + latest["state"]))
    evaluation = json.loads(read("reports/v3_evaluation.json"))
    retrieval = json.loads(read("reports/v3_retrieval_evaluation.json"))
    live = json.loads(read("reports/v3_live_validation.json"))
    ui = json.loads(read("reports/v3_ui_validation.json"))
    regression = json.loads(read("reports/v3_v2_regression_traces.json"))
    acceptance = json.loads(read("reports/v3_acceptance.json"))
    ident = state["investigation_id"]
    commands = f'''# Commands and operation

Run from PowerShell in the existing project directory. Ollama must already be running with the installed qwen3:1.7b; these commands do not download models.

```powershell
cd "D:\\Agentic_ai_rag projects"
.\\.venv\\Scripts\\streamlit.exe run ui.py
```

The default workspace is **Investigations (V3)**. Start a question, select a saved investigation, inspect its seven tabs, and use Resume. Approve dry run to inspect execution without training. The separate live-training checkbox plus approve button explicitly authorizes the displayed configuration. Reject or defer stops execution. Editing validates and invalidates approval. **Chat and runs (V1/V2)** retains manual, graph and simple modes.

```powershell
.\\.venv\\Scripts\\python.exe app.py --agent research --question "Investigate why lr_01_seed3 was worse than lr_005_seed3."
.\\.venv\\Scripts\\python.exe -m v3.cli list
.\\.venv\\Scripts\\python.exe -m v3.cli show {ident}
.\\.venv\\Scripts\\python.exe -m v3.cli resume {ident}
.\\.venv\\Scripts\\python.exe -m v3.cli export {ident}
```

The displayed demonstration is already dry-run completed; resuming it does not re-execute it. For a **new pending** proposal, copy its displayed investigation ID and exact SHA-256 into this command template:

```powershell
.\\.venv\\Scripts\\python.exe -m v3.cli decide "INV-ID-FROM-START" approved --hash "SHA256-FROM-SHOW" --mode dry_run
```

Use `rejected` or `deferred` instead of `approved` to stop/defer. `--mode live` is an explicit request for the displayed two-run training workload. No live-training command was executed during development. To edit via CLI, export/copy the displayed proposal JSON to a file and use `python -m v3.cli modify "INV-ID" "proposal.json"`; the UI provides the same operation. A changed proposal needs a new approval.

```powershell
.\\.venv\\Scripts\\python.exe -m v3.cli start "Investigate why lr_01_seed3 was worse than lr_005_seed3" --offline --lexical
.\\.venv\\Scripts\\python.exe evaluate_v3.py
.\\.venv\\Scripts\\python.exe evaluate_v3_retrieval.py
.\\.venv\\Scripts\\python.exe validate_v3_ui.py
.\\.venv\\Scripts\\python.exe validate_v3_live.py
.\\.venv\\Scripts\\python.exe -m v3.demo
.\\.venv\\Scripts\\python.exe docs\\build_v3_study.py
```

`--offline` means Python planning/hypothesis fallback with honest origins. `--lexical` additionally avoids embedding imports for lightweight investigation fixtures/debugging. These flags configure research nodes; simple questions delegated to the preserved V2 agent still require local Ollama. Ordinary investigations use existing Ollama and cached MiniLM. The demo explicitly grants development **dry-run only** permission and saves reviewable Markdown/JSON in `reports/v3_demo/`.

V1/V2 commands remain `app.py --agent simple`, `--agent manual`, and `--agent graph`. The old `validate_v2.py` and `evaluate_retrieval.py` remain available. The V2 validator's output location is unchanged; the V3 development regression output was copied to `reports/v3_v2_regression_traces.json` and the original historical artifact restored.

If the local server is stopped, run `& "D:\\Ollama\\ollama.exe" serve` in another PowerShell window. Its existing user environment sets `OLLAMA_MODELS=D:\\Ollama\\models`. Do not pull a new model for V3.
'''
    trace = f"# Verified V3 investigation trace\n\nInvestigation `{ident}`. The data are real saved runs; the final execution is a **dry run**, not new measured training. The actor `development_dry_run` records authorization supplied by the V3 development request.\n\n"
    trace += "## Full report\n\n" + state["report"] + "\n## Complete event data\n\n"
    for i, e in enumerate(state["trace"], 1):
        trace += f"### Event {i}: {e['kind']} — {e.get('origin', 'PYTHON')}\n" + fence(e["data"])
    trace += "\n## Exact preserved experiment snapshots\n"
    for rid, record in state["records"].items():
        trace += f"\n### runs/{rid}.json\n" + fence(record)
    trace += "\n## Reproduce and inspect\n\n" + commands

    table = "| Method | Recall@2 | MRR@2 |\n|---|---:|---:|\n"
    for name, metrics in retrieval["means"].items():
        table += f"| {name} | {metrics['recall_at_2']:.2f} | {metrics['mrr_at_2']:.2f} |\n"
    eval_doc = f'''# V3 evaluation — executed results

The deterministic suite ran **{evaluation['tests_run']} scenarios: {evaluation['passed']} passed, {evaluation['failed_or_errors']} failed/errors**. These are scenario checks and simulated failures, not an unrestricted live-model benchmark. Live training was not performed.

## Deterministic agent checks
''' + fence(evaluation) + "\n## Retrieval ablation on the preserved five V2 queries\n\n" + table
    eval_doc += "\nRemoving stopwords improved the small benchmark. Flat mixing of generated summaries regressed, so it was rejected as the default. The selected human-priority policy computes within-source ranks, preserves human-note ordering, exposes derived summaries separately, and gives exact known run IDs priority. The six exact-ID queries for unnoted runs all succeeded in V3 and cannot succeed in V2's human-only corpus. This coverage test is deliberately distinct from semantic relevance on open-ended questions. No general performance claim is justified by five labels or six exact-ID queries.\n\n"
    eval_doc += "## UI execution\n" + fence(ui) + "\n## Live model and process restart\n" + fence({k: v for k, v in live.items() if k != "cases"})
    eval_doc += "\n" + fence([{k: v for k, v in c.items() if k not in {"trace", "answer"}} for c in live["cases"]])
    eval_doc += f"\n## Existing V2 regression\n\nAll **{len(regression['cases'])} original V2 checks** passed using local Ollama/cache. Their full new traces are in `reports/v3_v2_regression_traces.json`; the historical V2 artifact is preserved. V1's real single-run answer was also checked.\n\n"
    eval_doc += "## Scientific and operational limits\n\nStructured citation checks count invalid references; they do not measure every unsupported sentence in arbitrary model prose. An unrestricted unsupported-claim count was not measured. The renderer uses verified snapshots and Python calculations, while qualitative hypothesis candidates are explicitly labeled. Tool-selection checks are simulated named scenarios; the separate tiny live sample is not a statistically meaningful success-rate estimate. UI checks use Streamlit AppTest, not browser visual/screenshot inspection. Successful new-result ingestion and post-experiment reporting use labeled fixtures. Training failure/timeout tests mock subprocesses. Actual full training, OS memory quotas, process reattachment/cancellation, broad topic coverage and general causal validity remain unverified or outside scope.\n\n"
    eval_doc += "## Historical failures found and resolved\n\nThe first Windows run exposed unclosed SQLite connections during test cleanup; the store now closes connections explicitly. The first seed grouping mixed different learning-rate pairs; analysis now restricts to the rates being investigated and deduplicates independent recorded blocks. The first free tool-call planner returned no calls; the planner now requests schema-constrained JSON, retains two-attempt bounds and visible fallbacks. Flat expanded retrieval degraded the old labels; the measured human-priority policy replaced it. These are development findings, not hidden successful trials.\n"
    eval_doc += "\n## Acceptance evidence and stage scope\n\nStage A core investigator is implemented and exercised. Stage B approval/execution/checkpoint workflow is implemented and exercised through dry runs, mocked failures and fixture results; full live training remains unverified. Stage C UI/retrieval/evaluation/documentation is implemented and exercised within the small local corpus and Streamlit AppTest scope.\n" + fence(acceptance)

    outputs = {"V3_ARCHITECTURE.md": ARCH, "V3_PLANNING_AND_STATE.md": STATE, "V3_HYPOTHESIS_ENGINE.md": HYP,
               "V3_HUMAN_IN_THE_LOOP.md": APPROVAL, "V3_COMPLETE_TRACE.md": trace,
               "V3_EVALUATION.md": eval_doc, "V2_VS_V3.md": COMPARISON, "STUDY_V3.md": STUDY}
    for name, text in outputs.items():
        (docs / name).write_text(text.strip() + "\n", encoding="utf-8")

    files = sorted((ROOT / "v3").glob("*.py"))
    file_map = "\n# Actual file map and responsibilities\n\n| File | Defined functions/classes |\n|---|---|\n"
    for p in files:
        names = [n.name for n in ast.parse(p.read_text()).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
        file_map += f"| v3/{p.name} | {', '.join(names) or 'package marker'} |\n"
    file_map += "\nEntry points: `app.py` research mode, `v3/cli.py`, `ui.py` workspace selector, `v3/ui.py`. Tests: `tests/test_v3.py`; runners: `evaluate_v3.py`, `evaluate_v3_retrieval.py`, `validate_v3_ui.py`, `validate_v3_live.py`. Training reuse: `phase0.py` with callable `run_training`; original CLI retained. Existing tools/retrieval/state/answers live in the root V2 modules. Runtime state is in ignored `investigations/`; reviewable executed artifacts are under `reports/v3_*`.\n"
    snippets = "\n# Important actual code and why it exists\n\n"
    for path, name, explanation in (
        ("v3/planner.py", "select", "This function bounds model attempts, validates the selected object, records raw requests, and marks fallbacks as APP POLICY. It never executes model-written code."),
        ("v3/investigation_state.py", "claim_execution", "The SQL transaction serializes concurrent execution claims. Hash, status and mode must match. The consumed approval cannot be reused."),
        ("v3/experiment_designer.py", "validate_proposal", "This is an independent validator: matched controls, supported variable, trainer hash, limits, IDs and duplicate configurations are checked before approval and again before execution."),
        ("v3/investigation_graph.py", "approval_node", "LangGraph persists the interrupt. Resuming requires both a current token and a persistent user decision. A returned model string cannot authorize this branch."),
        ("v3/service.py", "resume", "A fresh graph opens the durable thread, distinguishes interrupted from runnable state, and refuses to treat reopening as approval."),
        ("v3/experiment_executor.py", "evaluate_outcomes", "The predefined metric determines consistent/opposing/inconclusive after two completed arms. One block never turns a mechanism into a proven fact.")):
        snippets += f"## {path}: {name}\n\n{explanation}\n" + excerpt(path, name)
    schemas = "\n# Exact decision schemas and existing tool schemas\n\nThe V3 planner is a schema-constrained completion, not a free-form LLM plan. The hypothesis selector is a native Ollama tool call. Their actual schemas offered during this verified demonstration follow. Python implements the read-only collection/calculation nodes; no training/approval tool is offered to the model.\n"
    for e in state["trace"]:
        if e["kind"] == "TOOL MENU":
            schemas += fence(e["data"])
    schemas += "\n## Preserved V2 callable tool menu\n" + fence(TOOLS)
    snapshot = "\n# Actual investigation state and tool data flow\n\n"
    snapshot += "Input objective → classifier route → structured model plan → known/discovered IDs → exact JSON snapshots → control/curve/seed calculations → retrieved ML chunks → evidence registry → competing hypothesis selection → citation validation → controlled proposal → durable interrupt → exact persisted decision → atomic execution claim → dry/live execution → optional outcome analysis → Python report.\n\n"
    snapshot += fence({k: state.get(k) for k in ("investigation_id", "objective", "status", "selected_steps", "knowledge_topic", "plan", "run_ids", "uncertainties", "evidence_validation", "proposal_id", "execution", "outcome")})
    snapshot += "\n## Evidence-conditioned hypotheses from the real investigation\n" + fence(state["hypotheses"])
    snapshot += "\n## Exact source registry\n" + fence(state["evidence"])
    snapshot += "\n## Complete saved-run inventory\n\n| Source | LR | Model/shuffle seed | Train size | Epochs | Dropout | Final validation accuracy | Final loss |\n|---|---:|---|---:|---:|---|---:|---:|\n"
    for path in sorted((ROOT / "runs").glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        c, last = record["config"], record["metrics"][-1]
        snapshot += f"| runs/{path.name} | {c.get('learning_rate')} | {c.get('model_seed')}/{c.get('shuffle_seed')} | {c.get('train_size')} | {c.get('epochs')} | {c.get('dropout', 'not recorded')} | {100 * last['val_accuracy']:.2f}% | {last['val_loss']:.6f} |\n"
    snapshot += "\n## Original human-note corpus and separate ML knowledge\n\nThe following source files remain unmodified. Human observations are discovery aids; JSON supplies exact measurements. Knowledge documents describe possible mechanisms and carry their original source attribution.\n"
    for folder in ("notes", "knowledge"):
        for path in sorted((ROOT / folder).glob("*.md")):
            snapshot += f"\n### {folder}/{path.name}\n" + fence(path.read_text(encoding="utf-8"), "text")
    compact_trace = "\n# Real trace: every event, with repeated evidence snapshots referenced\n\n"
    for i, e in enumerate(state["trace"], 1):
        data = e["data"]
        if e["kind"] == "EXPERIMENT EVIDENCE":
            data = {"tool": data["tool"], "run_id": data["run_id"], "record_reference": f"RUN:{data['run_id']} (full JSON in source registry above)"}
        if e["kind"] == "TOOL EXECUTION" and data.get("tool") == "analyze_experiments":
            data = {"tool": data["tool"], "result": {k: v for k, v in data["result"].items() if k != "selected_records"},
                    "selected_records_reference": "Exact RUN source registry above"}
        compact_trace += f"## Event {i}: {e['kind']} — {e.get('origin', 'PYTHON')}\n" + fence(data)
    context = ARCH + file_map + "\n" + commands + "\n" + STATE + "\n" + HYP + "\n" + APPROVAL + snippets + schemas + snapshot + compact_trace
    context += "\n# Actual final investigation report\n\n" + state["report"]
    context += "\n" + eval_doc + "\n" + COMPARISON + "\n" + STUDY
    context += "\n# Complete core implementation source\n\nThe following source is copied from the actual working files. It supports studying all graph, persistence, model-choice, approval, execution, retrieval and reporting details without fetching additional files.\n"
    core = [str(p.relative_to(ROOT)).replace('\\', '/') for p in files]
    core += ["phase0.py", "app.py", "ui.py", "experiment_data.py", "note_retrieval.py", "v2_retrieval.py", "v2_tools.py", "v2_state.py", "v2_agent.py", "v2_answers.py", "v2_analysis.py", "graph_agent.py", "simple_agent.py", "tests/test_v3.py", "evaluate_v3.py", "evaluate_v3_retrieval.py", "validate_v3_live.py", "validate_v3_ui.py", "validate_v3_acceptance.py", "requirements.txt"]
    for path in core:
        context += f"\n## {path}\n\nSHA-256: `{hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}`\n" + fence(read(path), "python")
    context += "\n# Completeness verification\n\nArchitecture, actual file map, commands, state/graph behavior, schemas, important excerpts, exact evidence, real event sequence, hypotheses, proposal/approval, report, evaluated results, limitations, study sequence, and complete core source are all included above. All numerical benchmark claims were loaded from executed report artifacts. Live training is explicitly untested.\n"
    required = ["# Actual file map", "# Commands", "# Exact decision schemas", "# Real trace", "# Actual final investigation report", "# V3 evaluation", "# Complete core implementation source", "# Completeness verification"]
    assert context.startswith("# V3 architecture")
    assert all(x in context for x in required)
    out = docs / "V3_COMPLETE_IMPLEMENTATION_CONTEXT.md"
    out.write_text(context, encoding="utf-8")
    print(f"Built {len(outputs) + 1} verified study files. Context: {len(context.splitlines())} lines, {out.stat().st_size} bytes.")


if __name__ == "__main__":
    main()
