# ML Experiment Detective — Complete Learning Guide

This book explains the implemented local application from basic ML through retrieval, tools, planning, durable investigations and human approval. Examples labeled **illustrative** teach mathematics; examples labeled **measured** come from saved JSON or executed evaluation artifacts. Real code excerpts are inserted from the working source by `docs/build_final_docs.py`; no excerpt is invented.

Read in chapter order. Keep the app open beside the book, starting with Overview and Experiment Explorer. You need basic Python, but no previous knowledge of RAG or agents. The application combines the completed experiment tools and research workflow in one interface.

## Chapter 1 — What problem are we solving?

Training a model produces a number, but understanding that number requires context. Was the data split the same? Did dropout change? Was accuracy measured after the same number of epochs? Is a validation-loss increase a persistent effect or a temporary fluctuation? A folder of results becomes difficult to question reliably from memory.

The Detective makes those records inspectable. It lists and filters experiments, plots curves, compares measured outcomes, retrieves related notes, considers explanations and proposes a controlled test. It saves investigations so closing a window does not erase the research question. Training requires a separate explicit decision.

An LLM is useful because users describe objectives in language: “Have we seen unstable behavior?” does not specify a filename. Qwen can select a tool or choose useful planning options. It is not needed to multiply accuracy by 100 or subtract two losses. Python supplies those operations because a fluent sentence is not evidence of correct arithmetic.

**Concrete example:** “Which run was best?” invokes measured ranking. “Show its curve” uses conversation focus. “Investigate why it underperformed” can require retrieval, matched comparisons, knowledge and competing hypotheses. The same interface supports all three levels of effort. A reactive lookup should not create a full scientific plan unnecessarily.

The facade `ResearchAssistant.ask` connects resettable conversation state to the durable investigator. `question` is the user's text, `resolved` is the text after reference resolution, and `context` records what resolution occurred. It checks unknown IDs, calls the graph and remembers the successful result. Its output is a dictionary containing answer, trace, status and, for research, an investigation ID.

<!-- CODE assistant.py::ask -->

The next chapter establishes where the evidence comes from. The assistant cannot be more trustworthy than its experiment records.

## Chapter 2 — How experiment data is generated

Fashion-MNIST contains grayscale clothing images and category labels. An image is a grid of 28×28 values; `ToTensor` makes the grid available to PyTorch with a grayscale channel. A batch has shape `[B,1,28,28]`. Flattening changes each image into a vector of 784 inputs without discarding pixels.

The project takes a reproducible random permutation of the official **training** partition. With split seed 42, the first 10,000 positions form the training pool and positions 10,000–11,999 form validation. A smaller training-size experiment takes fewer images from the same training pool; it does not shift validation into newly available positions. The official test partition is excluded from proposal selection and follow-up analysis.

The MLP computes `h = ReLU(W1 x + b1)` and `z = W2 Dropout(h) + b2`. The hidden width is 128. Each output `z_j` is a logit, not a probability. Softmax converts logits to `p_j = exp(z_j) / sum_k exp(z_k)`. Cross-entropy for the correct class `y` is `L = -log(p_y)`; a confident wrong answer has high loss. Accuracy is `correct / total` and ignores how confident incorrect predictions were. Thus accuracy can improve while loss rises.

<!-- CODE phase0.py::SimpleMLP -->

An epoch processes the chosen training subset once. A batch is a smaller group used for one optimizer update. With 10,000 images and batch size 128, `ceil(10000/128)=79` batches are needed; the final batch has 16 images. Ten thousand images are not reduced to 128 images.

Backpropagation computes gradients describing how parameters affect loss. SGD uses `theta_next = theta - learning_rate * gradient`. **Illustrative scalar example:** if a parameter is 2, gradient 0.4 and rate 0.1, the update is `2 - 0.1×0.4 = 1.96`. Increasing the rate changes the update distance, but this alone does not prove the cause of a particular validation pattern.

`optimizer.zero_grad()` clears gradients from the previous batch; `loss.backward()` computes current gradients; `optimizer.step()` updates parameters. `model.train()` activates training behavior such as dropout; `model.eval()` changes that behavior for evaluation. `torch.no_grad()` avoids building a gradient graph when measuring results.

The evaluator multiplies each batch's average loss by its actual sample count, adds those totals, then divides by the whole dataset size. Averaging batch means without weights would give a short final batch too much influence. `train_loss_during_epoch` averages losses while the model changes; `train_loss_after_epoch` evaluates one fixed final-epoch model. They answer different questions.

<!-- CODE phase0.py::evaluate -->

Split, shuffle and model seeds control different pseudo-random choices. Sharing them helps control a comparison; it does not guarantee identical trajectories when learning rates differ, or identical results across every software/hardware environment. These details are saved as configuration, which makes the next chapter's structured data useful.

