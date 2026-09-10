# Research reassessment and development embedding identity incident

Date: 2026-09-10

Status: priority #1 completed under DEC-0045. Complete frozen-model development
reevaluation passed production audit (9/9) and standalone independent
validation (17/17). Original artifacts and the protected test remain unchanged.

## Corrected development results

The correction materially changes the scientific picture. The frozen simple
models have substantial positive-versus-unlabeled ranking signal. The specific
partner-gated architecture still does not earn its complexity under the
original rules. These are distinct conclusions.

All figures below are Horvitz–Thompson-weighted positive-versus-U concordance,
not biological interaction accuracy or calibrated probability. C3 withholds
both endpoints from supervised training; C2 withholds one; C1 uses endpoints
seen in training while withholding the evaluated positive pairs. These labels
do not establish absence of all homology or PLM pretraining exposure.

| Frozen scorer | Old C3 (invalid identity) | Corrected C3 | Corrected C2 | Corrected C1 |
|---|---:|---:|---:|---:|
| ESM-2 150M affine, lr 3e-4 | 0.491608 | 0.784142 | 0.799797 | 0.848565 |
| ESM-2 650M affine, lr 3e-4 | 0.485140 | 0.774678 | 0.808320 | 0.869093 |
| ESM-2 650M partner-gated, no dropout | 0.491347 | 0.759554 | 0.862241 | 0.939496 |
| Sequence-length ratio control | 0.660880 | 0.660880 | 0.561149 | 0.552608 |

The original selection procedure chooses the 150M affine lr-3e-4 ensemble.
Its C3 component-bootstrap 95% interval is [0.742820, 0.852716], with a C3
seed range of 0.004572. Its source-exclusive C3 concordances are 0.742127
(HI-II-14) and 0.786062 (HuRI).

The best partner-gated C3 ensemble is 0.024588 below that simple comparator;
the paired 95% interval for its difference is [-0.070512, 0.033187]. It does
not meet the required +0.02 gain with a positive interval. All three gated
configurations also fail the prespecified maximum seed range of 0.02; their
C3 ranges are 0.061245, 0.065453 and 0.025500. Gated-versus-simple differences
are negative in both source-specific C3 subsets. The matched no-gate
improvements have intervals crossing zero.

Consequently the unchanged rule engine still returns
`stop_complex_model_claim_and_stop_before_protected_evaluation`. This is a
rejection of the additional complex-model claim, not evidence that the frozen
representations contain no useful ranking signal. Better C1/C2 performance
does not substitute for the original primary C3 requirement.

Corrected machine-readable metrics and complete decision traces are in
`artifacts/results/development_evaluation/development_embedding_identity_correction_v2/`.

## Correction verification and custody

- Both encoders: all 17,000 raw vector hashes and all normalized vectors
  verified; explicit manifest identity joins correct 16,999 row positions.
- All 16,799 public training positives and 2,000,000 public training-U pairs
  verified against training-time embedding identities.
- All 30 frozen checkpoint forward checks passed. Input vectors agree exactly;
  the largest training-versus-optimized FP32 score difference was 0.000033379,
  below the declared 0.0001 batch-shape rounding tolerance.
- All nine development cells, 9,026,108 rows, 30 frozen checkpoints, ten
  ensembles and nine controls rescored. Old/new row-file and scorer-definition
  hashes agree in every cell. No rows, weights, checkpoints or rules changed.
- All original point metrics, 2,000-replicate paired component bootstraps,
  source, degree/hub, score-correlation and novel-U diagnostics recomputed.
- Complete unit suite: 329 passed. This includes identity permutation and
  fail-closed tests and an AST check that the standalone scientific formulas
  remain identical to the historical standalone implementation.
- Completed production audit: 9/9 checks passed. Standalone validation:
  17/17 checks passed. It retains storage-order matrices and translates pair
  indices, independently of the production matrix-reordering implementation.
- All 270,783,240 learned score values reproduced exactly, with zero maximum
  difference and zero swap-symmetry difference. All deterministic scores,
  ensemble values, point metrics, bootstraps, diagnostics, and the original
  selection/kill disposition passed independent recomputation/checks.
