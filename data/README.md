# Data zones

Data move only forward through explicit, manifested stages: source manifest, raw snapshot, staging parse, canonical warehouse, derived features, and frozen splits.

- `source_manifests/`: URLs, releases, licenses, retrieval times, checksums, and parser versions.
- `raw/`: immutable bytes exactly as acquired.
- `staging/`: parser outputs that preserve source-native identifiers and fields.
- `canonical/`: validated evidence records and sequence/construct mappings.
- `derived/`: features and views reproducible from canonical inputs.
- `splits/`: immutable benchmark assignments and contamination audits.

No raw source is acquired until its terms and release form are recorded in `governance/licenses/`.
