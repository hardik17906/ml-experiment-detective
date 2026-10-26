"""Small local learning UI for the V2 Experiment Detective."""

import re

import pandas as pd
import streamlit as st

from experiment_data import RUNS_DIR, get_experiment
from v2_agent import run_manual
from v2_analysis import plot_run_metrics
from v2_state import SessionState


st.set_page_config(page_title="ML Experiment Detective V3", page_icon="🔎", layout="wide")


def display_answer(text: str) -> str:
    """Show local file paths as paths, since Streamlit cannot serve them as links."""
    return re.sub(r"\[([^\]]+)\]\(((?:runs|notes)/[^)]+)\)", r"`\2`", text)


def render_v2():
    if "detective_session" not in st.session_state:
        st.session_state.detective_session = SessionState()
    if "chat_entries" not in st.session_state:
        st.session_state.chat_entries = []

    run_ids = sorted(path.stem for path in RUNS_DIR.glob("*.json"))
    with st.sidebar:
        st.title("Experiment Detective")
        st.caption("Local V2 learning interface")
        st.metric("Saved run records", len(run_ids))
        mode = st.radio("Agent", ("manual", "graph", "simple"), help="Both modes use the same Python tools.")
        rerank = st.checkbox("Optional cross-encoder reranking", value=False,
                            help="Hybrid order is the default. The reranker can make some searches worse.")
        selected = st.selectbox("Inspect a saved run", run_ids, index=run_ids.index("lr_01_seed3") if "lr_01_seed3" in run_ids else 0)
        chosen = get_experiment(selected)
        st.caption("Selected run settings")
        st.json({key: chosen["config"].get(key) for key in
                 ("learning_rate", "train_size", "epochs", "batch_size", "dropout", "split_seed", "shuffle_seed", "model_seed")})
        st.markdown("**Try asking**")
        st.caption("Have we seen unstable validation behavior before?\n\nCompare that run with lr_005_seed3.\n\nWhy might a high learning rate create unstable training?")
        if st.button("Clear conversation", width="stretch"):
            st.session_state.detective_session.clear()
            st.session_state.chat_entries = []
            st.rerun()

    st.title("ML Experiment Detective V2")
    st.caption("Ask about saved runs and general ML ideas. Expand a response to see memory, tool calls, retrieval stages, and sources.")

    for entry in st.session_state.chat_entries:
        with st.chat_message("user"):
            st.write(entry["question"])
        with st.chat_message("assistant"):
            st.markdown(display_answer(entry["answer"]))
            with st.expander("How did the agent answer this?"):
                for event in entry["trace"]:
                    if event["kind"] == "FINAL":
                        continue
                    st.markdown(f"**{event['kind']}**")
                    st.json(event["data"])

    question = st.chat_input("Ask about an experiment or a possible ML mechanism")
    if question:
        try:
            with st.spinner("Inspecting saved evidence..."):
                if mode == "simple":
                    from simple_agent import answer_question
                    result = {"answer": answer_question(question, trace=False), "trace": []}
                elif mode == "manual":
                    result = run_manual(question, st.session_state.detective_session, rerank=rerank)
                else:
                    from graph_agent import run_graph

                    result = run_graph(question, st.session_state.detective_session, rerank=rerank)
            st.session_state.chat_entries.append({
                "question": question, "answer": result["answer"], "trace": result["trace"],
            })
            st.rerun()
        except (OSError, ValueError, RuntimeError) as exc:
            st.error(f"Could not answer: {exc}")

    st.divider()
    st.subheader(f"Run detail: {selected}")
    st.caption(f"Exact source: runs/{selected}.json")
    left, right = st.columns(2)
    with left:
        st.metric("Final validation accuracy", f"{chosen['final_validation_accuracy_percent']:.2f}%")
    with right:
        st.metric("Final validation loss", f"{chosen['final_validation_loss']:.4f}")
    points = pd.DataFrame(plot_run_metrics(selected)["points"])
    tab_curve, tab_table, tab_memory = st.tabs(("Training and validation curves", "Epoch table", "Current session memory"))
    with tab_curve:
        st.line_chart(points, x="epoch", y=["train_loss", "validation_loss"])
        st.line_chart(points, x="epoch", y="validation_accuracy_percent")
        st.caption("Training loss is measured after each epoch. Accuracy is shown in percent on a separate chart.")
    with tab_table:
        st.dataframe(points, hide_index=True, width="stretch")
    with tab_memory:
        st.json(st.session_state.detective_session.snapshot())


area = st.sidebar.radio("Workspace", ("Investigations (V3)", "Chat and runs (V1/V2)"))
if area == "Investigations (V3)":
    from v3.ui import render_investigations
    render_investigations()
else:
    render_v2()
