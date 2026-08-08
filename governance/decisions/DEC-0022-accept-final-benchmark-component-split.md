# DEC-0022: Accept and freeze the final benchmark component split

**Date:** 2026-08-08

**Status:** Accepted and effective as the immutable benchmark
endpoint/component partition skeleton

**Decision owner:** Codex under delegated project-execution authority

**Controlling records:** `DEC-0020` and `DEC-0021`

## Decision

Accept `final_benchmark_component_split_v1` as technically complete and freeze
its selected endpoint/component assignments. Production ran from clean commit
`d348a027243e3409fefd62bb1027e774dbb7cde6`; independent validation ran from
clean commit `410b0d0d19c53008e35c4bdac3c286da0b249d26` and passed 20 checks with zero
warnings and zero failures.

The primary design remains reference-sequence positive-unlabeled ranking
(PU-R). Unreported eligible pairs remain unlabeled.

## Accepted allocation

The selected hard partition rule is 30% `local_domain_union`. Of 4,096
preregistered primary candidates, 2,653 passed every frozen acceptance
criterion. Candidate 1,064 was selected by the frozen lexicographic objective.
The 30% `sensitive_fl80_union` fallback was not evaluated because the primary
valid-candidate count was nonzero.

The immutable allocation is:

| Partition | Endpoints | Components |
|---|---:|---:|
| Training | 11,900 | 5,427 |
| Development | 2,550 | 1,071 |
| Protected test | 2,550 | 1,284 |
| **Total** | **17,000** | **7,782** |

The split has zero cross-partition edges and zero split components under both
the 176,264-edge `local_domain_union` and the 63,180-edge
`sensitive_fl80_union` at 30% identity.

## Accepted positive-evidence opportunity disposition

Aggregate released-positive opportunities are 22,333 C1 training-pool pairs,
11,455/13,633 C2 development/test pairs, and 2,265/2,379 C3
development/test pairs. Every pool passes the 500-pair, 50-component, and
50-pairs-per-source gates. These are opportunity summaries, not persisted
pair-level C1/C2/C3 labels.

## C3 and claim disposition

C3 is defined strictly as both exact frozen reference-sequence endpoints absent
from interaction-supervised training and component-disjoint from training under
30% `local_domain_union_v1`. Development and test endpoints are ineligible for
future interaction-supervised training.

This does not authorize unseen-biological-family, family-generalization,
PLM-unseen-protein, exhaustive-nonhomology, universal-nonbinding, prevalence,
calibration, or model-performance claims. “Unseen protein” may be used only
when immediately defined by the exact endpoint and named-rule statement above.

## Accepted evidence

| Evidence | SHA-256/result |
|---|---|
| Production audit report | `bbb8e65efd661342b22f54a6fa72ffe4115dfc1e18b4f97d066e4124fe9124c8` |
| Independent validation report | 20 pass, 0 warning, 0 fail; `e0864a857285c21341ce4db44d1a142ff6532101804ead5b8f421df6ab4d6e0f` |
| Production run manifest | `615051b335c25351a46a6de0eba8b87c9a82391cf7c63216c21280846b06d52e` |
| Canonical split manifest | `81800ec810d83a53d83e36dca277a425e4a8fd1f7f50009916da73e14021351a` |
| Frozen configuration | `b8dac7c7de5fc3935a5bf642afe12b2b5e7e5b40fa9883d1dc04962bfed25ecf` |
| Canonical schema | `e18c999753640c7d3b15bdaee60636d329b94ae3876cfaffc2290b7f1536ed30` |

The expert-facing interpretation is
`docs/reports/m0/M0_Final_Benchmark_Component_Split_Final_v1.md`.

## Scope confirmation

No candidate-pair universe or positive-pair rows were emitted. No negative or
pseudo-negative, evidence indicator, or pair-level C1/C2/C3 assignment was
created. No external panel, structure, model, embedding, prediction, protected-
test statistic, prevalence estimate, or calibration result entered allocation
or validation. Neither accepted parent audit was reopened, recomputed, or
extended.

`DEC-0017` remains binding: the TF-isoform panel is external-only and unsuitable
for training negatives or any training role, universal-nonbinding claims,
prevalence, calibration, and unseen-endpoint or family benchmarking.

## Continuing prohibitions and next authority

The component partition skeleton is immutable. This decision authorizes no
next work package. It does not authorize:

- candidate-pair materialization or sampling;
- positive/unlabeled evidence-indicator rows, negative labels, or
  pseudo-negatives;
- pair-level C1/C2/C3 assignment or evaluation-pair construction;
- external-panel integration or structural-label work;
- prevalence estimation, calibration, or probability interpretation; or
- model implementation, embedding, training, tuning, selection, evaluation,
  routing, or release.

Any later pair-level benchmark construction or model work requires a separate
numbered authorization and must preserve this frozen skeleton and PU-R design.
