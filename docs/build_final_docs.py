"""Generate faithful final learning artifacts from authored lessons, source and executed outputs."""
import ast
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from v2_tools import TOOLS


def read(path):return (ROOT/path).read_text(encoding="utf-8")
def load(path):return json.loads(read(path))
def block(value,lang="json"):
    return "\n```"+lang+"\n"+(value if isinstance(value,str) else json.dumps(value,indent=2,ensure_ascii=False)).rstrip()+"\n```\n"


def excerpt(path,name,limit=32):
    source=read(path)
    tree=ast.parse(source)
    node=next(n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name)
    end=min(node.end_lineno,node.lineno+limit-1)
    return f"\nActual source: `{path}:{node.lineno}`–`{end}`; excerpt of `{name}` (remaining lines, if any, are not reproduced here).\n"+block("\n".join(source.splitlines()[node.lineno-1:end]),"python")


ARCH=r'''# ML Experiment Detective — Final Project Master Context

## Architecture and purpose

This is the complete local experiment research application. It supports experiment exploration, conversational analysis, retrieval-augmented investigation, competing hypotheses, controlled proposals and explicitly approved bounded execution. Original measurements/notes remain intact. Full live training remains unverified pending explicit approval; final demonstrations execute dry runs only.

```mermaid
flowchart TD
    UI[Streamlit: Overview / Explorer / Chat / Investigations] --> A[ResearchAssistant facade]
    CLI[Primary CLI] --> A
    A --> M[Resolve bounded conversation references]
    M --> C[Persistent LangGraph classify node]
    C -->|unrelated / unknown / ambiguous| LIMIT[Explain limitation or ask clarification]
    C -->|simple| TG[Compact tool-choice graph]
    TG --> TOOLS[Validated registry: exact data, ranking, curves, notes, ML knowledge]
    TOOLS --> TG
    TG --> ANSWER[Python source-aware answer]
    C -->|research| P[Structured model plan + required Python checks]
    P --> R[Retrieve notes / read exact JSON / find recorded controls]
    R --> D[Python curve and seed analysis]
    D --> K[Separate attributed ML knowledge]
    K --> H[Evidence-conditioned hypotheses / model selects competitors]
    H --> V[Validate evidence and controlled proposal]
    V --> G[SQLite checkpoint + human approval interrupt]
    G -->|reject / defer| REPORT[Sourced report]
    G -->|exact approved hash + mode| EXEC[Restricted dry run or fixed training worker]
    EXEC --> OUT[Validate both measured arms and compare predefined metrics]
    OUT --> REPORT
```

### Responsibility and source boundaries

Qwen selects tools, optional plan steps and bounded competing hypotheses. Python resolves exact references, corrects explicit argument constraints, enforces scope, computes all numbers, validates configurations/citations, builds evidence-conditioned candidate wording, renders measured claims and enforces approval. LangGraph controls branching/checkpoints; it does not create scientific truth. User decisions alone authorize live resource use. Every fallback is labeled APP POLICY or APP FILTER.

Structured `runs/*.json` supplies exact settings/measurements. Original `notes/*.md` supplies discovery observations. Runtime-derived summaries are labeled DERIVED_ANALYSIS and point to JSON. Local `knowledge/*.md` supplies attributed general mechanisms, never proof of what caused a run. Hypotheses are labeled HYPOTHESIS. Tests use TEST_FIXTURE provenance and never create real run measurements.

### Main data flow and memory

`ResearchAssistant.ask` captures question/session state, resolves straightforward references and routes through `Investigator.start`. Simple requests reach the compact graph with the shared tool registry. Research creates a structured plan, collects exact snapshots, analyzes differences, retrieves knowledge, validates hypotheses/proposals and interrupts. The same database persists plan/status, tool history, hypotheses, proposal hashes, decision audit and graph checkpoints.

The conversation `SessionState` remembers four compact turns, a single focused run and the last comparison pair. The UI keeps a bounded visible chat list. A reset does not delete experiments or investigations. SQLite snapshots record what is known; checkpoints record where execution can resume. The model sees a bounded prompt/schema, not the full durable database. No embedding model is used for reference memory.

### Permission and execution

Approval is tied to proposal ID, canonical JSON hash and dry/live mode. Changing a proposal invalidates permission. The executor revalidates the trainer hash/configuration, atomically consumes approval and prevents concurrent live jobs. It accepts no model-written shell command. The fixed worker calls the original `phase0.run_training` with downloads disabled and exclusive output creation. The official test partition is excluded.

The supported intervention is a two-arm learning-rate comparison using shared fresh seeds, existing Fashion-MNIST MLP, fixed split/batch/hidden settings, at most five epochs per arm, two CPU threads and a 600-second total parent budget. Cancellation is cooperative between batches. Completed partial outputs survive; uncertain running work after restart is marked interrupted rather than relaunched. There is no hard OS RAM quota or automatic process reattachment.

### Retrieval algorithms and mathematics

Keyword overlap counts shared normalized tokens while preserving negation. MiniLM produces 384-dimensional vectors; cosine is `(a·b)/(||a|| ||b||)`. Reciprocal Rank Fusion is `sum_m 1/(60+rank_m)`. The primary source policy computes within-source ranks, prioritizes human notes for broad behavior search, exposes derived summaries separately and honors exact run IDs. Optional cross-encoder reranking retains source/identifier constraints. Retrieval scores are not probabilities. At this collection size documents are encoded for a request; the model object is cached, but no persistent vector database or ANN index is used.

### Numerical and scientific rules

Target-minus-baseline accuracy change is `100*(target_fraction-baseline_fraction)` in percentage points. Maximum positive loss rise is `max(0,L[t+1]-L[t])`. Best epoch, final epoch, minimum loss, recovery patterns and available train/validation gaps are calculated in Python. Changed settings, missing controls, different horizons, incomplete metrics and missing architecture/software provenance remain visible. Recorded seed blocks are deduplicated; a small descriptive mean is not a causal proof or confidence interval.

Higher-rate loss-rise ordering tests H1's predefined prediction; seed-dependent accuracy variation is a different hypothesis. General knowledge can suggest a mechanism but cannot establish the cause of an individual run. Fresh seed proposals respect recorded configurations and reserved legacy plans. One matched block does not establish general causation.
'''

