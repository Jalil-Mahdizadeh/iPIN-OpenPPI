# DEC-0021: Authorize the final benchmark component-partition skeleton

**Date:** 2026-08-08

**Status:** Accepted and effective for this work package only

**Decision basis:** Explicit project-owner instruction supplied in the active
session

**Controlling record:** `DEC-0020`

## Decision

Authorize `final_benchmark_component_split_v1` as the sole next technical work
package. It may construct and freeze one endpoint/component partition skeleton
from the immutable 17,000-reference-sequence universe accepted by `DEC-0018`
and the leakage evidence accepted by `DEC-0020`. It must not reopen, recompute,
replace, or modify either accepted parent audit.

The 30% `local_domain_union` is the primary hard assignment graph. Entire
connected components, never accessions or individual pairs, are assigned to
approximately 70% training, 15% development, and 15% protected test. No
component or qualifying edge under the selected hard rule may cross a
partition. The 30% `sensitive_fl80_union` may be evaluated as a fallback only
if the complete preregistered primary search yields zero allocations satisfying
every frozen acceptance criterion. Such a failure and every failed criterion
must be recorded before fallback selection.

## Frozen pre-result design

Before production selection, the configuration must freeze:

1. the candidate-generation algorithm and candidate count;
2. seed, component ordering, partition tie order, score quantization, and final
   tie-breaking;
3. the exact lexicographic selection objective;
4. endpoint-balance, positive-pair, participating-component, source-diversity,
   source-composition, development/test-balance, degree-mass, and hub-balance
   acceptance limits;
5. the C1, exclusive-C2, and C3 opportunity definitions; and
6. the primary-failure condition and fallback behavior.

Selection may use only frozen component size and released-positive network
counts, sources, endpoint degree, and hub ranks. It may not inspect or use any
model, embedding, score, prediction, protected-test performance statistic, or
future evaluation result.

## Binding C1/C2/C3 interpretation

The frozen output is a component/endpoint partition skeleton, not a pair-level
benchmark label table.

- C1 opportunity is a released-positive training/training pair whose endpoints
  each retain at least one other released-positive training partner.
- Exclusive-C2 opportunity for development or test is a released-positive
  training/held-out pair whose training endpoint has released-positive
  training exposure.
- C3 opportunity for development or test is a released-positive pair whose two
  exact endpoints are assigned to that held-out partition. Both exact frozen
  endpoints are therefore absent from interaction-supervised training, and
  their frozen component or components are disjoint from training under the
  selected rule.

Future interaction-supervised training must use training-assigned endpoints
only. Development- and test-assigned endpoints may never be introduced into
interaction-supervised training. This does not establish that a pretrained
language model did not encounter a sequence.

## Required evidence and validation

The package must independently verify:

- all 17,000 endpoint and component assignments;
- zero primary-rule component crossing;
- the selected allocation against both `local_domain_union` and
  `sensitive_fl80_union` at 30% identity;
- endpoint/component totals and fractions by partition;
- released-positive C1/C2/C3 opportunity counts and participating components;
- HI-II-14 and HuRI representation;
- endpoint degree distributions and hub concentration by partition; and
- exact adherence to the frozen candidate search, gates, objective, seed, and
  tie-breaking.

Production and independent validation must run from clean commits through the
pinned ARM64 Apptainer image. The result must return to governance with
immutable manifests, a scientific report, a numbered disposition, and a new
gate.

## Claim ceiling

If the primary graph passes, C3 may be described only as both exact frozen
reference-sequence endpoints absent from interaction-supervised training and
component-disjoint from training under the named 30%
`local_domain_union_v1` rule. This does not authorize claims of unseen genes,
isoforms, homologs, domains, biological families, or PLM-unseen proteins, nor
proof of exhaustive nonhomology.

## Continuing prohibitions

This decision does not authorize:

- candidate-pair universe materialization or sampling;
- positive/unlabeled indicator rows, negative labels, or pseudo-negatives;
- pair-level C1/C2/C3 assignments;
- external-panel integration or reopening either external audit;
- structural mapping or structure-derived labels;
- model implementation, embedding, training, tuning, selection, calibration,
  or evaluation;
- prevalence, universal-nonbinding, or calibrated-probability claims; or
- a change to the reference-sequence PU-R primary design.

The TF-isoform panel remains external-only and unsuitable for training
negatives or any training role, universal-nonbinding claims, prevalence,
calibration, and unseen-endpoint or family benchmarking.
