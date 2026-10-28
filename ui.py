"""Recommended local interface for the completed ML Experiment Detective."""
import re
from urllib.request import urlopen
import json

import pandas as pd
import streamlit as st

from assistant import ResearchAssistant
from experiment_data import RUNS_DIR, PROJECT_DIR, load_run
from v2_analysis import rank_experiments, plot_run_metrics
from v2_state import SessionState
from v3.analysis import compare_records

st.set_page_config(page_title="ML Experiment Detective", page_icon="🔎", layout="wide")


def display_answer(text):
    return re.sub(r"\[([^\]]+)\]\(((?:\.\./)?(?:runs|notes|knowledge)/[^)]+)\)", r"`\2`", text)


@st.cache_data(ttl=30)
def model_status():
    try:
        with urlopen("http://127.0.0.1:11434/api/tags", timeout=2) as response:
            names = [m["name"] for m in json.load(response)["models"]]
        return "Ready: qwen3:1.7b" if "qwen3:1.7b" in names else "Ollama running; qwen3:1.7b unavailable"
    except (OSError, ValueError, KeyError):
        return "Ollama unavailable; enable offline mode for Python fallbacks"


assistant = ResearchAssistant()
if "detective_session" not in st.session_state:
    st.session_state.detective_session = SessionState()
if "chat_entries" not in st.session_state:
    st.session_state.chat_entries = []

with st.sidebar:
    st.title("Experiment Detective")
    page = st.radio("Go to", ["Overview", "Experiment Explorer", "AI Chat", "Investigations"])
    st.caption("Saved evidence → cautious explanations → approved experiments")
    with st.expander("Advanced settings"):
        offline = st.checkbox("Use Python fallbacks without Ollama", value=False)
        semantic = st.checkbox("Use cached semantic retrieval", value=True)
        rerank = st.checkbox("Optional reranking", value=False)
        st.caption("Ranks are retrieval signals, not confidence probabilities. Reranking is off by default.")
    if st.button("Reset conversation"):
        st.session_state.detective_session.clear()
        st.session_state.chat_entries = []
        st.rerun()


def draw_run(run_id):
    record = load_run(run_id)
    st.caption(f"Exact source: runs/{run_id}.json")
    last = record["metrics"][-1]
    left, right = st.columns(2)
    left.metric("Final validation accuracy", f"{100*last['val_accuracy']:.2f}%")
    right.metric("Final validation loss", f"{last['val_loss']:.4f}")
    points = pd.DataFrame(plot_run_metrics(run_id)["points"])
    st.line_chart(points, x="epoch", y=["train_loss", "validation_loss"])
    st.line_chart(points, x="epoch", y="validation_accuracy_percent")
    with st.expander("Configuration and epoch measurements"):
        st.json(record["config"])
        st.dataframe(pd.DataFrame(record["metrics"]), hide_index=True, width="stretch")
    st.caption("Training loss is measured after each epoch when available; missing historical metrics remain blank.")


if page == "Overview":
    st.title("ML Experiment Detective")
    st.subheader("Agentic AI Research Assistant")
    st.write("Explore saved Fashion-MNIST experiments, ask questions, investigate unexpected behavior, and review controlled follow-ups before authorizing training.")
    columns = st.columns(4)
    for column, label, count in zip(columns, ["Experiments", "Human notes", "ML references", "Saved investigations"],
                                   [len(list(RUNS_DIR.glob("*.json"))), len(list((PROJECT_DIR/"notes").glob("*.md"))), len(list((PROJECT_DIR/"knowledge").glob("*.md"))), len(assistant.investigator.store.list(research_only=True))]):
        column.metric(label, count)
    st.info(model_status())
    st.caption("Primary agent: LangGraph. Models and datasets use the existing local D: caches.")
    st.markdown("**Start here**")
    st.write("1. Browse Experiment Explorer and choose a run. 2. Ask a question in AI Chat. 3. Open Investigations to inspect explanations and approve, reject or defer a follow-up.")
    for example in ["What experiments do we have?", "Which had the best final validation accuracy?", "Have we seen unstable validation-loss behavior before?", "Investigate why lr_01_seed3 underperformed."]:
        st.code(example, language=None)
    st.subheader("Saved results at a glance")
    st.dataframe(pd.DataFrame(rank_experiments()["matches"]), hide_index=True, width="stretch")
    st.caption("Saved rankings can mix different configurations; use a controlled comparison before interpreting a difference.")

