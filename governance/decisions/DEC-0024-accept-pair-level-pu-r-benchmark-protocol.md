# DEC-0024: Accept and freeze the pair-level PU-R benchmark protocol

**Date:** 2026-08-08

**Status:** Accepted and effective as the immutable pair-level benchmark
protocol; benchmark-row construction and all model work remain unauthorized

**Decision owner:** Codex under delegated project-execution authority

**Controlling records:** DEC-0022 and DEC-0023

## Decision

Accept configuration revision 2 of pair_level_pu_r_benchmark_protocol_v1 as
technically complete and freeze it before any model result exists.

Production ran from clean commit
8ee0ae58b365c68ffb5732c9995803d24e5fe6fa and passed 16 checks with zero
warnings and zero failures. Independent validation ran from clean commit
d32a26508eb9438cb693ae1ae3cf48f5324a37f7 and passed 18 checks with zero
warnings and zero failures.

The accepted protocol is scientifically feasible for later construction under
the frozen DEC-0022 endpoint/component skeleton. It preserves the primary
reference-sequence positive-unlabeled ranking design. Unreported eligible pairs
remain unlabeled.

## Accepted information and visibility boundary

The accepted evidence snapshot is the published-2020 HI-II-14/HuRI union pinned
by its acquisition, staging, reconciliation, and eligibility manifests.
Sequence endpoints remain the frozen UniProt 2026_02 reference-sequence
SHA-256s. The partition remains final_benchmark_component_split_v1 under 30%
local_domain_union.

Only training-role train/train positives may enter interaction supervision.
Development evidence becomes available only after a trained artifact is
frozen. Protected-test pair identities and metrics remain sealed behind a
read-only, one-first-evaluation evaluator.

Post-cutoff evidence, external panels, structures, teacher predictions,
protected labels, source/assay/publication fields, and protected full-graph
degree may not enter training, tuning, candidate exclusion, or model features
except where the accepted protocol explicitly permits curator-only visible
evidence for a named auxiliary diagnostic.

## Accepted pair rules

One unordered exact frozen-sequence pair has one full SHA-256 pair identifier
and one role across every reverse orientation, source observation, study,
construct, assay record, and repetition.

The C1 train/development/test role is the frozen 70/15/15 SHA-256 bucket rule
with public salt ipin-openppi-pair-level-pu-r-protocol-v1 and seed 20260803.
Training exposure is degree at least one using only C1 training-role positives.

- C1 requires two exposed training endpoints and a withheld development/test
  pair role.
- Exclusive C2 requires exactly one exposed training endpoint and one endpoint
  in the named held-out partition.
- C3 requires both exact endpoints in the same named held-out partition. Both
  are absent from interaction-supervised training and component-disjoint from
  training under local_domain_union_30.

Pairs failing exposure, partition, mapping, cutoff, or evidence-group guards
are quarantined and never reassigned.

## Accepted feasibility

Interaction supervision contains 16,799 released-positive pairs and exposes
4,675 training endpoints. Primary development/test positive counts are
3,259/3,187 for C1, 11,327/13,446 for C2, and 2,265/2,379 for C3. Every primary
cell passes the 500-pair, 50-component, and 50-pairs-per-source floors.

No pair or candidate rows were persisted to reach this disposition.

## Accepted unlabeled-sampling protocol

A later separately authorized construction must use deterministic stratified
bottom-SHA-256 sampling without replacement, salt ipin-openppi-benchmark-v1,
seed 20260803, fixed training-positive degree bins, one seat per nonempty
stratum, and Hamilton proportional apportionment. Each unlabeled stratum has
inclusion probability m_h / N_h and weight N_h / m_h; positives have probability
and weight 1.

The training cap is 2,000,000. Each C1/C2/C3 development/test cap is 1,000,000.
Strict source diagnostics use canonical cell identifier
source_exclusive:{target_source}:{primary_cell}. No sample was realized by this
decision.

## Accepted evaluation and uncertainty

Primary reporting consists of PU pairwise concordance with
Horvitz-Thompson weights, held-out-positive Recall@10/100/1000,
released-positive enrichment at candidate fractions 0.0001/0.001/0.01, and
positive rank percentile. Cells remain separate. Pair identifiers break score
ties deterministically.

Primary uncertainty is a 2,000-replicate two-endpoint
local_domain_union_30-component pigeonhole bootstrap with seed 20260803 and
PCG64DXSM. Paired comparisons reuse candidate samples and bootstrap draws.

Degree/hub strata and the frozen simple hash, endpoint-degree,
preferential-attachment, and component-degree-mass baselines use only the
training-positive graph. They are definitions for later work, not implemented
models.

## Auxiliary holdout disposition

A strict named-source diagnostic is supported with cellwise minimum-size
demotion and does not support an independent-study claim. HI-II-14-target C1
and C3 cells are descriptive only; its C2 cells pass. HuRI-target cells pass.

Independent study, assay-version/batch, and temporal holdouts are inactive
because the frozen evidence does not identify independent studies, has zero
assay-version/batch coverage, and provides only shared source-release date
metadata. These axes may not be inferred or pooled.

## Claim disposition

C3 means only both exact frozen reference-sequence endpoints absent from
interaction-supervised training and component-disjoint under
local_domain_union_30. It does not authorize unseen biological family,
family-generalization, unseen domain, PLM-unseen protein, or exhaustive
nonhomology claims.

Unlabeled-is-negative, universal-nonbinding, prevalence, biological precision,
calibration, and probability claims remain prohibited. The TF-isoform panel
remains external-only and unsuitable for training negatives or any training
role, universal-nonbinding claims, prevalence, calibration, and
unseen-endpoint/family benchmarking.

## Accepted evidence

| Evidence | SHA-256/result |
|---|---|
| Configuration revision 2 | 7b0cefa1b461f0e58d3e6f4ff72da2d6ad4ac39522a897ce4057e756fa84f2a6 |
| Production audit | b226a83fa31a78aa97cc6172adb65b386f0181b86ab2c7cb0939cf6dd4ea9d66; 16 pass |
| Independent validation | 8c94f10131ed7e100fadf1dc6174c4aaf7b5301d3dbece74725a994183a10741; 18 pass |
| Frozen split manifest | 81800ec810d83a53d83e36dca277a425e4a8fd1f7f50009916da73e14021351a |
| Production commit | 8ee0ae58b365c68ffb5732c9995803d24e5fe6fa |
| Validation commit | d32a26508eb9438cb693ae1ae3cf48f5324a37f7 |

The expert-facing interpretation is
docs/reports/m0/M0_Pair_Level_PU_R_Benchmark_Protocol_Final_v1.md.

The earlier unrevisioned protocol audit is retained as immutable
pre-hardening qualification history and is not accepted evidence.

## Continuing hold

This decision freezes rules only and authorizes no next work package. It does
not authorize pair-row or evidence-indicator construction, candidate-universe
materialization, unlabeled-sample realization, negative or pseudo-negative
creation, frozen-split modification, external-panel or structural-label work,
or model implementation, embedding, training, tuning, selection, calibration,
evaluation, routing, or release.
