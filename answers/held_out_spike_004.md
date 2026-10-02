# Answer

Yes, the held-out error (validation loss) spiked and recovered.

## Observed facts

- Validation loss rose from 0.8696 at epoch 1 to 1.4186 at epoch 2, then fell to 0.6663 at epoch 3. [source](../runs/baseline_gap_001.json)
- Validation loss rose from 0.7136 at epoch 3 to 0.8142 at epoch 4, then fell to 0.6793 at epoch 5. [source](../runs/lr_01_seed2.json)

## What remains unknown

- What was the exact validation loss at epoch 1 for run `lr_01_seed2`?
- What was the exact validation loss at epoch 5 for run `baseline_gap_001`?
