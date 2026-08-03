# DEC-0007: Accept the primary raw-source acquisition

**Date:** 2026-08-03  
**Status:** Accepted with documented source-representation warnings  
**Decision owner:** Codex under project execution authority  
**Gate effect:** Raw-acquisition subgate passes; overall evidence gate remains in progress

## Decision

Accept acquisition run `primary-raw-v1-20260803T135432Z` as the immutable primary raw snapshot for the current evidence phase.

The run acquired all 20 approved assets, including the optional IntAct mutation table, for 1,531,969,387 payload bytes. Every payload has a read-only raw file and read-only provenance sidecar. An independent verifier recalculated all SHA-256 values, recalculated four UniProt provider MD5 values, validated the UniProt `2026_02` metalink, reinspected ZIP central directories without extraction, and found no extra, missing, partial, linked, writable, or unexpected raw files.

## Source totals

| Source | Assets | Payload bytes |
|---|---:|---:|
| HuRI/CCSB | 9 | 238,907,387 |
| UniProt | 5 | 211,388,286 |
| IntAct/IMEx | 3 | 1,060,422,391 |
| PDB/SIFTS mappings | 3 | 21,251,323 |
| **Total** | **20** | **1,531,969,387** |

## Conditions

1. Raw payloads and their sidecars remain immutable and outside Git; the acquisition manifest and verification report are committed.
2. Nature supplementary payloads remain internal-only and may not be included in public release packages.
3. The HuRI and HI-II portal-count/TSV-row discrepancies in ISSUE-0004 must be preserved and reconciled during parsing, not edited away.
4. ISSUE-0003 continues to prohibit construction of negatives from unreported HuRI pairs.
5. No label construction or model training is authorized by this decision.

## Evidence

- `data/source_manifests/acquisitions/primary-raw-v1-20260803T135432Z/ACQUISITION_MANIFEST.json`
- `artifacts/validation/source_acquisition/raw_verification_primary_v1.json`
- Acquisition-manifest SHA-256: `5750fe08eac343e23c0f0c56cf749c7477cbfd92233f2679de5fedf9d8f22231`
- Verification-report SHA-256: `c836dfd9f2755d9f4f8b10f728c2c5ae38d83351d9540dfb980203f33afcb86f`
- Downloader Git commit: `af5e122ca59a2a26bbf93cfe308dcee2132c36b7`
- Active verifier Git commit: `3c3ebf13beca859fb41bda0b5818c19ebc249ab2`
- Qualified SIF SHA-256: `9259e1953dadc502af8949fe56db1fba56f4e3711ccb7542e7feda94c4718ce5`
