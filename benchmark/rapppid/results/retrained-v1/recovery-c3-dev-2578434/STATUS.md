# First evaluation attempt: stopped before latest-checkpoint scoring

The independent metric cross-check stopped on the existing epoch-4 ensemble result: historical weighted concordance `0.6927444044230223` versus weighted scikit-learn ranking `0.6927444044087584`, a difference of approximately `1.4264e-11`, above this wrapper's overly strict `1e-12` verification tolerance. No latest checkpoint was scored and no model or training checkpoint was changed.

All original attempt artifacts are retained here. The corrected, separately frozen attempt is in `../recovery-c3-dev-2578434-v2/`. It retains the identical historical scoring function and uses `1e-9` verification tolerance for million-row floating-point summation order, with an additional reverse-summation/long-double metric check. This is an evaluation-check correction, not a repair or restart of the failed training run.