COMPONENTS={
 "simple_agent.py":("Original native tool-using educational reference","answer_question","Shows the original bounded native-tool loop and its smaller allowed menu. Its semantic search reuses the shared encoder and its exact reads use experiment_data. It remains a reference CLI mode; the final primary application adds stronger scope, memory, graph/persistence and model-failure handling."),
 "legacy_ui.py":("Earlier educational UI and compatibility checks","render_v2","Keeps the older chat/run view and manual/graph/simple selection used by historical UI checks. It is not the recommended entry point. The current ui.py replaces its navigation with one coherent application while reusing the actual tools and investigation workspace."),
 "assistant.py":("Primary facade and shared conversation entry","ask","Captures the original/resolved question, checks ambiguous/unknown IDs, calls the durable investigator, records actual results in bounded conversation memory, and returns answer/trace/status. Inputs are text and SessionState; outputs are a result dictionary. Invalid references return helpful clarification/alternatives before evidence calls."),
 "ui.py":("Recommended four-area Streamlit interface","draw_run","Reads exact run data into tables/charts, displays local status and examples, retains chat state, and delegates research controls to v3.ui. Streamlit reruns the script on interaction; session state persists objects. UI errors become readable messages; API results remain inspectable in expanders."),
 "investigate.py":("Persistent investigation CLI entry point","main","Delegates start/list/show/resume/decide/modify/export/cancel to the tested research CLI. It preserves exact proposal hash/mode checks and existing stored investigations."),
 "app.py":("Primary interactive/single-question CLI and educational mode switches","main","Argparse selects the integrated assistant by default; manual/graph/simple/research aliases remain. Interactive clear resets only conversation memory. --offline and --lexical bound dependencies for the primary assistant. Errors print an evidence/application limitation."),
 "experiment_data.py":("Exact JSON read/filter/compare boundary","load_run","Validates IDs and epoch ordering, reads source records, filters explicit settings and computes final deltas. Paths are derived under runs; source IDs and file metadata are never supplied by unvalidated generated prose."),
 "note_retrieval.py":("Shared MiniLM encoding and baseline text/vector operations","cosine_similarity","Loads original observations, tokenizes baseline words, caches the installed encoder object and computes cosine ranking. Encoder arrays stay associated with document paths during sorting. Model revision/cache location are explicit; current queries use local-only weights."),
 "v2_retrieval.py":("Preserved baseline hybrid/reranker and local knowledge corpus loader","hybrid_search_notes","Loads note/knowledge metadata, applies historical ranking for baseline comparisons and supplies the cached optional cross-encoder. New primary note policy reuses its encoder/reranker rather than introducing another embedding implementation."),
 "v2_tools.py":("Shared allowlisted tool schemas and dispatcher","execute_tool","Checks names, required/extra fields, types, enum membership, finite numeric values and booleans before calling a handler. The registry includes ranking and existing read/search/analysis tools; it offers no approval or arbitrary execution tool to the model."),
 "v2_agent.py":("Shared turn preparation, policy, tool observation and manual reference loop","choose_next","The primary graph uses choose_next for one bounded model choice and transparent fallback. execute_call applies explicit user constraints, dispatches allowed tools, records full trace and feeds compact tool messages to the next model choice. run_manual retains the educational while-loop implementation."),
 "v2_state.py":("Bounded conversation and reference resolution","resolve","Uses explicit focused IDs and comparison pairs, not embeddings. Resolves corresponding-rate partners using recorded controls, tracks ranking focus, retains four turns and asks for clarification when a singular reference has no unique focus. clear resets every conversation reference."),
 "v2_answers.py":("Deterministic source-aware conversational answer renderer","render_answer","Groups successful Python results into observations, reference knowledge, interpretations, uncertainty and sources. Numeric formatting is downstream of tool calculations; no LLM arithmetic or invented source URL is required."),
 "v2_analysis.py":("Reusable measured ranking, curve summaries and descriptive heuristics","rank_experiments","Reads saved metrics, supports exact configuration filters, ranks accuracy/loss/spikes, returns chart points, and flags possible generalization intervals. Descriptive ranking is not statistical inference and does not silently match confounded records."),
 "graph_agent.py":("Compact reactive graph reused for simple questions","build_graph","agent_node calls shared choose_next, tools_node dispatches the pending allowed request, and final_node renders successful evidence. Conditional routing stops when the menu is empty, a tool fails, or the bounded call budget is exhausted."),
 "v3/planner.py":("Request classification and bounded model planning/hypothesis choices","select","Classifies local scope and complexity, requests schema-constrained planning or a native hypothesis tool call, validates choices, bounds attempts at two and records policy fallbacks. make_plan records step dependencies/status/origin and required user-requested additions."),
 "v3/investigation_state.py":("SQLite snapshots, proposals, audit history and atomic execution permission","claim_execution","Stores application JSON separately from framework checkpoints in one local database. Connection contexts close handles explicitly. Canonical hashes bind approval to configuration. claim_execution serializes permission consumption and limits active live work; actor labels are local audit fields, not authentication."),
 "v3/analysis.py":("Investigation-specific validation, controlled comparisons and seed blocks","compare_records","Checks metric completeness, compares the union of configuration keys, reports absent controls/provenance, computes curve statistics and deduplicates seed groups. matched_runs finds recorded partners. Missing required evidence suppresses deltas or executable proposals rather than filling defaults."),
 "v3/retrieval.py":("Primary source-aware note retrieval and guarded knowledge retrieval","search_notes","Builds human or clearly derived documents, filters exact configurations before matching, normalizes tokens, reuses MiniLM, fuses ranks and exposes all stages/scores. Exact-ID and human-source priorities are explicit. Knowledge remains a separate corpus with covered-topic and lexical fallback behavior."),
 "v3/hypothesis.py":("Evidence registry, competing candidates and reference validation","validate_evidence","build_evidence assigns source IDs and snapshot hashes. generate constructs measurement-conditioned candidate mechanisms; the model selects at least two. Validation rejects nonexistent references, knowledge used as experiment support, changed snapshots and missing competition. Statuses remain descriptive."),
 "v3/experiment_designer.py":("Machine-readable controlled learning-rate proposals and independent validator","validate_proposal","Creates two supported arms from a complete saved baseline, picks shared seeds beyond existing/reserved configurations and declares a primary metric. Validation enforces exact supported fields, unique IDs/configurations, matched controls, trainer hash and bounded resources."),
 "v3/experiment_executor.py":("Only approved bounded execution and measured result interpretation","execute","Rechecks hash/configuration, atomically claims permission, either completes a no-training dry run or launches a fixed subprocess. It writes logs/provenance, respects timeout/cancellation, validates output records and records failures. ingest_record and evaluate_outcomes support labeled fixture tests without creating real data."),
 "v3/training_worker.py":("Fixed worker calling the original trainer","main","Reads the application-produced input JSON, validates configuration and fixed output path, sets two torch threads, and calls phase0.run_training with download=False, provenance, timeout and cancellation marker. This module is not an LLM shell tool."),
 "phase0.py":("Original Fashion-MNIST model, evaluation and callable training implementation","run_training","SimpleMLP and evaluate preserve the existing model/evaluation code. run_training takes explicit config/output/provenance and optional runtime/cancel limits. Its split/shuffle/model generators preserve recorded semantics; new output uses exclusive creation. main preserves user-operated CLI and dry-run configuration output."),
 "v3/investigation_graph.py":("Primary durable graph with explicit conditional scientific workflow","approval_node","Classifies, plans, collects, measures, retrieves knowledge, selects/validates hypotheses, designs, interrupts, executes and reports. Simple questions delegate to the compact graph. Approval checks persistent decisions; execution reuses completed results or marks uncertain work interrupted. Nodes save application snapshots at explicit boundaries."),
 "v3/service.py":("Shared UI/CLI lifecycle operations for saved investigations","resume","start creates a thread/document and records failures; resume distinguishes pending interrupts from runnable nodes and never treats opening as approval. decide stores exact human decisions; modify invalidates permission and re-schedules approval; export writes Markdown/JSON; cancel requests cooperative stop through a fixed marker."),
 "v3/report.py":("Grounded persistent research report renderer","render_report","Renders the objective, exact observations, recorded controls, hypotheses and evidence registry, ML references, uncertainties, proposal hash, audit/execute status and outcomes. When no measured follow-up exists it says so explicitly."),
 "v3/ui.py":("Investigation plan/evidence/hypothesis/approval/execution/report controls","render_investigations","Uses the shared service and SQLite state. Human controls review exact JSON/hash, approve dry/live, reject/defer or modify. Live decisions run in a background thread so refresh/cancellation remain usable. UI traces expose model and policy origins; completed futures surface exceptions."),
 "v3/cli.py":("Explicit persistent research operation CLI","main","Supports start/list/show/resume/decide/modify/export/cancel. Exact IDs and proposal hashes are required for sensitive operations. Its research offline/lexical flags are separate from the integrated app.py interface."),
 "evaluate_final.py":("Combined deterministic scenario runner","main","Discovers retained core and integrated tests, records individual success/failure details and exits nonzero on failure. This suite contains mocks and fixtures; it does not claim live-model or live-training success."),
 "evaluate_final_retrieval.py":("Frozen relevance labels and separate exact-ID coverage benchmark","main","Runs original five plus twelve additional labeled queries across keyword, semantic, hybrid and reranked paths, then separately checks six unnoted IDs. Scores and actual top IDs are saved; new local judgments are not a hidden unbiased test set."),
 "demonstrate_final.py":("Six requested user journeys and real investigation artifact producer","main","Runs exploration, conversation, RAG, investigation, approval and error journeys; --live uses actual installed models. It explicitly proves pending/rejected execution rejection and grants only development dry-run permission. It saves the full investigation and timing/event data."),
 "validate_final_ui.py":("Integrated UI widget and result verification","main","Uses Streamlit AppTest with isolated SQLite state, exercises all four navigation areas, comparison/filter/chat references, research creation/resume, dry-run approval and export. It does not inspect browser screenshots or start real training."),
 "tests/test_final.py":("Integrated final user journeys and failure-boundary scenarios","FinalApplicationTests","Isolates SQLite state for each scenario and exercises exact ranking, single/pair/corresponding references, ambiguity/reset, unknown IDs, local scope, single/no-ID proposal discovery, model failure, cancellation and active-execution limits. Live training is mocked or prevented."),
 "tests/test_v3.py":("Preserved scientific workflow, approval, persistence and fixture scenarios","InvestigatorTests","Retains the original 56 checks over real saved data plus labeled in-memory fixtures. It verifies numerical comparison, missing controls, confounding, source grounding, proposal constraints, permission bypasses, resume/recovery, failure/timeout and post-experiment updates without publishing synthetic measurements."),
 "verify_final.py":("Final data, artifact, document and launch acceptance check","main","Verifies original data hashes, recorded tests/UI/compatibility/journeys, actual model events, dry-run completion, absence of new training records, all four documents, thirty chapters and embedded source/hash integrity. It reads the local Streamlit health endpoint and records COMPLETE only if every supported-scope check passes."),
}


