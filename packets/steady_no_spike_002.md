# Experiment evidence packet

**Question:** Did the held-out error spike and recover in lr_005_gap_001?
**Filters:** run ID = lr_005_gap_001
**Retrieval:** exact primary run ID `lr_005_gap_001`

This observation paraphrases saved run metrics. Exact run ID selection is not a causal conclusion.
Table values are rounded for display; the linked JSON records retain the saved precision.

## 1. lr_005_gap_001

- Match: exact run ID
- Source note: [notes/lr_005_gap_001.md](../notes/lr_005_gap_001.md)
- Primary run record: [runs/lr_005_gap_001.json](../runs/lr_005_gap_001.json)
- Observation: With learning rate 0.05, validation loss decreased in each of five epochs, from 1.0546 to 0.6876. Final training accuracy was 74.93% and validation accuracy was 75.15%.

Recorded configuration:

```json
{
  "run_id": "lr_005_gap_001",
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
  "learning_rate": 0.05,
  "epochs": 5
}
```

Recorded metrics by epoch (training values are post-epoch measurements when available):

| Epoch | Train loss | Train accuracy | Validation loss | Validation accuracy |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 1.0738 | 64.76% | 1.0546 | 64.90% |
| 2 | 0.9969 | 65.15% | 1.0083 | 65.65% |
| 3 | 0.7941 | 69.30% | 0.7633 | 70.90% |
| 4 | 0.7420 | 73.06% | 0.7394 | 72.70% |
| 5 | 0.6850 | 74.93% | 0.6876 | 75.15% |

Calculated validation-loss patterns (one epoch of increase followed by a decrease):
- None found in the recorded epochs.