## Chapter 3 — Structured and unstructured data

Structured data has explicit fields with defined meanings. A run JSON contains `config` and `metrics`. `config.learning_rate` is directly filterable; `metrics[4].val_accuracy` is the recorded epoch-five fraction. New approved runs can also include provenance identifying the proposal, investigation, approved hash and executor.

Unstructured text is written for reading. A note can say that validation loss rose and recovered. That description helps a user discover the experiment without remembering its ID. It is not an independent new measurement: the original notes explicitly say they paraphrase saved metrics. Counting a note and its source JSON as two independent experiments would exaggerate evidence.

Metadata describes the record: a path, run ID, source category or configuration field. Provenance describes where it came from. A derived summary is generated by Python from JSON and labeled `DERIVED_ANALYSIS`; original observations remain `EXPERIMENT_NOTE`. General ML documents use `ML_KNOWLEDGE`. A hypothesis is labeled `HYPOTHESIS`, even if its prose sounds persuasive.

<!-- CODE experiment_data.py::load_run -->

`load_run` restricts the identifier format, constructs a path under `runs`, checks that the file exists and verifies consecutive epochs and matching IDs. Those checks prevent a misspelled identifier or path-like argument from becoming a guessed answer. More detailed analysis checks required numeric metrics before calculating differences.

**Measured example:** both seed-three JSONs record the same split, subset, model/shuffle seeds, hidden width, optimizer, batch size and horizon; learning rate changes. Exact architecture implementation history is not fully recorded in old JSON, so the report still names missing provenance. Known settings are not proof that every possible condition was controlled.

The system needs all three data types: JSON for numbers, notes for behavior discovery and attributed knowledge for mechanisms. Retrieval begins with the simplest text method.

## Chapter 4 — Keyword retrieval

Keyword retrieval compares literal words. Tokenization turns text into comparable units. `words` lowercases and finds letters/digits; the primary `tokens` function removes common words while retaining negation and configuration numbers. The historical keyword scorer uses set overlap: `score(query,document)=|tokens(query) intersect tokens(document)|`.

<!-- CODE note_retrieval.py::keyword_rank -->
<!-- CODE v3/retrieval.py::tokens -->

**Illustrative example:** query tokens `{validation, loss, recovery}` and a note with `{validation, loss, rose, fell}` share two words, so the overlap score is 2. A note sharing only `loss` scores 1. Sorting chooses the larger overlap first; tied scores have a stable run-ID order so repeated queries do not randomly reorder.

Stopwords such as “the” and “we” can otherwise reward an irrelevant note. Negation is different: “without dropout” and “with dropout” mean different things, so `without`, `no` and `not` are retained. Exact numeric filters are handled by JSON, not by assuming that text overlap understands a condition like learning rate 0.05.

The real note `lr_005_gap_001` says validation loss decreased in each of five epochs. A query saying “steadily declining held-out error” may share few exact words despite referring to the same idea. Keyword matching also cannot reliably distinguish a number in the primary run from a number mentioned about a matched run. These are reasons to add semantic retrieval, not reasons to discard exact matching.

The final policy retains the historical scorer for comparison and uses normalized tokens in the primary investigator. Technical run IDs get explicit exact-match handling rather than being left entirely to embeddings. The next component addresses paraphrases.

## Chapter 5 — Embeddings

An embedding represents text as a list of real numbers. Texts with related meanings tend to point in related directions in the model's learned space. The coordinates are not manually assigned labels such as “coordinate 7 means overfitting.” The model learns internal features from training objectives and examples, and individual coordinates generally have no stable human interpretation.

The cached `all-MiniLM-L6-v2` encoder produces 384-dimensional vectors. Its local configuration was inspected. The project does not train this language model. The sentence-transformers wrapper tokenizes text, applies the pretrained transformer and its configured pooling into a sentence-level representation. Query and document vectors use the same encoder, making them comparable.

<!-- CODE note_retrieval.py::_embedding_model -->

`MODEL_ID` identifies the encoder; `MODEL_REVISION` pins the cached revision; `cache_folder` puts its files under the project on D:. `local_files_only=True` makes normal searches use installed weights rather than silently downloading another model. `lru_cache` reuses the loaded model object within a Python process.

**Illustrative two-dimensional teaching vectors:** give “loss oscillates” vector `[1,1]` and “validation error fluctuates” vector `[2,2]`. Their directions match even though lengths differ. These vectors are invented only to teach geometry; the real 384 coordinates are computed by MiniLM and are not these manually assigned values.

Many dimensions let the learned representation express more variation than a two-axis drawing can show. More dimensions do not automatically mean a better model or better evidence. A relevant vector match can still point to a note about a different seed or configuration. Embeddings identify candidate text; JSON inspection verifies measurements.