def table(scores):
    return "| Method | Recall@2 | MRR@2 |\n|---|---:|---:|\n"+"".join(f"| {m} | {v['recall_at_2']:.4f} | {v['mrr_at_2']:.4f} |\n" for m,v in scores.items())


def main():
    out=ROOT/"docs"
    state=load("reports/final/investigation.json")
    journeys=load("reports/final/journeys.json")
    deterministic=load("reports/final/deterministic.json")
    retrieval=load("reports/final/retrieval.json")
    ui=load("reports/final/ui.json")
    env=load("reports/final/environment.json")
    compatibility=load("reports/final/compatibility.json")
    identifier=state["investigation_id"]
    commands=f'''## Exact commands and study operation

```powershell
cd "D:\\Agentic_ai_rag projects"
.\\.venv\\Scripts\\streamlit.exe run ui.py
.\\.venv\\Scripts\\python.exe app.py --question "What experiments do we have?"
.\\.venv\\Scripts\\python.exe app.py --offline --lexical --question "Investigate why lr_01_seed3 underperformed."
.\\.venv\\Scripts\\python.exe investigate.py list
.\\.venv\\Scripts\\python.exe investigate.py show {identifier}
.\\.venv\\Scripts\\python.exe investigate.py resume {identifier}
.\\.venv\\Scripts\\python.exe investigate.py export {identifier}
```

The recorded demonstration is dry-run completed; resume does not retrain it. Start a new objective in the UI for a new pending proposal. Inspect its exact parameters and hash before deciding. A decision template for a new pending proposal is:

```powershell
.\\.venv\\Scripts\\python.exe investigate.py decide "INV-ID-FROM-LIST" approved --hash "EXACT-HASH-FROM-SHOW" --mode dry_run
.\\.venv\\Scripts\\python.exe investigate.py cancel "INV-ID-FROM-LIST"
```

Replace quoted placeholders with the displayed ID/hash. `rejected`/`deferred` are alternative decisions. `--mode live` is a distinct explicit authorization for the displayed workload; no live-training command was run during final development. Editing uses `modify ID proposal.json` or the UI, invalidates approval and requires review again. Completed proposals cannot be repurposed through another execution; create a new proposal/investigation.

The installed environment/caches permit local/offline operation. Primary `--offline --lexical` avoids Ollama and embedding imports; ordinary operation uses localhost and local-only model weights. Fresh setup requires internet for Python packages and initial Ollama/MiniLM weights; the optional reranker has its own explicit download. The restricted executor refuses missing datasets rather than downloading them. README gives the exact new-install setup and D: environment configuration.

```powershell
.\\.venv\\Scripts\\python.exe evaluate_final.py
.\\.venv\\Scripts\\python.exe validate_final_ui.py
.\\.venv\\Scripts\\python.exe evaluate_final_retrieval.py
.\\.venv\\Scripts\\python.exe demonstrate_final.py --live
.\\.venv\\Scripts\\python.exe docs\\build_final_docs.py
```

The educational references remain `app.py --agent manual`, `--agent graph`, `--agent simple`, and `legacy_ui.py`. The main application no longer requires selecting a historical version. Follow the learning guide's 30 chapters, then open the walkthrough beside source, then follow the complete runtime trace, then reproduce selected checks. Development is complete within the stated bounded scope; the next activity is study.
'''
    evaluation=f"## Actual final evaluation\n\nDeterministic suite: **{deterministic['passed']}/{deterministic['tests_run']} passed**, {deterministic['failures']} failures/errors. UI checks: **{ui['passed']} passed**. Final journeys used **{journeys['mode']}**. Separate compatibility/process-restart sample: **{compatibility['passed']}/{compatibility['total']} passed**. These are different evaluation scopes, not one blended model success rate.\n\n"
    evaluation+="### Original five labels under current methods\n\n"+table(retrieval["historical_five"])
    evaluation+="\nHistorical hybrid on those labels was 0.90 Recall@2 and 0.90 MRR@2; its separate archived artifacts remain intact.\n\n### Additional twelve local relevance labels\n\n"+table(retrieval["additional_twelve"])
    evaluation+="\n### All seventeen note-relevance labels\n\n"+table(retrieval["all_seventeen"])
    evaluation+=f"\nExact unnoted-ID coverage: {sum(x['found_first'] for x in retrieval['exact_unnoted_coverage'])}/{len(retrieval['exact_unnoted_coverage'])} found first. This is a separate identifier-coverage task, not semantic-relevance accuracy. Reranking remains off by default. Labels were frozen before scoring; no endless tuning was done after the expanded evaluation.\n"
    misses=[dict(id=c["id"],query=c["query"],relevant=c["relevant"],hybrid=c["methods"]["hybrid"]) for c in retrieval["cases"] if c["methods"]["hybrid"]["recall_at_2"]<1]
    evaluation+="\n### Observed primary-retrieval misses\n"+block(misses)
    evaluation+="\nNo unrestricted natural-language unsupported-claim percentage was measured. Structured grounding and approval checks are scenario assertions; live training remains untested. AppTest is UI execution, not browser visual inspection. An initial compatibility attempt encountered an unavailable Ollama server. The initial final investigation also used policy fallbacks for planning and hypotheses; that trace is preserved in reports/final/initial_investigation_fallback.json and initial_journeys.json. Ollama was restarted with its existing D: models. The final rerun recorded actual LLM planning and hypothesis selections, and compatibility passed separately. A server outage or fallback is not labeled as a successful model choice.\n"
    evaluation+="\n### Measured journey timings\n\n| Journey | Question | Seconds | Status |\n|---|---|---:|---|\n"
    for r in journeys["results"]:
        if "elapsed_seconds" in r:evaluation+=f"| {r['journey']} | {r['question']} | {r['elapsed_seconds']:.3f} | {r['status']} |\n"
    evaluation+="\nThese are observed local request durations for this run, not a controlled latency benchmark; caching, model startup and contention affect timing.\n"
    acceptance_path=ROOT/"reports/final/acceptance.json"
    if acceptance_path.exists():
        accepted=json.loads(acceptance_path.read_text(encoding="utf-8"))
        evaluation+="\n### Final artifact acceptance\n"+block({k:v for k,v in accepted.items() if k!="master_bytes"})

    guide=read("docs/final_lessons.md")
    guide=re.sub(r"<!-- CODE ([^:]+)::([^ ]+) -->",lambda m:excerpt(m[1],m[2]),guide)
    assert len(re.findall(r"^## Chapter \d+",guide,re.M))==30
    assert "<!-- CODE" not in guide
    guide+="\n# Executed results and operation\n\n"+evaluation+"\n"+commands+"\n## Verified model/environment inventory\n"+block(env)
    (out/"FINAL_COMPLETE_LEARNING_GUIDE.md").write_text(guide,encoding="utf-8")

    walkthrough="# Final Code Walkthrough\n\nOpen a source file beside this reference. Line numbers and excerpts are generated from the actual final files; they are not invented examples. The learning guide explains the concepts; this document explains responsibilities and control flow. Static call names below are syntactic references, not proof that every branch ran in the real trace.\n\n"
    symbols={}
    for path in COMPONENTS:
        tree=ast.parse(read(path))
        for n in ast.walk(tree):
            if isinstance(n,ast.Call):
                name=n.func.id if isinstance(n.func,ast.Name) else n.func.attr if isinstance(n.func,ast.Attribute) else None
                if name:symbols.setdefault(name,set()).add(path)
    for path,(purpose,selected,explanation) in COMPONENTS.items():
        source=read(path); tree=ast.parse(source)
        imports=[]
        for n in tree.body:
            if isinstance(n,(ast.Import,ast.ImportFrom)):imports.append(ast.unparse(n))
        routines=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))]
        walkthrough+=f"## {path}\n\n**Absolute path:** `{ROOT/path}`\n\n**Purpose:** {purpose}.\n\n{explanation}\n\n**Dependencies:** "+"; ".join(f"`{x}`" for x in imports)+".\n\n"
        walkthrough+="**Main symbols and input contracts:**\n\n"
        for n in routines:
            sig=f"{n.name}({ast.unparse(n.args)})" if isinstance(n,ast.FunctionDef) else n.name
            walkthrough+=f"- `{sig}` — source line {n.lineno}.\n"
        selected_node=next(n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==selected)
        calls=sorted({ast.unparse(n.func) for n in ast.walk(selected_node) if isinstance(n,ast.Call)})
        callers=sorted(symbols.get(selected,set())-{path})
        errors=sorted({ast.unparse(n.exc) for n in ast.walk(tree) if isinstance(n,ast.Raise) and n.exc is not None})
        walkthrough+="\n**Who references this selected routine:** "+(", ".join(callers) if callers else "Entry-point/framework callbacks or method dispatch; inspect the runtime trace for the actual caller")+".\n\n"
        walkthrough+="**What the selected routine calls:** "+", ".join(f"`{c}`" for c in calls)+".\n\n"
        walkthrough+="**Error/control boundaries:** "+("; ".join(f"`{e}`" for e in errors) if errors else "Delegated exceptions propagate to the service/UI/CLI boundaries described above; absence of an explicit raise is not absence of failure")+".\n"
        walkthrough+=excerpt(path,selected,40)
        walkthrough+="\n**How to follow it:** identify inputs at the function boundary, follow the called routines above, compare the returned dictionary/state with the saved tool result, and inspect the caller's next branch. Argument/state keys are contracts between these components; changing a key requires corresponding callers and tests to change. See the complete guide for mathematical meaning and the real trace for executed inputs/outputs.\n\n"
    walkthrough+="## Non-obvious implementation lines\n\n"
    annotations=[("v2_tools.py","isinstance(value, bool)","Python booleans inherit from int, so explicit exclusion prevents True from being accepted as an integer count or seed."),
                 ("phase0.py","total_loss += loss.item() * len(labels)","Weights each batch loss by its actual size, preserving the dataset mean when the last batch is short."),
                 ("v3/investigation_state.py","BEGIN IMMEDIATE","Serializes the read/check/write permission transition so concurrent requests cannot both consume one approval."),
                 ("v3/investigation_graph.py","token = interrupt","Durably suspends the graph. The node restarts when resumed; resource-consuming effects must occur after decision verification."),
                 ("v3/experiment_executor.py","shell=False","Runs a fixed argument list instead of interpreting model text as shell code."),
                 ("v3/experiment_executor.py","log.open(\"x\"","Exclusive creation prevents overwriting an existing log from an earlier execution attempt."),
                 ("v3/experiment_designer.py","training_code_sha256","Binds a proposal to the reviewed trainer implementation as well as parameter settings."),
                 ("v3/retrieval.py","within_source","Adding derived summaries must not silently perturb human-note rank positions; source priority is part of the measured ranking policy."),
                 ("v3/ui.py","pool.submit","Runs only an explicitly approved live decision in the background so UI refresh/cancellation remain possible."),
                 ("phase0.py","cancel_path is not None","Cancellation is checked between training batches; a marker does not interrupt every possible native operation instantly.")]
    for path,needle,explanation in annotations:
        hits=[(i,l) for i,l in enumerate(read(path).splitlines(),1) if needle in l]
        assert hits,(path,needle)
        line,text=hits[0]
        walkthrough+=f"### {path}:{line}\n"+block(text.strip(),"python")+"\n"+explanation+"\n\n"
    walkthrough+="## Historical references and evaluations\n\n`simple_agent.py` preserves the original native-tool reference; `legacy_ui.py` preserves the former UI; `validate_v2.py`, `evaluate_retrieval.py` and research validation scripts retain earlier checks. Old packet/prompt/hypothesis/planning scripts are educational standalone commands, not extra active services. Their presence is intentional preservation, not a requirement to execute all of them for one chat turn.\n\n`tests/test_v3.py` contains retained core scenarios and `tests/test_final.py` adds integrated journeys and missing boundaries. `evaluate_final.py` records both. `validate_final_ui.py` drives real Streamlit widgets with isolated state. `evaluate_final_retrieval.py` contains actual relevance labels/reasons and scores. `demonstrate_final.py` records real-model journeys and dry-run proof.\n"
    (out/"FINAL_CODE_WALKTHROUGH.md").write_text(walkthrough,encoding="utf-8")

    trace=f"# Final End-to-End Runtime Trace\n\n**Actual investigation:** `{identifier}`. **Execution scope:** {state['demonstration_mode']}. All model outputs below are actual saved runtime outputs; the experiment execution is a dry run and creates no measurements.\n\n"
    trace+="## 1. Original and resolved input\n"+block({k:state.get(k) for k in ("original_question","resolved_question","objective","reference_resolution","conversation_before")})
    trace+="\n## 2. Routing, structured plan and decision origins\n"+block({k:state.get(k) for k in ("route","selected_steps","optional_step_origins","plan")})
    trace+="\n## 3. Complete actual event sequence\n\nEach event's origin distinguishes model requests, Python operations, application policy and development dry-run authorization. Model choices and application-prescribed steps are not interchangeable. The order below is runtime order.\n"
    for i,e in enumerate(state["trace"],1):
        trace+=f"\n### Event {i}: {e['kind']} — {e.get('origin','PYTHON/tool event')}\n"+block(e["data"])
    trace+="\n## 4. Actual retrieval ranks and RRF arithmetic\n\n| Run | Source | Keyword rank | Semantic rank | Calculated RRF | Saved RRF |\n|---|---|---:|---:|---:|---:|\n"
    for row in state.get("notes",{}).get("matches",[]):
        score=sum(1/(60+row[k]) for k in ("keyword_rank","semantic_rank") if row.get(k))
        trace+=f"| {row['run_id']} | {row['source_type']} | {row.get('keyword_rank')} | {row.get('semantic_rank')} | {score:.6f} | {row['rrf_score']:.6f} |\n"
    trace+="\nExact-ID/source priority also affects final ordering. RRF arithmetic does not replace those explicit policies.\n"
    trace+="\n## 5. Exact measurements and source registry\n"+block(state["evidence"])
    trace+="\n## 6. Competing hypotheses and validation\n"+block({"hypotheses":state["hypotheses"],"evidence_validation":state["evidence_validation"],"uncertainties":state["uncertainties"]})
    trace+="\n## 7. Pending/rejected proof and dry-run decision\n"+block([r for r in journeys["results"] if r["journey"]=="5 Human approval"])
    trace+="\n## 8. Final investigation report\n\n"+state["report"]
    trace+="\n## 9. Final state and sources\n"+block({k:state.get(k) for k in ("investigation_id","status","proposal_id","execution","outcome","conversation_after_question")})
    trace+="\nNo new measured training outcomes exist. Both-arm successful ingestion, outcome interpretation and hypothesis updates were exercised with clearly labeled fixtures in deterministic tests; they are not substituted into this real saved-run demonstration. A separate new-process restart check is recorded in reports/final/compatibility.json.\n"
    (out/"FINAL_END_TO_END_TRACE.md").write_text(trace,encoding="utf-8")

    inventory="## Actual directory/file map\n\n| File | Responsibility |\n|---|---|\n"+"".join(f"| `{p}` | {v[0]} |\n" for p,v in COMPONENTS.items())
    inventory+="\nData directories: runs (measured JSON), notes (original observations), knowledge (attributed references), investigations (ignored runtime SQLite/logs/exports), reports/final (executed reviewable outputs), .model_cache and data (ignored local assets), docs (final learning package plus preserved historical guides), tests (core and integrated scenarios).\n"
    schemas="## Exact tool and decision schemas\n\n### Current read/analysis tool registry\n"+block(TOOLS)
    schemas+="\n### Actual planning and hypothesis menus in this run\n"
    for e in state["trace"]:
        if e["kind"]=="TOOL MENU":schemas+=block(e["data"])
    schemas+="\nThe workflow's approval/execution methods are intentionally not in this LLM menu. A Python graph calling a function is distinct from the model requesting a native tool call. The planner's schema-constrained JSON choice is also distinguished from native hypothesis tool requests in the saved events.\n"
    formats="## Actual data formats and persistence\n\n### Exact representative run JSON\n"+block(load("runs/lr_01_seed3.json"))
    formats+="\n### Original human note\n"+block(read("notes/lr_01_seed2.md"),"text")
    formats+="\n### All attributed local knowledge records\n"
    for p in sorted((ROOT/"knowledge").glob("*.md")):formats+=f"\n#### knowledge/{p.name}\n"+block(p.read_text(encoding="utf-8"),"text")
    formats+="\n### Stored research summary\n"+block({k:state.get(k) for k in ("investigation_id","objective","status","plan","proposal_id","uncertainties","conversation_before","conversation_after_question")})
    master=ARCH+"\n"+inventory+"\n"+commands+"\n## Installed models and dependencies\n"+block(env)+"\n"+schemas+"\n"+formats
    master+="\n# Complete beginner-first learning guide\n\n"+guide+"\n# Detailed actual code walkthrough\n\n"+walkthrough+"\n# Complete real execution trace\n\n"+trace
    master+="\n# Full core implementation appendix\n\nThe following files are the actual working sources. They make the master usable without access to the repository. Source-byte hashes are snapshot identifiers for this local checkout; line-ending changes on another platform can change byte hashes without changing Python semantics.\n"
    for path in COMPONENTS:
        master+=f"\n## {path}\n\nSHA-256: `{hashlib.sha256((ROOT/path).read_bytes()).hexdigest()}`\n"+block(read(path),"python")
    master+="\n## Complete scenario inventory\n"+block(deterministic)
    master+="\n## Completeness verification\n\nThis document begins with architecture and includes purpose, actual files, commands, models, schemas, formats, retrieval mathematics, memory/state, graph transitions, scientific analysis, hypotheses, approval/execution, UI, real source excerpts, a complete real trace, measured evaluation, limitations and study order. There are 30 learning chapters. Full live training is explicitly unverified. The complete implementation is ready to study.\n"
    required=["Architecture and purpose","Exact tool and decision schemas","Actual data formats","Chapter 30","Complete real execution trace","Actual final evaluation","Full core implementation appendix","Completeness verification"]
    assert all(x in master for x in required)
    (out/"FINAL_PROJECT_MASTER_CONTEXT.md").write_text(master,encoding="utf-8")

    audit="# Final Implementation Audit\n\n## Inventory and scope\n\nThe baseline working tree was clean. The audit read the actual agent tools/state/rendering, existing trainer and JSON/note corpora, research planner/state/hypotheses/designer/executor/graph/UI, tests and documentation. The existing 56 core scenarios passed before integration. No original run JSON or note was edited.\n\n"
    audit+="| Area | Final state and verification |\n|---|---|\n| Original simple / manual agents | Preserved educational CLI references; Original-agent live compatibility checked |\n| Compact reactive LangGraph | Reused for simple primary requests with visible bounded fallback |\n| Research investigator | Persistent scientific workflow reused and integrated; single/no-ID partner discovery completed |\n| Training / JSON | Original model/evaluate code reused; validated output/provenance/cancel path; no real training run created |\n| Keyword / semantic / hybrid / reranker | Existing models reused; normalized source-aware path; expanded measured benchmark; reranker off by default |\n| Knowledge | Five original records unchanged; two attributed seed/design notes added from primary docs |\n| Memory / persistence | Bounded focus/pair/corresponding references, clarification/reset and durable state/checkpoints tested |\n| Tools / model | Shared schemas/dispatcher; exact constraints and bounded model-error recovery; model decisions labeled |\n| Hypotheses / design | Evidence-conditioned candidates, competing selection, reference validation, controlled bounded proposals |\n| Approval / execution | Exact hash/mode, stale rejection, consumed permissions, single active live execution, dry-run/cancel/recovery checks |\n| UI | One four-area recommended interface; ten AppTest checks passed |\n| Evaluations | Deterministic, live journeys, retrieval labels, UI and process-restart results kept separate |\n| Learning | Four complete final documents generated from authored chapters, source and executed artifacts |\n\n"
    audit+="## Gaps found and resolved\n\nThe former main UI exposed separate historical workspaces and lacked a complete catalog/filter/visual-comparison flow. Ranking/focus and pair/corresponding references were incomplete. A single-ID investigation could fail to find its recorded control. No-ID design could choose incomplete historical comparisons. Model tool failures and stale-proposal rejection needed clearer boundaries. Live execution blocked a UI session and had no cooperative cancellation. These specific paths were completed without replacing the underlying trainer, retrieval encoder, validated tools or durable graph.\n\n"
    audit+="## Redundant paths and retained history\n\nThe final entry uses the shared facade/graph/registry. Historical packet/prompt/generation/hypothesis/planning scripts remain standalone learning artifacts. The manual loop and prior UI remain educational references, not mandatory main-application branches. Unused graph imports and an unused UI intermediate were removed. There was no large aesthetic directory refactor and no new framework, language model, vector database or multi-agent system.\n\n"
    audit+="## Partial or unverified areas\n\nFull live training and live UI worker cancellation were not executed, because no live-training approval was granted. Cancellation boundaries/failure outcomes are tested with mocks and dry runs. Successful output ingestion/report updates are checked with labeled fixtures. No OS memory quota, distributed scheduling, multi-user authorization, broad knowledge coverage or automatic process reattachment is claimed. UI verification uses AppTest, not browser screenshots. These limits are explicitly part of the final application's supported scope.\n\n"
    audit+=evaluation
    (out/"FINAL_AUDIT.md").write_text(audit,encoding="utf-8")
    print(f"Built final guide (30 chapters), walkthrough, full trace, audit and master ({len(master.splitlines())} lines, {len(master.encode())} bytes).")


if __name__=="__main__":main()
