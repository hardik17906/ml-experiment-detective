# ML Experiment Detective — Complete Learning Guide

This book explains the implemented local application from basic ML through retrieval, tools, planning, durable investigations and human approval. Examples labeled **illustrative** teach mathematics; examples labeled **measured** come from saved JSON or executed evaluation artifacts. Real code excerpts are inserted from the working source by `docs/build_final_docs.py`; no excerpt is invented.

Read in chapter order. Keep the app open beside the book, starting with Overview and Experiment Explorer. You need basic Python, but no previous knowledge of RAG or agents. The application combines the completed experiment tools and research workflow in one interface.

## Chapter 1 — What problem are we solving?

Training a model produces a number, but understanding that number requires context. Was the data split the same? Did dropout change? Was accuracy measured after the same number of epochs? Is a validation-loss increase a persistent effect or a temporary fluctuation? A folder of results becomes difficult to question reliably from memory.

The Detective makes those records inspectable. It lists and filters experiments, plots curves, compares measured outcomes, retrieves related notes, considers explanations and proposes a controlled test. It saves investigations so closing a window does not erase the research question. Training requires a separate explicit decision.

An LLM is useful because users describe objectives in language: “Have we seen unstable behavior?” does not specify a filename. Qwen can select a tool or choose useful planning options. It is not needed to multiply accuracy by 100 or subtract two losses. Python supplies those operations because a fluent sentence is not evidence of correct arithmetic.

**Concrete example:** “Which run was best?” invokes measured ranking. “Show its curve” uses conversation focus. “Investigate why it underperformed” can require retrieval, matched comparisons, knowledge and competing hypotheses. The same interface supports all three levels of effort. A reactive lookup should not create a full scientific plan unnecessarily.

The facade `ResearchAssistant.ask` connects resettable conversation state to the durable investigator. `question` is the user's text, `resolved` is the text after reference resolution, and `context` records what resolution occurred. It checks unknown IDs, calls the graph and remembers the successful result. Its output is a dictionary containing answer, trace, status and, for research, an investigation ID.


Actual source: `assistant.py:15`–`46`; excerpt of `ask` (remaining lines, if any, are not reproduced here).

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
```


The next chapter establishes where the evidence comes from. The assistant cannot be more trustworthy than its experiment records.

## Chapter 2 — How experiment data is generated

Fashion-MNIST contains grayscale clothing images and category labels. An image is a grid of 28×28 values; `ToTensor` makes the grid available to PyTorch with a grayscale channel. A batch has shape `[B,1,28,28]`. Flattening changes each image into a vector of 784 inputs without discarding pixels.

The project takes a reproducible random permutation of the official **training** partition. With split seed 42, the first 10,000 positions form the training pool and positions 10,000–11,999 form validation. A smaller training-size experiment takes fewer images from the same training pool; it does not shift validation into newly available positions. The official test partition is excluded from proposal selection and follow-up analysis.

The MLP computes `h = ReLU(W1 x + b1)` and `z = W2 Dropout(h) + b2`. The hidden width is 128. Each output `z_j` is a logit, not a probability. Softmax converts logits to `p_j = exp(z_j) / sum_k exp(z_k)`. Cross-entropy for the correct class `y` is `L = -log(p_y)`; a confident wrong answer has high loss. Accuracy is `correct / total` and ignores how confident incorrect predictions were. Thus accuracy can improve while loss rises.


Actual source: `phase0.py:14`–`25`; excerpt of `SimpleMLP` (remaining lines, if any, are not reproduced here).

```python
class SimpleMLP(nn.Module):
    def __init__(self, hidden_units, dropout):
        super().__init__()
        self.hidden = nn.Linear(28 * 28, hidden_units)
        self.output = nn.Linear(hidden_units, 10)
        self.dropout = nn.Dropout(dropout)

    def forward(self, images):
        pixels = images.flatten(start_dim=1)
        hidden = torch.relu(self.hidden(pixels))
        hidden = self.dropout(hidden)
        return self.output(hidden)
```


An epoch processes the chosen training subset once. A batch is a smaller group used for one optimizer update. With 10,000 images and batch size 128, `ceil(10000/128)=79` batches are needed; the final batch has 16 images. Ten thousand images are not reduced to 128 images.

Backpropagation computes gradients describing how parameters affect loss. SGD uses `theta_next = theta - learning_rate * gradient`. **Illustrative scalar example:** if a parameter is 2, gradient 0.4 and rate 0.1, the update is `2 - 0.1×0.4 = 1.96`. Increasing the rate changes the update distance, but this alone does not prove the cause of a particular validation pattern.

`optimizer.zero_grad()` clears gradients from the previous batch; `loss.backward()` computes current gradients; `optimizer.step()` updates parameters. `model.train()` activates training behavior such as dropout; `model.eval()` changes that behavior for evaluation. `torch.no_grad()` avoids building a gradient graph when measuring results.

The evaluator multiplies each batch's average loss by its actual sample count, adds those totals, then divides by the whole dataset size. Averaging batch means without weights would give a short final batch too much influence. `train_loss_during_epoch` averages losses while the model changes; `train_loss_after_epoch` evaluates one fixed final-epoch model. They answer different questions.


Actual source: `phase0.py:28`–`39`; excerpt of `evaluate` (remaining lines, if any, are not reproduced here).

```python
def evaluate(model, loader, loss_fn):
    model.eval()
    total_loss = 0.0
    correct_predictions = 0
    with torch.no_grad():
        for images, labels in loader:
            logits = model(images)
            loss = loss_fn(logits, labels)
            total_loss += loss.item() * len(labels)
            correct_predictions += (logits.argmax(dim=1) == labels).sum().item()
    count = len(loader.dataset)
    return total_loss / count, correct_predictions / count
```


Split, shuffle and model seeds control different pseudo-random choices. Sharing them helps control a comparison; it does not guarantee identical trajectories when learning rates differ, or identical results across every software/hardware environment. These details are saved as configuration, which makes the next chapter's structured data useful.

## Chapter 3 — Structured and unstructured data

Structured data has explicit fields with defined meanings. A run JSON contains `config` and `metrics`. `config.learning_rate` is directly filterable; `metrics[4].val_accuracy` is the recorded epoch-five fraction. New approved runs can also include provenance identifying the proposal, investigation, approved hash and executor.

Unstructured text is written for reading. A note can say that validation loss rose and recovered. That description helps a user discover the experiment without remembering its ID. It is not an independent new measurement: the original notes explicitly say they paraphrase saved metrics. Counting a note and its source JSON as two independent experiments would exaggerate evidence.

Metadata describes the record: a path, run ID, source category or configuration field. Provenance describes where it came from. A derived summary is generated by Python from JSON and labeled `DERIVED_ANALYSIS`; original observations remain `EXPERIMENT_NOTE`. General ML documents use `ML_KNOWLEDGE`. A hypothesis is labeled `HYPOTHESIS`, even if its prose sounds persuasive.


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


`load_run` restricts the identifier format, constructs a path under `runs`, checks that the file exists and verifies consecutive epochs and matching IDs. Those checks prevent a misspelled identifier or path-like argument from becoming a guessed answer. More detailed analysis checks required numeric metrics before calculating differences.

**Measured example:** both seed-three JSONs record the same split, subset, model/shuffle seeds, hidden width, optimizer, batch size and horizon; learning rate changes. Exact architecture implementation history is not fully recorded in old JSON, so the report still names missing provenance. Known settings are not proof that every possible condition was controlled.

The system needs all three data types: JSON for numbers, notes for behavior discovery and attributed knowledge for mechanisms. Retrieval begins with the simplest text method.

## Chapter 4 — Keyword retrieval

Keyword retrieval compares literal words. Tokenization turns text into comparable units. `words` lowercases and finds letters/digits; the primary `tokens` function removes common words while retaining negation and configuration numbers. The historical keyword scorer uses set overlap: `score(query,document)=|tokens(query) intersect tokens(document)|`.


Actual source: `note_retrieval.py:43`–`50`; excerpt of `keyword_rank` (remaining lines, if any, are not reproduced here).

```python
def keyword_rank(query, notes):
    query_words = words(query)
    matches = []
    for path, observation in notes:
        shared_words = query_words & words(observation)
        if shared_words:
            matches.append((len(shared_words), path, sorted(shared_words), observation))
    return sorted(matches, key=lambda match: (-match[0], match[1].stem))
