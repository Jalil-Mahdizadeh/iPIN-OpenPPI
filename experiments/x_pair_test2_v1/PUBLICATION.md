# Publication and reproduction scope

This completed study was authorized by the user's request to apply X-PAIR on
test2 and compare with existing competitors, followed by the instruction to
update relevant documentation, commit and push. The comparison is human PPI
ranking on the existing frozen candidates. The primary/default iPIN predictor
remains the unchanged iPIN-TUnA-31k ensemble.

Start with [interpretation](results/INTERPRETATION.md),
[all 15 predictors](results/RESULTS.md), or the
[project follow-up report](../../docs/reports/m1/M1_XPAIR_Test2_Comparison_v1.md).
The main experiment and the added-C3 exploratory analysis are complete.
The exploratory analysis followed observation of the cohort reversal; it did
not change the primary metric, checkpoints or predictions.

## Published and local files

Git contains the original experiment scripts, scheduler entry points, protocol,
source/checkpoint identities, input and prediction manifests, aggregate JSON
and CSV results, figures, preservation receipt, and
[validation summary](validation/SUMMARY.json). The original source/model freeze,
implementation freeze, exploratory addendum and completion records retain
their execution-time hashes. The validation summary omits the private
candidate indices and individual fixture scores from the full local checks.

Local execution assets include candidates and truth, per-pair predictions,
bootstrap arrays, embeddings, downloaded weights and upstream source trees,
the runtime environment, full identity-bearing qualification fixtures and
working logs. They remain outside Git. Manifests can therefore reference files
that are deliberately absent from a public checkout. Their paths and hashes
provide provenance; a checkout alone is not the full evaluation workspace.
The [publication manifest](PUBLICATION_MANIFEST.json) enumerates the public
experiment files and preserves the hashes of the completed scientific outputs.

The original v3 model card, promotion report, model registry and its 13-model
evidence remain unchanged. Current documentation points to this separate
15-predictor comparison. Unrelated local studies and manuscript drafts are
outside this publication.

## Pinned dependencies

- Upstream [X-PAIR](https://gitlab.lcqb.upmc.fr/srescalli/X-PAIR), commit
  `897646a4a768acd488f4163ff07dd5a1183d52b1`; selected released checkpoints are
  `multitask_xfair.ckpt` and `interaction_xfair.ckpt`.
  [Source freeze](sources/XPAIR_FREEZE.json) records their exact hashes.
- [Ankh-large](https://huggingface.co/ElnaggarLab/ankh-large), revision
  `74b371dbfa3ee0a05d32ae74df0c2e0b82d6b9a6`;
  [encoder freeze](sources/ANKH_FREEZE.json).
- [X-PAIR datasets](https://doi.org/10.5281/zenodo.21457017), archive
  `xpair_datasets.tar.gz`, MD5 `6311ab8eecd461a53d1eeab2379929ea`.
  Only its X-fair interaction/interface training and validation files are used
  for exposure auditing; [download metadata](sources/zenodo_21457017.json)
  records the public source.
- Existing ARM64 image
  `benchmark/containers/images/plm-interact-native-arm64-v1.sif`, with an
  experiment-local Python environment. The run used PyTorch 2.8.0a0
  (`34c6371d24.nv25.08`), NumPy 1.26.4, Transformers 4.50.3,
  PyTorch Lightning 2.5.1, TorchMetrics 1.7.1, tokenizers 0.21.4,
  sentencepiece 0.2.0 and hf-xet 1.1.10. Runtime hashes are retained in the
  execution manifests; the exact package freeze remains local.

Upstream code and model downloads retain their authors' attribution and
license terms. This publication contains the experiment's adapters and
aggregate outputs; it does not redistribute the upstream weights or source tree.

## Execution order and prerequisites

Reproduction requires the local frozen study inputs listed in
[INPUT_FREEZE.json](INPUT_FREEZE.json), including the original competitor
predictions, scaling-study sequences, test truth and metric helpers. These
come from `experiments/test2_frozen_competitors_v1/` and
`experiments/human_ppi_data_scaling_v1/`. The unchanged benchmark metric code
also uses `benchmark/tuna/scripts/`. Recreating those studies or acquiring new
data would define additional work and must not silently replace these inputs.

The completed experiment directory contains immutable results. Use a separate
workspace for a new reproduction, preserve the pinned source/encoder identities,
and make the following prerequisites available there:

1. Clone X-PAIR at the pinned commit into `sources/X-PAIR/`; acquire the pinned
   Ankh assets under `sources/ankh-large/` using `scripts/acquire_ankh.py`.
   Acquire and verify the dataset archive, then place its README and X-fair
   files under `sources/datasets/xpair_datasets/`.
2. Create the experiment-local `data`, `logs`, `qualification` and runtime
   temporary/cache directories. Supply the existing read-only container.
   Place the pinned ARM64-compatible dependency wheels in `runtime/wheels/`;
   `run.sh runtime` installs them offline inside the experiment's environment.
   Source identities, candidates and previous results must match their manifests.
3. `run.sh prepare` freezes input hashes and identity-only candidates.
   `run.sh exposure` audits the released interaction/interface train and
   validation pairs. `run.sh embedding --rank 0 --qualify` verifies the
   embedding runner against the unchanged upstream generator.
4. `embedding.sbatch` runs eight length-balanced full-sequence feature workers.
   After feature completion, `run.sh score --qualify` checks native forward
   agreement, and `run.sh integration` checks actual candidate mapping and
   production indexing. `run.sh evaluate --qualify` checks the metric oracle.
5. `score.sbatch` runs eight workers for both fixed checkpoints. It caches only
   each protein's independent linear projection; native cross-attention and
   interaction scoring remain intact. Shards resume only against matching
   provenance and verified completed chunks.
6. `evaluate.sbatch`, dependent on successful scoring, first invokes `collect`
   without the truth mount, freezes complete finite predictions, then invokes
   `evaluate` with the frozen truth mounted read-only and finally `preserve`.
   `run.sh cohort_detail` produces the separately labeled exploratory C3
   cohort analysis.

The supplied scheduler files use the original Arrhenius account and environment;
their portability depends on local allocations. The executed jobs are recorded
in [JOBS.json](JOBS.json): embedding `3040577`, scoring `3040586`, comparison
`3040611`. Every task completed successfully. No further jobs are required to
read or interpret these results.
