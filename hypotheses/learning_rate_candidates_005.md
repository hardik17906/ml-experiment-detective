# Model-selected hypothesis candidates

Ollama selected two of three prepared, testable candidates. Python supplied their wording, measured evidence, and run links.

## Candidate 1: loss rise

The higher learning rate may be associated with larger temporary validation-loss rises in this setup.

### Supporting observations

- **E2:** For model/shuffle seeds 44/43, the largest one-epoch validation-loss rise was none at learning rate 0.05 and +0.5489 (epochs 1→2) at 0.1. Sources: [lr_005_gap_001](../runs/lr_005_gap_001.json), [baseline_gap_001](../runs/baseline_gap_001.json).
- **E5:** For model/shuffle seeds 144/143, the largest one-epoch validation-loss rise was +0.0012 (epochs 3→4) at learning rate 0.05 and +0.1005 (epochs 3→4) at 0.1. Sources: [lr_005_seed2](../runs/lr_005_seed2.json), [lr_01_seed2](../runs/lr_01_seed2.json).
- **E8:** For model/shuffle seeds 244/243, the largest one-epoch validation-loss rise was none at learning rate 0.05 and +0.1387 (epochs 1→2) at 0.1. Sources: [lr_005_seed3](../runs/lr_005_seed3.json), [lr_01_seed3](../runs/lr_01_seed3.json).

### Evidence to weigh against it

- None selected from these saved runs.

### Missing evidence

More matched seed blocks and finer training measurements would show whether this pattern persists and help investigate the training trajectory.


## Candidate 2: seed dependence

The final-accuracy effect of learning rate may depend on the model and shuffle seeds.

### Supporting observations

- **E3:** For model/shuffle seeds 44/43, final validation accuracy was 75.15% at learning rate 0.05 and 71.25% at 0.1 (-3.90 percentage points for high minus low). Sources: [lr_005_gap_001](../runs/lr_005_gap_001.json), [baseline_gap_001](../runs/baseline_gap_001.json).
- **E6:** For model/shuffle seeds 144/143, final validation accuracy was 76.05% at learning rate 0.05 and 76.35% at 0.1 (+0.30 percentage points for high minus low). Sources: [lr_005_seed2](../runs/lr_005_seed2.json), [lr_01_seed2](../runs/lr_01_seed2.json).
- **E9:** For model/shuffle seeds 244/243, final validation accuracy was 75.90% at learning rate 0.05 and 71.45% at 0.1 (-4.45 percentage points for high minus low). Sources: [lr_005_seed3](../runs/lr_005_seed3.json), [lr_01_seed3](../runs/lr_01_seed3.json).
- **E10:** Across 3 matched seed blocks, the high-minus-low final validation-accuracy differences were -3.90, +0.30, -4.45 percentage points in listed order; the direction varied. Sources: [lr_005_gap_001](../runs/lr_005_gap_001.json), [baseline_gap_001](../runs/baseline_gap_001.json), [lr_005_seed2](../runs/lr_005_seed2.json), [lr_01_seed2](../runs/lr_01_seed2.json), [lr_005_seed3](../runs/lr_005_seed3.json), [lr_01_seed3](../runs/lr_01_seed3.json).

### Evidence to weigh against it

- None selected from these saved runs.

### Missing evidence

More matched seed blocks, each with both learning rates and the same validation split, would show how often the final-accuracy difference changes direction.

## Evidence boundary

Python checked the selected candidate types and exact evidence assignments. The selected hypotheses remain unproven; the saved runs do not establish a causal mechanism or a general effect across seeds.
