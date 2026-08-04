# Source and license register v5

**Status:** Current; negative-evidence audit accepted with record-level
Negatome redistribution prohibited

**Decision date:** 2026-08-04

**Supersedes:** `governance/licenses/SOURCE_LICENSE_REGISTER_v4.md`

**Active manifest set:** `data/source_manifests/PREACQUISITION_INDEX_v4.yaml`

## Operative decisions

| Material | License/terms decision | Acquisition | Raw redistribution | Required treatment |
|---|---|---|---|---|
| Published Interactome Atlas data | CC BY 4.0 | Approved | With attribution | Cite portal and HuRI/original paper; do not infer negatives from missing pairs |
| Nature-hosted HuRI supplements | Publisher/author copyright; not covered by portal terms | Internal audit copy approved | Not approved without separate permission | Release only provenance, checksums, and non-extractive derived metadata |
| UniProt release `2026_02` | CC BY 4.0 | Approved | With attribution | Preserve canonical and isoform sequences separately |
| IntAct Release 252 / archive `2026-01-09` | CC BY 4.0 for data | Approved | With attribution | Preserve source evidence and explicit negative state; no absence-derived or universal negatives |
| PDB archive and RCSB API | CC0 1.0 | Approved under child-manifest workflow | Approved; attribution encouraged | Experimental entries only; freeze revisions and coordinates |
| PDBe/SIFTS weekly files | CC0 under PDBe public-data statement | Approved | Approved; attribution encouraged | Bind rolling files to HTTP metadata and SHA-256 |
| Negatome 2.0 pair files and download page | No explicit database/payload license located | Complete for internal audit | **Not approved** without explicit provider permission | Do not commit raw/record-level payloads; publish citations, hashes, code, schemas, and non-extractive aggregate results only |
| Negatome 2.0 article | CC BY-NC 3.0 | Approved for reading and citation | Article reuse subject to CC BY-NC 3.0 | Do not extend the article license to separately served database payloads |
| Lambourne et al. 2026 article and included supplementary material | Article states CC BY 4.0 unless a separate credit line applies | Reading and source survey only | Not yet determined for every linked payload | New preacquisition review required before any download or use |
| Lambourne et al. 2026 code/archive/IMEx records | MIT reported for code; archive and IMEx payload scopes require asset-level confirmation | **Not authorized in this gate** | Pending asset-level review | Treat as a future bounded-panel candidate, not a population-negative source |

All unchanged v4 source findings remain incorporated by reference.

## Negatome audit determination

The production audit verified all four provider payloads and retained their
immutable hashes:

| Dataset | Rows | SHA-256 |
|---|---:|---|
| Manual | 2,171 | `f05410c9ba1748e0d36a13e9b873a67e61bdcef2446904735fc3e172ca78aa16` |
| Manual stringent | 1,991 | `6391316c19abaf8a677ef65878891e9ae6fd9346dff53e2c0617cb34516f578c` |
| PDB | 4,397 | `85232908f1b993b9bb54abc0547a2566cc99930538d134faec8db56f303df182` |
| PDB stringent | 4,161 | `61026a6147d5729980efc80f84e85d92bbd9424b11a586332c8ebf193011cc3c` |

The official Negatome page publicly offers the downloads, explains intended
research uses, and supplies citation information. Neither the page nor any of
the four pair files states a database license, redistribution grant,
commercial-use grant, terms of use, or database-right waiver. The article is
licensed CC BY-NC 3.0, but that is not evidence that separately hosted payloads
carry the same license.

The binding project decision is:

- internal computational research and audit use: approved;
- citation and non-extractive aggregate findings: approved;
- repository or release redistribution of raw rows or record-level
  derivatives: prohibited pending explicit permission; and
- commercial use: unresolved and not authorized.

The committed `AUDIT_REPORT.json`, `VALIDATION_REPORT.json`, code, schemas,
source survey, and expert report are aggregate or non-extractive and remain
inside this boundary. The raw, staging, and canonical record-level Negatome
trees remain internal and excluded from Git.

This is a conservative compliance determination, not legal advice.

## IntAct determination

The IntAct About page states that its downloadable and service-delivered data
are under CC BY 4.0. The audit enumerated all 939 frozen source-asserted negative
records under that license. Attribution and source provenance remain required.
The license permits reuse; it does not strengthen the biological meaning of an
observation or authorize a universal nonbinding interpretation.

## Additional-source survey boundary

The public-source survey identified the Lambourne et al. 2026 human
AI-prediction Y2H panel as the highest-priority follow-up candidate for a
bounded conditional diagnostic. This register does not approve acquisition.
Before any linked article source data, Git repository, Zenodo archive, or IMEx
record enters `data/raw/`, the project must create a new source-policy revision
and preacquisition manifest that confirms, per asset:

1. exact version and retrieval endpoint;
2. license and redistribution scope;
3. pair-level attempted, evaluable, `NA`, and observed-outcome semantics;
4. sequence and orientation availability;
5. sampling and selection mechanism; and
6. permissible public-release form.

## Negative-evidence release boundary

No Negatome, IntAct, HuRI-panel, or future selected-panel record is a universal
statement that two proteins can never bind. Manual observations remain
conditional on the reported assay, constructs, orientation, species,
publication, conditions, and evaluability to the extent those fields exist.
PDB-derived rows record only a historical structure-specific non-contact
classification. Missing context remains missing and is never imputed.

## TLS provenance note

The v4 TLS determination remains active. The provider-specific issuing
intermediate is pinned under `governance/provenance/tls/`; hostname and
signature verification stay enabled, and no insecure acquisition is permitted.
