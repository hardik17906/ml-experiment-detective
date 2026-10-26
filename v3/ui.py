"""Streamlit investigation workspace; human actions call the service, not an LLM."""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from v3.service import Investigator

EXAMPLE = "Investigate why lr_01_seed3 had worse final validation accuracy than lr_005_seed3. Examine the curves, retrieve relevant ML knowledge, compare possible explanations, and propose a controlled follow-up."


def render_investigations():
    app = Investigator()
    st.title("ML Experiment Detective V3")
    st.caption("Investigate saved evidence, compare explanations, and review controlled follow-ups. Training requires your explicit approval.")
    with st.expander("Start a new investigation", expanded=not bool(app.store.list())):
        with st.form("new_investigation"):
            question = st.text_area("Research question", value=EXAMPLE)
            model = st.checkbox("Use local Ollama for planning and hypothesis selection", value=True)
            semantic = st.checkbox("Use cached MiniLM semantic retrieval", value=True)
            start = st.form_submit_button("Start investigation")
        if start:
            try:
                with st.spinner("Collecting evidence and checking competing explanations..."):
                    state = app.start(question, model_enabled=model, semantic=semantic)
                st.session_state.v3_selected = state["investigation_id"]
                st.rerun()
            except (ValueError, RuntimeError, OSError) as exc:
                st.error(str(exc))
    items = app.store.list()
    if not items:
        st.info("Start an investigation to save its plan, evidence, proposals, and report locally.")
        return
    ids = [x["id"] for x in items]
    if st.session_state.get("v3_selected") not in ids:
        st.session_state.v3_selected = ids[0]
    labels = {x["id"]: f"{x['id']} — {x['status']} — {x['objective'][:70]}" for x in items}
    identifier = st.selectbox("Saved investigations", ids, format_func=lambda x: labels[x], key="v3_selected")
    state = app.store.load(identifier)
    st.write(state["objective"])
    st.write(f"Status: **{state['status']}**")
    if state.get("last_error"):
        st.error(state["last_error"])
    if st.button("Resume saved investigation"):
        try:
            with st.spinner("Resuming saved workflow..."):
                app.resume(identifier)
            st.rerun()
        except (ValueError, PermissionError, RuntimeError, OSError) as exc:
            st.error(str(exc))
    tabs = st.tabs(["Plan", "Evidence and curves", "Hypotheses", "Proposals and approval", "Execution", "Report", "Educational trace"])
    with tabs[0]:
        st.caption("The plan records selected tools, dependencies, status, and who proposed each step.")
        st.dataframe(pd.DataFrame(state.get("plan", [])), hide_index=True, width="stretch")
        st.write("Remaining uncertainties")
        for uncertainty in state.get("uncertainties", []):
            st.write("• " + uncertainty)
    with tabs[1]:
        for rid, record in state.get("records", {}).items():
            with st.expander(rid):
                st.caption(f"EXPERIMENT_JSON: runs/{rid}.json")
                st.json(record["config"])
                data = pd.DataFrame(record["metrics"])
                if "val_loss" in data:
                    losses = [x for x in ("train_loss_after_epoch", "val_loss") if x in data]
                    st.line_chart(data, x="epoch", y=losses)
                if "val_accuracy" in data:
                    data["validation_accuracy_percent"] = data["val_accuracy"] * 100
                    st.line_chart(data, x="epoch", y="validation_accuracy_percent")
                st.dataframe(data, hide_index=True)
        with st.expander("Retrieved notes, knowledge and deterministic comparisons"):
            st.json({k: state.get(k, {}) for k in ("notes", "knowledge", "analysis", "evidence_validation")})
    with tabs[2]:
        for h in state.get("hypotheses", []):
            st.subheader(f"{h['hypothesis_id']}: {h['status']}")
            st.write(h["statement"])
            st.json(h)
        st.caption("A hypothesis status is descriptive. General ML documentation does not establish what caused a particular run.")
    with tabs[3]:
        if not state.get("proposal_id"):
            st.info(state.get("proposal_limitation", "No training proposal was needed for this request."))
        else:
            row = app.store.proposal(state["proposal_id"])
            st.write(f"Proposal **{row['id']}** — **{row['status']}**")
            st.code(row["hash"], language=None)
            st.json(row["payload"])
            if row["status"] in {"pending", "approved", "rejected", "deferred", "failed", "interrupted"}:
                st.caption("Dry runs validate the execution path without training. Live approval authorizes this exact two-run configuration for up to 600 seconds total.")
                live = st.checkbox("I explicitly authorize live training for this exact proposal", key=f"live_{identifier}")
                columns = st.columns(3)
                actions = [("Approve and train" if live else "Approve dry run", "approved"), ("Reject proposal", "rejected"), ("Defer proposal", "deferred")]
                for column, (label, decision) in zip(columns, actions):
                    if column.button(label, key=f"{decision}_{identifier}"):
                        try:
                            with st.spinner("Applying your decision..."):
                                app.decide(identifier, row["hash"], decision, mode="live" if live else "dry_run")
                            st.rerun()
                        except (ValueError, PermissionError, RuntimeError, OSError) as exc:
                            st.error(str(exc))
                with st.expander("Modify proposal parameters"):
                    st.caption("Saving a change validates the entire proposal and invalidates previous approval.")
                    payload = st.text_area("Proposal JSON", value=json.dumps(row["payload"], indent=2), key=f"edit_{identifier}", height=300)
                    if st.button("Validate and save modification", key=f"modify_{identifier}"):
                        try:
                            app.modify(identifier, json.loads(payload))
                            st.rerun()
                        except (ValueError, PermissionError, RuntimeError, OSError) as exc:
                            st.error(str(exc))
            st.json(app.store.decisions(row["id"]))
    with tabs[4]:
        st.json(state.get("execution", {"status": "No execution"}))
        if state.get("outcome"):
            st.json(state["outcome"])
        for log in state.get("execution", {}).get("logs", []):
            path = Path(log)
            if path.is_file():
                with st.expander(path.name):
                    st.code(path.read_text(encoding="utf-8", errors="replace")[-20000:])
        if state.get("execution", {}).get("status") == "dry_run_completed":
            st.info("No trainer ran and no new metric values were generated.")
    with tabs[5]:
        report = state.get("report", "") or state.get("answer", "")
        st.markdown(report)
        st.download_button("Download investigation report", report, file_name=f"{identifier}.md", mime="text/markdown")
        if st.button("Save report locally"):
            st.success(str(app.export(identifier)))
    with tabs[6]:
        for i, e in enumerate(state.get("trace", [])):
            with st.expander(f"{i + 1}. {e['kind']} — {e.get('origin', 'V2 trace')}"):
                st.json(e["data"])
