# V3 evaluation — executed results

The deterministic suite ran **56 scenarios: 56 passed, 0 failed/errors**. These are scenario checks and simulated failures, not an unrestricted live-model benchmark. Live training was not performed.

## Deterministic agent checks

```json
{
  "generated_at": "2026-10-26T06:29:22.570550+00:00",
  "type": "deterministic scenarios / simulated failures",
  "tests_run": 56,
  "passed": 56,
  "failed_or_errors": 0,
  "checks": {
    "numeric_correctness": {
      "passed": 8,
      "total": 8
    },
    "approval_bypass_attempts_blocked": {
      "passed": 9,
      "total": 9
    },
    "grounding_checks": {
      "passed": 5,
      "total": 5
    },
    "simulated_tool_selection_and_termination": {
      "passed": 8,
      "total": 8
    },
    "persistence_and_resume": {
      "passed": 7,
      "total": 7
    }
  },
  "unsupported_claim_count": "Not measured for unrestricted natural language. Structured citation checks are measured separately.",
  "scenarios": [
    {
      "scenario": "test_v3.InvestigatorTests.test_01_exact_numeric_difference",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_02_controlled_pair_checks_every_field",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_03_missing_historical_controls_not_assumed",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_04_confounded_comparison",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_05_incomplete_metrics",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_06_unequal_epochs_do_not_compare_final",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_07_pending_approval_blocks_execution",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_08_rejection_blocks_execution",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_09_dry_run_cannot_authorize_live_training",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_10_stale_hash_cannot_approve",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_11_modification_invalidates_approval",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_12_arbitrary_command_field_rejected",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_13_resource_limits_enforced",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_14_changed_trainer_requires_new_proposal",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_15_duplicate_configuration_rejected",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_16_new_seed_block_and_exact_shared_controls",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_17_structured_plan_dependencies",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_18_offline_trace_never_claims_model_decisions",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_19_hypothesis_grounding_and_competition",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_20_forged_evidence_rejected",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_21_knowledge_cannot_prove_run_outcome",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_22_state_survives_new_store",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_23_checkpoint_resume_dry_run_no_trainer",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_24_resume_token_does_not_grant_permission",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_25_reject_routes_to_report",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_26_wrong_model_tool_bounded_fallback",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_27_no_model_tool_call_bounded_fallback",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_28_valid_model_decision_changes_plan",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_29_unrelated_question_never_searches",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_30_uncovered_ml_question_explains_limit",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_31_wrong_run_id_fails_explicitly",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_32_training_failure_captured_without_training",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_33_fixture_ingestion_and_post_experiment_cycle",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_34_fixture_label_and_config_mandatory",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_35_evidence_snapshot_tampering_detected",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_36_memory_is_separate_from_persistence",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_37_derived_summaries_include_unnoted_run",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_38_configuration_filter",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_39_stopwords_removed_negation_retained",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_40_simple_question_uses_v2_without_full_plan",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_41_approval_consumed_once",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_42_missing_file_reported",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_43_defer_preserves_proposal",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_44_retrieval_failure_falls_back_to_explicit_runs",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_45_invalid_tool_arguments",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_46_model_cannot_grant_live_permission",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_47_outcome_incomplete_opposing_and_equal",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_48_timeout_recorded_and_no_unbounded_retry",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_49_report_numbers_and_source_attribution",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_50_source_priority_protects_human_notes",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_51_no_run_id_discovers_and_inspects_sources",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_52_restart_during_execution_does_not_relaunch",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_53_completed_execution_recovery_is_idempotent",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_54_successful_fixture_execution_updates_report_and_hypothesis",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_55_wrong_run_in_simple_comparison_is_not_ignored",
      "passed": true
    },
    {
      "scenario": "test_v3.InvestigatorTests.test_56_general_ml_mechanism_is_a_simple_question",
      "passed": true
    }
  ]
}
```

## Retrieval ablation on the preserved five V2 queries

| Method | Recall@2 | MRR@2 |
|---|---:|---:|
| v2_keyword | 0.90 | 0.80 |
| v2_semantic | 1.00 | 0.90 |
| v2_hybrid | 0.90 | 0.90 |
| v2_reranked | 0.80 | 0.70 |
| v3_normalized_human | 1.00 | 0.90 |
| v3_normalized_expanded | 0.60 | 0.60 |
| v3_original_keyword_expanded | 0.70 | 0.60 |
| v3_human_priority_expanded | 1.00 | 0.90 |

Removing stopwords improved the small benchmark. Flat mixing of generated summaries regressed, so it was rejected as the default. The selected human-priority policy computes within-source ranks, preserves human-note ordering, exposes derived summaries separately, and gives exact known run IDs priority. The six exact-ID queries for unnoted runs all succeeded in V3 and cannot succeed in V2's human-only corpus. This coverage test is deliberately distinct from semantic relevance on open-ended questions. No general performance claim is justified by five labels or six exact-ID queries.

