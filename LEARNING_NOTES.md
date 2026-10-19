# ML Experiment Detective learning record

## Current integrated MVP

Start the interactive local CLI with `.\.venv\Scripts\python.exe app.py`. The working path is `app.py` -> `simple_agent.py` -> `experiment_data.py` or `note_retrieval.py` -> saved `runs/` and `notes/`. The agent uses local Ollama `qwen3:1.7b`, shows a tool trace, and renders measured facts with source links. See `README.md` and the three files in `docs/` for the current architecture, reading order, and a real RAG trace. Historical scripts and artifacts below remain available; the fourth seed block was not trained.

## What we have built

- A small Fashion-MNIST MLP that records configuration and per-epoch training and validation metrics in `runs/*.json`.
- Fixed data selection and recorded seeds so runs can be reproduced and paired comparisons can hold known settings constant.
- A deterministic comparison script that reports changed settings, final metric differences, train-validation gaps, and a simple curve observation. It saves Markdown reports in `reports/`.
- A structured search script that filters saved runs by exact configuration fields or measured validation behavior.
- Fact-grounded observation notes in `notes/*.md` and a keyword search that ranks them by shared words.
- A local semantic search script that embeds the question and five observations, then ranks them by cosine similarity.
- A five-question retrieval evaluation that compares keyword and semantic rankings with Recall@2 and MRR@2.
- Exact `--dropout` and `--train-size` filters for both note searches, checked against the JSON configuration of each note's primary run before text ranking.
- A Markdown evidence-packet builder that combines retrieved observations with the linked run configuration and per-epoch metrics.
- A provider-neutral answer prompt built from an evidence packet, with allowed run-record citations and separate instructions for facts and hypotheses.
- A local Ollama factual-answer step using a small model, structured run-tagged facts, deterministic source-link rendering, and saved generation metadata.
- A numeric evidence gate that checks four-decimal loss values and two-decimal percentage accuracies in each model fact against its cited run JSON before saving an answer.
- A structured observation gate that verifies each model-selected run, epoch, metric, and displayed value together. For the held-out-error question, Python also checks that consecutive validation-loss values rise and then fall before stating the conclusion.
- Exact `--run-id` selection for evidence packets, plus a negative-case check that requires every cited validation-loss epoch before accepting a no-pattern answer.
- An offline answer evaluator with one Yes and one No case. It compares expected run scope, saved direct answers, source-backed observations, pattern coverage, and citations.
- A first hypothesis worksheet built from two matched learning-rate pairs, with supporting observations, counterevidence, missing evidence, and a proposed controlled follow-up.
- A local Ollama step that selects two of three prepared hypothesis candidates from a source-linked evidence catalog that grows with matched seed blocks. Python calculates each candidate's support and counterevidence IDs, verifies the model copied them exactly, and renders the report.
- A controlled follow-up planner that proposes a fresh matched seed block with two learning rates, checks unused run IDs and seeds, and saves a reviewable JSON and Markdown plan. The training script can print a proposed configuration with `--dry-run` before loading data.
- The follow-up planner now includes the measured outcomes from every source seed block and states how a new final-accuracy result would change the directional count. This makes the proposed test's purpose visible before training.
- A first local tool-using agent in `simple_agent.py` exposes two read-only run tools to Ollama, executes only allowlisted Python functions, returns JSON results as tool messages, and limits the loop to three calls. When the model stops, Python renders final measured facts and source links from the tool results; it does not publish the model's unchecked prose.
- The agent also exposes `search_notes(query)`, which calls the existing MiniLM embedding and cosine-ranking functions, returns the two highest-ranked observation notes with primary run IDs and scores, and lets the model inspect chosen runs with `get_experiment` in later turns.
- A third matched learning-rate seed block was trained from that plan, checked against the planned configurations, compared, and added to a new three-block hypothesis worksheet.

## Why these choices

