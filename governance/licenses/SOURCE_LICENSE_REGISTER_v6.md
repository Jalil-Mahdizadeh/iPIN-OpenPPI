# Source and license register v6

**Status:** Current; bounded Lambourne human Y2H audit acquisition approved

**Decision date:** 2026-08-04

**Supersedes:** `governance/licenses/SOURCE_LICENSE_REGISTER_v5.md`

**Active manifest set:** `data/source_manifests/PREACQUISITION_INDEX_v5.yaml`

## New asset-level determinations

| Material | License evidence | Acquisition | Redistribution boundary |
|---|---|---|---|
| Lambourne et al. article, methods, Supplementary Data 22, and source data | Article rights statement: CC BY 4.0 unless a separate credit line applies | Approved | CC BY 4.0 attribution; inspect any third-party credit line before public redistribution |
| Zenodo record 19118078 v2.1, archived code v1.1, and input-data archive | Record metadata declares MIT; archived Git code also contains MIT license | Approved | MIT notice/attribution required; preserve version DOI and provider checksums |
| IMEx study IM-30553 preview exports | IntAct About page states CC BY 4.0 for data | Approved as dated provider preview | CC BY 4.0 attribution; never present the preview as Release 252 or an integrated current IntAct service result |

All unchanged v5 determinations remain incorporated by reference, including
the internal-only, no-record-level-redistribution boundary for Negatome.

## IMEx integration-state determination

On 2026-08-04 the official IMEx query page reported that the publication for
IM-30553 had been curated but was not yet integrated into services. It exposed
editor-service preview exports. Those exports have no advertised release tag,
stable checksum, or immutable provider version identifier. The project may
freeze them only as `preview-snapshot-2026-08-04`, with response metadata and
local SHA-256. They must remain a separate source representation from frozen
IntAct Release 252 (2026-01-09).

## Scientific-use boundary

The licenses permit the scoped audit; they do not strengthen study semantics.
Lambourne outcomes remain conditional on the selected pair population, exact
constructs, bait/prey orientation, Y2H-v1 protocol, sequence-confirmation and
technical-evaluability state. A reported negative is not universal
nonbinding, and `NA` or technical failure is not negative.

The project will keep raw assets outside Git under its data policy. Any future
record-level derived release requires governance review for attribution,
third-party material, participant identifiers, and source-representation
scope. This is a conservative compliance determination, not legal advice.
