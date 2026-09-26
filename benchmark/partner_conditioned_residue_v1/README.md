# Partner-conditioned residue study v1

New human PPI ranking models using the existing frozen ESM-2 150M residue
embeddings. This directory contains an independent study; the three frozen iPIN
predictors and their historical results are read-only references.

Status: qualified and training started on 24 September 2026. SLURM training job
**2943130** runs the four recipes; the mean control also starts on the interactive
GPU under an exclusive recipe lock. Dependent job **2943131** performs development
selection and the conditional C1/C2/C3 comparison. See [STATUS.md](STATUS.md) for
the published lifecycle status. No new test results are available at startup.

See [PROTOCOL.md](PROTOCOL.md) and [config.json](config.json) for the prospective
comparison. `runs/` contains private training artifacts and the immutable
execution snapshot; `logs/` contains worker logs; `private/` contains protected
test predictions; `results/` contains aggregate development and test reports.

The four recipes compare a mean-pooling control, learned residue pooling, and
two sizes of bidirectional attention between learned residue summaries. The
last two perform actual cross-protein attention. Their latent tokens are not
physical contact labels or validated interface predictions.

Runtime: the existing pinned `../containers/images/tuna-arm64-v1.sif`.
The raw residue cache and TRAIN/development data are reused read-only from
`../tuna`. No ESM retraining or new sequence extraction is required.

Numerical and pipeline checks passed; aggregate evidence is in
[results/QUALIFICATION.json](results/QUALIFICATION.json). The unused first
execution snapshot and its pre-fit refinement are documented in
[PREFIT_AMENDMENT.md](PREFIT_AMENDMENT.md).

Monitoring: `squeue -j 2943130,2943131`; worker progress is in
`logs/train-2943130-task*.log` and `logs/interactive-mean_pool.log`. Completed
development results will appear at `results/DEVELOPMENT.md`. When models pass
the development promotion rule, the comparison will appear at
`results/RESULTS.md`, `results/scores.csv`, and `results/paired_differences.csv`.
Otherwise, `results/NO_PROMOTION.json` records why test evaluation was skipped.