- Original and corrected bootstrap component-draw hashes agree in all three
  primary cells. No post-result threshold or numerical tolerance change was
  needed for the standalone validator.

Source freeze: `5548baa20ae832abfc7f7eae41ecebd261f38c54`.
Production evidence freeze: `1bae702a98c488201b7c7078f3b665bcc026db90`.
Independent validator source: `bcebdca7db1c5d69aff248f42dd38a006509e2dd`.
Independent evidence freeze: `37c030b34546c32c31d91aac002c4a2e3f7626ee`.

Detailed evidence is in
`artifacts/validation/development_evaluation/development_embedding_identity_correction_v2/`.
Original evaluation and validator evidence remain intact in their v1 paths.
Existing development plaintext was reused without another decryption. No
private key or protected candidate/truth plaintext was opened. Protected
ciphertext checksum checks matched the frozen registry. Commits are local;
nothing was pushed or published.

The independent report SHA-256 is
`3908652a7cd7e595197fca2ad19d74c06c9f77b66cf716b1cddd83b8630766a9`.
The separate validation artifact registry binds the validator source, its
tests, report, private execution log and protected ciphertext checksum checks.
"Independent" here refers to a standalone implementation and recomputation,
not an external expert-group review.

## Recommendation after the correction

Do not abandon the broad project because the previous learned scores were
near chance: that observation was an input-identity failure. Keep the simple
150M model as a credible baseline, while retiring the current claim that the
gated head adds value on unseen endpoints.

The next decision-worthy experiment would test whether the corrected signal
is partner-specific rather than endpoint/assay propensity: compare an
endpoint-only score with pair-dependent scoring in within-anchor partner
retrieval, with length, similarity and degree controls. Design and freeze that
comparison prospectively on public-training/internal-validation data; the
already inspected development set is no longer an untouched source for a new
architecture search. A pair-aware/residue-level model is worth considering
only after such a baseline and its PPI-pretraining exposure audit are defined.
None of that additional training or evaluation is part of this correction.

This remains an evidence-ranking research opportunity, not an established
probability-of-binding predictor or a demonstrated novel architecture. The
unavailable assay denominator, unlabeled-pair uncertainty, limited source
diversity, residual homology and the independent coarse-local negative result
remain real constraints. Protected evaluation stays unauthorized regardless
of the more encouraging corrected scores.

## Initial assessment at discovery

The repository has not established that its trained models are a scientific
dead end. The development scorer supplies almost every protein's model input
from a different protein's embedding row. The independent completed-evaluation
validator repeats the same error. The learned-model results used by DEC-0039
therefore cannot estimate performance on the intended sequence pairs.

This finding does not establish that corrected models will perform well. The
separate coarse local-representation result and the public-data limitations
must be assessed on their own evidence.

## Research design and remaining limitations

The original programme targeted evidence-aware direct human heteromeric PPI
prioritization and conditional assay prediction. The audited HuRI release does
not reconstruct the complete selected, attempted, and technically evaluable
pair universe. The project consequently adopted positive-versus-unlabeled
ranking of released evidence, without calibrated biological-probability claims.

The frozen benchmark contains 17,000 reference-sequence endpoints. Stage 1 uses
16,799 training-positive pairs and 2,000,000 sampled training-U observations.
Its 30 runs fit affine or nonlinear symmetric heads on frozen, globally pooled
ESM-2 150M/650M representations. They do not test a residue joint encoder,
cross-attention model, adapted PLM, or interface-supervised architecture.

The later public-training-only local diagnostic uses a consistent identity
ordering. Its primary top-four segment cosine scored 0.5531708398478847 versus
matched global cosine 0.5687588309531323, missing the required +0.01 increment.
That result argues against this coarse similarity heuristic. It is not an
information upper bound for learned residue or domain compatibility.

## Confirmed defect

| Stage | Ordering |
|---|---|
| Stored pooled and standardized embeddings | `(sequence_length, sequence_sha256)` |
| Training endpoint indices | `(sequence_length, sequence_sha256)` |
| Development endpoint indices | `sequence_sha256` alone |

