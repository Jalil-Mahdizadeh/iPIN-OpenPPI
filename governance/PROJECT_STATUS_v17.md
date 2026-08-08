# iPIN-OpenPPI project status and execution checkpoint

**Checkpoint date:** 2026-08-08

**Execution environment:** NAISS Arrhenius; every scientific operation must run
through the pinned ARM64 Apptainer image

**Scientific programme state:** benchmark-eligibility and sequence-component
audit technically accepted after independent validation; primary PU-R design
preserved; project returned to governance with all downstream work on hold

The authoritative gate is `governance/gates/gate_status_v17.yaml`.

## External-panel governance remains closed

`DEC-0017` remains effective without modification. The completed TF-isoform
audit and `DEC-0016` disposition are technically accepted. The panel remains
an **external-only diagnostic candidate** and is unsuitable for training
negatives or any other training role, universal-nonbinding claims, prevalence
estimation, calibration, or unseen-endpoint/family benchmarking.

The TF-isoform and Lambourne external audits were not reopened, recomputed, or
extended during the sequence-component work. Their outcomes were not used as
inputs.

## Completed bounded audit

`DEC-0018` accepts
`benchmark_eligibility_and_sequence_component_audit_v1` as technically
complete. The independent validator passed 21 checks with zero warnings and
zero failures.

The audit executed exactly the work authorized at
`governance/checkpoints/RESUME-001-post-tf-isoform-audit.md`:

- froze the eligibility, mapping, identity, coverage, and tool semantics;
- accounted for every Space III gene without imputation;
- counted the unordered endpoint universe algebraically without materializing
  pair rows;
- constructed deterministic 40%, 30%, and 20% sequence components under exact
  bidirectional coverage;
- reported only aggregate positive mapping and pre-split component feasibility;
  and
- independently reconstructed all consequential eligibility, edge, component,
  and aggregate results.

## Accepted aggregate results

| Result | Accepted value |
|---|---:|
| Space III genes | 17,408 |
| Eligible genes | 17,172 |
| Distinct eligible reference sequences | 17,000 |
| Eligible UniProt accessions | 17,033 |
| Algebraic unordered non-self endpoint count | 144,491,500 |
| Components at 40% identity | 12,467 |
| Components at 30% identity | 11,311 |
| Components at 20% identity | 10,497 |
| Distinct eligible positive sequence pairs, ALL | 58,049 |

The mapping states are 17,121 unique, 51 sequence-equivalent multi-accession,
16 ambiguous multi-sequence, and 220 unmapped genes. The latter two states are
excluded. Eighteen eligible sequences contain 19 source-faithful
selenocysteine residues.

The MMseqs2 run produced 163,441 raw alignment records. Independent exact
postfiltering found zero structurally invalid records and excluded 531 records
below the exact identity rule. No threshold was relaxed. The accepted 20%
edge set contains 75,662 normalized non-self edges.

Total component and positive-pair count floors are met at each threshold. This
is a pre-split necessary-condition result only. It does not determine a split,
threshold, leakage profile, held-out floor, or expected generalization.

## Immutable evidence

- production commit:
  `3ea96166eab2c3600a290ee8109410a7d040b153`;
- clean validator commit:
  `d0ed03735ce6adb0566c39c4396ad08b669f20c4`;
- production audit report SHA-256:
  `6f77fe0fb65205e0a45dd9c61631a3982c4b999efc0c5575f1799b7a726df41c`;
- independent validation SHA-256:
  `6fd3b822c9c02e138d94f6ea78386fcdea2f43acff9156f5fc0e0a4e632f58a8`;
- production run manifest SHA-256:
  `81af038c3468e5b15f0e9dc287fd8f191181a059cfed239a9e36485c82cc47b4`;
- canonical manifest SHA-256:
  `1a7769fa550ac7eef9acd40da72c8f5247c0c81cb1bb77a913e185d090d83f96`;
- pinned container SHA-256:
  `72e4a13299df1c7036dbf5c8845f3a1d9d02bf6143bd2e4ee675aabd03112629`.

The final interpretation is
`docs/reports/m0/M0_Benchmark_Eligibility_and_Sequence_Component_Audit_Final_v1.md`.

## Current stopping point

The bounded audit has returned to governance. No next work package is
authorized. The primary design remains reference-sequence PU-R and unreported
eligible pairs remain unlabeled.

The following remain prohibited:

- candidate-pair materialization or describing the algebraic universe as
  tested;
- positive/unlabeled evidence-indicator construction, negative labels,
  pseudo-negative sampling, or universal-nonbinding claims;
- threshold selection, C1/C2/C3 assignment, partitioning, or train/dev/test
  split construction;
- external-panel use, prevalence estimation, calibration, or probability
  interpretation;
- structural mapping or structure-derived training labels; and
- model implementation, training, tuning, selection, routing, or release.

Any continuation requires an explicit new governance decision.
