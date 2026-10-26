"""Competing mechanisms grounded in an explicit evidence registry."""

from v3.investigation_state import digest, event
from v3.planner import select


def build_evidence(state):
    registry = {}
    for rid, record in state.get("records", {}).items():
        registry[f"RUN:{rid}"] = {"source_type": "EXPERIMENT_JSON", "source": f"runs/{rid}.json",
                                  "sha256": digest(record), "value": record}
    analysis = state.get("analysis", {})
    for i, pair in enumerate(analysis.get("comparisons", []) + analysis.get("seed_pairs", [])):
        registry[f"PAIR:{i}"] = {"source_type": "DERIVED_ANALYSIS", "sources": pair["sources"], "value": pair}
    for item in state.get("knowledge", {}).get("matches", []):
        registry[f"ML:{item['id']}"] = {"source_type": "ML_KNOWLEDGE", "source": item["path"],
                                       "url": item["source_url"], "value": item["text"]}
    all_notes = state.get("notes", {}).get("matches", []) + state.get("notes", {}).get("supplementary_derived_matches", [])
    seen = set()
    for i, item in enumerate(all_notes):
        if item["run_id"] in seen:
            continue
        seen.add(item["run_id"])
        registry[f"NOTE:{i}"] = {"source_type": item["source_type"], "source": item["source"],
                                 "value": item["observation"]}
    state["evidence"] = registry


def generate(state):
    registry = state["evidence"]
    pairs = [(k, v["value"]) for k, v in registry.items() if k.startswith("PAIR:")]
    ml = [k for k in registry if k.startswith("ML:")]
    rate_pairs = [(k, p) for k, p in pairs if set(p["changed_settings"]) == {"learning_rate"} and "rise_delta" in p]
    # All comparisons here are reoriented from lower to higher rate before assigning evidence signs.
    oriented = []
    for key, p in rate_pairs:
        change = p["changed_settings"]["learning_rate"]
        sign = 1 if change["target"] > change["baseline"] else -1
        oriented.append((key, p, sign))
    common = {"source_type": "HYPOTHESIS", "relevant_ml_knowledge": ml,
              "assumptions": ["Recorded configurations and epoch metrics accurately describe the runs."],
              "missing_evidence": ["Independent replication and optimizer-step/gradient measurements are absent."],
              "status": "Inconclusive"}
    def candidate(identifier, statement, support, opposing, missing, test):
        return {**common, "hypothesis_id": identifier, "statement": statement,
                "supporting_experiment_evidence": list(dict.fromkeys(support)),
                "contradicting_experiment_evidence": list(dict.fromkeys(opposing)),
                "missing_evidence": common["missing_evidence"] + missing,
                "proposed_test": test,
                "status": "Consistent with current evidence" if support and not opposing else "Inconclusive"}
    candidates = []
    if oriented:
        candidates.append(candidate("H1", "A higher learning rate may contribute to larger validation-loss rises through unstable optimization.",
            [k for k, p, s in oriented if s * p["rise_delta"] > 0],
            [k for k, p, s in oriented if s * p["rise_delta"] <= 0],
            ["Validation-loss rises cannot directly demonstrate overshooting; gradients and optimizer trajectories were not recorded."],
            "Compare maximum positive consecutive-epoch validation-loss rises under matched new seeds and different learning rates."))
        signs = {1 if s * p["accuracy_delta_pp"] > 0 else -1 if s * p["accuracy_delta_pp"] < 0 else 0 for _, p, s in oriented}
        candidates.append(candidate("H2", "Seed-dependent training variability may contribute to differences in final validation accuracy.",
            [k for k, _, _ in oriented] if len(signs) > 1 else [], [],
            ["A small number of observed seed blocks cannot establish a distribution or separate all sources of randomness."],
            "Repeat a controlled learning-rate comparison under a new shared model/shuffle seed block; predefine accuracy and loss-rise comparisons."))
    else:
        candidates.append(candidate("H1", "Recorded configuration differences or unrecorded conditions may contribute to the observed outcome.",
            [k for k, p in pairs if p["confounded"] or p["missing_controls"]], [],
            ["A fully matched comparison is missing."], "Choose one variable and record all other controls before comparing."))
    run_refs = [key for key in registry if key.startswith("RUN:")]
    candidates.append(candidate("H3", "The short recorded training horizon may leave the final-epoch ranking sensitive to transient behavior.",
        run_refs, [], ["Longer independently approved training and predeclared stopping criteria are unavailable."],
        "Replicate the existing horizon first; consider a separately approved longer-horizon study if ambiguity remains."))
    intervals = [k for k, v in registry.items() if k.startswith("PAIR:") and any(
        c.get("candidate_generalization_intervals") for c in v["value"]["curves"].values())]
    if intervals:
        candidates.append(candidate("H4", "A generalization gap may contribute during intervals where training loss improves and validation loss rises.",
            intervals, [], ["This interval rule is a diagnostic candidate, not proof of overfitting."],
            "Inspect matched train/validation curves and test one regularization change in a separate controlled proposal."))
    ids = [x["hypothesis_id"] for x in candidates]
    def validate(args):
        selected = args["hypothesis_ids"]
        if not isinstance(selected, list) or len(selected) < 2 or len(selected) != len(set(selected)) or set(selected) - set(ids):
            raise ValueError("Choose at least two distinct measured candidate hypotheses")
    choice, origin = select(state, "select_hypotheses",
        "Select and order competing hypotheses for the objective. These are candidate mechanisms, never facts. "
        + str([{k: h[k] for k in ("hypothesis_id", "statement", "supporting_experiment_evidence", "contradicting_experiment_evidence")} for h in candidates]),
        {"hypothesis_ids": {"type": "array", "items": {"type": "string", "enum": ids}, "minItems": 2, "maxItems": len(ids)}},
        {"hypothesis_ids": ids}, validate)
    by_id = {h["hypothesis_id"]: h for h in candidates}
    state["hypotheses"] = [dict(by_id[x], selected_by=origin, statement_origin="PYTHON evidence-conditioned candidate") for x in choice["hypothesis_ids"]]
    state["uncertainties"] = list(dict.fromkeys(state.get("uncertainties", []) + [x for h in state["hypotheses"] for x in h["missing_evidence"]]))
    event(state, "HYPOTHESIS GENERATED", state["hypotheses"], origin)


def validate_evidence(state):
    errors = []
    registry = state["evidence"]
    for h in state["hypotheses"]:
        for field in ("supporting_experiment_evidence", "contradicting_experiment_evidence", "relevant_ml_knowledge"):
            for key in h[field]:
                if key not in registry:
                    errors.append(f"Unknown citation {key}")
                elif field != "relevant_ml_knowledge" and registry[key]["source_type"] == "ML_KNOWLEDGE":
                    errors.append("General knowledge cannot establish an experiment observation")
    for key, evidence in registry.items():
        if evidence["source_type"] == "EXPERIMENT_JSON" and digest(evidence["value"]) != evidence["sha256"]:
            errors.append(f"Evidence changed after collection: {key}")
    if len(state["hypotheses"]) < 2:
        errors.append("Competing hypotheses missing")
    state["evidence_validation"] = {"valid": not errors, "errors": errors,
                                    "unsupported_structured_citations": len(errors),
                                    "scope": "Structured evidence links and recorded snapshots; not a proof of causal mechanisms."}
    event(state, "HYPOTHESIS VALIDATION", state["evidence_validation"])
    return not errors
