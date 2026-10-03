"""Source-aware final text. Only successful Python tool results supply numbers."""


def render_answer(question: str, tool_results: list[tuple[str, dict]]) -> str:
    by_name = {}
    for name, result in tool_results:
        by_name.setdefault(name, []).append(result)
    observations = []
    experiment_sources = set()
    knowledge_sources = {}

    for result in by_name.get("compare_experiments", []):
        changes = ", ".join(
            f"{key}: {values['baseline']} -> {values['target']}"
            for key, values in result["changed_settings"].items()
        ) or "none recorded"
        observations.append(
            f"- **{result['baseline_run_id']} -> {result['target_run_id']}** at epoch {result['final_epoch']}: "
            f"validation accuracy {result['baseline_validation_accuracy_percent']:.2f}% -> "
            f"{result['target_validation_accuracy_percent']:.2f}% "
            f"({result['accuracy_change_target_minus_baseline_pp']:+.2f} percentage points); "
            f"validation loss {result['baseline_validation_loss']:.4f} -> "
            f"{result['target_validation_loss']:.4f} "
            f"({result['loss_change_target_minus_baseline']:+.4f}). "
            f"Changed recorded settings: {changes}."
        )
        experiment_sources.update((result["baseline_source"], result["target_source"]))

    inspections = {item["run_id"]: item for item in by_name.get("get_experiment", [])}
    for search in by_name.get("search_notes", []):
        for match in search["matches"]:
            record = inspections.get(match["run_id"])
            if record is None:
                continue
            observations.append(
                f"- **{match['run_id']}** (note rank {match['final_rank']}, "
                f"cosine {match['cosine_similarity']:.4f}): {match['observation']}"
            )
            for pattern in record["validation_loss_recoveries"]:
                epochs, losses = pattern["epochs"], pattern["losses"]
                observations.append(
                    f"  - Saved validation loss, epochs {epochs[0]}->{epochs[1]}->{epochs[2]}: "
                    f"{losses[0]:.4f} -> {losses[1]:.4f} -> {losses[2]:.4f}."
                )
            experiment_sources.update((match["note_source"], record["source"]))
    noted_ids = {
        match["run_id"] for result in by_name.get("search_notes", []) for match in result["matches"]
    }
    compared_ids = {
        run_id for result in by_name.get("compare_experiments", [])
        for run_id in (result["baseline_run_id"], result["target_run_id"])
    }
    for run_id, result in inspections.items():
        if run_id in noted_ids or run_id in compared_ids:
            continue
        observations.append(
            f"- **{run_id}**: final validation accuracy {result['final_validation_accuracy_percent']:.2f}% "
            f"and loss {result['final_validation_loss']:.4f} at epoch {result['final_epoch']}."
        )
        experiment_sources.add(result["source"])

    for result in by_name.get("search_runs", []):
        matches = result["matches"]
        filter_text = ", ".join(f"{k}={v}" for k, v in result["filters"].items()) or "all saved records"
        if "worst" in question.lower() and matches:
            worst = min(matches, key=lambda row: row["final_validation_accuracy_percent"])
            observations.append(
                f"- Among {len(matches)} saved records matching {filter_text}, "
                f"**{worst['run_id']}** has the lowest final validation accuracy: "
                f"{worst['final_validation_accuracy_percent']:.2f}% at epoch {worst['final_epoch']}."
            )
        else:
            observations.append(f"- {len(matches)} saved records match {filter_text}.")
            for row in matches:
                observations.append(
                    f"  - {row['run_id']}: final validation accuracy "
                    f"{row['final_validation_accuracy_percent']:.2f}% at epoch {row['final_epoch']}."
                )
        experiment_sources.update(item["source"] for item in matches)

    for result in by_name.get("summarize_run_curve", []):
        observations.append(
            f"- **{result['run_id']} curve**: final accuracy {result['final_validation_accuracy_percent']:.2f}%; "
            f"best accuracy {result['best_validation_accuracy_percent']:.2f}% at epoch {result['best_accuracy_epoch']}; "
            f"minimum validation loss {result['minimum_validation_loss']:.4f} at epoch {result['minimum_loss_epoch']}; "
            f"largest one-epoch loss rise {result['largest_one_epoch_validation_loss_rise']:.4f}. "
            f"Rise-then-fall patterns: {len(result['validation_loss_recoveries'])}."
        )
        experiment_sources.add(result["source"])

    for result in by_name.get("find_overfitting_candidates", []):
        observations.append(
            f"- **{len(result['matches'])} possible overfitting candidate records** by this rule: "
            f"{result['rule']}."
        )
        for match in result["matches"]:
            first = match["intervals"][0]
            observations.append(
                f"  - {match['run_id']}, epochs {first['epochs'][0]}->{first['epochs'][1]}: "
                f"training loss {first['train_loss'][0]:.4f}->{first['train_loss'][1]:.4f}; "
                f"validation loss {first['validation_loss'][0]:.4f}->{first['validation_loss'][1]:.4f}."
            )
            experiment_sources.add(match["source"])

    for result in by_name.get("compare_run_group", []):
        for rate, group in result["groups"].items():
            mean = f"{group['mean_validation_accuracy_percent']}%" if group['count'] else "n/a"
            median = f"{group['median_validation_accuracy_percent']}%" if group['count'] else "n/a"
            observations.append(
                f"- Learning rate {rate}: {group['count']} saved records; "
                f"mean final validation accuracy {mean}; median {median}."
            )
            experiment_sources.update(row["source"] for row in group["runs"])

    for result in by_name.get("plot_run_metrics", []):
        observations.append(
            f"- **{result['run_id']}** has {len(result['points'])} saved epoch points for "
            "post-epoch training loss, validation loss, and validation accuracy. "
            "Select the run in the UI to view the chart."
        )
        experiment_sources.add(result["source"])

    knowledge = []
    for result in by_name.get("search_ml_knowledge", []):
        for match in result["matches"]:
            if match["source_url"] in knowledge_sources:
                continue
            knowledge.append(
                f"- **{match['source_title']}** ({match['topic']}): {match['text']}"
            )
            knowledge_sources[match["source_url"]] = match["source_title"]

    sections = []
    if observations:
        sections.append("### Observed experiment facts\n" + "\n".join(observations))
    if knowledge:
        sections.append("### Relevant ML knowledge\n" + "\n".join(knowledge))
    if observations and knowledge:
        sections.append(
            "### Possible interpretation\nThe observed pattern is compatible with one or more general "
            "mechanisms described above. The saved runs do not establish which mechanism, if any, caused it."
        )
    limits = []
    if any(name in {"search_notes", "search_ml_knowledge"} for name, _ in tool_results):
        limits.append("A similarity or reranker score ranks text; it is not a probability or proof.")
    if any(name == "find_overfitting_candidates" for name, _ in tool_results):
        limits.append("The overfitting flag is a descriptive heuristic, not a diagnosis.")
    if any(name in {"compare_experiments", "compare_run_group", "search_runs"} for name, _ in tool_results):
        limits.append("Saved records can repeat configurations or differ in other settings; differences do not prove causation.")
    if limits:
        sections.append("### Limitations\n" + "\n".join(f"- {line}" for line in limits))
    source_lines = []
    if experiment_sources:
        source_lines.append("**Experiment records and notes**")
        source_lines.extend(f"- [{path}]({path})" for path in sorted(experiment_sources))
    if knowledge_sources:
        source_lines.append("**General ML references**")
        source_lines.extend(f"- [{title}]({url})" for url, title in knowledge_sources.items())
    if source_lines:
        sections.append("### Sources\n" + "\n".join(source_lines))
    if not observations and not knowledge:
        sections.insert(0, "No successful evidence tool result was collected.")
    return "\n\n".join(sections)
