# Experiment comparison: lr_005_gap_001 vs lr_01_seed2

Sources: [lr_005_gap_001](../runs/lr_005_gap_001.json), [lr_01_seed2](../runs/lr_01_seed2.json)

## Recorded configuration differences

| Setting | lr_005_gap_001 | lr_01_seed2 |
| --- | ---: | ---: |
| learning_rate | 0.05 | 0.1 |
| model_seed | 44 | 144 |
| shuffle_seed | 43 | 143 |

**Comparison scope:** Multiple recorded settings differ; no single setting is isolated.

## Final metrics (epoch 5)

| Metric | lr_005_gap_001 | lr_01_seed2 | Change (second - first) |
| --- | ---: | ---: | ---: |
| Validation loss | 0.6876 | 0.6793 | -0.0083 |
| Validation accuracy | 75.15% | 76.35% | +1.20 pp |

## Final train-validation gaps

Loss gap is validation minus training. Accuracy gap is training minus validation.
Both use the same model after the epoch.

| Run | Loss gap | Accuracy gap |
| --- | ---: | ---: |
| lr_005_gap_001 | +0.0026 | -0.22 pp |
| lr_01_seed2 | -0.0124 | -0.60 pp |

## Curve observation

| Run | Largest one-epoch validation-loss increase |
| --- | --- |
| lr_005_gap_001 | no increase recorded |
| lr_01_seed2 | epoch 3 to 4: +0.1005 |

## Evidence boundary

These are measurements from the saved run records. They do not identify a cause
or establish how the result behaves across other random seeds.
