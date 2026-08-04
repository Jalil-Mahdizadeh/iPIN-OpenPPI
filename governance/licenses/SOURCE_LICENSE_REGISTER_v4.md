# Source and license register v4

**Status:** Current; Negatome acquisition approved for internal audit only
**Decision date:** 2026-08-04
**Supersedes:** `governance/licenses/SOURCE_LICENSE_REGISTER_v3.md`
**Active manifest set:** `data/source_manifests/PREACQUISITION_INDEX_v4.yaml`

## Operative decisions

| Material | License/terms decision | Acquisition | Raw redistribution | Required treatment |
|---|---|---|---|---|
| Published Interactome Atlas data | CC BY 4.0 | Approved | With attribution | Cite portal and HuRI/original paper; do not infer negatives from missing pairs |
| Nature-hosted HuRI supplements | Publisher/author copyright; not covered by portal terms | Internal audit copy approved | Not approved without separate permission | Release only provenance, checksums, and non-extractive derived metadata |
| UniProt release `2026_02` | CC BY 4.0 | Approved | With attribution | Preserve canonical and isoform sequences separately |
| IntAct Release 252 / archive `2026-01-09` | CC BY 4.0 for data | Approved | With attribution | Preserve source evidence and explicit negative state; no absence-derived negatives |
| PDB archive and RCSB API | CC0 1.0 | Approved under child-manifest workflow | Approved; attribution encouraged | Experimental entries only; freeze revisions and coordinates |
| PDBe/SIFTS weekly files | CC0 under PDBe public-data statement | Approved | Approved; attribution encouraged | Bind rolling files to HTTP metadata and SHA-256 |
| Negatome 2.0 pair files and download page | No explicit database/payload license located | Approved for internal research audit | **Not approved** without explicit provider permission | Do not commit raw/record-level payloads; publish citations, hashes, code, schemas, and non-extractive aggregate results only |
| Negatome 2.0 article | CC BY-NC 3.0 | Approved for reading and citation | Article reuse subject to CC BY-NC 3.0 | Do not extend the article license to the separately served database payloads without evidence |

All unchanged v3 source findings remain incorporated by reference.

## Negatome licensing determination

The official Negatome page publicly offers text downloads, describes their
intended use in evaluating experiments and training interaction-prediction
algorithms, and supplies citation information. Neither that page nor the four
pair files states a database license, redistribution grant, commercial-use
grant, terms of use, or waiver of database rights. The open-access paper is
licensed CC BY-NC 3.0, but that notice applies to the article and is not treated
as evidence that the separately hosted database payloads share the same terms.

The defensible project decision is therefore:

- internal computational research and audit use: approved;
- citation and publication of non-extractive aggregate findings: approved;
- repository or release redistribution of raw rows or record-level derivatives:
  prohibited pending explicit permission; and
- commercial use: unresolved and not authorized.

This is a conservative compliance determination, not legal advice.

## TLS provenance note

On 2026-08-04 the Negatome HTTPS server returned a currently valid leaf
certificate whose hostname covered `mips.helmholtz-muenchen.de`, but omitted
the issuing `GEANT TLS RSA 1` intermediate. The project retrieved that public
intermediate from HARICA's documented repository, checked its SHA-256
fingerprint, pinned the PEM bytes under `governance/provenance/tls/`, and uses
it only for this provider. Hostname and signature verification remain enabled;
no `--insecure` acquisition is permitted.

## Negative-evidence release boundary

No row from Negatome or IntAct is a universal statement that two proteins can
never bind. Manual observations remain conditional on the reported assay,
constructs (when supplied), orientation, species, publication, and conditions.
PDB-derived rows mean only that two members of a particular structural complex
were classified as lacking direct contact under the historical Negatome
procedure. Missing provenance remains missing and is never imputed.
