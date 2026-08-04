# Source TLS provenance

`HARICA-GEANT-TLS-R1.pem` is the public issuing certificate needed because the
Negatome server did not transmit its intermediate certificate on 2026-08-04.
It was retrieved inside the pinned data Apptainer image from
`https://repo.harica.gr/certs/HARICA-GEANT-TLS-R1.der`.

- DER SHA-256 / X.509 fingerprint:
  `5b678dc44095a52895b63b31f27227f4b36c3e347491bf2bfa691837a5fb8c79`
- PEM SHA-256:
  `cdc78c3185ce918c8e87f9b2559197d641288e564c5a8b789cd796abdea298d4`
- Subject: `CN=GEANT TLS RSA 1,O=Hellenic Academic and Research Institutions CA,C=GR`
- Issuer: `CN=HARICA TLS RSA Root CA 2021,O=Hellenic Academic and Research Institutions CA,C=GR`
- Validity: 2025-01-03 through 2039-12-31 UTC

The downloader adds this certificate only for
`mips.helmholtz-muenchen.de`. It still verifies the requested hostname and the
server signature; it never uses an insecure TLS mode.
