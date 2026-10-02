import argparse
import json
import re

from note_retrieval import (
    MODEL_ID,
    MODEL_REVISION,
    PROJECT_DIR,
    encode_queries_and_notes,
    filter_notes,
    load_notes,
    semantic_rank,
)


def percent(value):
    return "n/a" if value is None else f"{100 * value:.2f}%"


def loss(value):
    return "n/a" if value is None else f"{value:.4f}"


def rise_then_fall(metrics):
    patterns = []
    for before, peak, after in zip(metrics, metrics[1:], metrics[2:]):
        if before["val_loss"] < peak["val_loss"] > after["val_loss"]:
            patterns.append(
                f"epoch {before['epoch']} {loss(before['val_loss'])} → "
                f"epoch {peak['epoch']} {loss(peak['val_loss'])} → "
                f"epoch {after['epoch']} {loss(after['val_loss'])}; "
                f"below the pre-rise value: {'yes' if after['val_loss'] < before['val_loss'] else 'no'}"
            )
    return patterns


parser = argparse.ArgumentParser(description="Save source-backed context for an experiment question")
parser.add_argument("query")
parser.add_argument("--packet-id", required=True, help="filename under packets/, without .md")
parser.add_argument("--top-k", type=int, default=2)
parser.add_argument("--dropout", type=float)
parser.add_argument("--train-size", type=int)
parser.add_argument("--run-id", help="exact primary run ID of a note")
args = parser.parse_args()

if not args.query.strip():
    parser.error("query must not be empty")
if not re.fullmatch(r"[a-z0-9_-]+", args.packet_id):
    parser.error("--packet-id must use lowercase letters, numbers, underscores, or hyphens")
if args.top_k < 1:
    parser.error("--top-k must be at least 1")
if args.run_id is not None and not re.fullmatch(r"[a-z0-9_-]+", args.run_id):
    parser.error("--run-id must use lowercase letters, numbers, underscores, or hyphens")

packet_path = PROJECT_DIR / "packets" / f"{args.packet_id}.md"
if packet_path.exists():
    parser.error(f"packet already exists: {packet_path}")

notes = filter_notes(
    load_notes(), dropout=args.dropout, train_size=args.train_size, run_id=args.run_id
)
if not notes:
    parser.error("no notes satisfy the filters")

if args.run_id is not None:
    selected = [(None, path, observation) for path, observation in notes]
    retrieval = f"exact primary run ID `{args.run_id}`"
else:
    embeddings = encode_queries_and_notes([args.query], notes)
    selected = semantic_rank(embeddings[0], embeddings[1:], notes)[: args.top_k]
    retrieval = (
        f"cosine similarity using `{MODEL_ID}` at revision `{MODEL_REVISION}`; top {args.top_k}"
    )
filters = []
if args.dropout is not None:
    filters.append(f"dropout = {args.dropout:g}")
if args.train_size is not None:
    filters.append(f"train size = {args.train_size}")
if args.run_id is not None:
    filters.append(f"run ID = {args.run_id}")

lines = [
    "# Experiment evidence packet",
    "",
    f"**Question:** {args.query}",
    f"**Filters:** {', '.join(filters) if filters else 'none'}",
    f"**Retrieval:** {retrieval}",
    "",
    (
        "This observation paraphrases saved run metrics. Exact run ID selection is not a causal conclusion."
        if args.run_id is not None
        else "These are candidate observations paraphrased from saved run metrics. Similarity scores rank notes; they are not probabilities or causal evidence."
    ),
    "Table values are rounded for display; the linked JSON records retain the saved precision.",
]

for rank, (score, note_path, observation) in enumerate(selected, start=1):
    run_path = PROJECT_DIR / "runs" / f"{note_path.stem}.json"
    record = json.loads(run_path.read_text(encoding="utf-8"))
    lines.extend(
        [
            "",
            f"## {rank}. {note_path.stem}",
            "",
            f"- Similarity: {score:.3f}" if score is not None else "- Match: exact run ID",
            f"- Source note: [notes/{note_path.name}](../notes/{note_path.name})",
            f"- Primary run record: [runs/{run_path.name}](../runs/{run_path.name})",
            f"- Observation: {observation}",
            "",
            "Recorded configuration:",
            "",
            "```json",
            json.dumps(record["config"], indent=2),
            "```",
            "",
            "Recorded metrics by epoch (training values are post-epoch measurements when available):",
            "",
            "| Epoch | Train loss | Train accuracy | Validation loss | Validation accuracy |",
            "| ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for metric in record["metrics"]:
        lines.append(
            f"| {metric['epoch']} | {loss(metric.get('train_loss_after_epoch'))} "
            f"| {percent(metric.get('train_accuracy_after_epoch'))} "
            f"| {loss(metric['val_loss'])} | {percent(metric['val_accuracy'])} |"
        )
    lines.extend(["", "Calculated validation-loss patterns (one epoch of increase followed by a decrease):"])
    patterns = rise_then_fall(record["metrics"])
    lines.extend(f"- {pattern}" for pattern in patterns)
    if not patterns:
        lines.append("- None found in the recorded epochs.")

packet_path.parent.mkdir(parents=True, exist_ok=True)
with packet_path.open("x", encoding="utf-8") as packet_file:
    packet_file.write("\n".join(lines) + "\n")

print(f"Saved: {packet_path}")
print(f"Question: {args.query}")
print(f"Candidate notes: {len(selected)}")
for score, note_path, _ in selected:
    match_detail = f"cosine similarity {score:.3f}" if score is not None else "exact run ID"
    print(f"  {note_path.stem}: {match_detail}")