```


Actual source: `v3/retrieval.py:15`–`17`; excerpt of `tokens` (remaining lines, if any, are not reproduced here).

```python
def tokens(text):
    # Preserve negation ('no', 'not') and configuration numbers.
    return words(text) - STOPWORDS
```


**Illustrative example:** query tokens `{validation, loss, recovery}` and a note with `{validation, loss, rose, fell}` share two words, so the overlap score is 2. A note sharing only `loss` scores 1. Sorting chooses the larger overlap first; tied scores have a stable run-ID order so repeated queries do not randomly reorder.

Stopwords such as “the” and “we” can otherwise reward an irrelevant note. Negation is different: “without dropout” and “with dropout” mean different things, so `without`, `no` and `not` are retained. Exact numeric filters are handled by JSON, not by assuming that text overlap understands a condition like learning rate 0.05.

The real note `lr_005_gap_001` says validation loss decreased in each of five epochs. A query saying “steadily declining held-out error” may share few exact words despite referring to the same idea. Keyword matching also cannot reliably distinguish a number in the primary run from a number mentioned about a matched run. These are reasons to add semantic retrieval, not reasons to discard exact matching.

The final policy retains the historical scorer for comparison and uses normalized tokens in the primary investigator. Technical run IDs get explicit exact-match handling rather than being left entirely to embeddings. The next component addresses paraphrases.

## Chapter 5 — Embeddings

An embedding represents text as a list of real numbers. Texts with related meanings tend to point in related directions in the model's learned space. The coordinates are not manually assigned labels such as “coordinate 7 means overfitting.” The model learns internal features from training objectives and examples, and individual coordinates generally have no stable human interpretation.

The cached `all-MiniLM-L6-v2` encoder produces 384-dimensional vectors. Its local configuration was inspected. The project does not train this language model. The sentence-transformers wrapper tokenizes text, applies the pretrained transformer and its configured pooling into a sentence-level representation. Query and document vectors use the same encoder, making them comparable.


Actual source: `note_retrieval.py:54`–`62`; excerpt of `_embedding_model` (remaining lines, if any, are not reproduced here).

```python
def _embedding_model(local_only):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(
        MODEL_ID,
        revision=MODEL_REVISION,
        cache_folder=str(PROJECT_DIR / ".model_cache"),
        local_files_only=local_only,
    )
```


`MODEL_ID` identifies the encoder; `MODEL_REVISION` pins the cached revision; `cache_folder` puts its files under the project on D:. `local_files_only=True` makes normal searches use installed weights rather than silently downloading another model. `lru_cache` reuses the loaded model object within a Python process.

**Illustrative two-dimensional teaching vectors:** give “loss oscillates” vector `[1,1]` and “validation error fluctuates” vector `[2,2]`. Their directions match even though lengths differ. These vectors are invented only to teach geometry; the real 384 coordinates are computed by MiniLM and are not these manually assigned values.

Many dimensions let the learned representation express more variation than a two-axis drawing can show. More dimensions do not automatically mean a better model or better evidence. A relevant vector match can still point to a note about a different seed or configuration. Embeddings identify candidate text; JSON inspection verifies measurements.

The question is now how to compare two vectors. That requires cosine similarity.

## Chapter 6 — Cosine similarity

For vectors `a` and `b`, the dot product is `a·b = sum_i a_i b_i`. The Euclidean norm is `||a|| = sqrt(sum_i a_i²)`. Geometry gives `a·b = ||a|| ||b|| cos(theta)`, so dividing by both lengths gives `cosine(a,b) = (a·b)/(||a|| ||b||)`.

**Illustrative calculation:** let `a=[1,2]`, `b=[2,1]`. The dot product is `1×2+2×1=4`. Both norms are `sqrt(5)`, so cosine is `4/(sqrt(5)×sqrt(5))=4/5=0.8`. For `c=[-2,1]`, `a·c=-2+2=0`, giving cosine 0. The first document direction is closer to the query direction.

Scaling `b` by ten changes its length but not its cosine. This is useful because semantic closeness should not simply reward a larger vector magnitude. Cosine is bounded by -1 and 1 for nonzero vectors. A cosine of 0.8 does **not** mean an 80% probability that a causal explanation is true.


Actual source: `note_retrieval.py:71`–`74`; excerpt of `cosine_similarity` (remaining lines, if any, are not reproduced here).

```python
def cosine_similarity(first, second):
    import numpy as np

    return float(np.dot(first, second) / (np.linalg.norm(first) * np.linalg.norm(second)))
```


`np.dot` computes the numerator; `np.linalg.norm` computes each length; `float` converts the numerical library's scalar into an ordinary Python number for JSON. The code assumes nonzero valid encoder output. The real model normally produces nonzero vectors; the project is not a general vector-processing library with arbitrary zero-vector inputs.

The angle for cosine 0.8 is approximately 36.87 degrees. Orthogonal vectors have a 90-degree angle and cosine 0; same-direction vectors have angle 0 and cosine 1; opposite directions have angle 180 degrees and cosine -1. These geometric examples explain ranking, not scientific confidence.

A similarity score is a ranking instrument, not a calibration of truth. We next apply this calculation to every candidate document.

## Chapter 7 — Semantic retrieval

The semantic search steps are: load candidate notes; encode the query and note texts; calculate one cosine per note; sort by descending cosine; return the top `k` candidates. `k` is how many candidates to inspect, not how many experiments exist.


Actual source: `note_retrieval.py:65`–`68`; excerpt of `encode_queries_and_notes` (remaining lines, if any, are not reproduced here).

```python
def encode_queries_and_notes(queries, notes, *, local_only=False):
    return _embedding_model(local_only).encode(
        queries + [observation for _, observation in notes]
    )
```


Actual source: `note_retrieval.py:77`–`82`; excerpt of `semantic_rank` (remaining lines, if any, are not reproduced here).

```python
def semantic_rank(query_embedding, note_embeddings, notes):
    matches = [
        (cosine_similarity(query_embedding, embedding), path, observation)
        for (path, observation), embedding in zip(notes, note_embeddings)
    ]
    return sorted(matches, key=lambda match: (-match[0], match[1].stem))
```


`encode_queries_and_notes` returns vectors with the query vectors first and note vectors after them. `semantic_rank` zips each note path/text with its vector. The paths remain attached during sorting, preventing a high similarity from being accidentally assigned to the wrong source. A stable secondary sort on file stem handles ties.

Indexing means organizing documents and their searchable representations. At this collection size, the implementation reads the small corpus and computes embeddings for a request. It caches the encoder object, not a permanent vector index. There is no approximate-nearest-neighbor database hidden in the code. The work is roughly proportional to the number of candidates times vector dimension, in addition to encoding cost.

**Real query to inspect:** “Have we seen unstable validation-loss behavior before?” The saved journey contains the actual search results, cosine values and the subsequent `get_experiment` result. The agent cannot treat a retrieved note as enough to invent the exact current loss; it follows the returned run ID into JSON.

At millions of documents, repeated encoding and exhaustive comparison would be expensive. A persistent embedding index could then be justified. Eleven saved runs and a handful of notes do not demonstrate that need. The chosen implementation favors explicit, inspectable operations.

Semantic retrieval handles paraphrases, while keyword retrieval preserves exact terminology. Combining their rankings is the next step.

## Chapter 8 — Hybrid retrieval and RRF

Keyword and semantic methods can disagree usefully. A technical identifier may match exactly while meaning-oriented wording matches another observation. Reciprocal Rank Fusion combines **rank positions**, avoiding the need to pretend an overlap count and a cosine share the same scale.

For document `d`, `RRF(d)=sum_m 1/(K+rank_m(d))`. This project uses `K=60`. A method that does not return the document contributes zero. The constant reduces the dominance of tiny top-rank differences; it is not the requested top-k result count.

**Illustrative worked example:** A has keyword rank 1 and semantic rank 3, giving `1/61+1/63≈0.032266`. B has ranks 2 and 1, giving `1/62+1/61≈0.032522`. B ranks ahead because it is well placed by both signals. Raw cosine 0.8 is never added directly to overlap count 2.


Actual source: `v3/retrieval.py:57`–`88`; excerpt of `search_notes` (remaining lines, if any, are not reproduced here).

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
```