The question is now how to compare two vectors. That requires cosine similarity.

## Chapter 6 — Cosine similarity

For vectors `a` and `b`, the dot product is `a·b = sum_i a_i b_i`. The Euclidean norm is `||a|| = sqrt(sum_i a_i²)`. Geometry gives `a·b = ||a|| ||b|| cos(theta)`, so dividing by both lengths gives `cosine(a,b) = (a·b)/(||a|| ||b||)`.

**Illustrative calculation:** let `a=[1,2]`, `b=[2,1]`. The dot product is `1×2+2×1=4`. Both norms are `sqrt(5)`, so cosine is `4/(sqrt(5)×sqrt(5))=4/5=0.8`. For `c=[-2,1]`, `a·c=-2+2=0`, giving cosine 0. The first document direction is closer to the query direction.

Scaling `b` by ten changes its length but not its cosine. This is useful because semantic closeness should not simply reward a larger vector magnitude. Cosine is bounded by -1 and 1 for nonzero vectors. A cosine of 0.8 does **not** mean an 80% probability that a causal explanation is true.

<!-- CODE note_retrieval.py::cosine_similarity -->

`np.dot` computes the numerator; `np.linalg.norm` computes each length; `float` converts the numerical library's scalar into an ordinary Python number for JSON. The code assumes nonzero valid encoder output. The real model normally produces nonzero vectors; the project is not a general vector-processing library with arbitrary zero-vector inputs.

The angle for cosine 0.8 is approximately 36.87 degrees. Orthogonal vectors have a 90-degree angle and cosine 0; same-direction vectors have angle 0 and cosine 1; opposite directions have angle 180 degrees and cosine -1. These geometric examples explain ranking, not scientific confidence.

A similarity score is a ranking instrument, not a calibration of truth. We next apply this calculation to every candidate document.

## Chapter 7 — Semantic retrieval

The semantic search steps are: load candidate notes; encode the query and note texts; calculate one cosine per note; sort by descending cosine; return the top `k` candidates. `k` is how many candidates to inspect, not how many experiments exist.

<!-- CODE note_retrieval.py::encode_queries_and_notes -->
<!-- CODE note_retrieval.py::semantic_rank -->

`encode_queries_and_notes` returns vectors with the query vectors first and note vectors after them. `semantic_rank` zips each note path/text with its vector. The paths remain attached during sorting, preventing a high similarity from being accidentally assigned to the wrong source. A stable secondary sort on file stem handles ties.

Indexing means organizing documents and their searchable representations. At this collection size, the implementation reads the small corpus and computes embeddings for a request. It caches the encoder object, not a permanent vector index. There is no approximate-nearest-neighbor database hidden in the code. The work is roughly proportional to the number of candidates times vector dimension, in addition to encoding cost.

**Real query to inspect:** “Have we seen unstable validation-loss behavior before?” The saved journey contains the actual search results, cosine values and the subsequent `get_experiment` result. The agent cannot treat a retrieved note as enough to invent the exact current loss; it follows the returned run ID into JSON.

At millions of documents, repeated encoding and exhaustive comparison would be expensive. A persistent embedding index could then be justified. Eleven saved runs and a handful of notes do not demonstrate that need. The chosen implementation favors explicit, inspectable operations.

Semantic retrieval handles paraphrases, while keyword retrieval preserves exact terminology. Combining their rankings is the next step.

## Chapter 8 — Hybrid retrieval and RRF

Keyword and semantic methods can disagree usefully. A technical identifier may match exactly while meaning-oriented wording matches another observation. Reciprocal Rank Fusion combines **rank positions**, avoiding the need to pretend an overlap count and a cosine share the same scale.

For document `d`, `RRF(d)=sum_m 1/(K+rank_m(d))`. This project uses `K=60`. A method that does not return the document contributes zero. The constant reduces the dominance of tiny top-rank differences; it is not the requested top-k result count.

**Illustrative worked example:** A has keyword rank 1 and semantic rank 3, giving `1/61+1/63≈0.032266`. B has ranks 2 and 1, giving `1/62+1/61≈0.032522`. B ranks ahead because it is well placed by both signals. Raw cosine 0.8 is never added directly to overlap count 2.

<!-- CODE v3/retrieval.py::search_notes -->

Read `kr` as keyword rank and `sr` as semantic rank. `rows` joins scores, source categories, paths and observation text. The final policy calculates ranks within source types, prioritizes original notes for broad behavior discovery, exposes derived summaries separately, and gives exact run-ID matches priority. This source policy is part of ranking; it is not plain RRF alone.

The complete trace contains an automatically calculated table of actual note ranks and their `1/(60+rank)` contributions. Compare the formula with `rrf_score`, allowing for display rounding. Generated summaries may be useful but cannot be counted as independent human observations.

