# Active raw-verification entry point

Run `verify_raw_acquisition_v3.py`.

The verifier is deliberately layered:

- `verify_raw_acquisition.py` provides independent hashing, sidecar comparison, format inventories, ZIP safety, UniProt metalink validation, and raw-tree completeness.
- `verify_raw_acquisition_v2.py` hardens every direct and parent path component against symbolic links and injects code provenance.
- `verify_raw_acquisition_v3.py` is the active entry point and records provider-advertised interaction counts separately from downloaded row counts.

The v3 distinction is scientifically necessary. Portal headline counts can describe a different representation or mapping level than a downloadable gene-pair TSV. A mismatch is retained as a source-representation warning; it is not silently altered and is not treated as byte-integrity failure when the payload matches its HTTP metadata and SHA-256 provenance.
