# V3 planning, state and resumption

## Five kinds of information

1. **LLM context:** the current prompt/schema and compact candidate evidence sent to Ollama. It is a bounded request, not durable memory.
2. **Conversation memory:** V2 `SessionState` remembers up to four turns, focused run IDs and reference resolution inside the current chat. Clearing it does not delete investigations.
3. **Persistent workflow state:** SQLite stores the objective, plan, exact evidence snapshots, hypotheses, proposal IDs, trace, execution outcome and report. LangGraph checkpoints store where execution stopped.
4. **Experiment knowledge:** `runs/*.json`, original `notes/*.md` and deterministically derived summaries. These survive independently of chat and investigation state.
5. **Retrieved external knowledge:** the five local `knowledge/*.md` chunks contain attributed material from external ML documentation. They are curated offline sources, not live web browsing.

## What the plan really is

`make_plan` stores a list of objects. Every step has `id`, `description`, `tool`, `depends_on`, `status` and `proposed_by`. Statuses include pending, completed, skipped, failed and waiting. A trace records the raw model decision and any Python-required additions. `optional_step_origins` distinguishes a model-selected step from one inserted to satisfy the question.

The initial model decision selects from `search_notes`, `compare_seed_pairs`, and `retrieve_knowledge`, plus one covered knowledge topic. Exact reading, deterministic checks, hypothesis grounding, independent proposal validation, and the approval gate are Python requirements. With no run ID, a note search discovers IDs, then the collection node records a visible REPLANNING event before inspecting their JSON. This is bounded evidence-driven replanning, not an open-ended autonomous research planner.

Reactive calling chooses the next tool after an observation. Planning chooses useful work before collecting evidence. Replanning changes the concrete run references after search. A deterministic workflow prescribes scientific checks and their ordering. Genuine LLM decisions select optional tools and hypothesis candidates. V3 combines these explicitly instead of calling every operation an agent decision.

## Persistence mechanics

`InvestigationStore` creates `investigations`, `proposals` and append-only `decisions` audit rows. `SqliteSaver` creates its own checkpoint tables in the same database. The store always closes SQLite connections, including on Windows. Each node saves its application document; LangGraph commits a checkpoint at the node boundary. The investigation ID is also the LangGraph `thread_id`.

An application snapshot answers “What do we know?” A checkpoint answers “Which node is next, and are we interrupted?” These are separate writes, not one transaction. Important replay behavior is therefore explicit: unchanged proposals preserve approval; execution permission is consumed atomically; a finished execution result is reused; a running execution discovered after restart is marked interrupted rather than relaunched.

`resume` opens a fresh graph/checkpointer, reads the saved snapshot, and checks `snapshot.next` and task interrupts. Loading a pending investigation does not imply approval. A stored human decision is required before sending `Command(resume=...)`. A process-restart validation closes one Python process and resumes from a completely new process.

The interrupt node restarts from its beginning when resumed. Code before `interrupt` can run twice. It can render/save the request again, but cannot launch training. Side effects that spend resources occur only after a persisted exact decision and atomic execution claim.

## Recovery limits

A failed evidence/model node can be resumed from its checkpoint; each model decision still has at most two attempts. The graph does not retry training by itself. If an app crashes while a worker might still exist, inspect the saved logs and process before making a new proposal. Partial run records remain intact; both arms are needed for post-experiment interpretation. V3 does not automatically attach a surviving Windows process, cancel it, or reconstruct a partially completed pair. Those are deliberate limits of this local implementation.

Opening a deferred/rejected proposal and explicitly approving it schedules the approval gate again. Modifying a proposal validates it, invalidates its previous approval, updates the graph state as the design node, and suspends at a fresh gate. Completed proposals cannot be edited into new experiments; create a new investigation.
