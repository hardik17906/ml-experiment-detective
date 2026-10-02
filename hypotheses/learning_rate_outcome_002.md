# Hypothesis worksheet: learning_rate_outcome_002

**Question:** Across three matched seed blocks, did raising the learning rate consistently lower final validation accuracy?

## Candidate hypothesis

Raising the learning rate from 0.05 to 0.1 may contribute to lower final validation accuracy by producing larger temporary validation-loss increases. This is a testable possibility, not a causal finding.

## Matched observations

Within each seed block, the saved configurations differ only in `learning_rate`. Across blocks, settings recorded in every run agree; model and shuffle seeds change together.
All final measurements are from epoch 5.
Metadata gap: `dropout`, `validation_start` are absent from some older run records. Their equality across all blocks cannot be verified from saved JSON.

| Seed block (model/shuffle) | Learning rates and source runs | Largest validation-loss rise (low → high) | Final validation accuracy (low → high; high − low) |
| --- | --- | --- | --- |
| 44/43 | 0.05: [lr_005_gap_001](../runs/lr_005_gap_001.json); 0.1: [baseline_gap_001](../runs/baseline_gap_001.json) | none → +0.5489 (epochs 1→2) | 75.15% → 71.25% (-3.90 pp) |
| 144/143 | 0.05: [lr_005_seed2](../runs/lr_005_seed2.json); 0.1: [lr_01_seed2](../runs/lr_01_seed2.json) | +0.0012 (epochs 3→4) → +0.1005 (epochs 3→4) | 76.05% → 76.35% (+0.30 pp) |
| 244/243 | 0.05: [lr_005_seed3](../runs/lr_005_seed3.json); 0.1: [lr_01_seed3](../runs/lr_01_seed3.json) | none → +0.1387 (epochs 1→2) | 75.90% → 71.45% (-4.45 pp) |

## Evidence supporting the hypothesis

- With seeds 44/43, the higher learning rate had a larger maximum one-epoch validation-loss increase: +0.5489 (epochs 1→2) versus none.
- With seeds 44/43, final validation accuracy was 3.90 percentage points lower at the higher learning rate.
- With seeds 144/143, the higher learning rate had a larger maximum one-epoch validation-loss increase: +0.1005 (epochs 3→4) versus +0.0012 (epochs 3→4).
- With seeds 244/243, the higher learning rate had a larger maximum one-epoch validation-loss increase: +0.1387 (epochs 1→2) versus none.
- With seeds 244/243, final validation accuracy was 4.45 percentage points lower at the higher learning rate.

## Counterevidence and limits

- With seeds 144/143, final validation accuracy was 0.30 percentage points higher at the higher learning rate. A larger loss rise did not imply worse final accuracy in this block.
- Only 3 matched seed blocks are recorded here. A one-epoch validation-loss rise is a descriptive measure, not a direct measurement of the optimizer's mechanism.

## Missing evidence and next controlled test

Run more matched seed blocks: train one model at learning rate 0.05 and one at 0.1 per block, keeping the same recorded settings and validation split within and across blocks. Compare per-block final validation accuracy and maximum one-epoch validation-loss rise before making a broader claim.

The saved runs show an association in these blocks. They do not establish that the learning rate caused an accuracy change, and they do not estimate how often either outcome occurs across seeds.