Hybrid retrieval is not guaranteed to beat semantic retrieval. A noisy keyword ranking can pull an irrelevant candidate upward. During retrieval development, flat mixing of derived summaries reduced performance on the old labels. The measured source-priority policy was retained instead. The final expanded benchmark reports its misses and does not repeatedly tune to force a perfect score.

The next stage can reconsider candidate text jointly with the query, at additional cost.

## Chapter 9 — Reranking

A bi-encoder independently maps the query and each document into vectors. Their representations can be reused, making candidate search efficient. A cross-encoder reads the query and document together and predicts a relevance score for that pair. Joint attention can model interactions that separate vectors miss, but it requires a separate inference for each candidate pair.

<!-- CODE v2_retrieval.py::_reranker -->

The optional cached model is `cross-encoder/ms-marco-MiniLM-L2-v2`. `predict([(query,text), ...])` produces scores used to reorder candidates. These are relevance signals, not measurements, probabilities of a hypothesis, or permission to ignore source types. The final implementation preserves exact-ID and source-priority constraints when reranking.

The historical five-query results favored leaving reranking off: Recall@2 0.80 and MRR@2 0.70 for the historical reranked path, versus 0.90/0.90 for historical hybrid. Final results are reported separately because the corpus/policy and benchmark have expanded. A model trained for web-style relevance need not improve this small scientific-note collection.

The UI exposes reranking in Advanced settings. If weights are absent, the tool retains hybrid ordering and records that fallback instead of downloading weights during a normal query. Reranking is a candidate refinement stage; it does not solve missing experiment metadata.

These retrieval components become RAG only when they supply evidence to the answer workflow.

## Chapter 10 — What exactly is RAG?

Retrieval-Augmented Generation combines retrieval of relevant external information with producing an answer conditioned on that information. Retrieval finds candidates. Augmentation puts selected evidence into a model's context. Generation produces a response. Grounding means the response is tied to appropriate evidence rather than relying on plausible remembered text alone.

In conventional RAG, the application often always retrieves passages, builds one prompt, and asks a model to write an answer. The Detective uses retrieval as an agent tool: the model can ask for notes, observe returned IDs, request exact JSON and ask for ML knowledge. Python renders factual numbers. That is a retrieval-augmented tool workflow rather than an unrestricted model paraphrase of everything retrieved.

<!-- CODE v2_agent.py::execute_call -->

The dispatcher validates a permitted call, executes Python, records a tool result and appends a `role='tool'` message. `model_result` can be compact while the visible trace retains full results. This matters because the model's context window is limited; an audit trace and an LLM prompt need not contain the same amount of data.

A hallucination is an unsupported invented claim, such as a run ID that was never saved. A citation alone does not fix it: a real source can fail to support the attached claim. The system limits IDs, verifies measurements, distinguishes source types and uses a deterministic renderer. It still does not prove that every qualitative statement is a statistically valid explanation.

**Concrete example:** a note says loss spiked, JSON verifies the epochs and values, a general reference describes high learning-rate behavior, and the report says instability is a possible mechanism. The reference cannot turn “possible” into “this caused that run's failure.” Next we examine that separate knowledge corpus.

## Chapter 11 — External ML knowledge RAG

Experiment RAG asks “What happened in our runs?” Knowledge RAG asks “What general mechanisms might be relevant?” These questions use different sources. A general dropout reference does not contain the final accuracy of a locally trained Fashion-MNIST run.

<!-- CODE v2_retrieval.py::_knowledge_chunks -->
<!-- CODE v3/retrieval.py::knowledge -->

Each knowledge file supplies a title, URL, topic, source type and a short attributed paraphrase. The corpus includes the original five topics plus final notes about seeds and experimental design/data leakage. The two additional references were checked against primary PyTorch and scikit-learn documentation. Those URLs record provenance; ordinary questions search local text and do not browse the internet.

`knowledge` checks whether the question is covered, reuses the existing MiniLM/RRF search, and can use a transparent lexical fallback. A transformer-attention question is recognized as ML-related but outside this small local corpus; the assistant says that it cannot provide a grounded answer from available sources.

**Example:** a learning-rate comparison produces measured loss changes. Retrieved optimization/validation material can explain why rates, gradients and generalization might matter. The report puts measured observations, retrieved mechanisms, possible interpretation and uncertainty in separate sections. A missing knowledge result remains missing; the app does not silently fill it with unmarked model knowledge.

The model that chooses these tools is distinct from the models that retrieve text, which is the next chapter's focus.

## Chapter 12 — LLMs and Ollama

An LLM is a trained language model that predicts and generates token sequences conditioned on an input context. It can follow instructions and generate structured choices, but a likely token sequence is not automatically a true statement or a correctly executed function.

