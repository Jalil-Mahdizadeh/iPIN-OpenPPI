# RAPPPID retraining: C3-development checkpoints

All rows retained: 2,265 observed positives and 1,000,000 unlabeled pairs. No test evaluation or automatic epoch selection.

| Epoch | Seed 20260803 | Seed 20260817 | Seed 20260831 | Mean-logit ensemble |
|---|---:|---:|---:|---:|
| 4 | 0.622185 | 0.670013 | 0.672436 | 0.692744 |

Scores are ranking metrics, not calibrated interaction probabilities. Training uses native padded batches; development uses the declared native singleton inference policy.

Every listed epoch and all three seed checkpoints remain available. The user will decide which epoch proceeds to a separately authorized test evaluation.
