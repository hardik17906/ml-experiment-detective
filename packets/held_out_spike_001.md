# Experiment evidence packet

**Question:** Did the held-out error spike and recover?
**Filters:** none
**Retrieval:** cosine similarity using `sentence-transformers/all-MiniLM-L6-v2` at revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`; top 2

These are candidate observations paraphrased from saved run metrics. Similarity scores rank notes; they are not probabilities or causal evidence.
Table values are rounded for display; the linked JSON records retain the saved precision.

## 1. baseline_gap_001

- Similarity: 0.430
- Source note: [notes/baseline_gap_001.md](../notes/baseline_gap_001.md)
- Primary run record: [runs/baseline_gap_001.json](../runs/baseline_gap_001.json)
- Observation: Validation loss rose from 0.8696 at epoch 1 to 1.4186 at epoch 2, then fell to 0.6663 at epoch 3. At epoch 5, post-epoch training loss was 0.8092 and validation loss was 0.8208.

Recorded configuration:

```json
{
  "run_id": "baseline_gap_001",
  "dataset": "FashionMNIST",
  "source_partition": "train",
  "preprocessing": "ToTensor",
  "train_size": 10000,
  "val_size": 2000,
  "split_seed": 42,
  "shuffle_seed": 43,
  "model_seed": 44,
  "batch_size": 128,
  "hidden_units": 128,
  "optimizer": "SGD",
  "learning_rate": 0.1,
  "epochs": 5
}
```

Recorded metrics by epoch (training values are post-epoch measurements when available):

| Epoch | Train loss | Train accuracy | Validation loss | Validation accuracy |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 0.8892 | 66.50% | 0.8696 | 66.35% |
| 2 | 1.3987 | 61.88% | 1.4186 | 61.50% |
| 3 | 0.6898 | 73.87% | 0.6663 | 75.10% |
| 4 | 0.7390 | 72.32% | 0.7384 | 73.10% |
| 5 | 0.8092 | 70.91% | 0.8208 | 71.25% |

## 2. lr_01_seed2

- Similarity: 0.406
- Source note: [notes/lr_01_seed2.md](../notes/lr_01_seed2.md)
- Primary run record: [runs/lr_01_seed2.json](../runs/lr_01_seed2.json)
- Observation: With alternate model and shuffle seeds, validation loss rose from 0.7136 at epoch 3 to 0.8142 at epoch 4, then fell to 0.6793 at epoch 5. Final validation accuracy was 76.35%.

Recorded configuration:

```json
{
  "run_id": "lr_01_seed2",
  "dataset": "FashionMNIST",
  "source_partition": "train",
  "preprocessing": "ToTensor",
  "train_size": 10000,
  "val_size": 2000,
  "split_seed": 42,
  "shuffle_seed": 143,
  "model_seed": 144,
  "batch_size": 128,
  "hidden_units": 128,
  "optimizer": "SGD",
  "learning_rate": 0.1,
  "epochs": 5
}
```

Recorded metrics by epoch (training values are post-epoch measurements when available):

| Epoch | Train loss | Train accuracy | Validation loss | Validation accuracy |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 1.1093 | 63.43% | 1.1125 | 64.15% |
| 2 | 0.9086 | 67.57% | 0.9026 | 67.40% |
| 3 | 0.7325 | 73.59% | 0.7136 | 75.40% |
| 4 | 0.7922 | 73.20% | 0.8142 | 72.05% |
| 5 | 0.6917 | 75.75% | 0.6793 | 76.35% |