Ollama is the local inference server/runtime. `qwen3:1.7b` is the installed generative model served by it. MiniLM is a separate sentence encoder used for retrieval. The optional cross-encoder is a separate relevance model. Installing Ollama does not itself create embeddings, and an embedding model does not replace the text model.

<!-- CODE v2_agent.py::ask_ollama -->

The request goes to localhost `/api/chat`, includes messages and offered tool schemas, disables streaming/thinking output, and uses temperature zero for repeatable choices where the runtime permits. `num_ctx=4096` bounds the configured context window; `num_predict=400` bounds output length. Tokens are model units, not one-to-one words. A long trace can exceed a useful prompt size, so the app sends compact evidence for choices.

The research planner uses a JSON-schema completion; hypothesis selection uses native tool calling. Both are actual local model outputs recorded in the trace. Python validates those outputs. If a local model is unavailable or emits a malformed request, the primary graph records a bounded policy fallback. Offline mode deliberately uses Python choices and must not be presented as an LLM decision.

No paid API or larger replacement model is required. Model files remain on D:. With that distinction clear, we can examine how a tool request becomes Python work.

## Chapter 13 — Tools and function calling

A tool is an application function described to the model through a schema. The schema supplies a name, description, argument properties and required fields. The model returns structured arguments; it does not directly invoke Python or gain a shell.

<!-- CODE v2_tools.py::_schema -->
<!-- CODE v2_tools.py::execute_tool -->

The registry maps allowed names to handlers. Validation rejects unsupported names, unexpected fields, absent required arguments, wrong types, invalid enum values, non-finite numbers and invalid ranges enforced by handlers. A run ID is also validated when opening its JSON. Booleans are explicitly excluded from integer/number arguments because Python otherwise treats `True` as an integer.

**Example input:** `get_experiment` with `{'run_id':'lr_01_seed3'}` returns measured configuration and metrics. `{'run_id':'../secret'}` fails ID validation. A request named `shell` is not in the menu and cannot turn a string into a command. Exact constraints stated in the question can correct model arguments with an `APP FILTER` trace.

The final application adds `rank_experiments` to the same registry. It ranks saved accuracy, loss or maximum positive loss rises and supports exact filters. It does not infer causes from ranking. Its numbers are calculated in Python and passed to the renderer.

The complete master reference includes the exact current tool schemas and actual planner/hypothesis menus. Scientific workflow functions executed by Python are labeled as such; they are not falsely listed as autonomous model calls. Tool requests, tool execution and results form the next chapter's loop.

## Chapter 14 — What is an AI agent?

An agent uses observations to choose actions toward a goal. A fixed workflow always follows prescribed steps. A single tool call adds an action to a language-model interaction. A multi-step agent can choose a tool, inspect its result and decide whether another action is needed.

<!-- CODE v2_agent.py::run_manual -->

The educational manual loop makes choose → act → observe explicit. The tool menu changes after evidence: a behavior search is followed by exact inspection; a question asking why can then retrieve general knowledge. A bounded call count prevents an endless tool loop. The primary graph uses the same state, dispatcher and renderer with additional visible recovery for model failure.

The Detective is intentionally a bounded agent. Python narrows the menu, enforces IDs and requires some evidence steps. The LLM chooses within that menu. Calling a deterministic routing rule an autonomous decision would hide how the system actually works. Conversely, a graph does not become non-agentic merely because important safety boundaries are prescribed.

**Example:** “Have we seen unstable validation before?” first searches notes. The result identifies candidate runs. The model can request a returned run and then stop or ask for a relevant mechanism when the question needs it. Its next context contains the previous tool's observation, which is the key difference from a single isolated function call.

Simple questions can finish with a direct tool result. Complex research benefits from a plan, which the next chapter adds.

## Chapter 15 — Agent planning

A plan is structured intended work, not just a paragraph saying “I will investigate.” The project stores step IDs, tools, dependency lists, status and decision origin. Planning is useful when an objective requires several kinds of evidence and a later human decision. It is wasteful for a request asking for one saved accuracy.

<!-- CODE v3/planner.py::make_plan -->

The model can select optional note search, seed comparisons and ML-knowledge retrieval, plus a covered topic. Python prescribes exact measurements, scientific validation and the permission boundary. `optional_step_origins` records a model choice separately from a step inserted to honor the user's explicit request. A missing run ID requires discovery; “search notes” in the objective requires that step even if the model omits it.

Observation can revise the concrete plan. For a single-run underperformance investigation, the collection node finds a corresponding saved run whose recorded changes are limited to learning rate. For a no-ID design request, retrieval discovers candidates and Python selects a fully recorded controlled pair when one exists. The trace records `REPLANNING` with the actual IDs and policy reason.

Replanning is bounded: it is not autonomous code writing or an unlimited research loop. The initial choice has at most two model attempts, the graph has a finite route and recursion bound, and training is never the automatic consequence of a plan.