The scorer uses the development indices on the stored matrix without a join
or row permutation. Both encoders have 16,999 mismatched endpoint indices out
of 17,000. For example, development index 0 expects a 2,137-residue protein,
but stored row 0 belongs to a 25-residue protein. The intended vector is at
row 16,801.

Source locations at discovery:

- `src/ipin_openppi/stage1/embeddings.py:89`: length/hash ordering.
- `src/ipin_openppi/stage1/embeddings.py:281`: normalization preserves rows.
- `src/ipin_openppi/stage1/preparation.py:90`: correct training lookup.
- `src/ipin_openppi/development_evaluation/scoring.py:98`: hash-only universe.
- `src/ipin_openppi/development_evaluation/scoring.py:255`: pair index lookup.
- `src/ipin_openppi/development_evaluation/scoring.py:460`: unaligned matrix use.
- `scripts/model/validate_development_completed_independent_v1.py:1133` and
  `:1617`: the independent validator repeats the same mismatch.

The original scoring source SHA-256 is
`874b84270be2fe47211a3936907762ebb6442052eb6928adbdcda50ace60ca5f`.
It matches the source registered in the original independent validation report.

## Initial read-only verification at discovery

A read-only diagnostic in `containers/images/ipin-data-arm64_0.1.2.sif`:

1. Joined public endpoint identities to both frozen embedding manifests.
2. Confirmed the 16,999/17,000 mismatch in both models.
3. Verified both standardized matrices against their frozen hashes.
4. Checked raw vector hashes and exact normalization reconstruction on nine
   spread-out rows per model.
5. Verified that all 16,799 public training-positive pair indices agree with
   the actual embedding identity order.

This diagnostic did not open development or protected pair packages, retrain,
or produce corrected performance metrics.

## Scope of invalidation

All 30 learned scorer columns and their ten ensembles across all nine
development cells are affected. Their metrics, comparisons, candidate
selection and scientific stopping interpretation require corrected evaluation.
The deterministic degree, length, k-mer and interolog controls use consistent
identity mappings and are not affected by this particular error. The separate
local diagnostic constructs its embedding and pair indices in the same order.

## Original prioritized continuation

1. Repair identity alignment, validate it against the frozen manifests, test
   invariance to endpoint-table permutation, and rerun the existing models
   using identical development rows, weights, metrics and scientific rules.
2. If useful signal survives, prioritize partner retrieval and evidence-aware
   evaluation beyond length, similarity and degree explanations.
3. If it does not, consider one prospective comparison with an established
   pair-aware model before committing to another architectural programme.
   PPI-pretraining exposure must be audited.
4. A narrower isoform/partner-effect task is an alternative: the existing TF
   audit found 848 contrast groups, only 149 fully reference-mapped, and no
   endpoint-protected group under its audited exposure snapshot.
5. Evidence semantics and benchmark infrastructure may support a distinct
   methodology/resource contribution, provided its novelty and evaluation go
   beyond generic leakage warnings.

Relevant primary literature: [PPLM](https://www.nature.com/articles/s41467-026-70457-5),
[MINT](https://www.nature.com/articles/s41467-025-67971-3), and
[DataSAIL](https://www.nature.com/articles/s41467-025-58606-8).

## Authorized correction

The user's instruction was: "save your findings in a file and initiate the
priority #1. Do your best." DEC-0045 records that authority. It authorizes the
bounded correction and complete development reevaluation, with new artifacts,
the frozen trained models, and the protected test remaining sealed.

## Repository navigation maintenance

Graphify was used to navigate the original code and document relationships.
After the correction and standalone validator were added, `graphify update .`
refreshed the code graph: 3,415 nodes, 8,132 edges and 278 communities, with no
LLM/API use. This AST-only update does not semantically index the new reports
or result JSON; it warned that 101 sources produced no AST nodes. The report,
versioned status and hash-bound artifacts are the authoritative correction
record. Existing unrelated graph working-tree changes were preserved.
