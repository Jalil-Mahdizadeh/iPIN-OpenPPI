# DEC-0008: Accept the primary evidence staging layer

**Date:** 2026-08-03
**Status:** Accepted with one downstream structural blocker
**Decision owner:** Codex under project execution authority
**Gate effect:** Source-parsing subgate passes; overall evidence gate remains in progress

## Decision

Accept production run family `primary_sources_v1` as the immutable, provenance-preserving primary staging layer for HuRI, UniProt, IntAct/IMEx, and PDB/SIFTS.

The run produced 21 datasets in 152 Parquet files, containing 14,021,899 rows across all tables and 1,369,917,702 Parquet bytes. The strict production validator returned 150 passes, zero failures, and one warning. The warning corresponds to ISSUE-0005: the SIFTS snapshot declares UniProt `2026.03`, while the frozen human sequence corpus is UniProt `2026_02`.

Source reconciliation and identifier/construct mapping are authorized. Label construction and model training are not authorized.

## Scientific basis

- All 17 selected raw scientific inputs were reverified against the immutable acquisition record before parsing.
- The common layer retains 773,376 evidence records, 2,213,524 participant rows, and 1,397,319 participant-feature rows.
- All 41,964 IntAct records with more than two participants remain original n-ary records; no expansion was performed.
- All 2,198 unary IntAct records remain unary and are explicitly quality-flagged rather than treated as n-ary.
- All 939 negative observations are explicit IntAct source assertions; zero technical failures were encoded as negatives.
- HuRI pair views, contact annotations, and fusion-interference annotations have zero label-authorized rows.
- UniProt sequence length and SHA-256 checks pass for all 169,637 sequence rows.
- HuRI workbook error values, source-native mappings, and SIFTS interval directions were preserved rather than silently corrected.

## Conditions

1. `data/staging/primary_sources_v1` remains immutable and outside Git. Any change requires a new run family, manifest, checksum, validation report, and decision.
2. ISSUE-0003 continues to prohibit converting unreported HuRI pairs into negative labels. The primary design remains PU/latent-observation unless its exit criteria are satisfied.
3. ISSUE-0004 remains open through deterministic reconciliation of portal counts, detailed evidence, constructs/isoforms, orientations, self-pair filtering, and provider-derived pair views.
4. ISSUE-0005 prohibits exact structure-to-sequence claims and structure-derived labels until release alignment or an approved exact-sequence restricted subset is demonstrated.
5. Source-native label-like annotations remain annotations; `label_authorized=false` must be preserved.
6. No label construction or model training may occur until a later explicit gate decision.

## Next authorized unit

Perform source reconciliation and identifier/construct mapping. Produce auditable mapping states and complete transition counts; do not construct training labels or train models.

## Evidence

- `docs/reports/m0/M0_Primary_Source_Parsing_and_Evidence_QC_Final_v1.md`
- `data/staging/primary_sources_v1/PARSE_MANIFEST.json`
- Parse-manifest SHA-256: `ca8380eec0cc1899823b43b109aa2ff9466aa44ba62a6856af76858c352960aa`
- `artifacts/validation/evidence_parsing/primary_sources_v1/VALIDATION_REPORT.json`
- Validation-report SHA-256: `375aadc78db8783bd338a1703e84395023f26b9517999ff8985168206df271ba`
- Parser Git commit: `403397cd52dec8d7e37f571b13c73f47173fd6f0`
- Parser version: `1.2.0`
- Accepted data-SIF SHA-256: `72e4a13299df1c7036dbf5c8845f3a1d9d02bf6143bd2e4ee675aabd03112629`