To continue a plan later, intended work and observations need durable state.

## Chapter 16 — Memory and state

Conversation memory helps interpret language; investigation state preserves work. A source corpus is neither of those. A context window contains only what a particular LLM request sees. Treating all four as one vague “memory” makes errors hard to diagnose.

<!-- CODE v2_state.py::resolve -->

`focused_run_id` supplies a clear single-run referent. `comparison_run_ids` preserves the pair used by “the difference.” A corresponding learning-rate request searches saved configurations rather than asking embeddings to guess a partner. A fresh/reset session with “it” asks which run the user means. After a comparison, an ambiguous singular reference is not silently assigned to either member.

The last four conversation turns supply bounded summaries; the UI retains a bounded visible chat list. Reset clears conversational focus and history while leaving runs and saved investigations intact. An explicit research objective is saved with its resolved question and conversation snapshot, so a later report can show what was actually asked.

<!-- CODE v3/investigation_state.py::save -->

SQLite stores application snapshots, proposal configurations and decision audit events. LangGraph checkpoints store progress and suspended tasks. These are different responsibilities even though they share a database. The store closes each connection, which matters on Windows because open SQLite handles can keep files locked.

The next chapter explains how graph checkpoints control resumption rather than merely storing a transcript.

## Chapter 17 — LangGraph

State is the information passed among graph nodes. A node is a Python function reading state and returning an update. An edge chooses the next node; a conditional edge chooses among routes based on state. A tool node executes validated functions. `START` and `END` describe entry and termination.

<!-- CODE graph_agent.py::build_graph -->

The retained compact graph implements agent → tools → agent → final. The investigator graph adds classify, plan, collect, analyze, knowledge, hypotheses, validate, design, approval, execute, outcome and report nodes. Simple questions route directly to the compact tool graph. Unrelated questions return a scope limitation. A proposal failure routes to a report without training.

An interrupt suspends the graph at a checkpoint. It differs from simply returning “please approve”: a new process can reopen the same thread ID and supply a resume command. `SqliteSaver` makes the checkpoints durable. The investigation ID is the graph thread ID; it is not an embedding search key.

<!-- CODE v3/service.py::resume -->

`get_state` reveals pending nodes and interrupts. Loading a pending proposal is not approval. Only a persisted decision allows `Command(resume=...)`. The interrupted node executes again from its beginning, so work before `interrupt` must not launch training or consume an execution permission. Terminal results can be returned without rerunning the trainer.

LangGraph was introduced to make branching, pause/resume and workflow inspection explicit. A while loop remains a useful teaching reference. The framework itself does not supply scientific judgment; node functions and the model/policy decisions do. Next we examine the numerical reasoning those nodes perform.

## Chapter 18 — Deterministic analysis

For two comparable runs, define target minus baseline so the sign is unambiguous. Accuracy fractions are converted to percentages before reporting percentage-point differences. **Measured seed-three example:** `100×(0.7145−0.7590)=−4.45 pp`. Loss difference from full-precision JSON rounds to `+0.1303`. A percentage-point change is not a relative percentage change.

<!-- CODE v3/analysis.py::compare_records -->

For losses `L1,...,LT`, the maximum positive one-epoch rise is `max(0, L2−L1, ..., LT−L(T−1))`. **Illustrative curve:** `[0.8,1.0,0.7]` has largest rise 0.2 and a rise/recovery pattern across all three epochs. Recovery is descriptive; it does not erase the earlier increase or identify its cause.

Best accuracy is the maximum saved validation accuracy; final accuracy is the last saved value. Choosing the best epoch after inspecting validation is a selection decision, not an independent test-set result. The system reports both where relevant. A generalization-loss gap is `validation_loss−post_epoch_training_loss` when both exist. A falling training loss with rising validation loss flags a candidate interval, not a definitive overfitting diagnosis.

The comparison examines the union of configuration fields, explicit missing controls and provenance limitations. Different horizons or incomplete required metrics suppress final deltas. Seed-group summaries deduplicate repeated configurations; multiple filenames from the same conditions are not automatically independent replications. Means and population standard deviations describe observed blocks and are not confidence intervals.

These calculations establish observations. Hypotheses add possible mechanisms without changing those observations into causal proof.

## Chapter 19 — Hypothesis generation

An observation describes what was measured. A hypothesis proposes why it might happen. An assumption states what must hold for an interpretation to be useful. Confounding means multiple relevant variables changed, leaving their effects hard to separate. Missing evidence identifies what the current records cannot decide.

<!-- CODE v3/hypothesis.py::generate -->

Python constructs candidate statements conditioned on measured comparisons. H1 considers higher-rate loss-rise instability; H2 considers seed-dependent accuracy variation; H3 considers short-horizon sensitivity; H4 appears when an explicit train/validation interval rule is observed. When a rate comparison is unavailable, the candidate wording changes to a qualified configuration/unrecorded-condition explanation.

