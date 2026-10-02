# Controlled follow-up plan: learning_rate_seed4_001

Source hypothesis case: [worksheet](../hypotheses/learning_rate_outcome_002.md)

## Why another seed block?

Each row below compares learning rate 0.1 with 0.05 on the same saved validation split. A negative accuracy difference means the higher learning rate finished worse in that seed block.

| Model/shuffle seeds | Source runs (low, high) | Final accuracy difference (high − low) | Larger loss rise at high rate? |
| --- | --- | ---: | --- |
| 44/43 | [lr_005_gap_001](../runs/lr_005_gap_001.json), [baseline_gap_001](../runs/baseline_gap_001.json) | -3.90 pp | yes |
| 144/143 | [lr_005_seed2](../runs/lr_005_seed2.json), [lr_01_seed2](../runs/lr_01_seed2.json) | +0.30 pp | yes |
| 244/243 | [lr_005_seed3](../runs/lr_005_seed3.json), [lr_01_seed3](../runs/lr_01_seed3.json) | -4.45 pp | yes |

So far, final accuracy was lower at the higher rate in 2/3 blocks; its largest one-epoch validation-loss rise was larger in 3/3.
If the new pair has lower final accuracy at the higher rate, the first count becomes 3/4; otherwise it stays 2/4. Either result adds one observation, not a general rule.

## Question this pair tests

In one new seed block, does raising learning rate produce a larger temporary validation-loss rise or lower final validation accuracy? Does the final-accuracy difference point down, up, or stay level?

## Controlled settings

Both runs use model seed 344 and shuffle seed 343. They differ only in `learning_rate` among planned settings.
Both use Fashion-MNIST, training size 10000, split seed 42, and the same validation indices selected from positions 10000 through 11999 of the seeded permutation.
Both train for 5 epochs with dropout 0.

## Planned runs

| Run ID | Learning rate | Model seed | Shuffle seed |
| --- | ---: | ---: | ---: |
| lr_005_seed4 | 0.05 | 344 | 343 |
| lr_01_seed4 | 0.1 | 344 | 343 |

Commands to execute after reviewing the plan:

```powershell
python phase0.py --run-id lr_005_seed4 --learning-rate 0.05 --model-seed 344 --shuffle-seed 343 --train-size 10000 --epochs 5 --dropout 0
python phase0.py --run-id lr_01_seed4 --learning-rate 0.1 --model-seed 344 --shuffle-seed 343 --train-size 10000 --epochs 5 --dropout 0
```

## Verification boundary

Older source JSON does not explicitly record `dropout`, `validation_start`. The new runs will record those current-script settings; equality with older runs cannot be established from old JSON alone.
No training runs were launched while creating this plan. This file contains no new run metrics.
Training script SHA-256 at planning time: `a2de5de5ad8fa31eda8d1905003ba591eed7c74e77ee36d29a7cfb4bc54c383e`.
