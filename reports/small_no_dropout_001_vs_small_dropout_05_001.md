# Experiment comparison: small_no_dropout_001 vs small_dropout_05_001

Sources: [small_no_dropout_001](../runs/small_no_dropout_001.json), [small_dropout_05_001](../runs/small_dropout_05_001.json)

## Recorded configuration differences

| Setting | small_no_dropout_001 | small_dropout_05_001 |
| --- | ---: | ---: |
| dropout | 0.0 | 0.5 |

**Comparison scope:** One recorded setting differs. This pair isolates it among recorded settings.

## Final metrics (epoch 40)

| Metric | small_no_dropout_001 | small_dropout_05_001 | Change (second - first) |
| --- | ---: | ---: | ---: |
| Validation loss | 0.6891 | 0.7121 | +0.0231 |
| Validation accuracy | 76.85% | 76.45% | -0.40 pp |

## Final train-validation gaps

Loss gap is validation minus training. Accuracy gap is training minus validation.
Both use the same model after the epoch.

| Run | Loss gap | Accuracy gap |
| --- | ---: | ---: |
| small_no_dropout_001 | +0.0757 | +3.85 pp |
| small_dropout_05_001 | +0.0508 | +4.55 pp |

## Curve observation

| Run | Largest one-epoch validation-loss increase |
| --- | --- |
| small_no_dropout_001 | epoch 31 to 32: +0.0325 |
| small_dropout_05_001 | epoch 32 to 33: +0.0080 |

## Evidence boundary

These are measurements from the saved run records. They do not identify a cause
or establish how the result behaves across other random seeds.
