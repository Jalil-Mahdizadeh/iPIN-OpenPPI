# Primary raw acquisition v1

Run ID: `primary-raw-v1-20260803T135432Z`

The adjacent `ACQUISITION_MANIFEST.json` is the tracked inventory for 20 immutable payloads stored under `data/raw/`. Raw payloads and their per-file `.acquisition.json` sidecars are intentionally excluded from Git because of size and source redistribution controls.

The acquisition manifest records the exact downloader commit and qualified Apptainer lock, request/final URLs, HTTP metadata, byte counts, SHA-256 values, provider checksums, detected formats, and non-extracting archive safety results.

Independent verification is recorded at `artifacts/validation/source_acquisition/raw_verification_primary_v1.json`. Do not edit or replace any raw payload. Any upstream correction or later release requires a new release/snapshot directory and a new acquisition run.
