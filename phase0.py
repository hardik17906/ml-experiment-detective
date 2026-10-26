import argparse
import json
import math
import re
import time
from pathlib import Path

import torch
from torch import nn
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, Subset


class SimpleMLP(nn.Module):
    def __init__(self, hidden_units, dropout):
        super().__init__()
        self.hidden = nn.Linear(28 * 28, hidden_units)
        self.output = nn.Linear(hidden_units, 10)
        self.dropout = nn.Dropout(dropout)

    def forward(self, images):
        pixels = images.flatten(start_dim=1)
        hidden = torch.relu(self.hidden(pixels))
        hidden = self.dropout(hidden)
        return self.output(hidden)


def evaluate(model, loader, loss_fn):
    model.eval()
    total_loss = 0.0
    correct_predictions = 0
    with torch.no_grad():
        for images, labels in loader:
            logits = model(images)
            loss = loss_fn(logits, labels)
            total_loss += loss.item() * len(labels)
            correct_predictions += (logits.argmax(dim=1) == labels).sum().item()
    count = len(loader.dataset)
    return total_loss / count, correct_predictions / count


def run_training(config, output_path, *, download=True, provenance=None, max_seconds=None):
    started = time.monotonic()
    # Convert images into PyTorch tensors
    transform = transforms.ToTensor()

    # Download Fashion-MNIST training data
    dataset = datasets.FashionMNIST(
        root=str(Path(__file__).resolve().parent / "data"),
        train=True,
        download=download,
        transform=transform
    )

    # Make the random selection reproducible
    generator = torch.Generator().manual_seed(config["split_seed"])

    # Generate a random ordering of all 60,000 image indices
    indices = torch.randperm(len(dataset), generator=generator)

    # Use the requested number from the fixed training pool
    train_indices = indices[:config["train_size"]]

    # Keep validation images fixed when the training subset size changes
    val_indices = indices[
        config["validation_start"]:config["validation_start"] + config["val_size"]
    ]

    # Create subsets using those indices
    train_dataset = Subset(dataset, train_indices)
    val_dataset = Subset(dataset, val_indices)

    # Keep the training shuffle reproducible and separate from the data split
    shuffle_generator = torch.Generator().manual_seed(config["shuffle_seed"])
    train_loader = DataLoader(
        train_dataset, batch_size=config["batch_size"], shuffle=True,
        generator=shuffle_generator
    )
    train_eval_loader = DataLoader(
        train_dataset, batch_size=config["batch_size"], shuffle=False
    )
    val_loader = DataLoader(val_dataset, batch_size=config["batch_size"], shuffle=False)

    torch.manual_seed(config["model_seed"])
    model = SimpleMLP(config["hidden_units"], config["dropout"])
    loss_fn = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=config["learning_rate"])

    print("Training images:", len(train_dataset))
    print("Validation images:", len(val_dataset))
    print("First 5 training indices:", train_indices[:5].tolist())
    print("Training batches per epoch:", len(train_loader))

    history = []
    for epoch in range(1, config["epochs"] + 1):
        model.train()
        total_loss = 0.0
        for images, labels in train_loader:
            if max_seconds is not None and time.monotonic() - started > max_seconds:
                raise TimeoutError("Approved training runtime exceeded")
            logits = model(images)
            loss = loss_fn(logits, labels)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(labels)
        average_train_loss = total_loss / len(train_dataset)

        train_eval_loss, train_eval_accuracy = evaluate(model, train_eval_loader, loss_fn)
        average_val_loss, val_accuracy = evaluate(model, val_loader, loss_fn)
        history.append({
            "epoch": epoch,
            "train_loss_during_epoch": average_train_loss,
            "train_loss_after_epoch": train_eval_loss,
            "train_accuracy_after_epoch": train_eval_accuracy,
            "val_loss": average_val_loss,
            "val_accuracy": val_accuracy,
        })

        print(
            f"Epoch {epoch}: train loss during = {average_train_loss:.4f}, "
            f"train loss after = {train_eval_loss:.4f}, val loss = {average_val_loss:.4f}, "
            f"train accuracy = {100 * train_eval_accuracy:.2f}%, "
            f"val accuracy = {100 * val_accuracy:.2f}%"
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    record = {"config": config, "metrics": history}
    if provenance is not None:
        record["provenance"] = provenance
    with output_path.open("x", encoding="utf-8") as output:
        json.dump(record, output, indent=2)
        output.write("\n")
    print("Saved run record:", output_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--learning-rate", type=float, default=0.1)
    parser.add_argument("--shuffle-seed", type=int, default=43)
    parser.add_argument("--model-seed", type=int, default=44)
    parser.add_argument("--train-size", type=int, default=10000)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--dropout", type=float, default=0.0)
    parser.add_argument("--dry-run", action="store_true", help="print configuration without training")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.run_id):
        parser.error("--run-id must use letters, digits, underscores, or hyphens")
    if not math.isfinite(args.learning_rate) or args.learning_rate <= 0:
        parser.error("--learning-rate must be positive")
    if not 1 <= args.train_size <= 10000:
        parser.error("--train-size must be between 1 and 10000")
    if args.epochs < 1:
        parser.error("--epochs must be positive")
    if not math.isfinite(args.dropout) or not 0 <= args.dropout < 1:
        parser.error("--dropout must be between 0 and 1, excluding 1")

    config = {
        "run_id": args.run_id,
        "dataset": "FashionMNIST",
        "source_partition": "train",
        "preprocessing": "ToTensor",
        "train_size": args.train_size,
        "val_size": 2000,
        "validation_start": 10000,
        "split_seed": 42,
        "shuffle_seed": args.shuffle_seed,
        "model_seed": args.model_seed,
        "batch_size": 128,
        "hidden_units": 128,
        "dropout": args.dropout,
        "optimizer": "SGD",
        "learning_rate": args.learning_rate,
        "epochs": args.epochs,
    }

    output_dir = Path(__file__).resolve().parent / "runs"
    output_path = output_dir / f"{config['run_id']}.json"
    if output_path.exists():
        parser.error(f"run record already exists: {output_path}")
    if args.dry_run:
        print(json.dumps(config, indent=2))
        print("Run record would be:", output_path)
        raise SystemExit(0)

    run_training(config, output_path)


if __name__ == "__main__":
    main()