Read `kr` as keyword rank and `sr` as semantic rank. `rows` joins scores, source categories, paths and observation text. The final policy calculates ranks within source types, prioritizes original notes for broad behavior discovery, exposes derived summaries separately, and gives exact run-ID matches priority. This source policy is part of ranking; it is not plain RRF alone.

The complete trace contains an automatically calculated table of actual note ranks and their `1/(60+rank)` contributions. Compare the formula with `rrf_score`, allowing for display rounding. Generated summaries may be useful but cannot be counted as independent human observations.

Hybrid retrieval is not guaranteed to beat semantic retrieval. A noisy keyword ranking can pull an irrelevant candidate upward. During retrieval development, flat mixing of derived summaries reduced performance on the old labels. The measured source-priority policy was retained instead. The final expanded benchmark reports its misses and does not repeatedly tune to force a perfect score.

The next stage can reconsider candidate text jointly with the query, at additional cost.

## Chapter 9 — Reranking

A bi-encoder independently maps the query and each document into vectors. Their representations can be reused, making candidate search efficient. A cross-encoder reads the query and document together and predicts a relevance score for that pair. Joint attention can model interactions that separate vectors miss, but it requires a separate inference for each candidate pair.


Actual source: `v2_retrieval.py:18`–`25`; excerpt of `_reranker` (remaining lines, if any, are not reproduced here).

```python
def _reranker():
    if not (RERANKER_DIR / "config.json").is_file():
        raise FileNotFoundError(f"Reranker is not cached at {RERANKER_DIR}")
    from sentence_transformers import CrossEncoder

    return CrossEncoder(
        str(RERANKER_DIR), local_files_only=True, device="cpu",
    )
```


The optional cached model is `cross-encoder/ms-marco-MiniLM-L2-v2`. `predict([(query,text), ...])` produces scores used to reorder candidates. These are relevance signals, not measurements, probabilities of a hypothesis, or permission to ignore source types. The final implementation preserves exact-ID and source-priority constraints when reranking.

The historical five-query results favored leaving reranking off: Recall@2 0.80 and MRR@2 0.70 for the historical reranked path, versus 0.90/0.90 for historical hybrid. Final results are reported separately because the corpus/policy and benchmark have expanded. A model trained for web-style relevance need not improve this small scientific-note collection.

The UI exposes reranking in Advanced settings. If weights are absent, the tool retains hybrid ordering and records that fallback instead of downloading weights during a normal query. Reranking is a candidate refinement stage; it does not solve missing experiment metadata.

These retrieval components become RAG only when they supply evidence to the answer workflow.

## Chapter 10 — What exactly is RAG?

Retrieval-Augmented Generation combines retrieval of relevant external information with producing an answer conditioned on that information. Retrieval finds candidates. Augmentation puts selected evidence into a model's context. Generation produces a response. Grounding means the response is tied to appropriate evidence rather than relying on plausible remembered text alone.

In conventional RAG, the application often always retrieves passages, builds one prompt, and asks a model to write an answer. The Detective uses retrieval as an agent tool: the model can ask for notes, observe returned IDs, request exact JSON and ask for ML knowledge. Python renders factual numbers. That is a retrieval-augmented tool workflow rather than an unrestricted model paraphrase of everything retrieved.


Actual source: `v2_agent.py:191`–`222`; excerpt of `execute_call` (remaining lines, if any, are not reproduced here).

```python
def execute_call(state: dict, name: str, arguments: dict, *, origin: str) -> None:
    available = available_tool_names(state)
    if name not in available:
        raise ValueError(f"{name} was not in the offered tool menu: {available}")
    corrected = dict(arguments)
    if name in {"rank_experiments", "get_experiment", "compare_experiments", "search_runs", "compare_run_group", "plot_run_metrics", "summarize_run_curve"}:
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
        if state.get("final_tools") and name == "search_notes":
```


The dispatcher validates a permitted call, executes Python, records a tool result and appends a `role='tool'` message. `model_result` can be compact while the visible trace retains full results. This matters because the model's context window is limited; an audit trace and an LLM prompt need not contain the same amount of data.

A hallucination is an unsupported invented claim, such as a run ID that was never saved. A citation alone does not fix it: a real source can fail to support the attached claim. The system limits IDs, verifies measurements, distinguishes source types and uses a deterministic renderer. It still does not prove that every qualitative statement is a statistically valid explanation.

**Concrete example:** a note says loss spiked, JSON verifies the epochs and values, a general reference describes high learning-rate behavior, and the report says instability is a possible mechanism. The reference cannot turn “possible” into “this caused that run's failure.” Next we examine that separate knowledge corpus.

## Chapter 11 — External ML knowledge RAG

Experiment RAG asks “What happened in our runs?” Knowledge RAG asks “What general mechanisms might be relevant?” These questions use different sources. A general dropout reference does not contain the final accuracy of a locally trained Fashion-MNIST run.


Actual source: `v2_retrieval.py:109`–`123`; excerpt of `_knowledge_chunks` (remaining lines, if any, are not reproduced here).

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
```


Actual source: `v3/retrieval.py:130`–`148`; excerpt of `knowledge` (remaining lines, if any, are not reproduced here).

```python
def knowledge(query, *, semantic=True):
    covered = re.search(r"learning.?rate|optimiz|gradient|sgd|dropout|overfit|validation|loss curve|seed|reproduc|experimental design|data leakage|generalization", query, re.I)
    if not covered:
        return {"matches": [], "limitation": "This topic is not covered by the small local ML knowledge base."}
    if semantic:
        try:
            result = search_ml_knowledge(query, top_k=2)
            result["matches"] = [dict(x, source_type="ML_KNOWLEDGE") for x in result["matches"]
                                 if tokens(query) & tokens(x["text"] + " " + x["topic"])]
            return result
        except (OSError, RuntimeError, ImportError) as exc:
            reason = f"APP POLICY: lexical knowledge fallback: {type(exc).__name__}"
    else:
        reason = "deterministic lexical fixture mode (no embeddings)"
    from v2_retrieval import _knowledge_chunks
    chunks = _knowledge_chunks()
    chunks.sort(key=lambda x: -len(tokens(query) & tokens(x["text"] + " " + x["topic"])))
    return {"matches": [dict(x, source_type="ML_KNOWLEDGE") for x in chunks
                        if tokens(query) & tokens(x["text"] + " " + x["topic"])][:2], "mode": reason}
