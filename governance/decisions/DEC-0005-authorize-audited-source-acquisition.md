# DEC-0005: Authorize acquisition from the audited primary sources

**Date:** 2026-08-03  
**Status:** Accepted  
**Decision owner:** Codex, acting under project-start authorization  
**Gate effect:** Source/license subgate passes with conditions; overall evidence gate remains in progress

## Decision

Authorize checksum-controlled acquisition, inside Apptainer on Arrhenius, of the assets listed by `data/source_manifests/PREACQUISITION_INDEX_v2.yaml`.

This authorization covers raw acquisition, integrity verification, format inspection, and provenance-preserving parsing for quality control. It does not authorize training-label construction or model training.

## Conditions

1. Every payload is written beneath its manifest-declared `data/raw/` release/snapshot directory and is immutable after successful verification.
2. Retrieval time, final URL, HTTP metadata, byte count, and local SHA-256 are recorded. UniProt provider MD5 values are also verified.
3. HuRI portal files may be redistributed with attribution; Nature supplements are internal-only unless separate permission is established.
4. HuRI missing pairs, invalid tests, autoactivators, and technical failures are not negatives.
5. IntAct PSI-MI XML 3.0 is primary; expanded binary projections are not direct interaction labels.
6. PDB acquisition is experimental-only and coordinate files require reviewed child manifests. Computed models are excluded.
7. All scientific acquisition and validation commands run through the qualified Apptainer SIF.

## Rationale

The four sources are technically accessible and legally reusable for the intended internal scientific work, subject to attribution and the Nature-supplement restriction. The unresolved HuRI negative universe affects statistical semantics, not the ability to begin auditable evidence acquisition. Delaying all acquisition would not resolve that issue and would prevent mapping, parser, and evidence-coverage analysis needed to choose the final estimator.

## Rejected interpretations

- Treating all unreported HuRI pairs as negatives.
- Treating the documented Space III gene set as proof that every pair was attempted and evaluable.
- Using IntAct MITAB/search-result binaries as automatically direct evidence.
- Treating AlphaFold or other computed structures as experimental PDB evidence.
- Assuming the HuRI portal CC BY declaration covers publisher-hosted supplementary files.

## Evidence

- `governance/licenses/SOURCE_LICENSE_REGISTER_v2.md`
- `configs/source_policy_v1.yaml`
- `artifacts/validation/source_manifests/preacquisition_validation_v2.json`
- `governance/licenses/snapshots/2026-08-03/SNAPSHOT_MANIFEST.json`
- `governance/issues/ISSUE-0003-huri-attempted-pair-universe.md`
