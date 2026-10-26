# Study V3 in this order

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
