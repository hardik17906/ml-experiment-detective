import argparse
import json
import re
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("first_run")
parser.add_argument("second_run")
args = parser.parse_args()

run_dir = Path(__file__).resolve().parent / "runs"
records = []
for run_id in (args.first_run, args.second_run):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        parser.error(f"invalid run ID: {run_id}")
    path = run_dir / f"{run_id}.json"
    if not path.exists():
        parser.error(f"run record not found: {path}")
    records.append(json.loads(path.read_text(encoding="utf-8")))

first, second = records
print(f"Comparing {args.first_run} -> {args.second_run}")
print("Changed settings:")
all_keys = sorted(set(first["config"]) | set(second["config"]))
changes = [
    key for key in all_keys
    if key != "run_id" and first["config"].get(key) != second["config"].get(key)
]
for key in changes:
    print(f"  {key}: {first['config'].get(key)} -> {second['config'].get(key)}")
if not changes:
    print("  none recorded")
if len(changes) == 1:
    scope = "One recorded setting differs. This pair isolates it among recorded settings."
elif len(changes) > 1:
    scope = "Multiple recorded settings differ; no single setting is isolated."
else:
    scope = "No recorded settings differ."
print("Comparison scope:", scope)

first_final = first["metrics"][-1]
second_final = second["metrics"][-1]
if first_final["epoch"] != second_final["epoch"]:
    parser.error("final metrics are from different epoch numbers")

loss_change = second_final["val_loss"] - first_final["val_loss"]
accuracy_change = 100 * (second_final["val_accuracy"] - first_final["val_accuracy"])
print(f"Final epoch: {first_final['epoch']}")
print(
    f"Validation loss: {first_final['val_loss']:.4f} -> "
    f"{second_final['val_loss']:.4f} ({loss_change:+.4f})"
)
print(
    f"Validation accuracy: {100 * first_final['val_accuracy']:.2f}% -> "
    f"{100 * second_final['val_accuracy']:.2f}% "
    f"({accuracy_change:+.2f} percentage points)"
)

print("Final train-validation gaps (same model after the epoch):")
gap_rows = []
for run_id, final in ((args.first_run, first_final), (args.second_run, second_final)):
    if "train_loss_after_epoch" not in final or "train_accuracy_after_epoch" not in final:
        print(f"  {run_id}: unavailable; post-epoch training metrics were not saved")
        gap_rows.append((run_id, "unavailable", "unavailable"))
        continue
    loss_gap = final["val_loss"] - final["train_loss_after_epoch"]
    accuracy_gap = 100 * (final["train_accuracy_after_epoch"] - final["val_accuracy"])
    gap_rows.append((run_id, f"{loss_gap:+.4f}", f"{accuracy_gap:+.2f} pp"))
    print(
        f"  {run_id}: loss gap (val - train) = {loss_gap:+.4f}, "
        f"accuracy gap (train - val) = {accuracy_gap:+.2f} percentage points"
    )

print("Largest one-epoch validation-loss increase:")
rise_rows = []
for run_id, record in ((args.first_run, first), (args.second_run, second)):
    rises = []
    metrics = record["metrics"]
    for before, after in zip(metrics, metrics[1:]):
        if after["epoch"] != before["epoch"] + 1:
            parser.error(f"nonconsecutive epochs in {run_id}")
        change = after["val_loss"] - before["val_loss"]
        if change > 0:
            rises.append((change, before["epoch"], after["epoch"]))
    if rises:
        change, start_epoch, end_epoch = max(rises)
        print(f"  {run_id}: epoch {start_epoch} -> {end_epoch}, +{change:.4f}")
        rise_rows.append((run_id, f"epoch {start_epoch} to {end_epoch}: +{change:.4f}"))
    else:
        print(f"  {run_id}: no increase recorded")
        rise_rows.append((run_id, "no increase recorded"))

report_lines = [
    f"# Experiment comparison: {args.first_run} vs {args.second_run}",
    "",
    f"Sources: [{args.first_run}](../runs/{args.first_run}.json), "
    f"[{args.second_run}](../runs/{args.second_run}.json)",
    "",
    "## Recorded configuration differences",
    "",
    f"| Setting | {args.first_run} | {args.second_run} |",
    "| --- | ---: | ---: |",
]
for key in changes:
    report_lines.append(
        f"| {key} | {first['config'].get(key)} | {second['config'].get(key)} |"
    )
if not changes:
    report_lines.append("| None recorded | - | - |")
report_lines += [
    "",
    f"**Comparison scope:** {scope}",
    "",
    f"## Final metrics (epoch {first_final['epoch']})",
    "",
    f"| Metric | {args.first_run} | {args.second_run} | Change (second - first) |",
    "| --- | ---: | ---: | ---: |",
    f"| Validation loss | {first_final['val_loss']:.4f} | "
    f"{second_final['val_loss']:.4f} | {loss_change:+.4f} |",
    f"| Validation accuracy | {100 * first_final['val_accuracy']:.2f}% | "
    f"{100 * second_final['val_accuracy']:.2f}% | {accuracy_change:+.2f} pp |",
    "",
    "## Final train-validation gaps",
    "",
    "Loss gap is validation minus training. Accuracy gap is training minus validation.",
    "Both use the same model after the epoch.",
    "",
    "| Run | Loss gap | Accuracy gap |",
    "| --- | ---: | ---: |",
]
for run_id, loss_gap, accuracy_gap in gap_rows:
    report_lines.append(f"| {run_id} | {loss_gap} | {accuracy_gap} |")
report_lines += [
    "",
    "## Curve observation",
    "",
    "| Run | Largest one-epoch validation-loss increase |",
    "| --- | --- |",
]
for run_id, rise in rise_rows:
    report_lines.append(f"| {run_id} | {rise} |")
report_lines += [
    "",
    "## Evidence boundary",
    "",
    "These are measurements from the saved run records. They do not identify a cause",
    "or establish how the result behaves across other random seeds.",
]

report_dir = Path(__file__).resolve().parent / "reports"
report_dir.mkdir(exist_ok=True)
report_path = report_dir / f"{args.first_run}_vs_{args.second_run}.md"
report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
print("Saved report:", report_path)
