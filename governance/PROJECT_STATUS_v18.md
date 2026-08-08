# iPIN-OpenPPI project status and execution checkpoint

**Checkpoint date:** 2026-08-08

**Execution environment:** NAISS Arrhenius; every scientific operation must run
through the pinned ARM64 Apptainer image

**Scientific programme state:** accepted sequence-component audit preserved;
bounded pre-split feasibility and leakage stress-test authorized but not yet
executed; all benchmark construction and model work remain on hold

The authoritative gate is `governance/gates/gate_status_v18.yaml`.

## Authorization now active

`DEC-0019` records the expert group's explicit authorization for
`pre_split_feasibility_and_leakage_stress_test_v1`. The unit may consume the
immutable `DEC-0018` artifacts, reconstruct released-positive sequence pairs
transiently, execute separately parameterized full-length and local/domain
MMseqs2 sensitivity searches, and emit aggregate-only feasibility and leakage
summaries.

Hypothetical 70%/15%/15% component allocations may exist only in memory during
the run. No selected trial, endpoint/component partition, positive pair, or
C1/C2/C3 label may be emitted. Reported C1/C2/C3 quantities are opportunity
counts under ephemeral allocations, not split assignments.

The sensitivity search can identify parameter-sensitive or residual similarity
edges. It cannot prove an exhaustive absence of homology or define a universal
protein family.

## Immutable parent evidence

The following accepted facts and artifacts remain unchanged:

- 17,000 distinct eligible frozen reference sequences;
- 12,467, 11,311, and 10,497 components at 40%, 30%, and 20% identity;
- 58,049 distinct eligible released-positive sequence pairs in aggregate;
- the accepted full-length alignment rule of at least 80% coverage of both
  endpoints;
- the primary reference-sequence PU-R design and its claim ceiling; and
- the hashes and technical acceptance recorded in `DEC-0018`.

This child audit must not rewrite or replace any accepted canonical or run
artifact from `benchmark_eligibility_and_sequence_component_audit_v1`.

## External panels remain closed

The TF-isoform and Lambourne audits are not inputs and may not be reopened,
recomputed, or extended. The TF-isoform panel remains external-only and is
unsuitable for training negatives or any training role,
universal-nonbinding claims, prevalence, calibration, and unseen-endpoint or
family benchmarking.

## Binding hold

The following remain prohibited:

- full candidate-pair materialization or candidate sampling;
- positive/unlabeled evidence indicators, negative labels, or pseudo-negatives;
- persisted C1/C2/C3 assignments or train/development/test splits;
- external-panel integration;
- structural mapping or structure-derived labels;
- prevalence, probability, or calibration claims; and
- model implementation, training, tuning, selection, evaluation, routing, or
  release.

The audit must return to governance after independent validation. Final split
construction requires a later numbered decision even if feasibility passes.
