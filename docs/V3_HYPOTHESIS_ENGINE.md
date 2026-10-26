# V3 evidence-backed hypothesis engine

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
