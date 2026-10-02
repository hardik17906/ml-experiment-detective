# Experiment comparison: lr_005_gap_001 vs baseline_gap_001

Sources: [lr_005_gap_001](../runs/lr_005_gap_001.json), [baseline_gap_001](../runs/baseline_gap_001.json)

## Recorded configuration differences

| Setting | lr_005_gap_001 | baseline_gap_001 |
| --- | ---: | ---: |
| learning_rate | 0.05 | 0.1 |

**Comparison scope:** One recorded setting differs. This pair isolates it among recorded settings.

## Final metrics (epoch 5)

| Metric | lr_005_gap_001 | baseline_gap_001 | Change (second - first) |
| --- | ---: | ---: | ---: |
| Validation loss | 0.6876 | 0.8208 | +0.1332 |
| Validation accuracy | 75.15% | 71.25% | -3.90 pp |

## Final train-validation gaps

Loss gap is validation minus training. Accuracy gap is training minus validation.
Both use the same model after the epoch.

| Run | Loss gap | Accuracy gap |
| --- | ---: | ---: |
| lr_005_gap_001 | +0.0026 | -0.22 pp |
| baseline_gap_001 | +0.0115 | -0.34 pp |

## Curve observation

| Run | Largest one-epoch validation-loss increase |
| --- | --- |
| lr_005_gap_001 | no increase recorded |
| baseline_gap_001 | epoch 1 to 2: +0.5489 |

## Evidence boundary

These are measurements from the saved run records. They do not identify a cause
or establish how the result behaves across other random seeds.
