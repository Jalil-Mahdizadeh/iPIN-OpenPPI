# iPIN-OpenPPI project status and execution checkpoint

**Checkpoint date:** 2026-08-08

**Execution environment:** NAISS Arrhenius; every scientific operation must run
through the pinned ARM64 Apptainer image

**Scientific programme state:** pre-split feasibility and leakage stress-test
accepted; final split construction is scientifically feasible in principle
under bounded leakage definitions but remains unauthorized; all benchmark
construction and model work remain on hold

The authoritative gate is `governance/gates/gate_status_v19.yaml`.

## Accepted audit

`DEC-0020` accepts `pre_split_feasibility_and_leakage_stress_test_v1` as
technically complete. The production audit ran from clean commit
`2dcd8b3585159a5d747176d36e08a57a11cb0950`. Independent validation ran from
clean commit `f1001cc8c9bc9c16a596139f1231bfae24f74c74` and passed 13 checks with
zero warnings and zero failures.

The immutable parent remains exactly 17,000 endpoints and 12,467/11,311/10,497
accepted components at 40%/30%/20% identity. The audit reconstructed 58,049
released-positive pairs transiently and emitted aggregate-only summaries. It
did not emit pair, endpoint, component-membership, trial, label, or split rows.

## Feasibility disposition

- Frozen and sensitivity-union full-length graphs are robustly feasible at
  40%, 30%, and 20% identity under the prespecified aggregate opportunity
  trials.
- The local/domain union is robust at 40%, conditional at primary 30% with a
  joint pass fraction of 0.893, and conditional at 20% with a joint pass
  fraction of 0.614.
- At primary 30%, every target-valid local/domain trial passed all positive
  pair, component, and source-diversity floors. A future split is therefore
  feasible in principle but requires a constrained allocator and exact final
  verification.
- The frozen 30% graph must not be the only future leakage guard. Any later
  package must use at least the 30% full-length sensitivity union and explicitly
  handle the 30% local/domain union.

No trial was selected and no split was constructed or frozen.

## Claim boundary

A future C3 statement may refer only to both exact frozen reference-sequence
endpoints being absent from training and component-disjoint under a named,
versioned leakage definition. Unseen biological-family, family-generalization,
and exhaustive-nonhomology claims remain prohibited.

## External panels remain closed

The TF-isoform and Lambourne panels remain external-only and unused. Neither
audit may be reopened, recomputed, or extended. The TF-isoform panel remains
unsuitable for training negatives or any training role,
universal-nonbinding claims, prevalence, calibration, and unseen-endpoint or
family benchmarking.

## Binding hold

No next work package is authorized. The following remain prohibited:

- candidate-pair materialization or sampling;
- positive/unlabeled evidence indicators, negative labels, or pseudo-negatives;
- selected component assignments, C1/C2/C3 labels, or splits;
- external-panel integration;
- structural mapping or structure-derived labels;
- prevalence, probability, or calibration claims; and
- model implementation, training, tuning, selection, evaluation, routing, or
  release.

A new numbered decision is required before final split construction.
