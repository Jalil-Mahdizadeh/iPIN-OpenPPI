# DEC-0028: Accept and freeze the model-governance and baseline/training protocol

**Date:** 2026-08-18

**Status:** Accepted and effective as a design freeze; model acquisition,
implementation, training, development release, and protected evaluation remain
unauthorized

**Decision owner:** Codex under the project owner's explicit delegated
execution instruction

**Controlling records:** `RESUME-002`, `DEC-0026`, and `DEC-0027`

## Decision

Accept `model_governance_and_baseline_training_protocol_v1` as technically
complete, independently validated, and frozen before any model execution.

The production audit ran from clean implementation commit
`547592d64aced7a1ab91ee4a320c643bf8c36bad` and passed 24 checks with zero
warnings and zero failures. Its immutable evidence was committed at
`9d7159b80e35416cbe0aa219066eab09817c3a49`. The independently implemented
validator then ran from that clean evidence commit and passed 20 checks with
zero warnings and zero failures. Its evidence is committed at
`d2e68c71786ac63864965924aea08fd9ad12cd79`.

This acceptance freezes rules for a possible later model stage. It does not
authorize that stage. No model file, tokenizer, cache, runtime image,
embedding, feature cache, model implementation, training job, checkpoint,
prediction, development release, model-selection result, or protected metric
was produced.

## Accepted design

Accept and freeze:

1. exactly two public frozen ESM-2 candidates: the 150M checkpoint as the
   mandatory lightweight PLM baseline and the 650M checkpoint as the primary
   encoder candidate, each fixed to an immutable repository revision,
   safetensors digest, file size, tokenizer/config co-revision rule, MIT
   license record, and offline project-local custody procedure;
2. the conservative exposure claim ceiling: UniRef/UR50-D provider provenance
   is recorded, but exact and homologous benchmark-endpoint exposure is unknown
   and possible, C3 is not a PLM-exposure split, and no PLM-unseen, family-
   unseen, temporal-cleanliness, or causal-exposure claim is permitted;
3. final-layer FP32 pooled protein embeddings, complete 1,022-residue
   overlapping-window coverage, overlap averaging before protein averaging,
   label-blind extraction eligibility for all 17,000 endpoints, and
   normalization from only the 11,900 training endpoints;
4. the deterministic hash, graph/degree, component-mass, common-neighbor,
   sequence-length, exact 3-mer, exact training-interolog, 150M affine-head,
   and 650M affine-head control ladder;
5. the class-prior-free, design-weighted positive-versus-unlabeled pairwise
   logistic ranking objective using the complete 16,799-P census and every one
   of the 2,000,000 frozen public training-U observations once per pass with
   unchanged exact rational design weights;
6. one simple swap-symmetric 650M pooled partner-gated head under two million
   trainable parameters and only the 650M linear and nonlinear-no-gate
   ablations needed to isolate encoder scale, nonlinearity, and partner gating;
7. three fixed seeds, a complete finite recipe grid of 30 runs, five complete
   U passes, at most 300,000,000 comparisons, one GH200, 100 GPU-hours,
   100 GiB, deterministic execution controls, complete-pass checkpoints,
   exact one-resume infrastructure handling, and no performance early stop;
8. a complete training-artifact registry and independent validation before any
   separately authorized development release, three-seed ensembles, C3 then C2
   then C1 quantized model selection, lower-complexity tie-breaking, and no
   post-release retraining or candidate addition;
9. the already accepted Horvitz-Thompson concordance, half-tie, component-
   bootstrap, and separate C3/C2/C1 reporting hierarchy, plus training-only
   degree/hub strata and a view-only C1 novel-U sensitivity retaining original
   rows and weights; and
10. prespecified complexity thresholds, simple fallbacks, and model-level kill
    rules when graph, degree, length, 3-mer, interolog, or frozen-PLM controls
    explain the apparent performance.

Residue/interface prediction, structure features, routing, retrieval,
calibration, encoder fine-tuning, adapters, custom pretraining, external
diagnostic panels, and post-cutoff evidence remain outside the stage.

## Independent validation disposition

The independent validator does not import the production protocol module or a
model framework. It separately verified all immutable parent and public-
training hashes; sensitive-path exclusion; exact model revisions, weight
digests, roles, and claim limits; unbuilt runtime and offline custody; complete
long-sequence coverage; mandatory baselines; symmetry and ablations; P/U
coverage and weight semantics; optimizer/search/stopping bounds; development
freeze and model-selection order; metric hierarchy; degree/hub and novel-U
rules; complexity and kill gates; and continuing prohibitions.

It independently reconstructed the exact positive repetition algebra: every
positive appears 119 or 120 times in one complete U pass, with 919 positives
receiving the ceiling count. It also reconstructed exactly 30 runs and the
300,000,000-comparison ceiling, and tested decimal `0.001` `ROUND_HALF_UP`
selection ordering.

Preproduction mutation tests exposed and corrected one schema-key mismatch in
the production architecture-status guard and one boundary-valued selection
fixture before either clean authoritative report was generated. The final
production and independent reports contain no failures or warnings.

## Accepted evidence

| Evidence | SHA-256/result |
|---|---|
| Configuration | `3b001efa026a57d2937b041c26217ff87e3fdcda3ca1553d851bf347330333d5` |
| Binding protocol | `5daf5809b864de75f236ca3552369f943300bdbc86557a3a99277665faeda851` |
| Scientific report | `3e79d50f9a2d9543cd12dc06131f9a2c870b2d8f2044ebe45c899fa25071e2a3` |
| Production audit | `62ca0deea443951925351edaf2b2f397b0490308193e9b2fdfd0759d9cda89b4`; 24 pass |
| Independent validation | `e5af1b7a30af7ed971a099f71c01518ba54ad9419fa63e5a0bc4ba4fa77a61ea`; 20 pass |
| Clean production commit | `547592d64aced7a1ab91ee4a320c643bf8c36bad` |
| Clean validation commit | `9d7159b80e35416cbe0aa219066eab09817c3a49` |
| Validation-evidence commit | `d2e68c71786ac63864965924aea08fd9ad12cd79` |

The human-readable interpretation is
`docs/reports/m1/M1_Model_Governance_and_Baseline_Training_Protocol_Final_v1.md`.

## Continuing hold and next decision boundary

This decision authorizes no executable next work package. A new numbered
decision is required before acquiring either checkpoint/tokenizer, populating
a cache, building or qualifying the model SIF, implementing baselines or model
heads, extracting embeddings, or beginning training. Such a decision must bind
the exact accepted configuration and define its own production/independent
validation return.

Development remains encrypted until all prespecified training candidates are
complete or fail closed, every selected checkpoint and ensemble is frozen, a
complete training-artifact registry hash is independently validated, and a
further numbered decision releases development. Protected candidates and truth
remain evaluator-only after final scorer selection and one-first reservation.

Modification of frozen benchmark semantics or artifacts, new pairs or samples,
negatives or pseudo-negatives, full-universe materialization, protected or
development access, external-panel integration, structural/residue/interface
work, and unsupported probability, prevalence, biological-precision,
unseen-family, or PLM-unseen claims remain prohibited.
