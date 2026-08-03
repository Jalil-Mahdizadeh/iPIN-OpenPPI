# Raw-acquisition verification

Use `verify_raw_acquisition_v2.py` as the verification entry point. It hardens all repository-path resolution against direct and parent-component symbolic links, records its Git and byte-level code provenance, and delegates format-specific inventory work to `verify_raw_acquisition.py`.

The verifier independently recalculates every payload SHA-256, recalculates UniProt provider MD5 values, compares immutable per-file sidecars, enforces read-only raw permissions, inventories text/gzip/ZIP formats without extracting archives, checks published HuRI pair counts, validates the UniProt release and license metalink, and rejects extra, missing, linked, or partial files in `data/raw/`.