```


Each knowledge file supplies a title, URL, topic, source type and a short attributed paraphrase. The corpus includes the original five topics plus final notes about seeds and experimental design/data leakage. The two additional references were checked against primary PyTorch and scikit-learn documentation. Those URLs record provenance; ordinary questions search local text and do not browse the internet.

`knowledge` checks whether the question is covered, reuses the existing MiniLM/RRF search, and can use a transparent lexical fallback. A transformer-attention question is recognized as ML-related but outside this small local corpus; the assistant says that it cannot provide a grounded answer from available sources.

**Example:** a learning-rate comparison produces measured loss changes. Retrieved optimization/validation material can explain why rates, gradients and generalization might matter. The report puts measured observations, retrieved mechanisms, possible interpretation and uncertainty in separate sections. A missing knowledge result remains missing; the app does not silently fill it with unmarked model knowledge.

The model that chooses these tools is distinct from the models that retrieve text, which is the next chapter's focus.

## Chapter 12 — LLMs and Ollama

An LLM is a trained language model that predicts and generates token sequences conditioned on an input context. It can follow instructions and generate structured choices, but a likely token sequence is not automatically a true statement or a correctly executed function.

Ollama is the local inference server/runtime. `qwen3:1.7b` is the installed generative model served by it. MiniLM is a separate sentence encoder used for retrieval. The optional cross-encoder is a separate relevance model. Installing Ollama does not itself create embeddings, and an embedding model does not replace the text model.


Actual source: `v2_agent.py:159`–`174`; excerpt of `ask_ollama` (remaining lines, if any, are not reproduced here).

```python
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


The request goes to localhost `/api/chat`, includes messages and offered tool schemas, disables streaming/thinking output, and uses temperature zero for repeatable choices where the runtime permits. `num_ctx=4096` bounds the configured context window; `num_predict=400` bounds output length. Tokens are model units, not one-to-one words. A long trace can exceed a useful prompt size, so the app sends compact evidence for choices.

The research planner uses a JSON-schema completion; hypothesis selection uses native tool calling. Both are actual local model outputs recorded in the trace. Python validates those outputs. If a local model is unavailable or emits a malformed request, the primary graph records a bounded policy fallback. Offline mode deliberately uses Python choices and must not be presented as an LLM decision.

No paid API or larger replacement model is required. Model files remain on D:. With that distinction clear, we can examine how a tool request becomes Python work.

## Chapter 13 — Tools and function calling

A tool is an application function described to the model through a schema. The schema supplies a name, description, argument properties and required fields. The model returns structured arguments; it does not directly invoke Python or gain a shell.


Actual source: `v2_tools.py:12`–`25`; excerpt of `_schema` (remaining lines, if any, are not reproduced here).

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
```


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


The registry maps allowed names to handlers. Validation rejects unsupported names, unexpected fields, absent required arguments, wrong types, invalid enum values, non-finite numbers and invalid ranges enforced by handlers. A run ID is also validated when opening its JSON. Booleans are explicitly excluded from integer/number arguments because Python otherwise treats `True` as an integer.

**Example input:** `get_experiment` with `{'run_id':'lr_01_seed3'}` returns measured configuration and metrics. `{'run_id':'../secret'}` fails ID validation. A request named `shell` is not in the menu and cannot turn a string into a command. Exact constraints stated in the question can correct model arguments with an `APP FILTER` trace.

The final application adds `rank_experiments` to the same registry. It ranks saved accuracy, loss or maximum positive loss rises and supports exact filters. It does not infer causes from ranking. Its numbers are calculated in Python and passed to the renderer.

The complete master reference includes the exact current tool schemas and actual planner/hypothesis menus. Scientific workflow functions executed by Python are labeled as such; they are not falsely listed as autonomous model calls. Tool requests, tool execution and results form the next chapter's loop.

## Chapter 14 — What is an AI agent?

An agent uses observations to choose actions toward a goal. A fixed workflow always follows prescribed steps. A single tool call adds an action to a language-model interaction. A multi-step agent can choose a tool, inspect its result and decide whether another action is needed.


Actual source: `v2_agent.py:298`–`321`; excerpt of `run_manual` (remaining lines, if any, are not reproduced here).

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
            raise RuntimeError("Tool agent reached its tool-call limit")
        # Reconsider the menu after each observation; a multi-call model response
        # cannot assume that later calls still belong to the next menu.
        function = calls[0]["function"]
        execute_call(state, function["name"], function["arguments"], origin="AGENT")
    raise RuntimeError("Tool agent did not stop within its step limit")
```


The educational manual loop makes choose → act → observe explicit. The tool menu changes after evidence: a behavior search is followed by exact inspection; a question asking why can then retrieve general knowledge. A bounded call count prevents an endless tool loop. The primary graph uses the same state, dispatcher and renderer with additional visible recovery for model failure.

The Detective is intentionally a bounded agent. Python narrows the menu, enforces IDs and requires some evidence steps. The LLM chooses within that menu. Calling a deterministic routing rule an autonomous decision would hide how the system actually works. Conversely, a graph does not become non-agentic merely because important safety boundaries are prescribed.

**Example:** “Have we seen unstable validation before?” first searches notes. The result identifies candidate runs. The model can request a returned run and then stop or ask for a relevant mechanism when the question needs it. Its next context contains the previous tool's observation, which is the key difference from a single isolated function call.

Simple questions can finish with a direct tool result. Complex research benefits from a plan, which the next chapter adds.

## Chapter 15 — Agent planning

A plan is structured intended work, not just a paragraph saying “I will investigate.” The project stores step IDs, tools, dependency lists, status and decision origin. Planning is useful when an objective requires several kinds of evidence and a later human decision. It is wasteful for a request asking for one saved accuracy.


Actual source: `v3/planner.py:77`–`108`; excerpt of `make_plan` (remaining lines, if any, are not reproduced here).

```python
def make_plan(state):
    ids = mentioned_run_ids(state["objective"])
    unknown = unknown_run_ids(state["objective"])
    if unknown:
        raise ValueError(f"Unknown run IDs: {unknown}")
    optional = ["search_notes", "compare_seed_pairs", "retrieve_knowledge"]
    fallback = {"steps": optional, "knowledge_topic": "high learning rate optimization instability"}
    topics = ["high learning rate optimization instability", "dropout overfitting validation loss", "training validation loss curves"]
    def validate(args):
        if not isinstance(args["steps"], list) or len(args["steps"]) != len(set(args["steps"])) or set(args["steps"]) - set(optional):
            raise ValueError("Invalid or repeated plan steps")
        if args["knowledge_topic"] not in topics:
            raise ValueError("Unknown knowledge topic")
    choice, origin = select(state, "create_investigation_plan",
        f"Objective: {state['objective']}. Known mentioned runs: {ids}. Choose useful optional research tools. "
        "Choose compare_seed_pairs to check replication/counterevidence; search_notes to find previous observations; "
        "retrieve_knowledge for mechanisms. Return a topic from the menu.",
        {"steps": {"type": "array", "items": {"type": "string", "enum": optional}, "maxItems": 3},
         "knowledge_topic": {"type": "string", "enum": topics}}, fallback, validate)
    prescribed_steps = []
    if not ids and "search_notes" not in choice["steps"]:
        choice["steps"].insert(0, "search_notes")
        prescribed_steps.append("search_notes")
        event(state, "APP POLICY", "Search is required to discover run IDs absent from the question")
    for phrase, required in ((r"retrieve.*knowledge|ml knowledge", "retrieve_knowledge"),
                             (r"previous experiments|across seeds|seed blocks", "compare_seed_pairs"),
                             (r"search.*notes|retrieve.*notes", "search_notes")):
        if re.search(phrase, state["objective"], re.I) and required not in choice["steps"]:
            choice["steps"].append(required)
            prescribed_steps.append(required)
            event(state, "APP POLICY", {"required_by_objective": required})
    state["selected_steps"] = choice["steps"]
```


The model can select optional note search, seed comparisons and ML-knowledge retrieval, plus a covered topic. Python prescribes exact measurements, scientific validation and the permission boundary. `optional_step_origins` records a model choice separately from a step inserted to honor the user's explicit request. A missing run ID requires discovery; “search notes” in the objective requires that step even if the model omits it.

Observation can revise the concrete plan. For a single-run underperformance investigation, the collection node finds a corresponding saved run whose recorded changes are limited to learning rate. For a no-ID design request, retrieval discovers candidates and Python selects a fully recorded controlled pair when one exists. The trace records `REPLANNING` with the actual IDs and policy reason.

