# V3 human-in-the-loop execution

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
