# V2 versus V3

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