Replanning is bounded: it is not autonomous code writing or an unlimited research loop. The initial choice has at most two model attempts, the graph has a finite route and recursion bound, and training is never the automatic consequence of a plan.

To continue a plan later, intended work and observations need durable state.

## Chapter 16 — Memory and state

Conversation memory helps interpret language; investigation state preserves work. A source corpus is neither of those. A context window contains only what a particular LLM request sees. Treating all four as one vague “memory” makes errors hard to diagnose.


Actual source: `v2_state.py:28`–`59`; excerpt of `resolve` (remaining lines, if any, are not reproduced here).

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
```


`focused_run_id` supplies a clear single-run referent. `comparison_run_ids` preserves the pair used by “the difference.” A corresponding learning-rate request searches saved configurations rather than asking embeddings to guess a partner. A fresh/reset session with “it” asks which run the user means. After a comparison, an ambiguous singular reference is not silently assigned to either member.

The last four conversation turns supply bounded summaries; the UI retains a bounded visible chat list. Reset clears conversational focus and history while leaving runs and saved investigations intact. An explicit research objective is saved with its resolved question and conversation snapshot, so a later report can show what was actually asked.


Actual source: `v3/investigation_state.py:62`–`66`; excerpt of `save` (remaining lines, if any, are not reproduced here).

```python
    def save(self, state):
        with self.connection() as db:
            db.execute("INSERT OR REPLACE INTO investigations VALUES (?,?,?,?,?)",
                       (state["investigation_id"], state["objective"], state["status"],
                        now(), json.dumps(state, allow_nan=False)))
