# Active pre-acquisition manifest set v4

The sole acquisition-authorizing index is:

`data/source_manifests/PREACQUISITION_INDEX_v4.yaml`

It retains all decisions in v3 and adds a tightly bounded Negatome 2.0 audit
source. The four protein-pair datasets are frozen by official URL, provider
HTTP metadata, byte length, and post-download SHA-256. The official homepage
and supplementary methods are acquired as source documentation.

Negatome has no explicit database-payload license on its download page.
Accordingly, acquisition is approved only for internal research/audit;
record-level and raw redistribution are prohibited unless the provider grants
permission. Public project outputs may contain citations, checksums, schema,
code, and non-extractive aggregate findings.

The provider server omitted its issuing TLS intermediate at audit time. The
downloader uses the fingerprint-pinned public intermediate in
`governance/provenance/tls/`; insecure TLS is prohibited.

This manifest set authorizes acquisition and provenance-preserving quality
control only. It does not authorize negative-label construction, candidate or
split construction, structural labels, model implementation, or training.
