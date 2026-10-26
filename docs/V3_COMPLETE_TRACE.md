# Verified V3 investigation trace

Investigation `INV-9B53F0C759`. The data are real saved runs; the final execution is a **dry run**, not new measured training. The actor `development_dry_run` records authorization supplied by the V3 development request.

## Full report

# Investigation report: INV-9B53F0C759

## 1. Research question

Investigate why lr_01_seed3 had worse final validation accuracy than lr_005_seed3. Examine the curves, retrieve relevant ML knowledge, compare possible explanations, and propose a controlled follow-up.

## 2. Relevant experiments

- `EXPERIMENT_JSON` runs/lr_005_seed3.json
- `EXPERIMENT_JSON` runs/lr_01_seed3.json
- `EXPERIMENT_JSON` runs/lr_005_gap_001.json
- `EXPERIMENT_JSON` runs/baseline_001.json
- `EXPERIMENT_JSON` runs/lr_005_seed2.json
- `EXPERIMENT_JSON` runs/lr_01_seed2.json

## 3. Measured observations

- lr_005_seed3: final validation accuracy **75.90%**, loss **0.6806**, epoch 5. [EXPERIMENT_JSON](../runs/lr_005_seed3.json)
- lr_01_seed3: final validation accuracy **71.45%**, loss **0.8109**, epoch 5. [EXPERIMENT_JSON](../runs/lr_01_seed3.json)
- lr_005_gap_001: final validation accuracy **75.15%**, loss **0.6876**, epoch 5. [EXPERIMENT_JSON](../runs/lr_005_gap_001.json)
- baseline_001: final validation accuracy **71.25%**, loss **0.8208**, epoch 5. [EXPERIMENT_JSON](../runs/baseline_001.json)
- lr_005_seed2: final validation accuracy **76.05%**, loss **0.6848**, epoch 5. [EXPERIMENT_JSON](../runs/lr_005_seed2.json)
- lr_01_seed2: final validation accuracy **76.35%**, loss **0.6793**, epoch 5. [EXPERIMENT_JSON](../runs/lr_01_seed2.json)

## 4. Controlled comparisons

### lr_01_seed3 minus lr_005_seed3

Controlled learning-rate pair: `True`. Confounded: `False`. Missing controls: `[]`.

- Accuracy difference: **-4.45 percentage points**; validation-loss difference: **+0.1303**.

```json
{
  "baseline_run_id": "lr_005_seed3",
  "target_run_id": "lr_01_seed3",
  "sources": [
    "runs/lr_005_seed3.json",
    "runs/lr_01_seed3.json"
  ],
  "source_type": "DERIVED_ANALYSIS",
  "changed_settings": {
    "learning_rate": {
      "baseline": 0.05,
      "target": 0.1
    }
  },
  "missing_controls": [],
  "curves": {
    "lr_005_seed3": {
      "final_accuracy_percent": 75.9,
      "final_loss": 0.6806,
      "final_epoch": 5,
      "best_accuracy_percent": 75.9,
      "best_epoch": 5,
      "minimum_loss": 0.6806,
      "minimum_loss_epoch": 5,
      "largest_loss_rise": 0.0,
      "recoveries": [],
      "final_loss_gap_val_minus_train": -0.01233,
      "candidate_generalization_intervals": []
    },
    "lr_01_seed3": {
      "final_accuracy_percent": 71.45,
      "final_loss": 0.810865,
      "final_epoch": 5,
      "best_accuracy_percent": 73.2,
      "best_epoch": 4,
      "minimum_loss": 0.682841,
      "minimum_loss_epoch": 4,
      "largest_loss_rise": 0.138654,
      "recoveries": [
        {
          "epochs": [
            1,
            2,
            3
          ],
          "losses": [
            0.8865,
            1.0252,
            0.8685
          ]
        }
      ],
      "final_loss_gap_val_minus_train": -0.002276,
      "candidate_generalization_intervals": []
    }
  },
  "matching_scope": "All recorded configuration fields; hidden_units and dropout describe architecture settings, not complete architecture provenance.",
  "missing_provenance": [
    "Exact model-class/trainer revision was not recorded in historical JSON.",
    "Hardware and software versions were not recorded in historical JSON."
  ],
  "controlled_learning_rate_pair": true,
  "confounded": false,
  "accuracy_delta_pp": -4.45,
  "loss_delta": 0.130265,
  "rise_delta": 0.138654
}
```

## 5. Competing hypotheses

### H1 — Consistent with current evidence

`HYPOTHESIS` A higher learning rate may contribute to larger validation-loss rises through unstable optimization.

- Supporting experiment evidence: PAIR:0, PAIR:1, PAIR:2, PAIR:3
- Opposing experiment evidence: None found; absence is not proof
- General ML knowledge: ML:validation, ML:overfitting
- Assumptions: Recorded configurations and epoch metrics accurately describe the runs.
- Missing evidence: Independent replication and optimizer-step/gradient measurements are absent. Validation-loss rises cannot directly demonstrate overshooting; gradients and optimizer trajectories were not recorded.
- Proposed test: Compare maximum positive consecutive-epoch validation-loss rises under matched new seeds and different learning rates.
- Selected by: LLM; wording: PYTHON evidence-conditioned candidate

### H2 — Consistent with current evidence

`HYPOTHESIS` Seed-dependent training variability may contribute to differences in final validation accuracy.

- Supporting experiment evidence: PAIR:0, PAIR:1, PAIR:2, PAIR:3
- Opposing experiment evidence: None found; absence is not proof
- General ML knowledge: ML:validation, ML:overfitting
- Assumptions: Recorded configurations and epoch metrics accurately describe the runs.
- Missing evidence: Independent replication and optimizer-step/gradient measurements are absent. A small number of observed seed blocks cannot establish a distribution or separate all sources of randomness.
- Proposed test: Repeat a controlled learning-rate comparison under a new shared model/shuffle seed block; predefine accuracy and loss-rise comparisons.
- Selected by: LLM; wording: PYTHON evidence-conditioned candidate

### H3 — Consistent with current evidence

`HYPOTHESIS` The short recorded training horizon may leave the final-epoch ranking sensitive to transient behavior.

- Supporting experiment evidence: RUN:lr_005_seed3, RUN:lr_01_seed3, RUN:lr_005_gap_001, RUN:baseline_001, RUN:lr_005_seed2, RUN:lr_01_seed2
- Opposing experiment evidence: None found; absence is not proof
- General ML knowledge: ML:validation, ML:overfitting
- Assumptions: Recorded configurations and epoch metrics accurately describe the runs.
- Missing evidence: Independent replication and optimizer-step/gradient measurements are absent. Longer independently approved training and predeclared stopping criteria are unavailable.
- Proposed test: Replicate the existing horizon first; consider a separately approved longer-horizon study if ambiguity remains.
- Selected by: LLM; wording: PYTHON evidence-conditioned candidate

### H4 — Consistent with current evidence

`HYPOTHESIS` A generalization gap may contribute during intervals where training loss improves and validation loss rises.

- Supporting experiment evidence: PAIR:2
- Opposing experiment evidence: None found; absence is not proof
- General ML knowledge: ML:validation, ML:overfitting
- Assumptions: Recorded configurations and epoch metrics accurately describe the runs.
- Missing evidence: Independent replication and optimizer-step/gradient measurements are absent. This interval rule is a diagnostic candidate, not proof of overfitting.
- Proposed test: Inspect matched train/validation curves and test one regularization change in a separate controlled proposal.
- Selected by: LLM; wording: PYTHON evidence-conditioned candidate

## 6. Supporting evidence

Evidence identifiers resolve in the source registry below. Hypothesis status is descriptive, not a statistical proof.

## 7. Contradicting evidence

- baseline_001 minus lr_005_gap_001: accuracy -3.9 pp; maximum validation-loss-rise difference 0.548924. Missing controls: ['validation_start', 'dropout']. `DERIVED_ANALYSIS`, sources: runs/lr_005_gap_001.json, runs/baseline_001.json
- lr_01_seed2 minus lr_005_seed2: accuracy 0.3 pp; maximum validation-loss-rise difference 0.099287. Missing controls: ['validation_start', 'dropout']. `DERIVED_ANALYSIS`, sources: runs/lr_005_seed2.json, runs/lr_01_seed2.json
- lr_01_seed3 minus lr_005_seed3: accuracy -4.45 pp; maximum validation-loss-rise difference 0.138654. Missing controls: []. `DERIVED_ANALYSIS`, sources: runs/lr_005_seed3.json, runs/lr_01_seed3.json

## 8. Relevant ML knowledge