## UI execution

```json
{
  "passed": 8,
  "checks": [
    "V3 empty investigation workspace renders",
    "New-investigation form executes and persists state",
    "Plan, evidence/charts, hypotheses, approval, execution, report, trace tabs render",
    "Resume preserves the pending approval gate",
    "Explicit UI approval reaches dry-run completion without training",
    "Markdown report export writes a real file",
    "V1/V2 workspace and saved-run charts still render",
    "V1 simple, V2 manual and V2 graph modes remain selectable"
  ],
  "limitation": "Streamlit AppTest execution; no screenshot or browser visual inspection and no live training."
}
```

## Live model and process restart

```json
{
  "passed": 4,
  "total": 4,
  "scope": "Small live Ollama sample and one process-restart demonstration; not a general model success-rate estimate."
}
```


```json
[
  {
    "case": "V1 simple agent live",
    "passed": true
  },
  {
    "case": "V3 simple route delegates to V2 live tools",
    "passed": true
  },
  {
    "case": "V3 no-ID live investigation discovers and inspects run IDs",
    "passed": true,
    "status": "evidence_collected"
  },
  {
    "case": "Actual app-process restart and SQLite interrupt resumption",
    "passed": true,
    "result": "dry_run_completed",
    "training": "not launched"
  }
]
```

## Existing V2 regression

All **17 original V2 checks** passed using local Ollama/cache. Their full new traces are in `reports/v3_v2_regression_traces.json`; the historical V2 artifact is preserved. V1's real single-run answer was also checked.

## Scientific and operational limits

Structured citation checks count invalid references; they do not measure every unsupported sentence in arbitrary model prose. An unrestricted unsupported-claim count was not measured. The renderer uses verified snapshots and Python calculations, while qualitative hypothesis candidates are explicitly labeled. Tool-selection checks are simulated named scenarios; the separate tiny live sample is not a statistically meaningful success-rate estimate. UI checks use Streamlit AppTest, not browser visual/screenshot inspection. Successful new-result ingestion and post-experiment reporting use labeled fixtures. Training failure/timeout tests mock subprocesses. Actual full training, OS memory quotas, process reattachment/cancellation, broad topic coverage and general causal validity remain unverified or outside scope.

## Historical failures found and resolved

The first Windows run exposed unclosed SQLite connections during test cleanup; the store now closes connections explicitly. The first seed grouping mixed different learning-rate pairs; analysis now restricts to the rates being investigated and deduplicates independent recorded blocks. The first free tool-call planner returned no calls; the planner now requests schema-constrained JSON, retains two-attempt bounds and visible fallbacks. Flat expanded retrieval degraded the old labels; the measured human-priority policy replaced it. These are development findings, not hidden successful trials.

## Acceptance evidence and stage scope

Stage A core investigator is implemented and exercised. Stage B approval/execution/checkpoint workflow is implemented and exercised through dry runs, mocked failures and fixture results; full live training remains unverified. Stage C UI/retrieval/evaluation/documentation is implemented and exercised within the small local corpus and Streamlit AppTest scope.

```json
{
  "checks": [
    {
      "requirement": "V1/V2 still run",
      "verified": true
    },
    {
      "requirement": "Original data unchanged",
      "verified": true,
      "original_files_checked": 22
    },
    {
      "requirement": "Persistent investigations survive restart",
      "verified": true
    },
    {
      "requirement": "Plans structured and traceable",
      "verified": true
    },
    {
      "requirement": "Hypotheses cite real evidence",
      "verified": true
    },
    {
      "requirement": "Controlled proposals valid",
      "verified": true
    },
    {
      "requirement": "Approval mandatory",
      "verified": true
    },
    {
      "requirement": "Rejected proposals blocked",
      "verified": true
    },
    {
      "requirement": "Dry run",
      "verified": true
    },
    {
      "requirement": "New-result ingestion",
      "verified": true,
      "scope": "Labeled fixtures; no actual new training output"
    },
    {
      "requirement": "Graph recovery",
      "verified": true
    },
    {
      "requirement": "UI investigation paths",
      "verified": true,
      "scope": "Streamlit AppTest, not browser screenshots"
    },
    {
      "requirement": "Unsupported questions",
      "verified": true
    },
    {
      "requirement": "Numeric accuracy and source grounding",
      "verified": true
    },
    {
      "requirement": "V3 evaluation suite",
      "verified": true
    },
    {
      "requirement": "D: local model/cache locations",
      "verified": true,
      "scope": "Existing D: folders and configured model path were inspected; no new models/datasets downloaded"
    },
    {
      "requirement": "Original model/evaluation algorithm preserved",
      "verified": true
    },
    {
      "requirement": "Full live training",
      "verified": false,
      "scope": "Not authorized or run; dry-run, failure mocks and fixture ingestion only"
    }
  ],
  "required_checks_passed": 17,
  "live_training_verified": false,
  "no_new_training_runs_created": true
}
```
