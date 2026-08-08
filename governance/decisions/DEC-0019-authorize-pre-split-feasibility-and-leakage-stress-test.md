# DEC-0019: Authorize the bounded pre-split feasibility and leakage stress-test

**Date:** 2026-08-08

**Status:** Accepted and effective for this audit only

**Decision basis:** Explicit expert-group instruction supplied by the project
owner in the active session

**Controlling record:** `DEC-0018`

## Decision

Authorize `pre_split_feasibility_and_leakage_stress_test_v1` as the sole next
technical work package. This is a label-free, aggregate-only child audit of the
immutable evidence accepted by `DEC-0018`. It is not benchmark construction and
does not reopen, recompute, replace, or modify the accepted eligibility or
40%/30%/20% component artifacts.

The work package shall:

1. verify and consume the frozen 17,000 reference-sequence endpoints, existing
   40%/30%/20% MMseqs2 components, positive-source inputs, manifests, and hashes;
2. reconstruct qualifying released-positive sequence pairs transiently in
   memory and emit only aggregate network, source, component, and feasibility
   summaries;
3. quantify endpoint and component positive degree, positive-edge
   concentration, within/cross-component evidence, and HI-II-14/HuRI source
   composition;
4. run aggregate, ephemeral component-allocation trials at the accepted
   70%/15%/15% targets to assess C1, exclusive-C2, and C3 opportunity counts at
   40%, 30%, and 20% identity without selecting or emitting any assignment;
5. execute a separately parameterized MMseqs2 sensitivity challenge against
   the primary 30% full-length graph and report both newly recovered qualifying
   edges and accepted edges not rediscovered;
6. search for substantial local/domain-level similarity that may escape the
   accepted 80%-of-both-endpoints rule, construct stricter leakage graphs only
   in memory, and report how their aggregate component and positive-evidence
   statistics change;
7. independently reconstruct and validate every consequential count; and
8. return a governance disposition on final-split feasibility and the exact
   leakage and claim language that a later split may use.

## Necessary interpretation of the expert comment

The requested completeness check is a **sensitivity challenge**, not proof that
all biologically homologous or qualifying pairs have been exhaustively found.
MMseqs2 is heuristic, and absence of a recovered edge cannot establish absence
of homology.

The requested train/development/test assessment authorizes only ephemeral
allocation trials whose identities are discarded. The audit may emit trial
distributions and feasibility rates, but it may not select a winning trial,
persist a component-to-partition row, assign a pair to C1/C2/C3, or create an
immutable split. C1/C2/C3 counts are explicitly **opportunity counts** under
hypothetical allocations, not benchmark labels.

An unseen-family claim may be recommended only if the evidence supports a
precisely operationalized family definition. Otherwise the disposition must
reject that wording and limit any future C3 language to exact endpoints and
the named, versioned sequence-similarity rule.

## Binding scientific design

- The primary design remains reference-sequence positive-unlabeled ranking
  (PU-R); unreported eligible pairs remain unlabeled.
- The accepted 30% identity graph with at least 80% coverage of each endpoint
  remains the primary component definition. The 40% and 20% graphs remain
  sensitivity definitions.
- A stricter leakage control may add statistically filtered local/domain edges
  to an accepted graph; it may not delete an accepted edge or silently relax an
  exact criterion.
- Allocation feasibility is a necessary pre-split result only. Later evidence
  grouping, source, assay, and temporal constraints may reduce retained counts.
- The 500 released-positive-pair and 50 independent-component floors remain
  pre-model gates. A 30% C3 headline regime must be demoted if either floor or
  meaningful source diversity is not robustly retained.
- Every scientific operation must run in the pinned ARM64 Apptainer image.

## Continuing prohibitions

This decision does **not** authorize:

- full candidate-pair materialization or candidate sampling;
- positive/unlabeled evidence-indicator tables, negative labels, or
  pseudo-negative sampling;
- persisted C1/C2/C3 labels, component-to-partition assignments, or frozen
  train/development/test splits;
- external diagnostic-panel integration or reopening either external audit;
- structural mapping or structure-derived labels;
- model implementation, training, tuning, selection, evaluation, calibration,
  routing, or release;
- prevalence or probability interpretation; or
- a change to the PU-R estimand or claim ceiling.

The TF-isoform and Lambourne panels remain external-only and unused. The
TF-isoform panel remains unsuitable for training negatives or any training
role, universal-nonbinding claims, prevalence, calibration, and
unseen-endpoint/family benchmarking.

## Required return

Production and independent validation must run from clean commits. The work
must return to governance with immutable manifests, a scientific report, an
explicit disposition, and a new gate. Final split construction remains on hold
unless a later numbered decision authorizes it.