elif page == "Experiment Explorer":
    st.title("Experiment Explorer")
    rows = rank_experiments(top_k=20)["matches"]
    rates = sorted({r["learning_rate"] for r in rows if r["learning_rate"] is not None})
    left, right = st.columns(2)
    selected_rate = left.selectbox("Learning rate filter", ["All"] + rates)
    query = right.text_input("Search experiment IDs")
    rows = [r for r in rows if (selected_rate == "All" or r["learning_rate"] == selected_rate) and query.lower() in r["run_id"].lower()]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    if rows:
        ids = [r["run_id"] for r in rows]
        selected = st.selectbox("View experiment", ids)
        draw_run(selected)
        if st.button("Use this run in chat"):
            st.session_state.detective_session.focused_run_id = selected
            st.success(f"Chat focus set to {selected}. Choose AI Chat in the navigation.")
        compare = st.selectbox("Compare with", ["None"] + [p.stem for p in sorted(RUNS_DIR.glob("*.json")) if p.stem != selected])
        if compare != "None":
            result = compare_records(load_run(selected), load_run(compare))
            st.subheader(f"{compare} minus {selected}")
            if "accuracy_delta_pp" in result:
                st.write(f"Accuracy difference: **{result['accuracy_delta_pp']:+.2f} percentage points**. Validation-loss difference: **{result['loss_delta']:+.4f}**.")
            st.json({k: result[k] for k in ("changed_settings", "missing_controls", "missing_provenance", "confounded", "controlled_learning_rate_pair")})
            a = pd.DataFrame(plot_run_metrics(selected)["points"]).set_index("epoch")
            b = pd.DataFrame(plot_run_metrics(compare)["points"]).set_index("epoch")
            st.line_chart(pd.DataFrame({selected: a["validation_loss"], compare: b["validation_loss"]}))
            st.line_chart(pd.DataFrame({selected: a["validation_accuracy_percent"], compare: b["validation_accuracy_percent"]}))
            st.caption("Validation loss and validation accuracy are separate charts. Recorded differences do not prove a cause.")
    else:
        st.info("No saved experiments match these filters.")

elif page == "AI Chat":
    st.title("AI Chat")
    st.caption("Ask about saved results or local ML references. Follow up with 'that run', 'the corresponding run', or 'the difference'.")
    for entry in st.session_state.chat_entries:
        with st.chat_message("user"):
            st.write(entry["question"])
        with st.chat_message("assistant"):
            st.markdown(display_answer(entry["answer"]))
            if entry.get("investigation_id") and entry.get("plan"):
                st.info(f"Saved investigation: {entry['investigation_id']}. Review its proposal in Investigations; asking a question does not authorize training.")
            for name, result in entry.get("tool_results", []):
                if name == "plot_run_metrics":
                    data = pd.DataFrame(result["points"])
                    st.line_chart(data, x="epoch", y=["train_loss", "validation_loss"])
            with st.expander("Explain how the AI worked"):
                st.caption("Model choices, Python policy, exact tool results, sources and state changes are recorded separately.")
                for event in entry.get("trace", []):
                    st.markdown(f"**{event['kind']}**")
                    st.json(event["data"])
    question = st.chat_input("Ask about experiments, comparisons, mechanisms or investigations")
    if question:
        with st.spinner("Inspecting saved evidence..."):
            try:
                result = assistant.ask(question, st.session_state.detective_session, offline=offline, semantic=semantic, rerank=rerank)
                result["question"] = question
                st.session_state.chat_entries.append(result)
                st.session_state.chat_entries = st.session_state.chat_entries[-8:]
                st.rerun()
            except (ValueError, RuntimeError, OSError) as exc:
                st.error(f"Could not complete this question: {exc}")
else:
    from v3.ui import render_investigations
    render_investigations()
