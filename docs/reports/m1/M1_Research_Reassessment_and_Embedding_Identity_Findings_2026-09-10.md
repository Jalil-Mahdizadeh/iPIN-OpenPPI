# Research reassessment and development embedding identity incident

Date: 2026-09-10

Status: confirmed defect; correction and frozen-model development reevaluation
authorized by the project user under DEC-0045. Corrected performance is pending.

## Assessment

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

## Verification already performed

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

## Prioritized continuation

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
