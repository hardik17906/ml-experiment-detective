# Exact study order

1. Run `app.py --agent simple --question "What is the final validation accuracy of lr_01_seed3?"`. Read `simple_agent.py` to recall the V1 manual loop.
2. Read `docs/V2_ARCHITECTURE.md`, then `v2_state.py` and `docs/MEMORY.md`. In the CLI, ask about `lr_01_seed3` and then compare “that run” with `lr_005_seed3`.
3. Read `note_retrieval.py`, `v2_retrieval.py`, and `docs/HYBRID_RAG.md`. Run `evaluate_retrieval.py`; inspect the raw rank and score stages in a note-search trace.
4. Turn on `--rerank` for one note question and compare `RERANKED RESULTS` with `HYBRID RESULTS`. Keep the five-case evaluation limits in mind.
5. Read `experiment_data.py`, `v2_analysis.py`, and `v2_tools.py`. Ask for an exact comparison, a curve summary, candidates, a group, and chart data; look at their Python results.
6. Read the `knowledge/*.md` metadata, `docs/EXTERNAL_KNOWLEDGE_RAG.md`, and `v2_answers.py`. Ask why a named pair differs and find which lines are observed facts versus general mechanisms.
7. Follow `docs/V2_COMPLETE_TRACE.md` against the full JSON trace. Locate every memory event, tool menu, tool argument, tool result, retrieval stage, and final source.
8. Read `v2_agent.py` from `prepare_turn` through `run_manual`. Identify the decision, execution, observation, and stopping logic, including the clearly labeled application fallback.
9. Read `docs/MANUAL_VS_LANGGRAPH.md` and then `graph_agent.py`. Run the same question with `--agent manual` and `--agent graph`.
10. Start `ui.py`. Inspect one run's settings, accuracy, loss chart, epoch table, chat answer, and expandable trace. Clear the conversation to see the state reset.

The useful next task is to explain the observed trace back in your own words and inspect the code at each transition. This project stops at V2.
