# Git publication scope

This is the completed 13-predictor study, preserved before the subsequent
[X-PAIR comparison](../x_pair_test2_v1/README.md). Read
[results/RESULTS.md](results/RESULTS.md) for the outcome. The scheduler snapshot
in the original `STATUS.md` is historical; `results/COMPLETE.json` and the
preservation record establish completion.

Git includes the inference/evaluation implementation, shell and SLURM entry
points, protocols, input/execution freezes, amendments, dispatch and job
records, preflight checks, aggregate results/figures, and compact scoring,
shard and SPRINT completion metadata. No predictor or metric changed during
publication.

Protected test candidates and truth, per-pair predictions, cached legacy
arrays, embeddings, source sequences, SPRINT HSPs and raw score payloads,
scheduler logs and runtime caches remain local. Existing input/prediction
manifests identify them by hash. A full rerun requires those frozen inputs and
the previously installed upstream predictors/images; Git contains the code
and evidence, not those environments or model weights.

See the [repository deposit inventory](../../DEPOSIT.md) for validation and
the distinction between public evidence and local execution assets.
