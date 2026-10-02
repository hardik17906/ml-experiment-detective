# Experiment comparison: lr_005_seed3 vs lr_01_seed3

Sources: [lr_005_seed3](../runs/lr_005_seed3.json), [lr_01_seed3](../runs/lr_01_seed3.json)

## Recorded configuration differences

| Setting | lr_005_seed3 | lr_01_seed3 |
| --- | ---: | ---: |
| learning_rate | 0.05 | 0.1 |

**Comparison scope:** One recorded setting differs. This pair isolates it among recorded settings.

## Final metrics (epoch 5)

| Metric | lr_005_seed3 | lr_01_seed3 | Change (second - first) |
| --- | ---: | ---: | ---: |
| Validation loss | 0.6806 | 0.8109 | +0.1303 |
| Validation accuracy | 75.90% | 71.45% | -4.45 pp |

## Final train-validation gaps

Loss gap is validation minus training. Accuracy gap is training minus validation.
Both use the same model after the epoch.

| Run | Loss gap | Accuracy gap |
| --- | ---: | ---: |
| lr_005_seed3 | -0.0123 | -0.56 pp |
| lr_01_seed3 | -0.0023 | +0.17 pp |

## Curve observation

| Run | Largest one-epoch validation-loss increase |
| --- | --- |
| lr_005_seed3 | no increase recorded |
| lr_01_seed3 | epoch 1 to 2: +0.1387 |

## Evidence boundary

These are measurements from the saved run records. They do not identify a cause
or establish how the result behaves across other random seeds.
