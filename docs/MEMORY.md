# Session memory

**State** is the small Python object carried across turns. `SessionState` holds recent user questions, compact prior answers, actual tool decisions, referenced run IDs, and a focused run ID. It lives only in the CLI process or a Streamlit `session_state`. `clear` in the CLI or **Clear conversation** in the UI resets it.

For `Tell me about lr_01_seed3.` followed by `Compare that run with lr_005_seed3.`, `resolve()` replaces the singular phrase with `lr_01_seed3` before planning the next tool. The trace shows the original and resolved question. A “worst learning rate 0.1 run” search focuses its lowest-accuracy returned run so “Show me its loss curve” can resolve it. This is a simple, explicit reference rule; it is not a general coreference model.

`history_messages()` sends at most four previous user/assistant pairs back to Ollama. Each user message is capped at 400 characters; each prior answer at 700 characters, plus a 300-character summary of tools used. Tool results themselves are not copied in full across turns. This bounds context growth, although a current turn can still use several tool results. `MAX_TOOL_CALLS=6` bounds its tool loop. The trace and session snapshot show what was retained.

Conversation memory is **not** the experiment database. It can be cleared without changing `runs/*.json`, `notes/*.md`, or `knowledge/*.md`. It is also not permanent personal memory or vector memory. The focused ID can be wrong for an ambiguous plural reference; name the run explicitly when precision matters.
