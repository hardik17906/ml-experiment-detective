# Controlled follow-up plan: learning_rate_seed3_001

Source hypothesis case: [worksheet](../hypotheses/learning_rate_outcome_001.md)

## Question this pair tests

In one new seed block, does raising learning rate produce a larger temporary validation-loss rise or lower final validation accuracy?

## Controlled settings

Both runs use model seed 244 and shuffle seed 243. They differ only in `learning_rate` among planned settings.
Both use Fashion-MNIST, training size 10000, split seed 42, and the same validation indices selected from positions 10000 through 11999 of the seeded permutation.
Both train for 5 epochs with dropout 0.

## Planned runs

| Run ID | Learning rate | Model seed | Shuffle seed |
| --- | ---: | ---: | ---: |
| lr_005_seed3 | 0.05 | 244 | 243 |
| lr_01_seed3 | 0.1 | 244 | 243 |

Commands to execute after reviewing the plan:

```powershell
python phase0.py --run-id lr_005_seed3 --learning-rate 0.05 --model-seed 244 --shuffle-seed 243 --train-size 10000 --epochs 5 --dropout 0
python phase0.py --run-id lr_01_seed3 --learning-rate 0.1 --model-seed 244 --shuffle-seed 243 --train-size 10000 --epochs 5 --dropout 0
```

## Verification boundary

Older source JSON does not explicitly record `dropout`, `validation_start`. The new runs will record those current-script settings; equality with older runs cannot be established from old JSON alone.
This file is a plan. No training runs were launched and no new run metrics exist yet.
Training script SHA-256 at planning time: `a2de5de5ad8fa31eda8d1905003ba591eed7c74e77ee36d29a7cfb4bc54c383e`.