```


SQLite stores application snapshots, proposal configurations and decision audit events. LangGraph checkpoints store progress and suspended tasks. These are different responsibilities even though they share a database. The store closes each connection, which matters on Windows because open SQLite handles can keep files locked.

The next chapter explains how graph checkpoints control resumption rather than merely storing a transcript.

## Chapter 17 — LangGraph

State is the information passed among graph nodes. A node is a Python function reading state and returning an update. An edge chooses the next node; a conditional edge chooses among routes based on state. A tool node executes validated functions. `START` and `END` describe entry and termination.


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


The retained compact graph implements agent → tools → agent → final. The investigator graph adds classify, plan, collect, analyze, knowledge, hypotheses, validate, design, approval, execute, outcome and report nodes. Simple questions route directly to the compact tool graph. Unrelated questions return a scope limitation. A proposal failure routes to a report without training.

An interrupt suspends the graph at a checkpoint. It differs from simply returning “please approve”: a new process can reopen the same thread ID and supply a resume command. `SqliteSaver` makes the checkpoints durable. The investigation ID is the graph thread ID; it is not an embedding search key.


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


`get_state` reveals pending nodes and interrupts. Loading a pending proposal is not approval. Only a persisted decision allows `Command(resume=...)`. The interrupted node executes again from its beginning, so work before `interrupt` must not launch training or consume an execution permission. Terminal results can be returned without rerunning the trainer.

LangGraph was introduced to make branching, pause/resume and workflow inspection explicit. A while loop remains a useful teaching reference. The framework itself does not supply scientific judgment; node functions and the model/policy decisions do. Next we examine the numerical reasoning those nodes perform.

## Chapter 18 — Deterministic analysis

For two comparable runs, define target minus baseline so the sign is unambiguous. Accuracy fractions are converted to percentages before reporting percentage-point differences. **Measured seed-three example:** `100×(0.7145−0.7590)=−4.45 pp`. Loss difference from full-precision JSON rounds to `+0.1303`. A percentage-point change is not a relative percentage change.


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


For losses `L1,...,LT`, the maximum positive one-epoch rise is `max(0, L2−L1, ..., LT−L(T−1))`. **Illustrative curve:** `[0.8,1.0,0.7]` has largest rise 0.2 and a rise/recovery pattern across all three epochs. Recovery is descriptive; it does not erase the earlier increase or identify its cause.

Best accuracy is the maximum saved validation accuracy; final accuracy is the last saved value. Choosing the best epoch after inspecting validation is a selection decision, not an independent test-set result. The system reports both where relevant. A generalization-loss gap is `validation_loss−post_epoch_training_loss` when both exist. A falling training loss with rising validation loss flags a candidate interval, not a definitive overfitting diagnosis.

The comparison examines the union of configuration fields, explicit missing controls and provenance limitations. Different horizons or incomplete required metrics suppress final deltas. Seed-group summaries deduplicate repeated configurations; multiple filenames from the same conditions are not automatically independent replications. Means and population standard deviations describe observed blocks and are not confidence intervals.

These calculations establish observations. Hypotheses add possible mechanisms without changing those observations into causal proof.

## Chapter 19 — Hypothesis generation

An observation describes what was measured. A hypothesis proposes why it might happen. An assumption states what must hold for an interpretation to be useful. Confounding means multiple relevant variables changed, leaving their effects hard to separate. Missing evidence identifies what the current records cannot decide.


Actual source: `v3/hypothesis.py:29`–`60`; excerpt of `generate` (remaining lines, if any, are not reproduced here).

```python
def generate(state):
    registry = state["evidence"]
    pairs = [(k, v["value"]) for k, v in registry.items() if k.startswith("PAIR:")]
    ml = [k for k in registry if k.startswith("ML:")]
    rate_pairs = [(k, p) for k, p in pairs if set(p["changed_settings"]) == {"learning_rate"} and "rise_delta" in p]
    # All comparisons here are reoriented from lower to higher rate before assigning evidence signs.
    oriented = []
    for key, p in rate_pairs:
        change = p["changed_settings"]["learning_rate"]
        sign = 1 if change["target"] > change["baseline"] else -1
        oriented.append((key, p, sign))
    common = {"source_type": "HYPOTHESIS", "relevant_ml_knowledge": ml,
              "assumptions": ["Recorded configurations and epoch metrics accurately describe the runs."],
              "missing_evidence": ["Independent replication and optimizer-step/gradient measurements are absent."],
              "status": "Inconclusive"}
    def candidate(identifier, statement, support, opposing, missing, test):
        return {**common, "hypothesis_id": identifier, "statement": statement,
                "supporting_experiment_evidence": list(dict.fromkeys(support)),
                "contradicting_experiment_evidence": list(dict.fromkeys(opposing)),
                "missing_evidence": common["missing_evidence"] + missing,
                "proposed_test": test,
                "status": "Consistent with current evidence" if support and not opposing else "Inconclusive"}
    candidates = []
    if oriented:
        candidates.append(candidate("H1", "A higher learning rate may contribute to larger validation-loss rises through unstable optimization.",
            [k for k, p, s in oriented if s * p["rise_delta"] > 0],
            [k for k, p, s in oriented if s * p["rise_delta"] <= 0],
            ["Validation-loss rises cannot directly demonstrate overshooting; gradients and optimizer trajectories were not recorded."],
            "Compare maximum positive consecutive-epoch validation-loss rises under matched new seeds and different learning rates."))
        signs = {1 if s * p["accuracy_delta_pp"] > 0 else -1 if s * p["accuracy_delta_pp"] < 0 else 0 for _, p, s in oriented}
        candidates.append(candidate("H2", "Seed-dependent training variability may contribute to differences in final validation accuracy.",
            [k for k, _, _ in oriented] if len(signs) > 1 else [], [],
```


Python constructs candidate statements conditioned on measured comparisons. H1 considers higher-rate loss-rise instability; H2 considers seed-dependent accuracy variation; H3 considers short-horizon sensitivity; H4 appears when an explicit train/validation interval rule is observed. When a rate comparison is unavailable, the candidate wording changes to a qualified configuration/unrecorded-condition explanation.

Ollama selects and orders at least two competing candidates through a tool schema. It does not freely invent measured evidence or write arbitrary causal conclusions. The candidate's `statement_origin` and `selected_by` fields make that distinction visible. An evidence registry links supporting/opposing references to exact JSON, derived calculations, notes or general knowledge.

**Measured counterevidence:** the higher-rate final accuracy changes direction across recorded seed blocks. This opposes “higher learning rate always lowers accuracy.” It does not automatically oppose the separate claim that the higher-rate arms showed larger maximum loss rises in those blocks. Different hypotheses need different predicted observations.

A status such as “consistent with current evidence” is descriptive and carries no arbitrary numerical confidence percentage. General ML material can support considering a mechanism; it cannot prove a local run's cause. The next step turns a hypothesis into a testable proposal.

## Chapter 20 — Controlled experiment design

A controlled comparison changes a specified variable while keeping relevant conditions matched. If learning rate and train size both change, a difference cannot be attributed specifically to rate. Matching recorded conditions reduces confounding but cannot account for every unrecorded condition.


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


The executable designer supports one concrete family: two Fashion-MNIST MLP runs with different learning rates and matched other settings. It uses a complete saved reference configuration, records shared fresh model/shuffle seeds, checks existing run IDs/configurations and reserved legacy plans, and enforces resource limits. The paused legacy seed-four branch is not automatically resumed.

Matching seeds makes the arms comparable under one randomness block. Replication means repeating the intervention under another independent block. A single successful block is evidence about that block, not a general population theorem. Same seeds also do not force identical parameter trajectories at different rates.

The primary metric is predeclared: compare each arm's maximum positive validation-loss rise. A larger higher-rate rise is consistent with the directional prediction; a smaller rise opposes it; equality is inconclusive. Final accuracy and loss are secondary. This prevents choosing whichever post-hoc metric tells the nicest story.

The proposal is machine-readable and independently validated before becoming eligible for approval. Candidate hypotheses about dropout, long horizons or arbitrary model families can need designs the restricted executor does not support; the report states that limitation. The next chapter addresses who may authorize the supported proposal.

## Chapter 21 — Human-in-the-loop agents

Human-in-the-loop means a person makes a required decision inside the workflow. Here that boundary protects time/resources and keeps a proposed experiment distinct from an authorized experiment. An LLM request cannot stand in for the user's consent.


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


The proposal hash is SHA-256 over canonical JSON with sorted keys. Approval stores the proposal ID, exact hash, execution mode, actor, reason and timestamp. A changed payload invalidates the earlier approval. Dry-run approval cannot authorize live execution. The training-code hash is checked as part of the proposal, so a changed trainer requires review again.

The graph interrupt saves the waiting state. Resume checks its token and the persisted decision; the token itself is not permission. The executor atomically changes approved to running inside a SQLite transaction, so approval is consumed once. A second live workload is blocked while another is running. Tests try pending, rejected, stale-hash, wrong-mode, repeated and model-origin bypasses.

Development demos explicitly use `development_dry_run`. They do not claim that the user clicked a live-training button. This is a trusted local application boundary, not multi-user authentication or protection against someone who can edit Python and the database. Stale proposals can still be rejected even when code changes make them ineligible for approval.

After an authorized decision, execution must remain restricted and observable.

## Chapter 22 — Experiment execution

The executor accepts a validated proposal, not an arbitrary shell string. A dry run validates permission/configuration, records planned runs and stops without launching a trainer or inventing metrics. Live mode requires its own explicit exact approval.


Actual source: `v3/experiment_executor.py:39`–`70`; excerpt of `execute` (remaining lines, if any, are not reproduced here).

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
```


The fixed subprocess argument list invokes `v3.training_worker` with a JSON input path and `shell=False`. That worker reuses `phase0.run_training`. It restricts output to the run-ID-derived location, disables dataset downloads, uses the fixed training-partition split and records provenance. Exclusive file creation prevents overwriting old experiments.

The parent enforces a 600-second total budget, at most two runs and two CPU threads; the worker checks elapsed time and cancellation between training batches. Limits also cap epochs, subset size, batch size and hidden width. There is no OS-level RAM quota, and cancellation is cooperative rather than an instant guarantee during a native operation.

The UI runs explicitly approved live work in a background thread so execution status/cancel controls remain available. Logs and partial completed records are retained. A CLI cancellation request writes the fixed proposal cancellation marker. A worker failure, timeout or cancellation is recorded instead of being converted into a successful result.

After both arms complete, their configurations and metrics are checked, predefined comparisons are calculated and the report/hypothesis status can update. A restart that finds uncertain running work does not silently launch it again. Full live training was not run in final development; this integration is verified through dry runs, mocks and labeled ingestion fixtures. That distinction is part of the result, not a footnote to hide.

## Chapter 23 — Answer generation and grounding

The LLM selects bounded work; Python supplies measured facts. The final renderer groups observations, relevant ML knowledge, possible interpretation, limitations and sources. This is deliberately less flexible than letting a small local model freely compose numerical claims.


Actual source: `v2_answers.py:4`–`35`; excerpt of `render_answer` (remaining lines, if any, are not reproduced here).

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
```


`tool_results` contains successful handler outputs. The renderer extracts accuracy, loss, curve patterns and rankings directly from those objects, attaches source paths and distinguishes general-reference URLs. It never asks the model to subtract two decimal values or invent a citation title. Source categories remain visible in research reports.

Exact argument constraints stated by the user can correct a model's request through a visible `APP FILTER`. A malformed/unavailable model call can use `APP POLICY` recovery. These interventions must not be called `AGENT CHOICE`. Failed tools stop bounded progress and produce an evidence limitation rather than a plausible invented result.

Unknown IDs get saved alternatives. Unrelated questions are rejected before irrelevant retrieval. Unsupported ML topics identify the small knowledge corpus's limitation. Ambiguous references ask for clarification. These behaviors protect the meaning of the answer as much as a mathematical check does.

A grounded answer is traceable, not infallible. Scientific validity and tool behavior require evaluation, the next chapter's subject.

## Chapter 24 — Evaluation

Evaluation compares behavior with explicit expectations. Retrieval labels say which notes are relevant to a query. `Recall@K = number of relevant items in top K / total relevant items`. With two relevant notes and one returned in top two, Recall@2 is 1/2. `RR@K` is the reciprocal rank of the first relevant result within K, or zero if none; if the first relevant note is second, RR@2 is 1/2. MRR averages reciprocal ranks across queries.

**Illustrative two-query example:** query A has first relevant rank 1, query B rank 2; MRR=(1+0.5)/2=0.75. Recall can differ because it counts all relevant items, while reciprocal rank only uses the first relevant item. Neither metric says whether a causal explanation is true.


Actual source: `evaluate_final_retrieval.py:23`–`25`; excerpt of `score` (remaining lines, if any, are not reproduced here).

```python
def score(ids, relevant):
    return {"recall_at_2":len(set(ids[:2])&set(relevant))/len(relevant),
            "mrr_at_2":next((1/i for i,r in enumerate(ids[:2],1) if r in relevant),0)}
```


The final benchmark preserves the five historical labels, adds twelve frozen note-relevance judgments and six explicit unnoted-run coverage checks. The subsets are reported separately. Exact-ID coverage is easier than open-ended semantic relevance, so its success must not be advertised as general semantic accuracy. New labels are local judgments, not an independent hidden test set.

Deterministic tests cover numbers, invalid tools, memory, ambiguity, hypotheses, proposals, approval bypass, recovery and cancellation. Live Ollama journeys are reported separately. Streamlit AppTest exercises real widget paths without claiming browser screenshot inspection. A simulated trainer failure tests error handling; it is not a real measured training run.

The measured result tables are inserted below from executed artifacts. No unrestricted natural-language unsupported-claim percentage was measured. Passing finite scenarios does not establish correctness for every possible user question.

## Chapter 25 — Streamlit UI

Streamlit reruns the script when widgets change. `st.session_state` keeps per-session conversation objects and visible entries across those reruns. The durable investigation store lives outside that browser-session lifetime. A local page refresh is not approval and a conversation reset is not deletion of saved experiments.

The navigation presents Overview, Experiment Explorer, AI Chat and Investigations. Overview gives counts, local-model status and examples. Explorer lets users find IDs through tables/filters, inspect exact configuration/epoch data and compare two curves. Chat retains references and displays tool-produced charts. Investigations exposes plans, hypotheses, review/approval, execution and reports.


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


`draw_run` gets its metrics from saved JSON and its chart points from `plot_run_metrics`. Percent accuracy uses a separate chart from loss because the scales have different units. Missing old training measurements remain blank. A changed setting is displayed rather than being silently treated as controlled.

Optional “Explain how the AI worked” expanders reveal resolved questions, available menus, actual model requests, policy/filter actions, results, retrieval stages and state changes. Ordinary users do not need to understand RRF or LangGraph to browse a table or reject a proposal.

The preserved older UI is an educational reference in `legacy_ui.py`; the recommended entry is `streamlit run ui.py`. There is no need to select a legacy runner before doing useful work. The next chapter follows one complete run through these layers.

## Chapter 26 — Complete end-to-end execution

The verified demonstration uses a real question asking why `lr_01_seed3` performed worse than `lr_005_seed3`, requests notes and ML knowledge, checks earlier experiments and proposes a controlled follow-up. `demonstrate_final.py --live` records actual local model requests, tool results and policy actions. It explicitly demonstrates only dry-run execution.


Actual source: `demonstrate_final.py:14`–`45`; excerpt of `main` (remaining lines, if any, are not reproduced here).

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
```


Follow the records in `FINAL_END_TO_END_TRACE.md`: input and conversation snapshot enter `ResearchAssistant.ask`; reference resolution produces a concrete question; `Investigator.start` creates a durable ID; classification chooses research; the planner selects optional steps; collection reads notes and JSON; analysis computes controls/curves/seed evidence; knowledge retrieval supplies general material; hypothesis selection chooses candidates; evidence validation checks references; design creates a validated proposal; the approval node interrupts.

The demo verifies that pending and rejected proposals cannot execute, then records a separate development dry-run authorization. Resume checks that decision, the executor records a dry-run result and the report is updated. No artificial metrics are inserted as “new experiment results.”

The trace document contains exact schemas, arguments, ranking contributions, source data, hypotheses, proposal, decision, report and final state. Where Python prescribed a step, it says so. If a model failed to choose a step and policy inserted it, that event remains visible. Use the actual event order, not an imagined idealized diagram, when explaining the demonstration.

## Chapter 27 — Problems encountered during development

The project evolved because specific failures taught useful constraints. Free-form local-model answers could invent numbers, motivating deterministic evidence extraction and rendering. Early behavior questions needed semantic note discovery, followed by exact JSON inspection. Conversation references needed structured focus rather than another embedding search.

Investigator testing found a Windows SQLite connection leak: transactions alone did not close connections, leaving files locked during cleanup. Connections now close explicitly. Seed grouping initially mixed learning-rate ranges; analysis now restricts the relevant comparison and deduplicates recorded blocks. Tool-call planning sometimes returned no call; schema-constrained planning and bounded visible fallbacks made the behavior explicit.

Flat mixing of generated summaries degraded the old retrieval labels. Source-priority ranking and separate supplementary summaries were measured instead. This demonstrates why a more elaborate algorithm is not automatically an improvement.

Final integration exposed fragmented navigation, missing ranked discovery, comparison-reference gaps and a one-run investigation that could miss its control. The final interface/facade and matched-run lookup address those concrete gaps. Stale proposals also needed to remain rejectable even when trainer changes made approval invalid. The audit and final evaluation artifacts document what was tested after these changes.

Historical examples remain in the repository for study. Their presence does not mean the primary application launches every old script or requires every earlier workflow. Current architecture and historical learning material should be distinguished.

## Chapter 28 — Limitations and engineering trade-offs

The collection is small, uses one validation split and contains repeated configurations and incomplete old metadata. Observed seed blocks do not establish general causal laws. Repeatedly choosing experiments against the same validation data can adapt to that validation set even without touching the official test set.

The model selects from bounded plan/hypothesis menus. It is not an unrestricted research scientist inventing arbitrary interventions. The executor supports one deliberately limited learning-rate comparison using the original MLP. Other scientific questions can yield useful reports while requiring a different, not-yet-supported executable design.

The small local knowledge base cannot answer arbitrary ML or general-world questions. Keyword scope/routing rules and limited reference patterns can miss unusual phrasing. Search relevance is imperfect, reranking may hurt and model output can fail. The trace and explicit limitations make those failures inspectable rather than claiming they disappear.

SQLite and background threads are suitable for a single local laptop. They are not a production distributed job scheduler, multi-user authorization service or robust process-reattachment system. Live training was integrated but not run during development. Cancellation is cooperative; no hard memory quota is implemented. UI verification uses AppTest, not full browser visual testing.

There is no measured need for a vector database, multi-agent system, cloud infrastructure or larger model here. Keeping the data flow visible supports the user's learning objective. Development ends after validation/documentation; the next phase is understanding this implementation.

## Chapter 29 — Final mental model

Think of the application as a research desk. JSON is the measurement ledger. Notes are index cards helping locate relevant behavior. Embeddings and keyword matches find candidate cards. RRF combines their rankings. The optional reranker reads candidate pairs more closely. ML references are a separate bookshelf explaining possible mechanisms.

The LLM is a bounded selector and organizer at the desk. The tool dispatcher checks what it asks to do. Python is the calculator, record reader and factual report writer. Conversation memory identifies “that run”; persistent state keeps the investigation folder; LangGraph keeps the workflow position; a checkpoint marks where work can resume.

The hypothesis sheet separates observations from possible explanations and missing evidence. The experiment proposal declares what will change and how outcomes will be judged. Human approval authorizes the exact sheet and mode. The executor is a restricted instrument, not a shell available to the LLM. A dry run checks that path without creating scientific data.

An answer is useful when the user can trace it from a claim to the appropriate source and understand its limits. A new experiment is useful when it discriminates plausible explanations rather than merely adding another number. These principles connect the mathematics, architecture and interface.

## Chapter 30 — Explaining the project to an interviewer

Describe the problem first: saved ML experiments contain measurements but are awkward to discover, compare and investigate through ordinary language. Explain the three workflows: exploration, evidence-backed investigation and explicitly approved controlled follow-up.

Then trace the architecture: Streamlit → conversation/reference resolution → conditional LangGraph route → validated tools → structured JSON or note/knowledge retrieval → deterministic analysis and source-aware answer. Research adds a structured plan, competing hypotheses, proposal validation, durable approval interrupt and restricted execution.

Explain one actual technical decision and its evidence. For example, source-priority hybrid retrieval was retained after flat mixing of derived summaries hurt old labels; reranking remains optional. Show the actual final benchmark rather than presenting a tiny local score as universal performance. Explain cosine/RRF arithmetic and why Python, not the LLM, supplies numerical comparisons.

Be precise about agency: the model selects bounded options and tools; Python enforces scope, scientific checks, exact constraints and permission. State that hypotheses have descriptive statuses, not invented confidence percentages. Mention real local-model journeys, deterministic failure scenarios and UI checks as different kinds of evidence.

End with the important limits: one small experiment corpus/validation split, incomplete historical provenance, restricted intervention family and full live training unverified pending explicit approval. Do not claim production scale, causal proof or autonomous research. The meaningful achievement is an integrated, inspectable local research assistant whose decisions and evidence can be studied end to end.

# Executed results and operation

## Actual final evaluation

Deterministic suite: **81/81 passed**, 0 failures/errors. UI checks: **10 passed**. Final journeys used **live Ollama and cached MiniLM; dry-run execution**. Separate compatibility/process-restart sample: **4/4 passed**. These are different evaluation scopes, not one blended model success rate.

### Original five labels under current methods

| Method | Recall@2 | MRR@2 |
|---|---:|---:|
| keyword | 0.9000 | 0.8000 |
| semantic | 1.0000 | 0.9000 |
| hybrid | 1.0000 | 0.9000 |
| reranked | 0.8000 | 0.7000 |

Historical hybrid on those labels was 0.90 Recall@2 and 0.90 MRR@2; its separate archived artifacts remain intact.

### Additional twelve local relevance labels

| Method | Recall@2 | MRR@2 |
|---|---:|---:|
| keyword | 0.7917 | 0.7500 |
| semantic | 0.9167 | 0.8333 |
| hybrid | 0.9583 | 0.9167 |
| reranked | 0.8750 | 0.8333 |

### All seventeen note-relevance labels

| Method | Recall@2 | MRR@2 |
|---|---:|---:|
| keyword | 0.8235 | 0.7647 |
| semantic | 0.9412 | 0.8529 |
| hybrid | 0.9706 | 0.9118 |
| reranked | 0.8529 | 0.7941 |

Exact unnoted-ID coverage: 6/6 found first. This is a separate identifier-coverage task, not semantic-relevance accuracy. Reranking remains off by default. Labels were frozen before scoring; no endless tuning was done after the expanded evaluation.

### Observed primary-retrieval misses

```json
[
  {
    "id": "heldout_paraphrase",
    "query": "Did validation loss increase and subsequently recover?",
    "relevant": [
      "baseline_gap_001",
      "lr_01_seed2"
    ],
    "hybrid": {
      "recall_at_2": 0.5,
      "mrr_at_2": 1.0,
      "top_ids": [
        "baseline_gap_001",
        "lr_005_gap_001"
      ]
    }
  }
]
```

No unrestricted natural-language unsupported-claim percentage was measured. Structured grounding and approval checks are scenario assertions; live training remains untested. AppTest is UI execution, not browser visual inspection. An initial compatibility attempt encountered an unavailable Ollama server. The initial final investigation also used policy fallbacks for planning and hypotheses; that trace is preserved in reports/final/initial_investigation_fallback.json and initial_journeys.json. Ollama was restarted with its existing D: models. The final rerun recorded actual LLM planning and hypothesis selections, and compatibility passed separately. A server outage or fallback is not labeled as a successful model choice.

### Measured journey timings

| Journey | Question | Seconds | Status |
|---|---|---:|---|
| 1 Exploration | What experiments do we have? | 6.125 | completed |
| 1 Exploration | Which had the best final validation accuracy? | 0.968 | completed |
| 1 Exploration | Show its training and validation curves. | 1.016 | completed |
| 2 Conversation | Tell me about lr_01_seed3. | 1.031 | completed |
| 2 Conversation | Compare that run with lr_005_seed3. | 1.594 | completed |
| 2 Conversation | Why might the difference exist? | 39.375 | completed |
| 3 RAG | Have we seen unstable validation-loss behavior before? | 4.578 | completed |
| 4 Investigation | Investigate why lr_01_seed3 performed worse than lr_005_seed3. Search notes, check previous experiments, retrieve ML knowledge, and propose a controlled follow-up. | 5.500 | awaiting_approval |
| 6 Error handling | Who won the football World Cup? | 0.141 | completed |
| 6 Error handling | Show lr_01_seed33 | 0.000 | invalid_request |
| 6 Error handling | Plot it. | 0.000 | clarification_needed |

These are observed local request durations for this run, not a controlled latency benchmark; caching, model startup and contention affect timing.

### Final artifact acceptance

```json
{
  "status": "COMPLETE",
  "checks": {
    "original_data_unchanged": true,
    "main_application_health": true,
    "deterministic_scenarios_pass": true,
    "unified_ui_checks_pass": true,
    "compatibility_and_process_restart_pass": true,
    "all_six_journeys_recorded": true,
    "real_local_model_trace": true,
    "dry_run_completed": true,
    "no_new_training_records": true,
    "all_four_documents_exist": true,
    "thirty_learning_chapters": true,
    "master_begins_with_architecture": true,
    "actual_core_sources_embedded": true,
    "actual_core_source_hashes_match": true,
    "no_unexpanded_code_placeholders": true
  },
  "scope": "Completed local application and learning package; live training explicitly unverified pending user approval.",
  "deterministic_passed": 81,
  "ui_checks_passed": 10,
  "live_training_verified": false,
  "browser_visual_inspection_performed": false,
  "investigation_id": "INV-A2B6989CC1"
}
```

## Exact commands and study operation

```powershell
cd "D:\Agentic_ai_rag projects"
.\.venv\Scripts\streamlit.exe run ui.py
.\.venv\Scripts\python.exe app.py --question "What experiments do we have?"
.\.venv\Scripts\python.exe app.py --offline --lexical --question "Investigate why lr_01_seed3 underperformed."
.\.venv\Scripts\python.exe investigate.py list
.\.venv\Scripts\python.exe investigate.py show INV-A2B6989CC1
.\.venv\Scripts\python.exe investigate.py resume INV-A2B6989CC1
.\.venv\Scripts\python.exe investigate.py export INV-A2B6989CC1
```

The recorded demonstration is dry-run completed; resume does not retrain it. Start a new objective in the UI for a new pending proposal. Inspect its exact parameters and hash before deciding. A decision template for a new pending proposal is:

```powershell
.\.venv\Scripts\python.exe investigate.py decide "INV-ID-FROM-LIST" approved --hash "EXACT-HASH-FROM-SHOW" --mode dry_run
.\.venv\Scripts\python.exe investigate.py cancel "INV-ID-FROM-LIST"
```

Replace quoted placeholders with the displayed ID/hash. `rejected`/`deferred` are alternative decisions. `--mode live` is a distinct explicit authorization for the displayed workload; no live-training command was run during final development. Editing uses `modify ID proposal.json` or the UI, invalidates approval and requires review again. Completed proposals cannot be repurposed through another execution; create a new proposal/investigation.

The installed environment/caches permit local/offline operation. Primary `--offline --lexical` avoids Ollama and embedding imports; ordinary operation uses localhost and local-only model weights. Fresh setup requires internet for Python packages and initial Ollama/MiniLM weights; the optional reranker has its own explicit download. The restricted executor refuses missing datasets rather than downloading them. README gives the exact new-install setup and D: environment configuration.

```powershell
.\.venv\Scripts\python.exe evaluate_final.py
.\.venv\Scripts\python.exe validate_final_ui.py
.\.venv\Scripts\python.exe evaluate_final_retrieval.py
.\.venv\Scripts\python.exe demonstrate_final.py --live
.\.venv\Scripts\python.exe docs\build_final_docs.py
```

The educational references remain `app.py --agent manual`, `--agent graph`, `--agent simple`, and `legacy_ui.py`. The main application no longer requires selecting a historical version. Follow the learning guide's 30 chapters, then open the walkthrough beside source, then follow the complete runtime trace, then reproduce selected checks. Development is complete within the stated bounded scope; the next activity is study.

## Verified model/environment inventory

```json
{
  "python": "3.12",
  "packages": {
    "torch": "2.14.1",
    "torchvision": "0.29.1",
    "sentence-transformers": "6.1.0",
    "streamlit": "1.65.0",
    "langgraph": "1.2.12",
    "langgraph-checkpoint-sqlite": "3.1.2"
  },
  "ollama_executable": "D:\\Ollama\\ollama.exe",
  "ollama_models": "D:\\Ollama\\models",
  "embedding_cache": "D:\\Agentic_ai_rag projects\\.model_cache",
  "pip_cache": "D:\\Agentic_ai_rag projects\\.pip_cache",
  "dataset_cache": "D:\\Agentic_ai_rag projects\\data",
  "new_model_or_dataset_downloaded": false
}
```