- JSON is sufficient for the current number of runs and keeps every experiment inspectable.
- Numerical differences and exact metadata filters are ordinary Python calculations. They do not require an LLM or semantic retrieval.
- The observation notes paraphrase run metrics and link to their source records. They are examples of searchable text, not independent evidence.
- The small pretrained encoder maps text to 384-number vectors. For five notes, a direct comparison is simpler than a vector database; embeddings are recomputed on each run.
- Each evaluation question names its relevant primary run notes and explains the label. Recall@K is the fraction of those notes in the first K results; MRR@K averages the reciprocal rank of the first relevant result.
- When a question specifies a known run setting, an exact metadata filter can remove incompatible run notes before ranking their text. The user supplies these filters explicitly; the script does not infer them from the question.
- RAG uses retrieval to provide question-specific context to a generator. The project now assembles a source-linked packet and sends a grounded prompt to local Ollama. With five short notes, each observation stays whole and the saved JSON remains the source for numeric facts.
- The answer prompt places the question, response rules, allowed citations, and packet text together. It guides the local generator but does not guarantee that its output will obey the rules.
- Prompt instructions alone did not make the small model reliably cite sources. A JSON schema supplies run IDs with facts; Python rejects unknown IDs and adds the Markdown links. This enforces citation paths, not factual truth.
- A valid run ID can still be attached to an invented number. The numeric gate checks displayed metric values against the cited run record and records which values it inspected.
- Free-text claims are difficult to verify reliably. The current answer format separates `run_id`, `epoch`, `metric`, and `value`; Python checks the exact combination and writes the cited measurement sentence. For the held-out-error question, it also calculates the rise-then-fall conclusion from those checked observations.
- A single verified rise-then-fall triple is enough to support Yes. To support No for a cited run, the checker requires its entire validation-loss history; otherwise an omitted epoch could hide the pattern.
- When a run ID is already known, the packet builder selects that note directly. Semantic ranking adds nothing to this exact lookup and is skipped.
- Answer evaluation checks saved artifacts without another model call. It compares a human-labeled expected answer with a reference calculated from unrounded run JSON, then separates wrong source selection from failures in the generated answer or evidence.
- A hypothesis is a testable explanation, not a recorded measurement. The worksheet calculates measurements from run JSON and labels the proposed learning-rate explanation as tentative. It checks that each pair changes only learning rate and that the two seed blocks share other recorded settings.
- Early free-form model drafts attached valid evidence IDs to unsupported mechanism language or omitted the opposite final-accuracy outcome. Valid citations do not verify the reasoning between evidence and hypothesis. The accepted first version therefore lets Ollama select among prepared candidates while Python supplies wording, counterevidence, missing-evidence text, numbers, and run links.
- A controlled pair changes one setting while using the same validation images. The follow-up plan uses split seed 42 and validation positions 10000–11999 for both new runs; model and shuffle seeds 244/243 are new but shared within the pair. This makes a later difference easier to interpret than comparing runs with different validation subsets.
- Train and validation gaps use the same model after an epoch. The loss measured during training uses changing weights and is kept as a separate metric.

## Useful commands

The project-local `.venv` was created with access to the existing PyTorch installation, then the semantic-search dependency was installed there:

```powershell
python -m venv --system-site-packages .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-semantic.txt
```

```powershell
python search_runs.py --train-size 1000 --epochs 40
python search_runs.py --min-val-loss-rise 0.1
python compare_runs.py small_no_dropout_001 small_dropout_05_001
python search_notes.py "validation loss rose" --top-k 2
.\.venv\Scripts\python.exe semantic_search_notes.py "Did the held-out error spike and recover?" --top-k 2
.\.venv\Scripts\python.exe evaluate_retrieval.py
.\.venv\Scripts\python.exe semantic_search_notes.py "Which small-data run trained without dropout?" --dropout 0 --train-size 1000
.\.venv\Scripts\python.exe build_context.py "Did the held-out error spike and recover?" --packet-id another_unique_id --top-k 2
python prepare_answer_prompt.py another_unique_id
python prepare_answer_prompt.py held_out_spike_002 --prompt-id another_new_prompt_id
python generate_answer.py another_new_prompt_id
python build_context.py "Did the held-out error spike and recover in lr_005_gap_001?" --packet-id new_negative_case --run-id lr_005_gap_001 --top-k 1
python evaluate_answers.py
python build_hypothesis_worksheet.py learning_rate_outcome_001
python generate_hypotheses.py learning_rate_outcome_001 --output-id another_new_hypothesis_id
python generate_hypotheses.py learning_rate_outcome_002 --output-id another_new_three_block_id
python plan_followup.py learning_rate_seed3_001
python plan_followup.py learning_rate_seed4_001
python simple_agent.py "Why did lr_01_seed3 perform worse than lr_005_seed3?"
.\.venv\Scripts\python.exe simple_agent.py "Have we seen unstable validation behavior before?"
python phase0.py --run-id lr_005_seed3 --learning-rate 0.05 --model-seed 244 --shuffle-seed 243 --train-size 10000 --epochs 5 --dropout 0 --dry-run
```

## Limits and observed failures

