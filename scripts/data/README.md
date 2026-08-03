# Data acquisition utilities

All scientific-source acquisition commands must run inside the qualified Apptainer SIF from the repository root.

Active tools:

- `validate_preacquisition_manifests.py`: validates manifest structure and label-safety guards.
- `probe_preacquisition_urls_v2.py`: performs no-payload HTTP metadata checks.
- `fetch_source_policy_snapshots.py`: freezes official policy pages.
- `acquire_manifest_assets.py`: whitelist-only atomic downloader with immutable raw files, per-file provenance sidecars, SHA-256, provider-checksum validation, archive safety inspection, resumable verification, and a final acquisition manifest.

The acquisition tool refuses host-native execution, dirty tracked code, URLs outside its fixed provider whitelist, paths outside `data/raw/`, symbolic-link traversal, overwrites, missing provenance sidecars, unsafe ZIP members, or any manifest that permits label construction or model training.
