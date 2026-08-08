# DEC-0017: Accept the TF-isoform Y2H audit and quarantine disposition

**Date:** 2026-08-08

**Status:** Accepted and effective for technical disposition only

**Decision owner:** Project owner, recorded by Codex under delegated
project-execution authority

**Controlling records:** `DEC-0015`, `DEC-0016`, and
`governance/checkpoints/RESUME-001-post-tf-isoform-audit.md`

## Decision

Accept the bounded 2025 human TF-isoform Y2H/N2H semantics and contamination
audit as technically complete. Accept the disposition proposed in `DEC-0016`:
the source is an **external-only diagnostic candidate**, and every outcome
remains quarantined.

This decision does not reopen, recompute, extend, reinterpret, or supersede the
audit. It accepts the immutable evidence already produced and closes the
technical disposition action requested by `DEC-0016`.

The panel is unsuitable for:

- training negatives or any other training, tuning, selection, routing, or
  pseudo-labelling role;
- universal-nonbinding claims;
- prevalence estimation;
- calibration or thresholding; and
- unseen-endpoint or family-generalizing benchmarking.

No benchmark, label, split, integration, structural-mapping, or model work is
authorized by this acceptance.

## Accepted evidence

The technical evidence and scientific findings enumerated in `DEC-0016` are
accepted without rerunning them. The immutable evidence anchors are:

| Evidence | SHA-256/result |
|---|---|
| Production audit report | `9235569bd40adc4114c0b1f4387e57fb4fcabc823a28a3509676607ef809a281` |
| Independent validation | 26 pass, 0 warning, 0 fail; `af9297e54203b7486a883eaa555d006dfac57da232f475f165395cf888f42327` |
| Staging manifest | `49221d602c1f2d966c451985604538c045fa9ffa8744363c35824aade7a9bffc` |
| Canonical manifest | `c71de2354bacfdef43b35d7f0ecbe07851568ab4abeb6a23df7065f1d8c39b68` |
| Acquisition manifest | `1c163f8cafaad152a49cc002af66a26a0779e9387a7cc9c3fca6bfaa56f60e96` |
| Raw verification | `59c4536b3ed07f2c78349a7adbd52dce48c9ddd4e2b609d0a8440b6656ba9bf2` |

## Continuing authority

The previously authorized
`benchmark_eligibility_and_sequence_component_audit_v1` may resume exactly
from its unstarted checkpoint and unchanged scope. The primary PU-R design and
every existing fail-closed prohibition remain binding. The resumed work must
return to governance before any downstream benchmark construction.