- Earlier JSON records lack post-epoch training metrics; their train-validation gaps are unavailable.
- Search returns matching records, including repeated configurations. A record count is not a count of independent seeds.
- Runs with different data, training duration, or seeds should not be ranked as though they were a controlled pair.
- In one 40-epoch, 1,000-image pair, dropout 0.5 did not improve final validation accuracy. That result does not establish how dropout behaves across other seeds or settings.
- Keyword search finds exact shared words only. It can miss a relevant observation when a query uses different words, and its score is not a measure of meaning or confidence.
- Semantic search ranked the two rise-then-fall notes highest for "held-out error spike and recover," but ranked a steadily improving run first for "oscillating optimization." Similarity is a ranking signal, not proof of relevance.
- On the five labeled questions, keyword search scored mean Recall@2 0.90 and MRR@2 0.80; semantic search scored 1.00 and 0.90. Both ranked the dropout run first for "without dropout" because that note also mentions its no-dropout match.
- These questions and labels were written after seeing some retrieval behavior. They are a small teaching check, not an independent benchmark or a claim about general search quality. A relevant label means the note's primary run satisfies the question, even when another note mentions it.
- For "without dropout," the unfiltered search ranked the dropout run first, while `--dropout 0 --train-size 1000` selected only `small_no_dropout_001`. Older run records without a saved `dropout` field are treated as unknown and excluded by a dropout filter.
- The pretrained model is `sentence-transformers/all-MiniLM-L6-v2` at revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`; the first run downloads it to `.model_cache/`.
- Evidence packets contain candidate notes and source-linked run facts, not a diagnosis. Their tables round values for display; the JSON records keep the saved precision. The packet filename must be new because the builder refuses to overwrite existing packets.
- The generated prompt in `prompts/held_out_spike_001.md` is an input artifact, not an answer. It was inspected to confirm that the packet is included once and the two run-record links are listed. Its filename must be new if regenerated.
- The first local answer contradicted its own loss facts; later raw answers omitted source links. The first structured answer falsely claimed two recorded epoch values were missing. These attempts are preserved in `answers/held_out_spike_001.md` through `_004.md`.
- The audited `answers/held_out_spike_005.md` correctly answers yes, cites both run JSON files, and avoids a causal claim. Its numeric facts were checked against those records.
- The first answer saved with the numeric gate is `answers/held_out_spike_006.md`; its metadata lists all eight loss values checked. The model's direct answer was only "Yes," although its cited facts describe validation loss. This illustrates that a numeric check does not enforce every prompt instruction.
- The numeric gate only checks whether a four-decimal loss value or two-decimal percentage accuracy occurs somewhere in the cited run's saved post-epoch metrics. It does not verify the named epoch, metric type, trend, other number formats, or the overall interpretation.
- The earlier numeric gate only checked whether a displayed value occurred somewhere in the cited run. The new structured gate rejected a value attached to the wrong epoch, metric, or run. `answers/held_out_spike_008.md` contains six verified measurements and two verified rise-then-fall patterns.
- Rise-then-fall checking currently applies to the specific held-out-error question and uses the displayed four-decimal values. Other question types still need their own answer checks; verified measurements do not establish a cause.
- `answers/steady_no_spike_002.md` is the checked No case: all five validation-loss epochs of `lr_005_gap_001` were verified, and no rise-then-fall triple was found. Removing epoch 5 makes the completeness check reject the No case.
- `python evaluate_answers.py` passed both saved cases. A copied answer record with epoch-2 validation loss changed to `9.9999` failed its evidence check. The two examples were selected after seeing the project data, so 2/2 is a regression check, not an estimate of general answer accuracy. The evaluator currently covers this one validation-loss question type.
- The evaluator calculates the expected rise-or-fall label separately from unrounded run JSON, but reuses the production measurement checker. A bug shared by that checker and the evaluator could escape this small test.
- `hypotheses/learning_rate_outcome_001.md` shows a mixed outcome: learning rate 0.1 has larger one-epoch validation-loss rises in both matched seed blocks, but final validation accuracy is 3.90 percentage points lower in one block and 0.30 points higher in the other. A cross-seed pair with three changed settings was rejected. Two seed blocks are insufficient to establish a general learning-rate effect or a mechanism.
- `hypotheses/learning_rate_candidates_004.md` is the accepted model-selected report. Ollama selected loss-rise and accuracy-drop candidates; the latter shows the opposite seed-block result as evidence against a broad accuracy-drop claim. The first free-form draft is marked historical, and a later rejected response is saved as `hypotheses/learning_rate_candidates_003.rejected.json` for inspection.
- This selection step is deliberately narrow: the candidate templates and their evidence roles are prepared for this learning-rate case. The model does not yet invent and verify open-ended mechanisms, and the selected candidates remain hypotheses rather than causal findings.
- `plans/learning_rate_seed3_001.md` proposes two new runs at learning rates 0.05 and 0.1 with model/shuffle seeds 244/243. No model was trained. Both training commands completed `--dry-run` and printed configurations matching the saved plan; no run JSON was written. Older source run JSON omitted `dropout` and `validation_start`, so the planner records that metadata gap instead of claiming those fields are verified equal to the old runs.
- The follow-up runs `lr_005_seed3` and `lr_01_seed3` have now completed. Their saved configurations match the plan exactly and differ only in learning rate. Both printed the same first five training indices. At epoch 5, validation accuracy was 75.90% versus 71.45% (high minus low = -4.45 percentage points), and the largest one-epoch validation-loss rise was none versus +0.1387.
- `hypotheses/learning_rate_outcome_002.md` compares all three matched seed blocks. Learning rate 0.1 has a larger one-epoch validation-loss rise in all three, but final validation accuracy is lower in two blocks and higher in one. The older run records omit `dropout` and `validation_start`, so the worksheet explicitly marks their cross-block equality as unverified from JSON.
- `hypotheses/learning_rate_candidates_005.md` is the accepted three-block model-selected report. Its catalog has 10 facts: three per pair plus one summary. Ollama selected loss-rise and seed-dependence candidates; the prior two-block report selected loss-rise and accuracy-drop. Python rejected a stale two-block evidence assignment missing the third block, then verified the saved three-block catalog, candidate assignments, report, and source paths. The change in model selection is descriptive, not proof that the extra block alone caused the choice, because the prompt and question also changed.
- `plans/learning_rate_seed4_001.md` proposes a fourth fresh seed block (model/shuffle 344/343) after displaying the three recorded high-minus-low final-accuracy differences: -3.90, +0.30, and -4.45 percentage points. The plan states the current counts, 2/3 lower final accuracy and 3/3 larger maximum loss rise at learning rate 0.1, and what a fourth accuracy result would add. Both proposed commands passed `--dry-run`; their configurations match the plan and differ only in learning rate. No fourth-block training record exists yet. A fourth block would add evidence about variation across seed blocks, not isolate model seed from shuffle seed or establish a general effect.
- The learning-rate follow-up branch is paused at the user's request. Do not train the fourth seed block or add more matched-seed, hypothesis-validation, or experiment-planning infrastructure for now.
- The first tool-using agent question about `lr_01_seed3` and `lr_005_seed3` initially chose two single-run lookups and made an unsupported causal attribution. Clearer tool descriptions led it to choose `compare_experiments`, which returned the correct -4.45 percentage-point accuracy difference and +0.1303 loss difference. The small model still wrote "primarily due to" in its final prose despite instructions not to claim a cause. Tool selection and tool facts work; the final model wording is not independently verified in this milestone.
- A one-run agent question fetched the correct 71.45% final validation accuracy, but the model invented a baseline difference that had not been requested. This motivated deterministic rendering from tool output at the end of the loop, without adding a separate evaluation suite. The final two-run demo used `compare_experiments` once and rendered -4.45 percentage points and +0.1303 validation loss with source links; the one-run demo used `get_experiment` once and rendered 71.45% and 0.8109. Tool choice and arguments can still fail on other questions.
- For "Have we seen unstable validation behavior before?", the agent called `search_notes` with the shorter query "unstable validation behavior", then inspected `lr_01_seed2` and `baseline_gap_001` with two `get_experiment` calls. Semantic scores were 0.468 and 0.415 for that rewritten query. The saved curves confirm a validation-loss rise then fall in both runs; those scores only rank the notes and are not probabilities or diagnoses.
- After adding search, the 1.7B model incorrectly chose it for a question naming two exact runs, then inspected unrelated retrieved runs. Repeating the instruction and explicitly listing detected IDs did not correct the choice. The agent now offers only direct comparison for questions containing two saved run IDs; questions without run IDs still expose all three tools. The named two-run question again called `compare_experiments` once. This is a small tool-availability rule, not a claim that the model generally selects tools well.
- The restricted execution shell could not see several packages installed in the user's Python site directory, so its first semantic-ranking attempt failed on `packaging`. Exact run selection needs no encoder and completed with regular Python. `packaging` was installed into the project virtual environment; a check outside the restricted shell imported PyTorch, NumPy, and sentence-transformers successfully. The restricted shell is not a reliable test of that user-site-backed semantic environment.
- The first local generation path was a narrow factual RAG step. The later tool-using agent adds a small loop over saved runs and semantic notes. Neither path establishes causal mechanisms, and the agent's model prose is still not independently verified; Python renders the displayed facts from tool results. Ollama installation and D: drive verification are recorded in `OLLAMA_SETUP.md`.