Ollama selects and orders at least two competing candidates through a tool schema. It does not freely invent measured evidence or write arbitrary causal conclusions. The candidate's `statement_origin` and `selected_by` fields make that distinction visible. An evidence registry links supporting/opposing references to exact JSON, derived calculations, notes or general knowledge.

**Measured counterevidence:** the higher-rate final accuracy changes direction across recorded seed blocks. This opposes “higher learning rate always lowers accuracy.” It does not automatically oppose the separate claim that the higher-rate arms showed larger maximum loss rises in those blocks. Different hypotheses need different predicted observations.

A status such as “consistent with current evidence” is descriptive and carries no arbitrary numerical confidence percentage. General ML material can support considering a mechanism; it cannot prove a local run's cause. The next step turns a hypothesis into a testable proposal.

## Chapter 20 — Controlled experiment design

A controlled comparison changes a specified variable while keeping relevant conditions matched. If learning rate and train size both change, a difference cannot be attributed specifically to rate. Matching recorded conditions reduces confounding but cannot account for every unrecorded condition.

<!-- CODE v3/experiment_designer.py::validate_proposal -->

The executable designer supports one concrete family: two Fashion-MNIST MLP runs with different learning rates and matched other settings. It uses a complete saved reference configuration, records shared fresh model/shuffle seeds, checks existing run IDs/configurations and reserved legacy plans, and enforces resource limits. The paused legacy seed-four branch is not automatically resumed.

Matching seeds makes the arms comparable under one randomness block. Replication means repeating the intervention under another independent block. A single successful block is evidence about that block, not a general population theorem. Same seeds also do not force identical parameter trajectories at different rates.

The primary metric is predeclared: compare each arm's maximum positive validation-loss rise. A larger higher-rate rise is consistent with the directional prediction; a smaller rise opposes it; equality is inconclusive. Final accuracy and loss are secondary. This prevents choosing whichever post-hoc metric tells the nicest story.

The proposal is machine-readable and independently validated before becoming eligible for approval. Candidate hypotheses about dropout, long horizons or arbitrary model families can need designs the restricted executor does not support; the report states that limitation. The next chapter addresses who may authorize the supported proposal.

## Chapter 21 — Human-in-the-loop agents

Human-in-the-loop means a person makes a required decision inside the workflow. Here that boundary protects time/resources and keeps a proposed experiment distinct from an authorized experiment. An LLM request cannot stand in for the user's consent.

<!-- CODE v3/investigation_state.py::claim_execution -->
<!-- CODE v3/investigation_graph.py::approval_node -->

The proposal hash is SHA-256 over canonical JSON with sorted keys. Approval stores the proposal ID, exact hash, execution mode, actor, reason and timestamp. A changed payload invalidates the earlier approval. Dry-run approval cannot authorize live execution. The training-code hash is checked as part of the proposal, so a changed trainer requires review again.

The graph interrupt saves the waiting state. Resume checks its token and the persisted decision; the token itself is not permission. The executor atomically changes approved to running inside a SQLite transaction, so approval is consumed once. A second live workload is blocked while another is running. Tests try pending, rejected, stale-hash, wrong-mode, repeated and model-origin bypasses.

Development demos explicitly use `development_dry_run`. They do not claim that the user clicked a live-training button. This is a trusted local application boundary, not multi-user authentication or protection against someone who can edit Python and the database. Stale proposals can still be rejected even when code changes make them ineligible for approval.

After an authorized decision, execution must remain restricted and observable.

## Chapter 22 — Experiment execution

The executor accepts a validated proposal, not an arbitrary shell string. A dry run validates permission/configuration, records planned runs and stops without launching a trainer or inventing metrics. Live mode requires its own explicit exact approval.

<!-- CODE v3/experiment_executor.py::execute -->

The fixed subprocess argument list invokes `v3.training_worker` with a JSON input path and `shell=False`. That worker reuses `phase0.run_training`. It restricts output to the run-ID-derived location, disables dataset downloads, uses the fixed training-partition split and records provenance. Exclusive file creation prevents overwriting old experiments.

The parent enforces a 600-second total budget, at most two runs and two CPU threads; the worker checks elapsed time and cancellation between training batches. Limits also cap epochs, subset size, batch size and hidden width. There is no OS-level RAM quota, and cancellation is cooperative rather than an instant guarantee during a native operation.

The UI runs explicitly approved live work in a background thread so execution status/cancel controls remain available. Logs and partial completed records are retained. A CLI cancellation request writes the fixed proposal cancellation marker. A worker failure, timeout or cancellation is recorded instead of being converted into a successful result.

