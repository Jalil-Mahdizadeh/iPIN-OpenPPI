# DEC-0006: Authorize final audited source manifest set v3

**Date:** 2026-08-03  
**Status:** Accepted  
**Supersedes:** DEC-0005  
**Decision owner:** Codex under project-start authorization

## Decision

Authorize checksum-controlled acquisition inside Apptainer on Arrhenius from the sole active index:

`data/source_manifests/PREACQUISITION_INDEX_v3.yaml`

The source/license subgate passes with conditions. The overall evidence gate remains in progress.

## Why a superseding decision was required

The first no-payload URL preflight detected that SIFTS's rolling files had advanced from the web-indexed 2026-07-12 state to live 2026-07-26 files. The stale draft was rejected before download. Manifest set v3 binds the current byte lengths, ETags, modification timestamps, and release-specific destinations. A second preflight passed all 20 asset checks.

HuRI v2 also separates portal data licensed CC BY 4.0 from publisher-hosted supplementary material whose raw redistribution is not authorized.

## Authorized operations

- atomic raw download to declared release/snapshot paths;
- response-header capture, byte counts, provider checksum verification where available, and local SHA-256;
- safe archive inspection and format detection;
- provenance-preserving parsing for quality control and coverage measurement.

## Not authorized

- deriving negatives from unreported HuRI or IntAct pairs;
- treating technical failure, invalidity, or autoactivation as a negative;
- treating IntAct spoke/matrix expansions as direct binary observations;
- acquiring computed structures as experimental evidence;
- downloading PDB coordinate payloads before reviewed child manifests;
- redistributing Nature supplementary files;
- building training labels or training a scientific model.

## Evidence

- `governance/licenses/SOURCE_LICENSE_REGISTER_v3.md`
- `configs/source_policy_v1.yaml`
- `data/source_manifests/ACTIVE_MANIFEST_SET_v3.md`
- `artifacts/validation/source_manifests/preacquisition_validation_v3.json`
- `artifacts/validation/source_manifests/preacquisition_url_probe_v3.json`
- `governance/issues/ISSUE-0003-huri-attempted-pair-universe.md`
