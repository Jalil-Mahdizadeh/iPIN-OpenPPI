# Source and license register v3

**Status:** Current; acquisition approved with conditions  
**Decision date:** 2026-08-03  
**Supersedes:** `governance/licenses/SOURCE_LICENSE_REGISTER_v2.md`  
**Active manifest set:** `data/source_manifests/PREACQUISITION_INDEX_v3.yaml`

## Operative decisions

| Material | License/terms decision | Acquisition | Raw redistribution | Required treatment |
|---|---|---|---|---|
| Published Interactome Atlas data | CC BY 4.0 | Approved | With attribution | Cite portal and HuRI/original paper; do not infer negatives from missing pairs |
| Nature-hosted HuRI supplements | Publisher/author copyright; not covered by portal terms | Internal audit copy approved | Not approved without separate permission | Release only provenance, checksums, and non-extractive derived metadata |
| UniProt release `2026_02` | CC BY 4.0 | Approved | With attribution | Verify `RELEASE.metalink` MD5 and local SHA-256; preserve isoforms |
| IntAct Release 252 / archive `2026-01-09` | CC BY 4.0 for data | Approved | With attribution | Use PSI-MI XML 3.0; do not label expanded n-ary projections as direct binaries |
| PDB archive and RCSB API | CC0 1.0 | Approved under child-manifest workflow | Approved; attribution encouraged | Experimental entries only; freeze entry revision, assembly, and coordinates |
| PDBe/SIFTS weekly files | CC0 under PDBe public-data statement | Approved | Approved; attribution encouraged | Bind the rolling files to live HTTP metadata and local SHA-256 |

The source-by-source legal, attribution, semantic, and redistribution analysis in v2 remains incorporated here except for the SIFTS snapshot correction below. The official policy-page snapshots and hashes remain at `governance/licenses/snapshots/2026-08-03/SNAPSHOT_MANIFEST.json`.

## SIFTS rolling-snapshot correction

The initial web-index review observed files dated 2026-07-12. A direct HTTP preflight from the qualified Apptainer image on 2026-08-03 found that the rolling SIFTS directory had advanced to 2026-07-26. The project therefore rejected the stale draft and bound the active manifest to:

| Asset | Bytes | ETag | Last-Modified |
|---|---:|---|---|
| `pdb_chain_uniprot.tsv.gz` | 6,065,626 | `"5c8dda-65778bdec5929"` | Sun, 26 Jul 2026 00:32:34 GMT |
| `pdb_chain_taxonomy.tsv.gz` | 4,561,221 | `"459945-65778d51112b8"` | Sun, 26 Jul 2026 00:39:02 GMT |
| `uniprot_segments_observed.tsv.gz` | 10,624,476 | `"a21ddc-657790036a228"` | Sun, 26 Jul 2026 00:51:06 GMT |

This correction demonstrates why the project treats rolling provider directories as mutable and defines its reproducible snapshot by local raw bytes, retrieval timestamp, HTTP metadata, and SHA-256.

## HuRI evidence boundary

The public HuRI portal and publication supplements remain insufficient to reconstruct a complete pair-level attempted/evaluable universe across all nine screens. The following are binding:

- unreported pairs are unknown, not negative;
- invalid, autoactivating, and technical-failure records are not negatives;
- explicit control outcomes retain their original sampling and assay scope; and
- training must use a positive–unlabeled or latent-observation formulation unless ISSUE-0003 is resolved.

## Deferred sources

UniRef, UniParc, systematic yeast, and systematic *E. coli* payloads remain deferred. Their general licensing may be compatible, but no acquisition is authorized until a concrete release-bound manifest and scientific need are approved.

## Final verification state

- Structural/policy manifest validation: pass, 0 errors, 3 provider-checksum warnings.
- Direct URL/metadata preflight: pass, 20 of 20 assets, 0 errors, 0 warnings.
- Scientific payloads downloaded during this audit: none.

The active evidence is:

- `artifacts/validation/source_manifests/preacquisition_validation_v3.json`
- `artifacts/validation/source_manifests/preacquisition_url_probe_v3.json`
- `data/source_manifests/ACTIVE_MANIFEST_SET_v3.md`
