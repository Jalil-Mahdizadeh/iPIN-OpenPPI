# M0 final primary raw acquisition and integrity report

**Project:** iPIN-OpenPPI  
**Date:** 2026-08-03  
**Run:** `primary-raw-v1-20260803T135432Z`  
**Executor:** Codex  
**Runtime:** Qualified Apptainer SIF on NAISS Arrhenius  
**Result:** **PASS WITH TWO SOURCE-REPRESENTATION WARNINGS**

## Executive result

All 20 assets authorized by `PREACQUISITION_INDEX_v3.yaml` were acquired successfully. The immutable snapshot contains 1,531,969,387 scientific payload bytes. There were no transfer errors, retries, missing assets, checksum failures, unsafe archive paths, linked raw paths, partial files, writable raw files, or unexpected files.

The raw-acquisition subgate passes. The evidence gate remains in progress: parsing and evidence-schema quality control may start, but training-label construction and model training remain prohibited.

## Safe cleanup

Before acquisition, four verified ignored/generated targets were removed:

- 11 GB of OCI/Apptainer build-cache blobs reproducible from the locked definition;
- an empty torchelastic runtime tree; and
- two Python bytecode caches.

No tracked files or symbolic links were present. The qualified SIF, locks, logs, policies, decisions, and validation history were preserved.

## Acquisition controls

The downloader was tested, committed at `af5e122ca59a2a26bbf93cfe308dcee2132c36b7`, and only then used inside Apptainer. It enforced the active manifest, a fixed HTTPS host whitelist, repository/raw-zone containment, symlink rejection, a clean tracked worktree, atomic same-directory downloads, no overwrites, streaming SHA-256/provider checksums, declared HTTP metadata, archive safety, and read-only payload/sidecar permissions.

Every raw payload has a `.acquisition.json` sidecar recording its source manifest hash, requested and final URLs, response headers, byte count, SHA-256, provider checksum, detected format, timestamp, and immutability state.

## Payload totals

| Source | Assets | Payload bytes |
|---|---:|---:|
| HuRI/CCSB | 9 | 238,907,387 |
| UniProt | 5 | 211,388,286 |
| IntAct/IMEx | 3 | 1,060,422,391 |
| PDB/SIFTS mappings | 3 | 21,251,323 |
| **Total** | **20** | **1,531,969,387** |

## Independent integrity verification

The independently tested verifier, active at commit `3c3ebf13beca859fb41bda0b5818c19ebc249ab2`, then:

- recalculated all 20 SHA-256 values;
- recalculated all four UniProt MD5 values;
- matched the downloader bytes to its recorded Git commit;
- verified the qualified-container lock;
- matched every raw sidecar to the acquisition manifest;
- confirmed 20 read-only payloads and 20 read-only sidecars;
- found only those 40 files plus `data/raw/README.md`;
- found no missing, extra, partial, linked, or writable raw files;
- validated release `2026_02`, CC BY 4.0 metadata, sizes, and MD5 values directly from UniProt's acquired metalink; and
- independently inventoried all text, gzip, PDF, and ZIP containers.

Final integrity result: **pass**, 20 assets, 1,531,969,387 bytes, zero errors.

## Format-level inventory

These counts describe raw source representations, not biological labels.

### HuRI/CCSB

| Asset | Inventory |
|---|---:|
| HuRI gene-pair TSV | 52,548 unique rows |
| HuRI detailed PSI-MI | 171,545 rows; 42 fields in every row |
| Test-space screens-19 TSV | 1,159 rows |
| Lit-BM TSV | 13,441 rows |
| HI-II-14 gene-pair TSV | 13,633 unique rows |
| HI-II-14 detailed PSI-MI | 49,389 rows; 42 fields in every row |
| HuRI supplementary ZIP | 60 safe members; 57,919,248 uncompressed bytes |
| Methods/table-guide PDFs | Both signatures passed |

The supplementary ZIP contains 50 text files, six XLS files, two XLSX files, one directory, and one macOS metadata file. It was not extracted.

### UniProt

| Asset | Inventory |
|---|---:|
| Canonical FASTA | 20,652 sequences |
| Additional/isoform FASTA | 148,985 sequences |
| Canonical DAT | 20,652 records |
| ID mapping | 4,377,974 lines |
| Release metalink | Release/license and all four acquired payloads cross-validated |

Canonical and additional sequences remain separate. Equal canonical FASTA and DAT counts provide an internal consistency check.

### IntAct/IMEx

| Asset | Inventory |
|---|---:|
| Human PSI-MI XML 3.0 ZIP | 329 XML files; 17,520,515,023 uncompressed bytes |
| Controlled vocabulary | 4,082 terms |
| Mutation annotations | 89,926 lines |

The ZIP has no unsafe paths, symlinks, encryption, or excessive compression ratio and was not extracted. Its XML members will be parsed while preserving original n-ary interactions.

### SIFTS

| Asset | Raw line count |
|---|---:|
| Chain–UniProt | 1,007,699 |
| Chain–taxonomy | 1,076,306 |
| Observed UniProt segments | 1,519,872 |

These are raw line counts; parser QC will separately count headers/comments and data records.

## Provider-count discrepancies

Two portal headline counts differ from their immutable gene-pair TSV rows:

| Dataset | Portal count | TSV rows | Difference |
|---|---:|---:|---:|
| HuRI | 52,569 | 52,548 | -21 |
| HI-II-14 | 13,993 | 13,633 | -360 |

Test-space screens-19 and Lit-BM match exactly. The mismatch is not a byte-integrity problem: detailed PSI-MI files contain many assay/evidence rows per derived gene-pair view. Construct/isoform mappings, orientation, repeated evidence, self-pair filtering, and deduplication must be reconciled explicitly.

No raw row will be added, removed, or collapsed to force agreement. ISSUE-0004 tracks the transformation audit.

## Scientific implications

The project now has locally frozen and independently verifiable sequence, interaction-evidence, controlled-vocabulary, mutation, and structural-mapping sources. The inventories confirm why evidence records must remain primary and consensus pairs derived.

ISSUE-0003 remains unchanged: the complete HuRI attempted/evaluable negative universe is not available publicly. Missing records remain unknown and cannot become negatives.

## Gate and next unit

The raw-acquisition subgate passes with documented representation warnings. The next authorized unit is source-specific parsing into a construct-aware evidence schema, accompanied by mapping and reconciliation reports. No labels or training are authorized yet.

## Reproducibility records

- Acquisition manifest: `data/source_manifests/acquisitions/primary-raw-v1-20260803T135432Z/ACQUISITION_MANIFEST.json`
- Acquisition-manifest SHA-256: `5750fe08eac343e23c0f0c56cf749c7477cbfd92233f2679de5fedf9d8f22231`
- Verification report: `artifacts/validation/source_acquisition/raw_verification_primary_v1.json`
- Verification-report SHA-256: `c836dfd9f2755d9f4f8b10f728c2c5ae38d83351d9540dfb980203f33afcb86f`
- Qualified SIF SHA-256: `9259e1953dadc502af8949fe56db1fba56f4e3711ccb7542e7feda94c4718ce5`
