# Experiment comparison: lr_001 vs baseline_001

Sources: [lr_001](../runs/lr_001.json), [baseline_001](../runs/baseline_001.json)

## Recorded configuration differences

| Setting | lr_001 | baseline_001 |
| --- | ---: | ---: |
| learning_rate | 0.01 | 0.1 |

**Comparison scope:** One recorded setting differs. This pair isolates it among recorded settings.

## Final metrics (epoch 5)

| Metric | lr_001 | baseline_001 | Change (second - first) |
| --- | ---: | ---: | ---: |
| Validation loss | 1.0304 | 0.8208 | -0.2096 |
| Validation accuracy | 66.40% | 71.25% | +4.85 pp |

## Final train-validation gaps

Loss gap is validation minus training. Accuracy gap is training minus validation.
Both use the same model after the epoch.

| Run | Loss gap | Accuracy gap |
| --- | ---: | ---: |
| lr_001 | unavailable | unavailable |
| baseline_001 | unavailable | unavailable |

## Curve observation

| Run | Largest one-epoch validation-loss increase |
| --- | --- |
| lr_001 | no increase recorded |
| baseline_001 | epoch 1 to 2: +0.5489 |

## Evidence boundary

These are measurements from the saved run records. They do not identify a cause
or establish how the result behaves across other random seeds.
