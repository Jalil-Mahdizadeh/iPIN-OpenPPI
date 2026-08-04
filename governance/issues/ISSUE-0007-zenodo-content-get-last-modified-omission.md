# ISSUE-0007: Zenodo content GET omits HEAD Last-Modified metadata

**Opened:** 2026-08-04

**State:** Resolved by explicit verifier semantics

The preacquisition HEAD response for the archived code and input-data files in
Zenodo record 19118078 supplied `Last-Modified`. The file-content GET response
omitted that optional header. The first controlled acquisition therefore
stopped before accepting either archive; its failed run report is retained at
`artifacts/runs/data_acquisition/lambourne-y2h-v1-20260804T113811Z/`.

The downloader now treats a missing optional GET `Last-Modified` value as
unavailable provenance, not as a contradictory value. If the GET supplies a
different value, acquisition still fails. Exact downloaded byte count, the
provider-published MD5 for both archives, local SHA-256, TLS verification,
atomic placement, and format inspection remain mandatory. This narrowly
resolves provider-method asymmetry without weakening payload integrity.
