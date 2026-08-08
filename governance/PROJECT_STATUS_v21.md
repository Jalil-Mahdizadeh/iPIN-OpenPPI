# iPIN-OpenPPI project status and execution checkpoint

**Checkpoint date:** 2026-08-08

**Execution environment:** NAISS Arrhenius; every scientific operation must run
through the pinned ARM64 Apptainer image

**Scientific programme state:** final benchmark endpoint/component partition
skeleton accepted and frozen; pair-level benchmark construction and all model
work remain unauthorized

The authoritative gate is `governance/gates/gate_status_v21.yaml`.

## Frozen benchmark component split

`DEC-0022` accepts `final_benchmark_component_split_v1` as technically complete.
Production ran from clean commit
`d348a027243e3409fefd62bb1027e774dbb7cde6`; independent validation ran from
clean commit `410b0d0d19c53008e35c4bdac3c286da0b249d26` and passed all 20 checks with
zero warnings and zero failures.

The 30% `local_domain_union` primary rule produced 2,653 valid allocations
among 4,096 candidates. Frozen candidate 1,064 assigns exactly 11,900/2,550/
2,550 endpoints and 5,427/1,071/1,284 components to training/development/test.
There are zero crossing edges and zero split components under both the selected
local/domain graph and the 30% full-length sensitivity union. The fallback was
not evaluated.

## Opportunity evidence

Aggregate released-positive opportunities are:

- C1 training pool: 22,333 pairs and 2,182 components;
- C2 development/test: 11,455/13,633 pairs;
- C3 development/test: 2,265/2,379 pairs and 353/505 components; and
- C3 development/test source counts: 588/510 HI-II-14 and 1,953/2,110 HuRI.

These are aggregate opportunity counts only. No pair-level C1/C2/C3 assignment
has been constructed.

## Binding C3 boundary

C3 means only that both exact frozen reference-sequence endpoints are absent
from interaction-supervised training and component-disjoint from training under
30% `local_domain_union_v1`. It does not mean unseen biological family,
unseen homolog/domain, or PLM-unseen protein and does not prove exhaustive
nonhomology.

## Parent evidence and external panels

The accepted eligibility/component and pre-split audits remain immutable and
were not reopened, recomputed, or extended. The primary reference-sequence
PU-R design is unchanged; unreported eligible pairs remain unlabeled.

The TF-isoform and Lambourne panels remain external-only and unused. The
TF-isoform panel remains unsuitable for training negatives or any training
role, universal-nonbinding claims, prevalence, calibration, and unseen-endpoint
or family benchmarking.

## Binding hold

No next work package is authorized. The following remain prohibited:

- candidate-pair materialization or sampling;
- positive/unlabeled indicator rows, negative labels, or pseudo-negatives;
- pair-level C1/C2/C3 assignment or evaluation-pair construction;
- modification of the frozen endpoint/component skeleton;
- external-panel integration;
- structural mapping or structure-derived labels;
- prevalence, probability, or calibration claims; and
- model implementation, embedding, training, tuning, selection, evaluation,
  routing, or release.

Any later pair-level benchmark construction or model work requires a new
numbered authorization.
