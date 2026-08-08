# DEC-0018: Accept the benchmark-eligibility and sequence-component audit

**Date:** 2026-08-08

**Status:** Accepted and effective as a technical M0 subgate; downstream
construction remains on governance hold

**Decision owner:** Codex under delegated project-execution authority

**Controlling records:** `DEC-0012`, `DEC-0017`, and
`governance/checkpoints/RESUME-001-post-tf-isoform-audit.md`

## Decision

Accept `benchmark_eligibility_and_sequence_component_audit_v1` as technically
complete. Its independent validator passed 21 checks with zero warnings and
zero failures. The production run was made from clean commit
`3ea96166eab2c3600a290ee8109410a7d040b153`; the final independent validator
ran from clean commit `d0ed03735ce6adb0566c39c4396ad08b669f20c4`.

This acceptance closes only the bounded audit authorized by `DEC-0012` and
resumed by `DEC-0017`. It does not authorize candidate-pair materialization,
labels, C1/C2/C3 assignments, splits, structural mappings, or model work. The
project has returned to governance and no downstream work package is
authorized by this record.

The primary design remains **reference-sequence positive-unlabeled ranking
(PU-R)**. Unreported eligible pairs remain unlabeled.

## Accepted evidence

| Evidence | SHA-256/result |
|---|---|
| Production audit report | `6f77fe0fb65205e0a45dd9c61631a3982c4b999efc0c5575f1799b7a726df41c` |
| Independent validation report | 21 pass, 0 warning, 0 fail; `6fd3b822c9c02e138d94f6ea78386fcdea2f43acff9156f5fc0e0a4e632f58a8` |
| Production run manifest | `81af038c3468e5b15f0e9dc287fd8f191181a059cfed239a9e36485c82cc47b4` |
| Canonical audit manifest | `1a7769fa550ac7eef9acd40da72c8f5247c0c81cb1bb77a913e185d090d83f96` |
| Frozen audit configuration | `b3bc6d802799d2fb47f351b6311c951945a8517d27e573be7fc4209e452a22e5` |
| Canonical schema | `60698389ee17e5c9d2cf8a586fbe92af9ef331120d01785f13b071759749a481` |

The expert-facing interpretation is
`docs/reports/m0/M0_Benchmark_Eligibility_and_Sequence_Component_Audit_Final_v1.md`.

## Accepted findings

- Frozen Space III contains 17,408 genes. Exactly 17,172 genes are usable under
  the frozen reference-sequence rule, representing 17,000 distinct sequences
  and 17,033 UniProt accessions.
- The mapping states are 17,121 unique reference sequences, 51
  sequence-equivalent multi-accession mappings, 16 ambiguous multi-sequence
  exclusions, and 220 unmapped exclusions. No imputation was performed.
- The unordered eligible endpoint universe is exactly
  `C(17,000, 2) = 144,491,500`. This is an algebraic count only: no candidate
  pair rows were materialized and the universe was not called tested.
- Source-faithful selenocysteine was retained in 18 eligible sequences, with
  19 `U` residues. No residue was silently rewritten.
- Under exact bidirectional endpoint coverage of at least 80%, deterministic
  components number 12,467 at 40% identity, 11,311 at 30%, and 10,497 at 20%.
  Their largest components contain 312, 362, and 485 sequences, respectively.
- Of 220,934 positive-source evidence rows, 212,156 map to eligible distinct
  sequence endpoints and collapse to 58,049 distinct eligible positive
  sequence pairs. These are positive-evidence aggregates only, not a pair
  table or a positive/unlabeled label construction.
- The total-component and total-positive-pair count floors are met at all
  three thresholds. This is a pre-split necessary-condition result only. It
  does not establish held-out feasibility, determine a threshold, or
  authorize any C1/C2/C3 or train/dev/test assignment.

## Fail-closed disposition

The frozen MMseqs2 search produced 163,441 raw alignment records. Independent
integer-identity and endpoint-coverage recomputation found zero structurally
invalid records. It excluded and counted 531 search candidates below the exact
identity criterion; none failed the exact endpoint-coverage criterion. The
remaining records normalized to 75,662 non-self unordered edges at the 20%
threshold. The threshold was not relaxed and rejected candidates were not
admitted.

Every canonical table, raw alignment, normalized edge file, input hash,
manifest, schema, permission, component assignment, aggregate, and governance
guard was independently checked. The validator also confirmed that no
candidate-pair, label, split, prevalence, calibration, structure, external
panel, or model output was constructed.

## External-panel disposition remains binding

`DEC-0017` is unchanged. The TF-isoform panel remains external-only and is
unsuitable for training negatives or any training role, universal-nonbinding
claims, prevalence estimation, calibration, and unseen-endpoint or
family-generalizing benchmarking. Neither that panel nor the Lambourne panel
was used by this audit. Neither external audit was reopened, recomputed, or
extended.

## Continuing prohibitions and next authority

This decision authorizes no next work package. In particular, it does not
authorize:

- candidate-pair materialization or a claim that the algebraic universe was
  experimentally tested;
- positive/unlabeled evidence-indicator construction, negative labels,
  pseudo-negatives, or universal-nonbinding claims;
- C1/C2/C3 assignment, threshold selection, partitioning, or train/dev/test
  split construction;
- prevalence estimation, calibration, probability interpretation, or use of
  external-panel outcomes;
- structural mapping or structure-derived labels; or
- model implementation, training, tuning, selection, routing, or release.

Any subsequent benchmark-construction unit requires a new explicit governance
authorization that preserves the accepted PU-R estimand and claim ceiling.
