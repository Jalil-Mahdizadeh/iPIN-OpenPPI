# Native SPRINT benchmark

Current completion record: [final results](results/original-v1/RESULTS.md),
completed 17 September 2026 with full C1/C2/C3 coverage. See the
[README](README.md) for current status. The dated snapshot below preserves
the pre-completion qualification, preprocessing, and execution history.

## Historical startup snapshot

Status checked: **2026-09-17, approximately 21:02 CEST**.

The dedicated SIF is built and qualified. Full HSP preprocessing is running;
C1/C2/C3 scoring and comparison will start automatically after it succeeds.
**Full-panel performance results are not available yet.** No test labels were
accessed during setup, qualification or timing measurement.

## Jobs and timing

| Job | Task | Status | Resources / limit |
|---|---|---|---|
| `2600174` | Native HSP preprocessing, all 17,000 sequences | Running on `n487`; started 20:58 CEST | 72 CPUs, 100 GiB RAM, one GPU-node allocation; 72-hour limit |
| `2600175` | C1/C2/C3 scoring, frozen iPIN comparison, paired bootstrap and publication | Pending, `afterok:2600174` | 72 CPUs, 100 GiB RAM, one GH200 GPU; 24-hour limit |

SPRINT is CPU code: HSP generation uses **64 OpenMP workers**, and prediction
uses the native serial executable. The GPU-node allocation provides the
qualified ARM64 architecture. GPU acceleration is used for the historical
bootstrap evaluation, not for SPRINT prediction. D-SCRIPT and all other existing
jobs were left untouched.

Measured on the current Arrhenius GH200 allocation:

- SIF build: **1 minute 53 seconds** (18:47:42–18:49:35 UTC).
- Authors' 150-protein toy HSP calculation: **110.06 s serial / 1.74 s on 64 threads**.
- Native toy prediction: approximately **0.045 s per 300-pair invocation**.
- Timing-only pilot: **512 TRAIN sequences, 291,874 residues, 9.06 s** for HSP
  generation on 64 threads; peak resident memory approximately 249 MiB.
- Production: **17,000 proteins, 9,237,157 residues**. The dense float32 scoring
  matrix alone is approximately 1.08 GiB, plus HSP/other working memory.

**Provisional total compute estimate: 30 minutes–4 hours, excluding queue delays.**
Confidence remains limited: HSP density, repeats and shared-map contention do not
scale linearly from a small pilot. The early full run advanced through about
1.8 million of 18.9 million buckets in the first of four hash tables in roughly
two minutes; this is consistent with an HSP stage on the order of one to two
hours, but is not a guaranteed ETA. Native scoring and bootstrap follow.
The walltime limits are safety margins, not predictions; the evaluation job may
also have a queue delay.