After both arms complete, their configurations and metrics are checked, predefined comparisons are calculated and the report/hypothesis status can update. A restart that finds uncertain running work does not silently launch it again. Full live training was not run in final development; this integration is verified through dry runs, mocks and labeled ingestion fixtures. That distinction is part of the result, not a footnote to hide.

## Chapter 23 — Answer generation and grounding

The LLM selects bounded work; Python supplies measured facts. The final renderer groups observations, relevant ML knowledge, possible interpretation, limitations and sources. This is deliberately less flexible than letting a small local model freely compose numerical claims.

<!-- CODE v2_answers.py::render_answer -->

`tool_results` contains successful handler outputs. The renderer extracts accuracy, loss, curve patterns and rankings directly from those objects, attaches source paths and distinguishes general-reference URLs. It never asks the model to subtract two decimal values or invent a citation title. Source categories remain visible in research reports.

Exact argument constraints stated by the user can correct a model's request through a visible `APP FILTER`. A malformed/unavailable model call can use `APP POLICY` recovery. These interventions must not be called `AGENT CHOICE`. Failed tools stop bounded progress and produce an evidence limitation rather than a plausible invented result.

Unknown IDs get saved alternatives. Unrelated questions are rejected before irrelevant retrieval. Unsupported ML topics identify the small knowledge corpus's limitation. Ambiguous references ask for clarification. These behaviors protect the meaning of the answer as much as a mathematical check does.

A grounded answer is traceable, not infallible. Scientific validity and tool behavior require evaluation, the next chapter's subject.

## Chapter 24 — Evaluation

Evaluation compares behavior with explicit expectations. Retrieval labels say which notes are relevant to a query. `Recall@K = number of relevant items in top K / total relevant items`. With two relevant notes and one returned in top two, Recall@2 is 1/2. `RR@K` is the reciprocal rank of the first relevant result within K, or zero if none; if the first relevant note is second, RR@2 is 1/2. MRR averages reciprocal ranks across queries.

**Illustrative two-query example:** query A has first relevant rank 1, query B rank 2; MRR=(1+0.5)/2=0.75. Recall can differ because it counts all relevant items, while reciprocal rank only uses the first relevant item. Neither metric says whether a causal explanation is true.

<!-- CODE evaluate_final_retrieval.py::score -->

The final benchmark preserves the five historical labels, adds twelve frozen note-relevance judgments and six explicit unnoted-run coverage checks. The subsets are reported separately. Exact-ID coverage is easier than open-ended semantic relevance, so its success must not be advertised as general semantic accuracy. New labels are local judgments, not an independent hidden test set.

Deterministic tests cover numbers, invalid tools, memory, ambiguity, hypotheses, proposals, approval bypass, recovery and cancellation. Live Ollama journeys are reported separately. Streamlit AppTest exercises real widget paths without claiming browser screenshot inspection. A simulated trainer failure tests error handling; it is not a real measured training run.

The measured result tables are inserted below from executed artifacts. No unrestricted natural-language unsupported-claim percentage was measured. Passing finite scenarios does not establish correctness for every possible user question.

## Chapter 25 — Streamlit UI

Streamlit reruns the script when widgets change. `st.session_state` keeps per-session conversation objects and visible entries across those reruns. The durable investigation store lives outside that browser-session lifetime. A local page refresh is not approval and a conversation reset is not deletion of saved experiments.

The navigation presents Overview, Experiment Explorer, AI Chat and Investigations. Overview gives counts, local-model status and examples. Explorer lets users find IDs through tables/filters, inspect exact configuration/epoch data and compare two curves. Chat retains references and displays tool-produced charts. Investigations exposes plans, hypotheses, review/approval, execution and reports.

<!-- CODE ui.py::draw_run -->

`draw_run` gets its metrics from saved JSON and its chart points from `plot_run_metrics`. Percent accuracy uses a separate chart from loss because the scales have different units. Missing old training measurements remain blank. A changed setting is displayed rather than being silently treated as controlled.

Optional “Explain how the AI worked” expanders reveal resolved questions, available menus, actual model requests, policy/filter actions, results, retrieval stages and state changes. Ordinary users do not need to understand RRF or LangGraph to browse a table or reject a proposal.

The preserved older UI is an educational reference in `legacy_ui.py`; the recommended entry is `streamlit run ui.py`. There is no need to select a legacy runner before doing useful work. The next chapter follows one complete run through these layers.

## Chapter 26 — Complete end-to-end execution

The verified demonstration uses a real question asking why `lr_01_seed3` performed worse than `lr_005_seed3`, requests notes and ML knowledge, checks earlier experiments and proposes a controlled follow-up. `demonstrate_final.py --live` records actual local model requests, tool results and policy actions. It explicitly demonstrates only dry-run execution.

<!-- CODE demonstrate_final.py::main -->

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
