import argparse
import json
from pathlib import Path


parser = argparse.ArgumentParser(description="Find saved ML experiment runs")
parser.add_argument("--learning-rate", type=float)
parser.add_argument("--dropout", type=float)
parser.add_argument("--train-size", type=int)
parser.add_argument("--epochs", type=int)
parser.add_argument("--model-seed", type=int)
parser.add_argument("--shuffle-seed", type=int)
parser.add_argument("--min-val-accuracy", type=float, help="percentage, from 0 to 100")
parser.add_argument("--min-val-loss-rise", type=float)
args = parser.parse_args()

if args.min_val_accuracy is not None and not 0 <= args.min_val_accuracy <= 100:
    parser.error("--min-val-accuracy must be between 0 and 100")
if args.min_val_loss_rise is not None and args.min_val_loss_rise < 0:
    parser.error("--min-val-loss-rise must be nonnegative")

metadata_filters = {
    "learning_rate": args.learning_rate,
    "dropout": args.dropout,
    "train_size": args.train_size,
    "epochs": args.epochs,
    "model_seed": args.model_seed,
    "shuffle_seed": args.shuffle_seed,
}
run_dir = Path(__file__).resolve().parent / "runs"
matches = []
for path in sorted(run_dir.glob("*.json")):
    record = json.loads(path.read_text(encoding="utf-8"))
    config = record["config"]
    if any(
        wanted is not None and config.get(key) != wanted
        for key, wanted in metadata_filters.items()
    ):
        continue

    metrics = record["metrics"]
    if not metrics:
        continue
    final_accuracy = 100 * metrics[-1]["val_accuracy"]
    loss_rises = [
        after["val_loss"] - before["val_loss"]
        for before, after in zip(metrics, metrics[1:])
    ]
    max_loss_rise = max([0.0] + loss_rises)
    if args.min_val_accuracy is not None and final_accuracy < args.min_val_accuracy:
        continue
    if args.min_val_loss_rise is not None and max_loss_rise < args.min_val_loss_rise:
        continue
    matches.append((path.stem, config, final_accuracy, max_loss_rise))

print(f"Matching runs: {len(matches)}")
print(f"{'Run ID':<28} {'LR':>6} {'Dropout':>8} {'Train':>6} {'Epochs':>6} {'Val acc':>8} {'Max loss rise':>13}")
for run_id, config, final_accuracy, max_loss_rise in matches:
    dropout = config.get("dropout", "unknown")
    print(
        f"{run_id:<28} {config['learning_rate']:>6g} {str(dropout):>8} "
        f"{config['train_size']:>6} {config['epochs']:>6} "
        f"{final_accuracy:>7.2f}% {max_loss_rise:>13.4f}"
    )