- `ML_KNOWLEDGE` [Overfitting: Interpreting loss curves](https://developers.google.com/machine-learning/crash-course/overfitting/interpreting-loss-curves), local `knowledge/validation.md`: Loss curves can oscillate or rise for several reasons. Reducing a learning rate can be useful when debugging an oscillating training-loss curve. When training loss improves but validation loss rises, overfitting is one possible interpretation. These are general diagnostic ideas, not proof of a cause for any particular saved run.
- `ML_KNOWLEDGE` [Validation curves: plotting scores to evaluate models](https://scikit-learn.org/stable/modules/learning_curve.html), local `knowledge/overfitting.md`: Training and validation scores together can help identify possible overfitting. A high training score paired with a lower validation score is a warning that performance may not generalize as well to unseen data. A pattern in one short saved curve is only a candidate signal; other explanations and repeated checks remain possible.

General documentation supports possible mechanisms; it cannot prove the cause of a saved run.

## 9. Missing evidence

- Independent replication and optimizer-step/gradient measurements are absent.
- Validation-loss rises cannot directly demonstrate overshooting; gradients and optimizer trajectories were not recorded.
- A small number of observed seed blocks cannot establish a distribution or separate all sources of randomness.
- Longer independently approved training and predeclared stopping criteria are unavailable.
- This interval rule is a diagnostic candidate, not proof of overfitting.

## 10. Proposed experiments

```json
{
  "proposal_id": "INV-9B53F0C759-P1",
  "investigation_id": "INV-9B53F0C759",
  "hypothesis_ids": [
    "H1",
    "H2"
  ],
  "changed_variable": "learning_rate",
  "controlled_variables": [
    "dataset",
    "source_partition",
    "preprocessing",
    "train_size",
    "val_size",
    "validation_start",
    "split_seed",
    "shuffle_seed",
    "model_seed",
    "batch_size",
    "hidden_units",
    "optimizer",
    "epochs",
    "dropout"
  ],
  "runs": [
    {
      "run_id": "v3_inv_9b53f0c759_control",
      "dataset": "FashionMNIST",
      "source_partition": "train",
      "preprocessing": "ToTensor",
      "train_size": 10000,
      "val_size": 2000,
      "validation_start": 10000,
      "split_seed": 42,
      "shuffle_seed": 443,
      "model_seed": 444,
      "batch_size": 128,
      "hidden_units": 128,
      "dropout": 0.0,
      "optimizer": "SGD",
      "learning_rate": 0.05,
      "epochs": 5
    },
    {
      "run_id": "v3_inv_9b53f0c759_target",
      "dataset": "FashionMNIST",
      "source_partition": "train",
      "preprocessing": "ToTensor",
      "train_size": 10000,
      "val_size": 2000,
      "validation_start": 10000,
      "split_seed": 42,
      "shuffle_seed": 443,
      "model_seed": 444,
      "batch_size": 128,
      "hidden_units": 128,
      "dropout": 0.0,
      "optimizer": "SGD",
      "learning_rate": 0.1,
      "epochs": 5
    }
  ],
  "rationale": "A new shared seed block tests whether the observed loss-rise ordering replicates while all other recorded controls are matched.",
  "seed_rationale": "Seeds exceed recorded runs and reserved legacy plans. The same fresh seeds are used by both arms.",
  "primary_metric": "largest_positive_consecutive_epoch_validation_loss_rise",
  "secondary_metrics": [
    "final_validation_accuracy_percent",
    "final_validation_loss"
  ],
  "supported_if": "The higher-rate arm has a strictly larger maximum validation-loss rise.",
  "contradicted_if": "The higher-rate arm has a smaller maximum rise; equality is inconclusive.",
  "limitations": [
    "One new seed block does not establish general causation.",
    "The same fixed validation split is reused; the official test set is excluded.",
    "Validation metrics do not directly measure overshooting.",
    "Other hypotheses may require separately approved designs."
  ],
  "limits": {
    "max_total_seconds": 600,
    "max_runs": 2,
    "cpu_threads": 2
  },
  "training_code_sha256": "2f368c1d74005e8c32520a496614a123c297531789371d97748ce0a571750e66"
}
```

Exact proposal SHA-256: `f7b95c2b8908ea4fc8a4005b969a52a9c7c9516f99c1afb3ec21ee03c6aa7b51`.

## 11. Approval/execution status

Investigation: **dry_run_completed**.
Proposal: **dry_run_completed**, mode: `dry_run`.

```json
[
  {
    "id": 3,
    "proposal_id": "INV-9B53F0C759-P1",
    "hash": "f7b95c2b8908ea4fc8a4005b969a52a9c7c9516f99c1afb3ec21ee03c6aa7b51",
    "decision": "approved",
    "mode": "dry_run",
    "actor": "development_dry_run",
    "reason": "V3 development demonstration; no live training permission",
    "timestamp": "2026-10-26T06:20:09.095165+00:00"
  }
]
```

## 12. Follow-up results

```json
{
  "status": "dry_run_completed",
  "mode": "dry_run",
  "started": "2026-10-26T06:20:09.223413+00:00",
  "run_ids": [],
  "logs": [],
  "ingested": [],
  "planned_configs": [
    {
      "run_id": "v3_inv_9b53f0c759_control",
      "dataset": "FashionMNIST",
      "source_partition": "train",
      "preprocessing": "ToTensor",
      "train_size": 10000,
      "val_size": 2000,
      "validation_start": 10000,
      "split_seed": 42,
      "shuffle_seed": 443,
      "model_seed": 444,
      "batch_size": 128,
      "hidden_units": 128,
      "dropout": 0.0,
      "optimizer": "SGD",
      "learning_rate": 0.05,
      "epochs": 5
    },
    {
      "run_id": "v3_inv_9b53f0c759_target",
      "dataset": "FashionMNIST",
      "source_partition": "train",
      "preprocessing": "ToTensor",
      "train_size": 10000,
      "val_size": 2000,
      "validation_start": 10000,
      "split_seed": 42,
      "shuffle_seed": 443,
      "model_seed": 444,
      "batch_size": 128,
      "hidden_units": 128,
      "dropout": 0.0,
      "optimizer": "SGD",
      "learning_rate": 0.1,
      "epochs": 5
    }
  ],
  "message": "Approval and resource checks passed. No trainer was launched; no metrics or run files were created.",
  "finished": "2026-10-26T06:20:09.239851+00:00"
}
```
No new measured follow-up outcomes. A dry run never creates synthetic measurements.

## 13. Interpretation

The saved data can support or oppose candidate explanations; it does not establish a unique cause.

## 14. Limitations

- One fixed validation split and a small number of recorded seed blocks limit generalization.
- Missing historical metadata remains unknown; no default is silently inferred.
- The model selects bounded plan options and hypotheses; Python calculates, validates, and renders facts.
- The current executor supports only the existing bounded Fashion-MNIST MLP learning-rate comparison.
- Live training has not been run during V3 development.

## 15. Sources

- `RUN:lr_005_seed3` — `EXPERIMENT_JSON` — runs/lr_005_seed3.json
- `RUN:lr_01_seed3` — `EXPERIMENT_JSON` — runs/lr_01_seed3.json
- `RUN:lr_005_gap_001` — `EXPERIMENT_JSON` — runs/lr_005_gap_001.json
- `RUN:baseline_001` — `EXPERIMENT_JSON` — runs/baseline_001.json
- `RUN:lr_005_seed2` — `EXPERIMENT_JSON` — runs/lr_005_seed2.json
- `RUN:lr_01_seed2` — `EXPERIMENT_JSON` — runs/lr_01_seed2.json
- `PAIR:0` — `DERIVED_ANALYSIS` — runs/lr_005_seed3.json, runs/lr_01_seed3.json
- `PAIR:1` — `DERIVED_ANALYSIS` — runs/lr_005_gap_001.json, runs/baseline_001.json
- `PAIR:2` — `DERIVED_ANALYSIS` — runs/lr_005_seed2.json, runs/lr_01_seed2.json
- `PAIR:3` — `DERIVED_ANALYSIS` — runs/lr_005_seed3.json, runs/lr_01_seed3.json
- `ML:validation` — `ML_KNOWLEDGE` — knowledge/validation.md
- `ML:overfitting` — `ML_KNOWLEDGE` — knowledge/overfitting.md
- `NOTE:0` — `DERIVED_ANALYSIS` — runs/lr_005_seed3.json
- `NOTE:1` — `DERIVED_ANALYSIS` — runs/lr_01_seed3.json
- `NOTE:2` — `EXPERIMENT_NOTE` — notes/lr_005_gap_001.md
- `NOTE:5` — `DERIVED_ANALYSIS` — runs/lr_001.json

## Structured plan

```json
[
  {
    "id": "collect",
    "description": "Read exact experiment evidence",
    "tool": "get_experiment",
    "depends_on": [],
    "status": "completed",
    "proposed_by": "PYTHON"
  },
  {
    "id": "notes",
    "description": "Find earlier experiment observations",
    "tool": "search_notes",
    "depends_on": [],
    "status": "completed",
    "proposed_by": "LLM"
  },
  {
    "id": "analyze",
    "description": "Compute curves, controls and seed comparisons",
    "tool": "analyze_experiments",
    "depends_on": [
      "collect"
    ],
    "status": "completed",
    "proposed_by": "PYTHON"
  },
  {
    "id": "knowledge",
    "description": "Retrieve possible general mechanisms",
    "tool": "search_ml_knowledge",
    "depends_on": [
      "analyze"
    ],
    "status": "completed",
    "proposed_by": "LLM"
  },
  {
    "id": "hypotheses",
    "description": "Select competing evidence-backed hypotheses",
    "tool": "select_hypotheses",
    "depends_on": [
      "analyze"
    ],
    "status": "completed",
    "proposed_by": "PYTHON"
  },
  {
    "id": "validate",
    "description": "Validate citations and hypothesis evidence",
    "tool": "validate_evidence",
    "depends_on": [
      "hypotheses"
    ],
    "status": "completed",
    "proposed_by": "PYTHON"
  },
  {
    "id": "design",
    "description": "Design a new controlled experiment",
    "tool": "design_followup",
    "depends_on": [
      "validate"
    ],
    "status": "completed",
    "proposed_by": "PYTHON"
  },
  {
    "id": "approval",
    "description": "Wait for an exact human decision",
    "tool": "human_approval",
    "depends_on": [
      "design"
    ],
    "status": "completed",
    "proposed_by": "APP POLICY"
  },
  {
    "id": "execute",
    "description": "Execute only an approved configuration",
    "tool": "restricted_executor",
    "depends_on": [
      "approval"
    ],
    "status": "completed",
    "proposed_by": "APP POLICY"
  },
  {
    "id": "outcome",
    "description": "Analyze new measured outcomes",
    "tool": "analyze_outcome",
    "depends_on": [
      "execute"
    ],
    "status": "skipped",
    "proposed_by": "PYTHON",
    "detail": "No complete new measured pair; dry runs contain no measurements"
  },
  {
    "id": "report",
    "description": "Save sourced investigation report",
    "tool": "render_report",
    "depends_on": [
      "validate"
    ],
    "status": "completed",
    "proposed_by": "PYTHON"
  }
]
```

## Complete event data

### Event 1: APP POLICY — PYTHON

```json
{
  "classification": "investigation"
}
```
### Event 2: TOOL MENU — PYTHON

```json
{
  "type": "function",
  "function": {
    "name": "create_investigation_plan",
    "description": "Objective: Investigate why lr_01_seed3 had worse final validation accuracy than lr_005_seed3. Examine the curves, retrieve relevant ML knowledge, compare possible explanations, and propose a controlled follow-up.. Known mentioned runs: ['lr_01_seed3', 'lr_005_seed3']. Choose useful optional research tools. Choose compare_seed_pairs to check replication/counterevidence; search_notes to find previous observations; retrieve_knowledge for mechanisms. Return a topic from the menu.",
    "parameters": {
      "type": "object",
      "properties": {
        "steps": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": [
              "search_notes",
              "compare_seed_pairs",
              "retrieve_knowledge"
            ]
          },
          "maxItems": 3
        },
        "knowledge_topic": {
          "type": "string",
          "enum": [
            "high learning rate optimization instability",
            "dropout overfitting validation loss",
            "training validation loss curves"
          ]
        }
      },
      "required": [
        "steps",
        "knowledge_topic"
      ],
      "additionalProperties": false
    }
  }
}
```
### Event 3: AGENT REQUEST — LLM

```json
{
  "attempt": 1,
  "response": {
    "structured_decision": {
      "steps": [
        "compare_seed_pairs",
        "search_notes",
        "retrieve_knowledge"
      ],
      "knowledge_topic": "training validation loss curves"
    },
    "format": "Ollama JSON schema"
  }
}
```
### Event 4: PLANNER DECISION — LLM

```json
{
  "choice": {
    "steps": [
      "compare_seed_pairs",
      "search_notes",
      "retrieve_knowledge"
    ],
    "knowledge_topic": "training validation loss curves"
  },
  "plan": [
    {
      "id": "collect",
      "description": "Read exact experiment evidence",
      "tool": "get_experiment",
      "depends_on": [],
      "status": "completed",
      "proposed_by": "PYTHON"
    },
    {
      "id": "notes",
      "description": "Find earlier experiment observations",
      "tool": "search_notes",
      "depends_on": [],
      "status": "completed",
      "proposed_by": "LLM"
    },
    {
      "id": "analyze",
      "description": "Compute curves, controls and seed comparisons",
      "tool": "analyze_experiments",
      "depends_on": [
        "collect"
      ],
      "status": "completed",
      "proposed_by": "PYTHON"
    },
    {
      "id": "knowledge",
      "description": "Retrieve possible general mechanisms",
      "tool": "search_ml_knowledge",
      "depends_on": [
        "analyze"
      ],
      "status": "completed",
      "proposed_by": "LLM"
    },
    {
      "id": "hypotheses",
      "description": "Select competing evidence-backed hypotheses",
      "tool": "select_hypotheses",
      "depends_on": [
        "analyze"
      ],
      "status": "completed",
      "proposed_by": "PYTHON"
    },
    {
      "id": "validate",
      "description": "Validate citations and hypothesis evidence",
      "tool": "validate_evidence",
      "depends_on": [
        "hypotheses"
      ],
      "status": "completed",
      "proposed_by": "PYTHON"
    },
    {
      "id": "design",
      "description": "Design a new controlled experiment",
      "tool": "design_followup",
      "depends_on": [
        "validate"
      ],
      "status": "completed",
      "proposed_by": "PYTHON"
    },
    {
      "id": "approval",
      "description": "Wait for an exact human decision",
      "tool": "human_approval",
      "depends_on": [
        "design"
      ],
      "status": "pending",
      "proposed_by": "APP POLICY"
    },
    {
      "id": "execute",
      "description": "Execute only an approved configuration",
      "tool": "restricted_executor",
      "depends_on": [
        "approval"
      ],
      "status": "pending",
      "proposed_by": "APP POLICY"
    },
    {
      "id": "outcome",
      "description": "Analyze new measured outcomes",
      "tool": "analyze_outcome",
      "depends_on": [
        "execute"
      ],
      "status": "pending",
      "proposed_by": "PYTHON"
    },
    {
      "id": "report",
      "description": "Save sourced investigation report",
      "tool": "render_report",
      "depends_on": [
        "validate"
      ],
      "status": "pending",
      "proposed_by": "PYTHON"
    }
  ],
  "distinction": "Model selects optional tools; Python prescribes scientific checks and the approval boundary."
}
```
### Event 5: TOOL EXECUTION — PYTHON

```json
{
  "tool": "search_notes",
  "result": {
    "query": "Investigate why lr_01_seed3 had worse final validation accuracy than lr_005_seed3. Examine the curves, retrieve relevant ML knowledge, compare possible explanations, and propose a controlled follow-up.",
    "mode": "keyword + cached MiniLM RRF",
    "source_policy": "human_first",
    "reranker": "disabled",
    "matches": [
      {
        "run_id": "lr_005_seed3",
        "source_type": "DERIVED_ANALYSIS",
        "source": "runs/lr_005_seed3.json",
        "run_source": "runs/lr_005_seed3.json",
        "observation": "DERIVED_ANALYSIS machine-generated summary from runs/lr_005_seed3.json. Run lr_005_seed3. Learning rate 0.05, dropout 0.0, train size 10000, model seed 244, shuffle seed 243. Final validation accuracy 75.9 percent; final loss 0.6806; largest validation loss rise 0.0. no recorded rise followed by recovery; validation loss decreased or stayed flat every epoch.",
        "keyword_rank": 1,
        "semantic_rank": 1,
        "cosine_similarity": 0.5925,
        "exact_run_id_match": true,
        "rrf_score": 0.032787
      },
      {
        "run_id": "lr_01_seed3",
        "source_type": "DERIVED_ANALYSIS",
        "source": "runs/lr_01_seed3.json",
        "run_source": "runs/lr_01_seed3.json",
        "observation": "DERIVED_ANALYSIS machine-generated summary from runs/lr_01_seed3.json. Run lr_01_seed3. Learning rate 0.1, dropout 0.0, train size 10000, model seed 244, shuffle seed 243. Final validation accuracy 71.45 percent; final loss 0.810865; largest validation loss rise 0.138654. validation loss spike and recovery.",
        "keyword_rank": 2,
        "semantic_rank": 5,
        "cosine_similarity": 0.575,
        "exact_run_id_match": true,
        "rrf_score": 0.031514
      },
      {
        "run_id": "lr_005_gap_001",
        "source_type": "EXPERIMENT_NOTE",
        "source": "notes/lr_005_gap_001.md",
        "run_source": "runs/lr_005_gap_001.json",
        "observation": "With learning rate 0.05, validation loss decreased in each of five epochs, from 1.0546 to 0.6876. Final training accuracy was 74.93% and validation accuracy was 75.15%.",
        "keyword_rank": 1,
        "semantic_rank": 2,
        "cosine_similarity": 0.509,
        "exact_run_id_match": false,
        "rrf_score": 0.032522
      }
    ],
    "supplementary_derived_matches": [
      {
        "run_id": "lr_005_seed3",
        "source_type": "DERIVED_ANALYSIS",
        "source": "runs/lr_005_seed3.json",
        "run_source": "runs/lr_005_seed3.json",
        "observation": "DERIVED_ANALYSIS machine-generated summary from runs/lr_005_seed3.json. Run lr_005_seed3. Learning rate 0.05, dropout 0.0, train size 10000, model seed 244, shuffle seed 243. Final validation accuracy 75.9 percent; final loss 0.6806; largest validation loss rise 0.0. no recorded rise followed by recovery; validation loss decreased or stayed flat every epoch.",
        "keyword_rank": 1,
        "semantic_rank": 1,
        "cosine_similarity": 0.5925,
        "exact_run_id_match": true,
        "rrf_score": 0.032787
      },
      {
        "run_id": "lr_01_seed3",
        "source_type": "DERIVED_ANALYSIS",
        "source": "runs/lr_01_seed3.json",
        "run_source": "runs/lr_01_seed3.json",
        "observation": "DERIVED_ANALYSIS machine-generated summary from runs/lr_01_seed3.json. Run lr_01_seed3. Learning rate 0.1, dropout 0.0, train size 10000, model seed 244, shuffle seed 243. Final validation accuracy 71.45 percent; final loss 0.810865; largest validation loss rise 0.138654. validation loss spike and recovery.",
        "keyword_rank": 2,
        "semantic_rank": 5,
        "cosine_similarity": 0.575,
        "exact_run_id_match": true,
        "rrf_score": 0.031514
      },
      {
        "run_id": "lr_001",
        "source_type": "DERIVED_ANALYSIS",
        "source": "runs/lr_001.json",
        "run_source": "runs/lr_001.json",
        "observation": "DERIVED_ANALYSIS machine-generated summary from runs/lr_001.json. Run lr_001. Learning rate 0.01, dropout unknown, train size 10000, model seed 44, shuffle seed 43. Final validation accuracy 66.4 percent; final loss 1.030395; largest validation loss rise 0.0. no recorded rise followed by recovery; validation loss decreased or stayed flat every epoch.",
        "keyword_rank": 3,
        "semantic_rank": 3,
        "cosine_similarity": 0.5884,
        "exact_run_id_match": false,
        "rrf_score": 0.031746
      }
    ],
    "stages": {
      "keyword": [
        "lr_005_seed3",
        "lr_01_seed3",
        "lr_001",
        "lr_005_seed2",
        "lr_gap_001",
        "baseline_001",
        "lr_005_gap_001",
        "lr_01_seed2",
        "small_dropout_05_001",
        "small_no_dropout_001",
        "baseline_gap_001"
      ],
      "semantic": [
        "lr_005_seed3",
        "lr_gap_001",
        "lr_001",
        "lr_005_seed2",
        "lr_01_seed3",
        "lr_01_seed2",
        "lr_005_gap_001",
        "baseline_001",
        "small_no_dropout_001",
        "small_dropout_05_001",
        "baseline_gap_001"
      ],
      "hybrid": [
        "lr_005_seed3",
        "lr_01_seed3",
        "lr_005_gap_001",
        "lr_01_seed2",
        "small_dropout_05_001",
        "small_no_dropout_001",
        "baseline_gap_001",
        "lr_001",
        "lr_gap_001",
        "lr_005_seed2",
        "baseline_001"
      ]
    },
    "corpus": {
      "human_notes": 5,
      "derived_summaries": 6
    }
  }
}
```
### Event 6: EXPERIMENT EVIDENCE — PYTHON

```json
{
  "tool": "get_experiment",
  "run_id": "lr_005_seed3",
  "record": {
    "config": {
      "run_id": "lr_005_seed3",
      "dataset": "FashionMNIST",
      "source_partition": "train",
      "preprocessing": "ToTensor",
      "train_size": 10000,
      "val_size": 2000,
      "validation_start": 10000,
      "split_seed": 42,
      "shuffle_seed": 243,
      "model_seed": 244,
      "batch_size": 128,
      "hidden_units": 128,
      "dropout": 0.0,
      "optimizer": "SGD",
      "learning_rate": 0.05,
      "epochs": 5
    },
    "metrics": [
      {
        "epoch": 1,
        "train_loss_during_epoch": 1.5768690871238709,
        "train_loss_after_epoch": 1.0953938115119934,
        "train_accuracy_after_epoch": 0.612,
        "val_loss": 1.077092869758606,
        "val_accuracy": 0.626
      },
      {
        "epoch": 2,
        "train_loss_during_epoch": 0.9157467240333557,
        "train_loss_after_epoch": 0.8976822423934937,
        "train_accuracy_after_epoch": 0.6745,
        "val_loss": 0.8978471145629883,
        "val_accuracy": 0.6775
      },
      {
        "epoch": 3,
        "train_loss_during_epoch": 0.7648744816780091,
        "train_loss_after_epoch": 0.8522588306427002,
        "train_accuracy_after_epoch": 0.6881,
        "val_loss": 0.8446058855056763,
        "val_accuracy": 0.687
      },
      {
        "epoch": 4,
        "train_loss_during_epoch": 0.6941012891769409,
        "train_loss_after_epoch": 0.6855860265254974,
        "train_accuracy_after_epoch": 0.7522,
        "val_loss": 0.6975534653663635,
        "val_accuracy": 0.7305
      },
      {
        "epoch": 5,
        "train_loss_during_epoch": 0.6385964094161988,
        "train_loss_after_epoch": 0.6929299505233765,
        "train_accuracy_after_epoch": 0.7534,
        "val_loss": 0.680600378036499,
        "val_accuracy": 0.759
      }
    ]
  }
}
```
### Event 7: EXPERIMENT EVIDENCE — PYTHON

```json
{
  "tool": "get_experiment",
  "run_id": "lr_01_seed3",
  "record": {
    "config": {
      "run_id": "lr_01_seed3",
      "dataset": "FashionMNIST",
      "source_partition": "train",
      "preprocessing": "ToTensor",
      "train_size": 10000,
      "val_size": 2000,
      "validation_start": 10000,
      "split_seed": 42,
      "shuffle_seed": 243,
      "model_seed": 244,
      "batch_size": 128,
      "hidden_units": 128,
      "dropout": 0.0,
      "optimizer": "SGD",
      "learning_rate": 0.1,
      "epochs": 5
    },
    "metrics": [
      {
        "epoch": 1,
        "train_loss_during_epoch": 1.2794325910568238,
        "train_loss_after_epoch": 0.9111308251380921,
        "train_accuracy_after_epoch": 0.6495,
        "val_loss": 0.8865399732589722,
        "val_accuracy": 0.6645
      },
      {
        "epoch": 2,
        "train_loss_during_epoch": 0.7691367017745971,
        "train_loss_after_epoch": 1.0264610683441162,
        "train_accuracy_after_epoch": 0.6864,
        "val_loss": 1.0251937484741211,
        "val_accuracy": 0.6875
      },
      {
        "epoch": 3,
        "train_loss_during_epoch": 0.6635693133354187,
        "train_loss_after_epoch": 0.8690615137100219,
        "train_accuracy_after_epoch": 0.6762,
        "val_loss": 0.8684509625434875,
        "val_accuracy": 0.674
      },
      {
        "epoch": 4,
        "train_loss_during_epoch": 0.6114804370880127,
        "train_loss_after_epoch": 0.6598312929391861,
        "train_accuracy_after_epoch": 0.7469,
        "val_loss": 0.6828413162231445,
        "val_accuracy": 0.732
      },
      {
        "epoch": 5,
        "train_loss_during_epoch": 0.5592419065475464,
        "train_loss_after_epoch": 0.8131413830757142,
        "train_accuracy_after_epoch": 0.7162,
        "val_loss": 0.810864956855774,
        "val_accuracy": 0.7145
      }
    ]
  }
}
```
### Event 8: TOOL EXECUTION — PYTHON

```json
{
  "tool": "analyze_experiments",
  "result": {
    "comparisons": [
      {
        "baseline_run_id": "lr_005_seed3",
        "target_run_id": "lr_01_seed3",
        "sources": [
          "runs/lr_005_seed3.json",
          "runs/lr_01_seed3.json"
        ],
        "source_type": "DERIVED_ANALYSIS",
        "changed_settings": {
          "learning_rate": {
            "baseline": 0.05,
            "target": 0.1
          }
        },
        "missing_controls": [],
        "curves": {
          "lr_005_seed3": {
            "final_accuracy_percent": 75.9,
            "final_loss": 0.6806,
            "final_epoch": 5,
            "best_accuracy_percent": 75.9,
            "best_epoch": 5,
            "minimum_loss": 0.6806,
            "minimum_loss_epoch": 5,
            "largest_loss_rise": 0.0,
            "recoveries": [],
            "final_loss_gap_val_minus_train": -0.01233,
            "candidate_generalization_intervals": []
          },
          "lr_01_seed3": {
            "final_accuracy_percent": 71.45,
            "final_loss": 0.810865,
            "final_epoch": 5,
            "best_accuracy_percent": 73.2,
            "best_epoch": 4,
            "minimum_loss": 0.682841,
            "minimum_loss_epoch": 4,
            "largest_loss_rise": 0.138654,
            "recoveries": [
              {
                "epochs": [
                  1,
                  2,
                  3
                ],
                "losses": [
                  0.8865,
                  1.0252,
                  0.8685
                ]
              }
            ],
            "final_loss_gap_val_minus_train": -0.002276,
            "candidate_generalization_intervals": []
          }
        },
        "matching_scope": "All recorded configuration fields; hidden_units and dropout describe architecture settings, not complete architecture provenance.",
        "missing_provenance": [
          "Exact model-class/trainer revision was not recorded in historical JSON.",
          "Hardware and software versions were not recorded in historical JSON."
        ],
        "controlled_learning_rate_pair": true,
        "confounded": false,
        "accuracy_delta_pp": -4.45,
        "loss_delta": 0.130265,
        "rise_delta": 0.138654
      }
    ],
    "seed_pairs": [
      {
        "baseline_run_id": "lr_005_gap_001",
        "target_run_id": "baseline_001",
        "sources": [
          "runs/lr_005_gap_001.json",
          "runs/baseline_001.json"
        ],
        "source_type": "DERIVED_ANALYSIS",
        "changed_settings": {
          "learning_rate": {
            "baseline": 0.05,
            "target": 0.1
          }
        },
        "missing_controls": [
          "validation_start",
          "dropout"
        ],
        "curves": {
          "lr_005_gap_001": {
            "final_accuracy_percent": 75.15,
            "final_loss": 0.687584,
            "final_epoch": 5,
            "best_accuracy_percent": 75.15,
            "best_epoch": 5,
            "minimum_loss": 0.687584,
            "minimum_loss_epoch": 5,
            "largest_loss_rise": 0.0,
            "recoveries": [],
            "final_loss_gap_val_minus_train": 0.002611,
            "candidate_generalization_intervals": []
          },
          "baseline_001": {
            "final_accuracy_percent": 71.25,
            "final_loss": 0.820787,
            "final_epoch": 5,
            "best_accuracy_percent": 75.1,
            "best_epoch": 3,
            "minimum_loss": 0.666292,
            "minimum_loss_epoch": 3,
            "largest_loss_rise": 0.548924,
            "recoveries": [
              {
                "epochs": [
                  1,
                  2,
                  3
                ],
                "losses": [
                  0.8696,
                  1.4186,
                  0.6663
                ]
              }
            ],
            "final_loss_gap_val_minus_train": null,
            "candidate_generalization_intervals": []
          }
        },
        "matching_scope": "All recorded configuration fields; hidden_units and dropout describe architecture settings, not complete architecture provenance.",
        "missing_provenance": [
          "Exact model-class/trainer revision was not recorded in historical JSON.",
          "Hardware and software versions were not recorded in historical JSON."
        ],
        "controlled_learning_rate_pair": false,
        "confounded": false,
        "accuracy_delta_pp": -3.9,
        "loss_delta": 0.133203,
        "rise_delta": 0.548924
      },
      {
        "baseline_run_id": "lr_005_seed2",
        "target_run_id": "lr_01_seed2",
        "sources": [
          "runs/lr_005_seed2.json",
          "runs/lr_01_seed2.json"
        ],
        "source_type": "DERIVED_ANALYSIS",
        "changed_settings": {
          "learning_rate": {
            "baseline": 0.05,
            "target": 0.1
          }
        },
        "missing_controls": [
          "validation_start",
          "dropout"
        ],
        "curves": {
          "lr_005_seed2": {
            "final_accuracy_percent": 76.05,
            "final_loss": 0.684773,
            "final_epoch": 5,
            "best_accuracy_percent": 76.55,
            "best_epoch": 3,
            "minimum_loss": 0.684773,
            "minimum_loss_epoch": 5,
            "largest_loss_rise": 0.001241,
            "recoveries": [
              {
                "epochs": [
                  3,
                  4,
                  5
                ],
                "losses": [
                  0.7457,
                  0.7469,
                  0.6848
                ]
              }
            ],
            "final_loss_gap_val_minus_train": -0.008717,
            "candidate_generalization_intervals": [
              [
                3,
                4
              ]
            ]
          },
          "lr_01_seed2": {
            "final_accuracy_percent": 76.35,
            "final_loss": 0.679277,
            "final_epoch": 5,
            "best_accuracy_percent": 76.35,
            "best_epoch": 5,
            "minimum_loss": 0.679277,
            "minimum_loss_epoch": 5,
            "largest_loss_rise": 0.100527,
            "recoveries": [
              {
                "epochs": [
                  3,
                  4,
                  5
                ],
                "losses": [
                  0.7136,
                  0.8142,
                  0.6793
                ]
              }
            ],
            "final_loss_gap_val_minus_train": -0.012381,
            "candidate_generalization_intervals": []
          }
        },
        "matching_scope": "All recorded configuration fields; hidden_units and dropout describe architecture settings, not complete architecture provenance.",
        "missing_provenance": [
          "Exact model-class/trainer revision was not recorded in historical JSON.",
          "Hardware and software versions were not recorded in historical JSON."
        ],
        "controlled_learning_rate_pair": false,
        "confounded": false,
        "accuracy_delta_pp": 0.3,
        "loss_delta": -0.005496,
        "rise_delta": 0.099287
      },
      {
        "baseline_run_id": "lr_005_seed3",
        "target_run_id": "lr_01_seed3",
        "sources": [
          "runs/lr_005_seed3.json",
          "runs/lr_01_seed3.json"
        ],
        "source_type": "DERIVED_ANALYSIS",
        "changed_settings": {
          "learning_rate": {
            "baseline": 0.05,
            "target": 0.1
          }
        },
        "missing_controls": [],
        "curves": {
          "lr_005_seed3": {
            "final_accuracy_percent": 75.9,
            "final_loss": 0.6806,
            "final_epoch": 5,
            "best_accuracy_percent": 75.9,
            "best_epoch": 5,
            "minimum_loss": 0.6806,
            "minimum_loss_epoch": 5,
            "largest_loss_rise": 0.0,
            "recoveries": [],
            "final_loss_gap_val_minus_train": -0.01233,
            "candidate_generalization_intervals": []
          },
          "lr_01_seed3": {
            "final_accuracy_percent": 71.45,
            "final_loss": 0.810865,
            "final_epoch": 5,
            "best_accuracy_percent": 73.2,
            "best_epoch": 4,
            "minimum_loss": 0.682841,
            "minimum_loss_epoch": 4,
            "largest_loss_rise": 0.138654,
            "recoveries": [
              {
                "epochs": [
                  1,
                  2,
                  3
                ],
                "losses": [
                  0.8865,
                  1.0252,
                  0.8685
                ]
              }
            ],
            "final_loss_gap_val_minus_train": -0.002276,
            "candidate_generalization_intervals": []
          }
        },
        "matching_scope": "All recorded configuration fields; hidden_units and dropout describe architecture settings, not complete architecture provenance.",
        "missing_provenance": [
          "Exact model-class/trainer revision was not recorded in historical JSON.",
          "Hardware and software versions were not recorded in historical JSON."
        ],
        "controlled_learning_rate_pair": true,
        "confounded": false,
        "accuracy_delta_pp": -4.45,
        "loss_delta": 0.130265,
        "rise_delta": 0.138654
      }
    ],
    "seed_summary": {
      "distinct_recorded_blocks": 3,
      "mean_accuracy_delta_pp": -2.6833,
      "population_sd_delta_pp": 2.1215,
      "limit": "Descriptive observed blocks; missing controls and reuse of one split limit causal interpretation."
    },
    "incomplete_records": [],
    "selected_records": [
      {
        "config": {
          "run_id": "lr_005_seed3",
          "dataset": "FashionMNIST",
          "source_partition": "train",
          "preprocessing": "ToTensor",
          "train_size": 10000,
          "val_size": 2000,
          "validation_start": 10000,
          "split_seed": 42,
          "shuffle_seed": 243,
          "model_seed": 244,
          "batch_size": 128,
          "hidden_units": 128,
          "dropout": 0.0,
          "optimizer": "SGD",
          "learning_rate": 0.05,
          "epochs": 5
        },
        "metrics": [
          {
            "epoch": 1,
            "train_loss_during_epoch": 1.5768690871238709,
            "train_loss_after_epoch": 1.0953938115119934,
            "train_accuracy_after_epoch": 0.612,
            "val_loss": 1.077092869758606,
            "val_accuracy": 0.626
          },
          {
            "epoch": 2,
            "train_loss_during_epoch": 0.9157467240333557,
            "train_loss_after_epoch": 0.8976822423934937,
            "train_accuracy_after_epoch": 0.6745,
            "val_loss": 0.8978471145629883,
            "val_accuracy": 0.6775
          },
          {
            "epoch": 3,
            "train_loss_during_epoch": 0.7648744816780091,
            "train_loss_after_epoch": 0.8522588306427002,
            "train_accuracy_after_epoch": 0.6881,
            "val_loss": 0.8446058855056763,
            "val_accuracy": 0.687
          },
          {
            "epoch": 4,
            "train_loss_during_epoch": 0.6941012891769409,
            "train_loss_after_epoch": 0.6855860265254974,
            "train_accuracy_after_epoch": 0.7522,
            "val_loss": 0.6975534653663635,
            "val_accuracy": 0.7305
          },
          {
            "epoch": 5,
            "train_loss_during_epoch": 0.6385964094161988,
            "train_loss_after_epoch": 0.6929299505233765,
            "train_accuracy_after_epoch": 0.7534,
            "val_loss": 0.680600378036499,
            "val_accuracy": 0.759
          }
        ]
      },
      {
        "config": {
          "run_id": "lr_01_seed3",
          "dataset": "FashionMNIST",
          "source_partition": "train",
          "preprocessing": "ToTensor",
          "train_size": 10000,
          "val_size": 2000,
          "validation_start": 10000,
          "split_seed": 42,
          "shuffle_seed": 243,
          "model_seed": 244,
          "batch_size": 128,
          "hidden_units": 128,
          "dropout": 0.0,
          "optimizer": "SGD",
          "learning_rate": 0.1,
          "epochs": 5
        },
        "metrics": [
          {
            "epoch": 1,
            "train_loss_during_epoch": 1.2794325910568238,
            "train_loss_after_epoch": 0.9111308251380921,
            "train_accuracy_after_epoch": 0.6495,
            "val_loss": 0.8865399732589722,
            "val_accuracy": 0.6645
          },
          {
            "epoch": 2,
            "train_loss_during_epoch": 0.7691367017745971,
            "train_loss_after_epoch": 1.0264610683441162,
            "train_accuracy_after_epoch": 0.6864,
            "val_loss": 1.0251937484741211,
            "val_accuracy": 0.6875
          },
          {
            "epoch": 3,
            "train_loss_during_epoch": 0.6635693133354187,
            "train_loss_after_epoch": 0.8690615137100219,
            "train_accuracy_after_epoch": 0.6762,
            "val_loss": 0.8684509625434875,
            "val_accuracy": 0.674
          },
          {
            "epoch": 4,
            "train_loss_during_epoch": 0.6114804370880127,
            "train_loss_after_epoch": 0.6598312929391861,
            "train_accuracy_after_epoch": 0.7469,
            "val_loss": 0.6828413162231445,
            "val_accuracy": 0.732
          },
          {
            "epoch": 5,
            "train_loss_during_epoch": 0.5592419065475464,
            "train_loss_after_epoch": 0.8131413830757142,
            "train_accuracy_after_epoch": 0.7162,
            "val_loss": 0.810864956855774,
            "val_accuracy": 0.7145
          }
        ]
      }
    ]
  }
}
```
### Event 9: KNOWLEDGE RETRIEVAL — PYTHON

```json
{
  "query": "training validation loss curves",
  "source_category": "general ML knowledge",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "ranking_method": "keyword + MiniLM reciprocal rank fusion",
  "matches": [
    {
      "id": "validation",
      "path": "knowledge/validation.md",
      "source_title": "Overfitting: Interpreting loss curves",
      "source_url": "https://developers.google.com/machine-learning/crash-course/overfitting/interpreting-loss-curves",
      "topic": "training and validation loss curves",
      "source_type": "ML_KNOWLEDGE",
      "text": "Loss curves can oscillate or rise for several reasons. Reducing a learning rate can be useful when debugging an oscillating training-loss curve. When training loss improves but validation loss rises, overfitting is one possible interpretation. These are general diagnostic ideas, not proof of a cause for any particular saved run.",
      "semantic_rank": 2,
      "keyword_rank": 1,
      "cosine_similarity": 0.5254,
      "hybrid_score": 0.032522,
      "rank": 1
    },
    {
      "id": "overfitting",
      "path": "knowledge/overfitting.md",
      "source_title": "Validation curves: plotting scores to evaluate models",
      "source_url": "https://scikit-learn.org/stable/modules/learning_curve.html",
      "topic": "overfitting and validation behavior",
      "source_type": "ML_KNOWLEDGE",
      "text": "Training and validation scores together can help identify possible overfitting. A high training score paired with a lower validation score is a warning that performance may not generalize as well to unseen data. A pattern in one short saved curve is only a candidate signal; other explanations and repeated checks remain possible.",
      "semantic_rank": 1,
      "keyword_rank": 3,
      "cosine_similarity": 0.5255,
      "hybrid_score": 0.032266,
      "rank": 2
    }
  ]
}
```
### Event 10: TOOL MENU — PYTHON

```json
{
  "type": "function",
  "function": {
    "name": "select_hypotheses",
    "description": "Select and order competing hypotheses for the objective. These are candidate mechanisms, never facts. [{'hypothesis_id': 'H1', 'statement': 'A higher learning rate may contribute to larger validation-loss rises through unstable optimization.', 'supporting_experiment_evidence': ['PAIR:0', 'PAIR:1', 'PAIR:2', 'PAIR:3'], 'contradicting_experiment_evidence': []}, {'hypothesis_id': 'H2', 'statement': 'Seed-dependent training variability may contribute to differences in final validation accuracy.', 'supporting_experiment_evidence': ['PAIR:0', 'PAIR:1', 'PAIR:2', 'PAIR:3'], 'contradicting_experiment_evidence': []}, {'hypothesis_id': 'H3', 'statement': 'The short recorded training horizon may leave the final-epoch ranking sensitive to transient behavior.', 'supporting_experiment_evidence': ['RUN:lr_005_seed3', 'RUN:lr_01_seed3', 'RUN:lr_005_gap_001', 'RUN:baseline_001', 'RUN:lr_005_seed2', 'RUN:lr_01_seed2'], 'contradicting_experiment_evidence': []}, {'hypothesis_id': 'H4', 'statement': 'A generalization gap may contribute during intervals where training loss improves and validation loss rises.', 'supporting_experiment_evidence': ['PAIR:2'], 'contradicting_experiment_evidence': []}]",
    "parameters": {
      "type": "object",
      "properties": {
        "hypothesis_ids": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": [
              "H1",
              "H2",
              "H3",
              "H4"
            ]
          },
          "minItems": 2,
          "maxItems": 4
        }
      },
      "required": [
        "hypothesis_ids"
      ],
      "additionalProperties": false
    }
  }
}
```
### Event 11: AGENT REQUEST — LLM

```json
{
  "attempt": 1,
  "response": {
    "role": "assistant",
    "content": "",
    "tool_calls": [
      {
        "id": "call_luzh1exq",
        "function": {
          "index": 0,
          "name": "select_hypotheses",
          "arguments": {
            "hypothesis_ids": [
              "H1",
              "H2",
              "H3",
              "H4"
            ]
          }
        }
      }
    ]
  }
}
```
### Event 12: HYPOTHESIS GENERATED — LLM

```json
[
  {
    "source_type": "HYPOTHESIS",
    "relevant_ml_knowledge": [
      "ML:validation",
      "ML:overfitting"
    ],
    "assumptions": [
      "Recorded configurations and epoch metrics accurately describe the runs."
    ],
    "missing_evidence": [
      "Independent replication and optimizer-step/gradient measurements are absent.",
      "Validation-loss rises cannot directly demonstrate overshooting; gradients and optimizer trajectories were not recorded."
    ],
    "status": "Consistent with current evidence",
    "hypothesis_id": "H1",
    "statement": "A higher learning rate may contribute to larger validation-loss rises through unstable optimization.",
    "supporting_experiment_evidence": [
      "PAIR:0",
      "PAIR:1",
      "PAIR:2",
      "PAIR:3"
    ],
    "contradicting_experiment_evidence": [],
    "proposed_test": "Compare maximum positive consecutive-epoch validation-loss rises under matched new seeds and different learning rates.",
    "selected_by": "LLM",
    "statement_origin": "PYTHON evidence-conditioned candidate"
  },
  {
    "source_type": "HYPOTHESIS",
    "relevant_ml_knowledge": [
      "ML:validation",
      "ML:overfitting"
    ],
    "assumptions": [
      "Recorded configurations and epoch metrics accurately describe the runs."
    ],
    "missing_evidence": [
      "Independent replication and optimizer-step/gradient measurements are absent.",
      "A small number of observed seed blocks cannot establish a distribution or separate all sources of randomness."
    ],
    "status": "Consistent with current evidence",
    "hypothesis_id": "H2",
    "statement": "Seed-dependent training variability may contribute to differences in final validation accuracy.",
    "supporting_experiment_evidence": [
      "PAIR:0",
      "PAIR:1",
      "PAIR:2",
      "PAIR:3"
    ],
    "contradicting_experiment_evidence": [],
    "proposed_test": "Repeat a controlled learning-rate comparison under a new shared model/shuffle seed block; predefine accuracy and loss-rise comparisons.",
    "selected_by": "LLM",
    "statement_origin": "PYTHON evidence-conditioned candidate"
  },
  {
    "source_type": "HYPOTHESIS",
    "relevant_ml_knowledge": [
      "ML:validation",
      "ML:overfitting"
    ],
    "assumptions": [
      "Recorded configurations and epoch metrics accurately describe the runs."
    ],
    "missing_evidence": [
      "Independent replication and optimizer-step/gradient measurements are absent.",
      "Longer independently approved training and predeclared stopping criteria are unavailable."
    ],
    "status": "Consistent with current evidence",
    "hypothesis_id": "H3",
    "statement": "The short recorded training horizon may leave the final-epoch ranking sensitive to transient behavior.",
    "supporting_experiment_evidence": [
      "RUN:lr_005_seed3",
      "RUN:lr_01_seed3",
      "RUN:lr_005_gap_001",
      "RUN:baseline_001",
      "RUN:lr_005_seed2",
      "RUN:lr_01_seed2"
    ],
    "contradicting_experiment_evidence": [],
    "proposed_test": "Replicate the existing horizon first; consider a separately approved longer-horizon study if ambiguity remains.",
    "selected_by": "LLM",
    "statement_origin": "PYTHON evidence-conditioned candidate"
  },
  {
    "source_type": "HYPOTHESIS",
    "relevant_ml_knowledge": [
      "ML:validation",
      "ML:overfitting"
    ],
    "assumptions": [
      "Recorded configurations and epoch metrics accurately describe the runs."
    ],
    "missing_evidence": [
      "Independent replication and optimizer-step/gradient measurements are absent.",
      "This interval rule is a diagnostic candidate, not proof of overfitting."
    ],
    "status": "Consistent with current evidence",
    "hypothesis_id": "H4",
    "statement": "A generalization gap may contribute during intervals where training loss improves and validation loss rises.",
    "supporting_experiment_evidence": [
      "PAIR:2"
    ],
    "contradicting_experiment_evidence": [],
    "proposed_test": "Inspect matched train/validation curves and test one regularization change in a separate controlled proposal.",
    "selected_by": "LLM",
    "statement_origin": "PYTHON evidence-conditioned candidate"
  }
]
```
### Event 13: HYPOTHESIS VALIDATION — PYTHON

```json
{
  "valid": true,
  "errors": [],
  "unsupported_structured_citations": 0,
  "scope": "Structured evidence links and recorded snapshots; not a proof of causal mechanisms."
}
```
### Event 14: APPROVAL REQUEST — APP POLICY

```json
{
  "proposal_id": "INV-9B53F0C759-P1",
  "hash": "f7b95c2b8908ea4fc8a4005b969a52a9c7c9516f99c1afb3ec21ee03c6aa7b51",
  "payload": {
    "proposal_id": "INV-9B53F0C759-P1",
    "investigation_id": "INV-9B53F0C759",
    "hypothesis_ids": [
      "H1",
      "H2"
    ],
    "changed_variable": "learning_rate",
    "controlled_variables": [
      "dataset",
      "source_partition",
      "preprocessing",
      "train_size",
      "val_size",
      "validation_start",
      "split_seed",
      "shuffle_seed",
      "model_seed",
      "batch_size",
      "hidden_units",
      "optimizer",
      "epochs",
      "dropout"
    ],
    "runs": [
      {
        "run_id": "v3_inv_9b53f0c759_control",
        "dataset": "FashionMNIST",
        "source_partition": "train",
        "preprocessing": "ToTensor",
        "train_size": 10000,
        "val_size": 2000,
        "validation_start": 10000,
        "split_seed": 42,
        "shuffle_seed": 443,
        "model_seed": 444,
        "batch_size": 128,
        "hidden_units": 128,
        "dropout": 0.0,
        "optimizer": "SGD",
        "learning_rate": 0.05,
        "epochs": 5
      },
      {
        "run_id": "v3_inv_9b53f0c759_target",
        "dataset": "FashionMNIST",
        "source_partition": "train",
        "preprocessing": "ToTensor",
        "train_size": 10000,
        "val_size": 2000,
        "validation_start": 10000,
        "split_seed": 42,
        "shuffle_seed": 443,
        "model_seed": 444,
        "batch_size": 128,
        "hidden_units": 128,
        "dropout": 0.0,
        "optimizer": "SGD",
        "learning_rate": 0.1,
        "epochs": 5
      }
    ],
    "rationale": "A new shared seed block tests whether the observed loss-rise ordering replicates while all other recorded controls are matched.",
    "seed_rationale": "Seeds exceed recorded runs and reserved legacy plans. The same fresh seeds are used by both arms.",
    "primary_metric": "largest_positive_consecutive_epoch_validation_loss_rise",
    "secondary_metrics": [
      "final_validation_accuracy_percent",
      "final_validation_loss"
    ],
    "supported_if": "The higher-rate arm has a strictly larger maximum validation-loss rise.",
    "contradicted_if": "The higher-rate arm has a smaller maximum rise; equality is inconclusive.",
    "limitations": [
      "One new seed block does not establish general causation.",
      "The same fixed validation split is reused; the official test set is excluded.",
      "Validation metrics do not directly measure overshooting.",
      "Other hypotheses may require separately approved designs."
    ],
    "limits": {
      "max_total_seconds": 600,
      "max_runs": 2,
      "cpu_threads": 2
    },
    "training_code_sha256": "2f368c1d74005e8c32520a496614a123c297531789371d97748ce0a571750e66"
  }
}
```
### Event 15: USER DECISION — DEVELOPMENT_DRY_RUN

```json
{
  "id": 3,
  "proposal_id": "INV-9B53F0C759-P1",
  "hash": "f7b95c2b8908ea4fc8a4005b969a52a9c7c9516f99c1afb3ec21ee03c6aa7b51",
  "decision": "approved",
  "mode": "dry_run",
  "actor": "development_dry_run",
  "reason": "V3 development demonstration; no live training permission",
  "timestamp": "2026-10-26T06:20:09.095165+00:00"
}
```
### Event 16: EXECUTION RESULT — USER_AUTHORIZED

```json
{
  "status": "dry_run_completed",
  "mode": "dry_run",
  "started": "2026-10-26T06:20:09.223413+00:00",
  "run_ids": [],
  "logs": [],
  "ingested": [],
  "planned_configs": [
    {
      "run_id": "v3_inv_9b53f0c759_control",
      "dataset": "FashionMNIST",
      "source_partition": "train",
      "preprocessing": "ToTensor",
      "train_size": 10000,
      "val_size": 2000,
      "validation_start": 10000,
      "split_seed": 42,
      "shuffle_seed": 443,
      "model_seed": 444,
      "batch_size": 128,
      "hidden_units": 128,
      "dropout": 0.0,
      "optimizer": "SGD",
      "learning_rate": 0.05,
      "epochs": 5
    },
    {
      "run_id": "v3_inv_9b53f0c759_target",
      "dataset": "FashionMNIST",
      "source_partition": "train",
      "preprocessing": "ToTensor",
      "train_size": 10000,
      "val_size": 2000,
      "validation_start": 10000,
      "split_seed": 42,
      "shuffle_seed": 443,
      "model_seed": 444,
      "batch_size": 128,
      "hidden_units": 128,
      "dropout": 0.0,
      "optimizer": "SGD",
      "learning_rate": 0.1,
      "epochs": 5
    }
  ],
  "message": "Approval and resource checks passed. No trainer was launched; no metrics or run files were created.",
  "finished": "2026-10-26T06:20:09.239851+00:00"
}
```
### Event 17: FINAL REPORT — PYTHON

```json
{
  "status": "dry_run_completed",
  "sources": [
    "RUN:lr_005_seed3",
    "RUN:lr_01_seed3",
    "RUN:lr_005_gap_001",
    "RUN:baseline_001",
    "RUN:lr_005_seed2",
    "RUN:lr_01_seed2",
    "PAIR:0",
    "PAIR:1",
    "PAIR:2",
    "PAIR:3",
    "ML:validation",
    "ML:overfitting",
    "NOTE:0",
    "NOTE:1",
    "NOTE:2",
    "NOTE:5"
  ]
}
```

## Exact preserved experiment snapshots

### runs/lr_005_seed3.json

```json
{
  "config": {
    "run_id": "lr_005_seed3",
    "dataset": "FashionMNIST",
    "source_partition": "train",
    "preprocessing": "ToTensor",
    "train_size": 10000,
    "val_size": 2000,
    "validation_start": 10000,
    "split_seed": 42,
    "shuffle_seed": 243,
    "model_seed": 244,
    "batch_size": 128,
    "hidden_units": 128,
    "dropout": 0.0,
    "optimizer": "SGD",
    "learning_rate": 0.05,
    "epochs": 5
  },
  "metrics": [
    {
      "epoch": 1,
      "train_loss_during_epoch": 1.5768690871238709,
      "train_loss_after_epoch": 1.0953938115119934,
      "train_accuracy_after_epoch": 0.612,
      "val_loss": 1.077092869758606,
      "val_accuracy": 0.626
    },
    {
      "epoch": 2,
      "train_loss_during_epoch": 0.9157467240333557,
      "train_loss_after_epoch": 0.8976822423934937,
      "train_accuracy_after_epoch": 0.6745,
      "val_loss": 0.8978471145629883,
      "val_accuracy": 0.6775
    },
    {
      "epoch": 3,
      "train_loss_during_epoch": 0.7648744816780091,
      "train_loss_after_epoch": 0.8522588306427002,
      "train_accuracy_after_epoch": 0.6881,
      "val_loss": 0.8446058855056763,
      "val_accuracy": 0.687
    },
    {
      "epoch": 4,
      "train_loss_during_epoch": 0.6941012891769409,
      "train_loss_after_epoch": 0.6855860265254974,
      "train_accuracy_after_epoch": 0.7522,
      "val_loss": 0.6975534653663635,
      "val_accuracy": 0.7305
    },
    {
      "epoch": 5,
      "train_loss_during_epoch": 0.6385964094161988,
      "train_loss_after_epoch": 0.6929299505233765,
      "train_accuracy_after_epoch": 0.7534,
      "val_loss": 0.680600378036499,
      "val_accuracy": 0.759
    }
  ]
}
```

### runs/lr_01_seed3.json

```json
{
  "config": {
    "run_id": "lr_01_seed3",
    "dataset": "FashionMNIST",
    "source_partition": "train",
    "preprocessing": "ToTensor",
    "train_size": 10000,
    "val_size": 2000,
    "validation_start": 10000,
    "split_seed": 42,
    "shuffle_seed": 243,
    "model_seed": 244,
    "batch_size": 128,
    "hidden_units": 128,
    "dropout": 0.0,
    "optimizer": "SGD",
    "learning_rate": 0.1,
    "epochs": 5
  },
  "metrics": [
    {
      "epoch": 1,
      "train_loss_during_epoch": 1.2794325910568238,
      "train_loss_after_epoch": 0.9111308251380921,
      "train_accuracy_after_epoch": 0.6495,
      "val_loss": 0.8865399732589722,
      "val_accuracy": 0.6645
    },
    {
      "epoch": 2,
      "train_loss_during_epoch": 0.7691367017745971,
      "train_loss_after_epoch": 1.0264610683441162,
      "train_accuracy_after_epoch": 0.6864,
      "val_loss": 1.0251937484741211,
      "val_accuracy": 0.6875
    },
    {
      "epoch": 3,
      "train_loss_during_epoch": 0.6635693133354187,
      "train_loss_after_epoch": 0.8690615137100219,
      "train_accuracy_after_epoch": 0.6762,
      "val_loss": 0.8684509625434875,
      "val_accuracy": 0.674
    },
    {
      "epoch": 4,
      "train_loss_during_epoch": 0.6114804370880127,
      "train_loss_after_epoch": 0.6598312929391861,
      "train_accuracy_after_epoch": 0.7469,
      "val_loss": 0.6828413162231445,
      "val_accuracy": 0.732
    },
    {
      "epoch": 5,
      "train_loss_during_epoch": 0.5592419065475464,
      "train_loss_after_epoch": 0.8131413830757142,
      "train_accuracy_after_epoch": 0.7162,
      "val_loss": 0.810864956855774,
      "val_accuracy": 0.7145
    }
  ]
}
```

### runs/lr_005_gap_001.json

```json
{
  "config": {
    "run_id": "lr_005_gap_001",
    "dataset": "FashionMNIST",
    "source_partition": "train",
    "preprocessing": "ToTensor",
    "train_size": 10000,
    "val_size": 2000,
    "split_seed": 42,
    "shuffle_seed": 43,
    "model_seed": 44,
    "batch_size": 128,
    "hidden_units": 128,
    "optimizer": "SGD",
    "learning_rate": 0.05,
    "epochs": 5
  },
  "metrics": [
    {
      "epoch": 1,
      "train_loss_during_epoch": 1.5666301128387452,
      "train_loss_after_epoch": 1.073829147720337,
      "train_accuracy_after_epoch": 0.6476,
      "val_loss": 1.0545751457214356,
      "val_accuracy": 0.649
    },
    {
      "epoch": 2,
      "train_loss_during_epoch": 0.9119185653686523,
      "train_loss_after_epoch": 0.9968783388137817,
      "train_accuracy_after_epoch": 0.6515,
      "val_loss": 1.0082858295440673,
      "val_accuracy": 0.6565
    },
    {
      "epoch": 3,
      "train_loss_during_epoch": 0.7680734439849853,
      "train_loss_after_epoch": 0.7941052691459656,
      "train_accuracy_after_epoch": 0.693,
      "val_loss": 0.763293098449707,
      "val_accuracy": 0.709
    },
    {
      "epoch": 4,
      "train_loss_during_epoch": 0.6890689352989197,
      "train_loss_after_epoch": 0.7420328899860382,
      "train_accuracy_after_epoch": 0.7306,
      "val_loss": 0.7394451971054077,
      "val_accuracy": 0.727
    },
    {
      "epoch": 5,
      "train_loss_during_epoch": 0.6421152505874633,
      "train_loss_after_epoch": 0.6849735041618347,
      "train_accuracy_after_epoch": 0.7493,
      "val_loss": 0.6875842409133911,
      "val_accuracy": 0.7515
    }
  ]
}
```

### runs/baseline_001.json

```json
{
  "config": {
    "run_id": "baseline_001",
    "dataset": "FashionMNIST",
    "source_partition": "train",
    "preprocessing": "ToTensor",
    "train_size": 10000,
    "val_size": 2000,
    "split_seed": 42,
    "shuffle_seed": 43,
    "model_seed": 44,
    "batch_size": 128,
    "hidden_units": 128,
    "optimizer": "SGD",
    "learning_rate": 0.1,
    "epochs": 5
  },
  "metrics": [
    {
      "epoch": 1,
      "train_loss_during_epoch": 1.2743709097385407,
      "val_loss": 0.8696367411613465,
      "val_accuracy": 0.6635
    },
    {
      "epoch": 2,
      "train_loss_during_epoch": 0.7620800113677979,
      "val_loss": 1.4185610065460206,
      "val_accuracy": 0.615
    },
    {
      "epoch": 3,
      "train_loss_during_epoch": 0.6735970516681671,
      "val_loss": 0.6662915515899658,
      "val_accuracy": 0.751
    },
    {
      "epoch": 4,
      "train_loss_during_epoch": 0.6022407117843628,
      "val_loss": 0.7384269852638244,
      "val_accuracy": 0.731
    },
    {
      "epoch": 5,
      "train_loss_during_epoch": 0.5674220984458923,
      "val_loss": 0.8207873892784119,
      "val_accuracy": 0.7125
    }
  ]
}
```

### runs/lr_005_seed2.json

```json
{
  "config": {
    "run_id": "lr_005_seed2",
    "dataset": "FashionMNIST",
    "source_partition": "train",
    "preprocessing": "ToTensor",
    "train_size": 10000,
    "val_size": 2000,
    "split_seed": 42,
    "shuffle_seed": 143,
    "model_seed": 144,
    "batch_size": 128,
    "hidden_units": 128,
    "optimizer": "SGD",
    "learning_rate": 0.05,
    "epochs": 5
  },
  "metrics": [
    {
      "epoch": 1,
      "train_loss_during_epoch": 1.5315584199905397,
      "train_loss_after_epoch": 1.0901034973144532,
      "train_accuracy_after_epoch": 0.6104,
      "val_loss": 1.0847976474761962,
      "val_accuracy": 0.6245
    },
    {
      "epoch": 2,
      "train_loss_during_epoch": 0.9101661073684693,
      "train_loss_after_epoch": 0.9570370040893554,
      "train_accuracy_after_epoch": 0.6502,
      "val_loss": 0.9494747867584229,
      "val_accuracy": 0.656
    },
    {
      "epoch": 3,
      "train_loss_during_epoch": 0.7630627304077149,
      "train_loss_after_epoch": 0.7550262860298157,
      "train_accuracy_after_epoch": 0.7568,
      "val_loss": 0.7456555824279785,
      "val_accuracy": 0.7655
    },
    {
      "epoch": 4,
      "train_loss_during_epoch": 0.6889050116539002,
      "train_loss_after_epoch": 0.7424132695198059,
      "train_accuracy_after_epoch": 0.7367,
      "val_loss": 0.7468963384628295,
      "val_accuracy": 0.732
    },
    {
      "epoch": 5,
      "train_loss_during_epoch": 0.6398591944694519,
      "train_loss_after_epoch": 0.6934895318031311,
      "train_accuracy_after_epoch": 0.7545,
      "val_loss": 0.6847728147506714,
      "val_accuracy": 0.7605
    }
  ]
}
```

### runs/lr_01_seed2.json

```json
{
  "config": {
    "run_id": "lr_01_seed2",
    "dataset": "FashionMNIST",
    "source_partition": "train",
    "preprocessing": "ToTensor",
    "train_size": 10000,
    "val_size": 2000,
    "split_seed": 42,
    "shuffle_seed": 143,
    "model_seed": 144,
    "batch_size": 128,
    "hidden_units": 128,
    "optimizer": "SGD",
    "learning_rate": 0.1,
    "epochs": 5
  },
  "metrics": [
    {
      "epoch": 1,
      "train_loss_during_epoch": 1.2585902948379517,
      "train_loss_after_epoch": 1.1092852766036987,
      "train_accuracy_after_epoch": 0.6343,
      "val_loss": 1.1125362911224366,
      "val_accuracy": 0.6415
    },
    {
      "epoch": 2,
      "train_loss_during_epoch": 0.771264350605011,
      "train_loss_after_epoch": 0.9085725147247314,
      "train_accuracy_after_epoch": 0.6757,
      "val_loss": 0.9025846681594849,
      "val_accuracy": 0.674
    },
    {
      "epoch": 3,
      "train_loss_during_epoch": 0.6569976014137268,
      "train_loss_after_epoch": 0.7324729803562164,
      "train_accuracy_after_epoch": 0.7359,
      "val_loss": 0.7136394624710083,
      "val_accuracy": 0.754
    },
    {
      "epoch": 4,
      "train_loss_during_epoch": 0.6016732814788819,
      "train_loss_after_epoch": 0.7922292562484741,
      "train_accuracy_after_epoch": 0.732,
      "val_loss": 0.8141668553352356,
      "val_accuracy": 0.7205
    },
    {
      "epoch": 5,
      "train_loss_during_epoch": 0.5686421188354492,
      "train_loss_after_epoch": 0.6916582312107086,
      "train_accuracy_after_epoch": 0.7575,
      "val_loss": 0.6792771730422974,
      "val_accuracy": 0.7635
    }
  ]
}
```

## Reproduce and inspect

# Commands and operation

Run from PowerShell in the existing project directory. Ollama must already be running with the installed qwen3:1.7b; these commands do not download models.

```powershell
cd "D:\Agentic_ai_rag projects"
.\.venv\Scripts\streamlit.exe run ui.py
```

The default workspace is **Investigations (V3)**. Start a question, select a saved investigation, inspect its seven tabs, and use Resume. Approve dry run to inspect execution without training. The separate live-training checkbox plus approve button explicitly authorizes the displayed configuration. Reject or defer stops execution. Editing validates and invalidates approval. **Chat and runs (V1/V2)** retains manual, graph and simple modes.

```powershell
.\.venv\Scripts\python.exe app.py --agent research --question "Investigate why lr_01_seed3 was worse than lr_005_seed3."
.\.venv\Scripts\python.exe -m v3.cli list
.\.venv\Scripts\python.exe -m v3.cli show INV-9B53F0C759
.\.venv\Scripts\python.exe -m v3.cli resume INV-9B53F0C759
.\.venv\Scripts\python.exe -m v3.cli export INV-9B53F0C759
```

The displayed demonstration is already dry-run completed; resuming it does not re-execute it. For a **new pending** proposal, copy its displayed investigation ID and exact SHA-256 into this command template:

```powershell
.\.venv\Scripts\python.exe -m v3.cli decide "INV-ID-FROM-START" approved --hash "SHA256-FROM-SHOW" --mode dry_run
```

Use `rejected` or `deferred` instead of `approved` to stop/defer. `--mode live` is an explicit request for the displayed two-run training workload. No live-training command was executed during development. To edit via CLI, export/copy the displayed proposal JSON to a file and use `python -m v3.cli modify "INV-ID" "proposal.json"`; the UI provides the same operation. A changed proposal needs a new approval.

```powershell
.\.venv\Scripts\python.exe -m v3.cli start "Investigate why lr_01_seed3 was worse than lr_005_seed3" --offline --lexical
.\.venv\Scripts\python.exe evaluate_v3.py
.\.venv\Scripts\python.exe evaluate_v3_retrieval.py
.\.venv\Scripts\python.exe validate_v3_ui.py
.\.venv\Scripts\python.exe validate_v3_live.py
.\.venv\Scripts\python.exe -m v3.demo
.\.venv\Scripts\python.exe docs\build_v3_study.py
```

`--offline` means Python planning/hypothesis fallback with honest origins. `--lexical` additionally avoids embedding imports for lightweight investigation fixtures/debugging. These flags configure research nodes; simple questions delegated to the preserved V2 agent still require local Ollama. Ordinary investigations use existing Ollama and cached MiniLM. The demo explicitly grants development **dry-run only** permission and saves reviewable Markdown/JSON in `reports/v3_demo/`.

V1/V2 commands remain `app.py --agent simple`, `--agent manual`, and `--agent graph`. The old `validate_v2.py` and `evaluate_retrieval.py` remain available. The V2 validator's output location is unchanged; the V3 development regression output was copied to `reports/v3_v2_regression_traces.json` and the original historical artifact restored.

If the local server is stopped, run `& "D:\Ollama\ollama.exe" serve` in another PowerShell window. Its existing user environment sets `OLLAMA_MODELS=D:\Ollama\models`. Do not pull a new model for V3.
