import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


run_dir = Path(__file__).resolve().parent / "runs"
run_ids = ("lr_gap_001", "lr_005_gap_001", "baseline_gap_001")
records = [json.loads((run_dir / f"{run_id}.json").read_text(encoding="utf-8"))
           for run_id in run_ids]

reference = records[0]["config"]
for record in records[1:]:
    changed = {key for key in reference if reference[key] != record["config"][key]}
    if changed - {"run_id", "learning_rate"}:
        raise ValueError(f"Runs are not comparable: {sorted(changed)}")

fig, ax = plt.subplots(figsize=(7, 4))
for record in records:
    epochs = [row["epoch"] for row in record["metrics"]]
    losses = [row["val_loss"] for row in record["metrics"]]
    learning_rate = record["config"]["learning_rate"]
    ax.plot(epochs, losses, marker="o", label=f"learning rate {learning_rate:g}")

ax.set_title(
    "Fashion-MNIST validation loss\n"
    f"split seed {reference['split_seed']}, shuffle seed {reference['shuffle_seed']}, "
    f"model seed {reference['model_seed']}"
)
ax.set_xlabel("Epoch")
ax.set_ylabel("Cross-entropy loss")
ax.set_xticks(epochs)
ax.grid(alpha=0.25)
ax.legend()
fig.tight_layout()

output_path = run_dir / "validation_loss_seed1.png"
fig.savefig(output_path, dpi=160)
plt.close(fig)
print("Plotted runs:", ", ".join(run_ids))
print("Saved plot:", output_path)
