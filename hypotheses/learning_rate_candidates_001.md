# Model-proposed hypothesis candidates

**Historical draft — not accepted.** Its first candidate linked larger loss rises to worse final accuracy but omitted the seed block where final accuracy improved. It also included model-written mechanism language that was not checked against recorded evidence. See `learning_rate_candidates_004.md` for the current constrained report.

These are possibilities to investigate. The numerical claims below come from the saved run JSON, not model-written text.

## Candidate 1

A higher learning rate may lead to temporary validation-loss rises that negatively impact final accuracy.

### Supporting observations

- **E2:** For model/shuffle seeds 44/43, the largest one-epoch validation-loss rise was none at learning rate 0.05 and +0.5489 (epochs 1→2) at 0.1. Sources: [lr_005_gap_001](../runs/lr_005_gap_001.json), [baseline_gap_001](../runs/baseline_gap_001.json).
- **E5:** For model/shuffle seeds 144/143, the largest one-epoch validation-loss rise was +0.0012 (epochs 3→4) at learning rate 0.05 and +0.1005 (epochs 3→4) at 0.1. Sources: [lr_005_seed2](../runs/lr_005_seed2.json), [lr_01_seed2](../runs/lr_01_seed2.json).

### Evidence to weigh against it

- None selected from these saved runs.

### Missing evidence

Additional runs with intermediate learning rate adjustments or detailed loss curves would help confirm if higher learning rates cause temporary loss spikes.


## Candidate 2

The final validation accuracy difference may vary across seed blocks due to differences in training dynamics.

### Supporting observations

- **E1:** For model/shuffle seeds 44/43, the recorded configurations differ only in learning rate (0.05 versus 0.1). Sources: [lr_005_gap_001](../runs/lr_005_gap_001.json), [baseline_gap_001](../runs/baseline_gap_001.json).
- **E3:** For model/shuffle seeds 44/43, final validation accuracy was 75.15% at learning rate 0.05 and 71.25% at 0.1 (-3.90 percentage points for high minus low). Sources: [lr_005_gap_001](../runs/lr_005_gap_001.json), [baseline_gap_001](../runs/baseline_gap_001.json).
- **E7:** The high-minus-low final validation-accuracy difference changed from -3.90 to +0.30 percentage points across the two matched seed blocks. Sources: [lr_005_gap_001](../runs/lr_005_gap_001.json), [baseline_gap_001](../runs/baseline_gap_001.json), [lr_005_seed2](../runs/lr_005_seed2.json), [lr_01_seed2](../runs/lr_01_seed2.json).

### Evidence to weigh against it

- None selected from these saved runs.

### Missing evidence

Runs with identical configurations but different seed blocks would help isolate whether the difference is due to training process variability or other factors.

## Evidence boundary

Python checked the evidence IDs and supplied the measured claims and links. It did not verify that the model assigned each fact to the right hypothesis or establish a causal explanation. More matched seed blocks are needed before a broad conclusion.
