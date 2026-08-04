# Source and license register v7

**Status:** Current; bounded 2025 TF-isoform Y2H audit acquisition approved

**Decision date:** 2026-08-04

**Supersedes:** `governance/licenses/SOURCE_LICENSE_REGISTER_v6.md`

**Active manifest set:** `data/source_manifests/PREACQUISITION_INDEX_v6.yaml`

## New asset-level determinations

| Material | License evidence | Acquisition | Redistribution boundary |
|---|---|---|---|
| Lambourne et al., Molecular Cell 2025 author-hosted paper PDF | The paper states Copyright © 2025 Elsevier Inc. All rights reserved; no separate data license is asserted for this copy | Approved for bounded internal methods and provenance audit | Do not redistribute or commit the PDF; retain only checksums, citations, and original audit prose |
| Zenodo record 14969075, software/supplement archive v2.1.0 | Record metadata declares CC BY 4.0 and pins DOI `10.5281/zenodo.14969075` | Approved | Attribution and version DOI required; raw archive remains outside Git under project policy |
| Zenodo record 14968584, input-data archive v2 | Record metadata declares CC BY 4.0 and pins DOI `10.5281/zenodo.14968584` | Approved | Attribution and version DOI required; raw archive remains outside Git under project policy |

The GitHub repository exposes no repository-level license metadata. It is not
used as the licensing authority and is not acquired separately: the versioned
Zenodo deposits are authoritative for this audit. TFisoDB points to the public
supplementary tables and an unrelated AlphaFold bundle; neither is needed
beyond the exact files already frozen in the Zenodo archives.

All unchanged v6 determinations remain incorporated by reference, including
the internal-only Negatome redistribution boundary and the quarantined status
of the 2026 Lambourne Y2H-v1 panel.

## Fail-closed determination

The two necessary data/code deposits have an explicit CC BY 4.0 license, so
the semantics audit may proceed. The paper PDF has no redistribution grant;
its use is therefore restricted to internal scholarly audit. If a required
technical-state file proves absent from the deposits, the affected blank rows
must remain unknown and the final disposition must fail closed rather than
infer assay negatives.

The license permits analysis but does not alter assay meaning. Y2H negatives
remain construct-, orientation-, and condition-specific observations. N2H is
a separate assay and cannot relabel Y2H. Any later record-level release or
benchmark use requires a new governance review. This is a conservative
compliance determination, not legal advice.