The first job is already running, superseding Slurm's earlier 21:14 CEST start
forecast. The authors also distinguish fast prediction from potentially costly
HSP preprocessing in their [official documentation](https://github.com/lucian-ilie/SPRINT).

## Comparison and interpretation

This is the **original native algorithm with the 16,799 frozen TRAIN-positive
interactions**, not a neural pretrained checkpoint. No external graph,
development/test interaction labels, or TRAIN-unlabeled-as-negative data are
supplied to SPRINT. There is no optimizer, epoch selection, hyperparameter search
or separate retrained neural model.

| Cell | Released positives | Unlabeled pairs | Total |
|---|---:|---:|---:|
| C1 | 3,187 | 1,000,000 | 1,003,187 |
| C2 | 13,446 | 1,000,000 | 1,013,446 |
| C3 | 2,379 | 1,000,000 | 1,002,379 |
| Total | 19,012 | 3,000,000 | 3,019,012 |

Baseline and optimized iPIN predictions are reused byte-for-byte. The metric is
historical **design-weighted P-versus-U concordance**, with exact half-tie credit,
not AUROC against confirmed negatives. Uncertainty uses the same 2,000 paired
two-endpoint component bootstrap draws and cell seeds. C3 SPRINT-minus-optimized
iPIN is the primary contrast; C1/C2 and baseline-iPIN comparisons are additional.
This is a disclosed follow-up on previously examined panels, not an untouched
confirmatory test.

## Decisions frozen before test access

1. **Unmodified upstream C++**, commit
   `b6272c76e1a943e6812b1b815607691819e6202e`. Source identity is verified inside
   the SIF. Compiler flags follow the authors' makefile: `-O3`, `-Wall`, with
   OpenMP only for parallel binaries.
2. **Full frozen sequences**, lengths 25–7,570 residues. No truncation, padding,
   new UniProt downloads or sequence substitution. The authors' precomputed
   human HSP cache is not substituted for this exact sequence corpus.
3. **Published defaults**: HSP `Thit=15`, `Tsim=35`, `M=1` (PAM120); prediction
   high-count threshold `Thc=40`. No test-driven choice of settings.
4. **Sequence-only transductive preprocessing**: HSPs and high-count filtering
   see the fixed complete 17,000-sequence corpus, including held-out endpoints.
   Held-out interaction labels are unavailable. Disclose this sequence exposure;
   do not describe feature construction as strictly inductive.
5. **Parallel HSPs, serial prediction**. The upstream parallel scorer has
   unsynchronized shared-matrix updates in `scoreing_matrix.h::load_traing`.
   The released serial build avoids this race without changing the algorithm.
6. **Canonical HSP protein-pair block order**, with native records unchanged.
   Toy tests qualify identical serial/parallel records and identical printed
   scores after this ordering step.
7. **Label-free input adapter**: all candidate identities are routed through
   native `-pos`; `-neg` is empty. The output marker `1` is discarded and is never
   treated as ground truth. Both routing channels are numerically equivalent
   in qualification.
8. **Original printed score precision**: genuine zeros and native six-significant-
   digit ties are retained. No calibration, missing-score imputation or dropping
   difficult pairs. Every candidate must have a finite nonnegative native score.
9. **Separated restricted phases**: sequence preprocessing, candidate-only
   scoring, reference import, full prediction freeze, then sealed truth
   evaluation. Read-only mount allowlists and the established Landlock/seccomp
   guard are used. GPU computation is allowed. The cluster does not virtualize
   the PID namespace; none is claimed. Historical files and ledgers remain RO.

## Qualification passed

- Serial and 64-thread HSP generation produced the same **2,099 HSP records**
  in **1,183 protein-pair blocks**, including all 150 full-length self HSPs.
- Native printed scores matched exactly across the serial HSP path, canonical
  HSP ordering, and the OpenMP scorer constrained to one thread.
- Endpoint reversal, row permutation and alternative routing produced identical
  corresponding scores on all **300 toy pairs**.
- An empty interaction graph produced actual native zeros for every toy pair.
- GPU metric/bootstrap matched an independent brute-force oracle covering ties,
  unequal weights and same-component pairs: maximum absolute error **7.77e-16**,
  tolerance **1e-12**.
- Frozen input hashes, sequence hashes/lengths/alphabet, unique graph edges and
  TRAIN partition membership of every graph endpoint were verified.
- Python and shell syntax checks passed. Frozen-code/input revalidation passed
  after submission. Early production HSP logs show progress without errors.

The metric implementation and restriction guard are byte-identical copies of
the established RAPPPID helpers. The existing iPIN model SIF is reused read-only
for Parquet preparation and GPU evaluation; it does not execute SPRINT.

## Artifacts

- Image: `benchmark/containers/images/sprint-native-arm64-v1.sif`, **171.72 MiB**.
- SIF SHA-256:
  `699112807a7829b1b4268fa83d358a206d62de5a5a0f7c7d199beb18f9f47f09`.
- Ubuntu 24.04 ARM64 base OCI manifest:
  `sha256:11dc1ccb427f0464a2369e645454c272bb0baece7357c892ba69d313b3a332cf`.
- Build recipe/driver: `benchmark/containers/sprint-native-arm64-v1.def`,
  `benchmark/containers/build_sprint.sh`.
- Build log/source manifest: `benchmark/containers/logs/sprint-native-v1-build.log`,
  `benchmark/containers/manifests/sprint-source.json`.
- Compiler, installed package versions and binary hashes: `/opt/sprint/build/`
  inside the SIF. The image is hash-frozen; because installation used live Ubuntu
  repositories, the recipe alone is not a hermetic bit-for-bit rebuild guarantee.
- Pre-test policy/code: `runs/original-v1/INITIAL_FREEZE.json`,
  `runs/original-v1/code/`. Source scripts: `scripts/`.
- Input freeze: `runs/original-v1/data/DATA_FREEZE.json`.
- Qualifications: `runs/original-v1/qualification/`; timing pilot:
  `runs/original-v1/pilot/`. The pilot is not the production HSP cache.
- Production HSP log: `runs/original-v1/hsp/native-hsp.log`.
- Submission/job-script hashes: `runs/original-v1/SUBMISSION.json`.
- Slurm and phase logs: `logs/original-v1/`.
- On success: `results/original-v1/RESULTS.md`, `RESULTS.json`, `scores.csv`,
  `paired_differences.csv`, `coverage.csv`; completion marker
  `runs/original-v1/RUN_COMPLETE.json`.
- Native scores, candidate-token Parquet predictions and reference copies:
  restricted `private/original-v1/`. Aggregate reports contain no protected pair
  identities. Temporary decrypted truth is removed after evaluation.

All new work is confined to `benchmark/`. The boundary audit checked **1,912
tracked and non-ignored untracked files outside `benchmark/`**, finding no
additions, removals or content changes. See `provenance/original-v1/scope-audit.json`.
Graphify helped locate existing workflow components; its required AST-only
post-edit index is confined to `scripts/graphify-out/`, not the root index.
