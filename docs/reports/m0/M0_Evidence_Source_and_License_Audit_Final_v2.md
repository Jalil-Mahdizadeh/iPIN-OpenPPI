# M0 final evidence-source and license audit

**Project:** iPIN-OpenPPI  
**Date:** 2026-08-03  
**Executor:** Codex  
**Execution environment:** NAISS Arrhenius, qualified Apptainer SIF  
**Gate result:** **PASS WITH CONDITIONS** for source/license acquisition; overall evidence gate **IN PROGRESS**

## Executive conclusion

The project is feasible as a fully computational, provenance-first investigation. The official HuRI/CCSB, UniProt, IntAct/IMEx, and experimental PDB/SIFTS sources are accessible and operationally compatible with the planned work. The final active manifest set names 20 exact assets, 19 mandatory at this stage, plus a child-manifest process for later experimental PDB coordinates.

The decisive scientific limitation is that public HuRI material does not expose a complete pair-level record of selection, attempted status, technical evaluability, and outcome across all nine Space III screens. HuRI supports systematic positive evidence and scoped explicit controls, but absence from HuRI cannot be used as a negative label. Unless a fuller screen log is found, the statistically defensible first model is positive–unlabeled or latent-observation—not an ordinary positive-versus-all-unlisted classifier.

This limitation does not stop acquisition or parser development. It does stop training-label construction and model training until the evidence audit quantifies provenance, construct mapping, assay-state resolution, explicit-control scope, and source overlap.

## Final source decisions

| Source | Frozen identity | License/terms | Immediate role | Binding restriction |
|---|---|---|---|---|
| Interactome Atlas / HuRI | Published portal files, payload metadata dated 2020-03-09 | CC BY 4.0 | Systematic positive and explicit-control evidence | Missing pairs remain unknown |
| HuRI Nature supplements | DOI `10.1038/s41586-020-2188-x` | Publisher/author copyright | Internal reconstruction audit | Raw redistribution disabled |
| UniProt human proteome | `2026_02`, `UP000005640`, taxon 9606 | CC BY 4.0 | Canonical/additional sequences, annotations, mappings | Release metalink and provider MD5 required; no silent isoform collapse |
| IntAct/IMEx | Release 252, archive `2026-01-09`, HuRI cross-reference `IM-25472` | CC BY 4.0 data | Evidence-level molecular records | PSI-MI XML 3.0 primary; expansions are not direct labels |
| PDB/RCSB | Entry revision frozen at retrieval | CC0 1.0 | Experimental assembly/interface evidence | Experimental query only; coordinate child manifest required |
| PDBe/SIFTS | Weekly files dated 2026-07-26 | CC0 | Chain/residue mapping and construct audit | Rolling source must be frozen by raw checksum |

Preliminary or unpublished registered-user HuRI data are out of scope. UniRef, UniParc, systematic yeast, and systematic *E. coli* payloads remain deferred until release-specific scientific needs are fixed.

## HuRI feasibility and the negative-label problem

The portal documents roughly 17,500 genes in Space III, nine screens, three Y2H assay variants, differing clone constraints, removal of strong bait autoactivators, screen/run-specific candidate thresholds, and selected pairwise retesting. The downloadable pair files are positive lists. The supplementary guide provides mappings, positive records, selected retest/validation outcomes, random controls, and a restricted structure-known subset, but no complete all-screen pair-attempt matrix.

Therefore the following are mandatory:

1. Unreported pairs are `unknown`, never automatic negatives.
2. Invalid, autoactivating, and technical-failure records are not negatives.
3. Explicit negatives retain exact assay, construct, orientation, sampling, and control context.
4. Selection `s`, technical evaluability `e`, contextual direct binding `b`, and observed outcome `y` remain distinct fields.
5. The model's calibrated output is assay/evidence-conditioned detectability or compatibility, not universal binding probability.

ISSUE-0003 records the exit criteria. With no laboratory work available, resolution must come from a fuller official screen log or a formally approved PU/latent-label primary design supported by simulations and independent source holdouts.

## IntAct evidence semantics

IntAct is feasible and valuable, but a binary row is not automatically a direct experimental binary observation. PSI-MI XML 3.0 can preserve n-ary records that MITAB/search presentations may expand using spoke or matrix rules. The parser must retain original interaction structure, stable `EBI-*` identifiers, dataset/publication IDs, participant roles, host organism, interaction type, detection method, negative flag, and construct features.

Direct interaction (`MI:0407`), physical association (`MI:0915`), and association (`MI:0914`) will remain separate. `IM-25472` is an evidence/provenance cross-check, not a replacement one-row-per-HuRI-pair label file.

## Structural evidence semantics

RCSB queries will explicitly request experimental content, excluding computed models from the experimental-evidence layer. The exact search request and response will be frozen. Each selected coordinate payload will require a child manifest containing PDB ID, entry revision, method, resolution, biological assembly ID, HTTP metadata, and SHA-256.

Interfaces will be recalculated from frozen biological assemblies. SIFTS chain and residue mappings will be used to audit mutations, tags, chimeras, isoforms, and unobserved residues before a structure-derived interface record is admitted.

## Live preflight correction

The audit did not rely only on cached web indexing. A direct no-payload HTTP preflight inside Apptainer found that SIFTS had advanced from the initially observed 2026-07-12 state to 2026-07-26 weekly files. The stale draft was rejected before any scientific download. The final manifest now binds:

| Asset | Bytes | ETag | Last-Modified |
|---|---:|---|---|
| `pdb_chain_uniprot.tsv.gz` | 6,065,626 | `"5c8dda-65778bdec5929"` | 2026-07-26 00:32:34 GMT |
| `pdb_chain_taxonomy.tsv.gz` | 4,561,221 | `"459945-65778d51112b8"` | 2026-07-26 00:39:02 GMT |
| `uniprot_segments_observed.tsv.gz` | 10,624,476 | `"a21ddc-657790036a228"` | 2026-07-26 00:51:06 GMT |

The final repeated preflight passed all 20 endpoints and all recorded metadata comparisons.

## Feasibility judgment

| Component | Feasibility | Principal limitation | Project response |
|---|---|---|---|
| Release-aware human sequences | High | Gene/isoform ambiguity | Preserve canonical, additional, accession, and version layers |
| Systematic positive assay evidence | High | Construct/assay heterogeneity | Evidence record is primary; consensus pair is derived |
| Complete systematic negative universe | Low at present | HuRI attempt/evaluability log incomplete publicly | PU/latent formulation; ISSUE-0003 |
| Curated molecular evidence | Moderate–high | N-ary expansion and duplicate stages | PSI-MI XML 3.0 plus controlled-vocabulary filters |
| Experimental interfaces | Moderate | Structural and construct selection bias | Experimental-only, assembly and SIFTS residue audit |
| Fully computational validation | Feasible | No prospective wet-lab confirmation | Strict splits, temporal/source holdouts, simulations, calibration, uncertainty |

Overall feasibility is **conditional but strong**. A credible outcome is an assay-aware protein-pair compatibility/ranking model with calibrated uncertainty, strict generalization tests, and a reproducible hypothesis catalogue. A universal physical-binding probability, an experimentally validated novel-interaction claim, or a completed human interactome is outside the defensible claim ceiling.

## Reproducibility and gate evidence

All audit scripts ran inside `containers/images/ipin-qual-arm64_0.1.0.sif` on Arrhenius ARM64.

- Active index: `data/source_manifests/PREACQUISITION_INDEX_v3.yaml`
- Structural/policy validation: pass; 0 errors; 3 warnings; 76/76 checks passed
- The three warnings only record absence of provider checksum catalogues for HuRI, IntAct, and PDB/SIFTS; local SHA-256 is mandatory
- URL/metadata preflight: pass; 20/20 assets; 0 errors; 0 warnings
- Official policy snapshots: six pages with HTTP metadata and SHA-256
- Scientific payloads downloaded during this audit: **none**

Evidence files:

- `artifacts/validation/source_manifests/preacquisition_validation_v3.json`
- `artifacts/validation/source_manifests/preacquisition_url_probe_v3.json`
- `governance/licenses/snapshots/2026-08-03/SNAPSHOT_MANIFEST.json`
- `governance/licenses/SOURCE_LICENSE_REGISTER_v3.md`
- `governance/issues/ISSUE-0003-huri-attempted-pair-universe.md`
- `governance/decisions/DEC-0006-authorize-final-source-manifest-set.md`

## Gate outcome and next execution unit

The source/license subgate passes with conditions because source identity, release/snapshot logic, exact retrieval endpoints, terms, redistribution treatment, checksum strategy, and label guards are now explicit and machine-tested. The evidence gate remains in progress because its quantitative provenance and mapping thresholds require acquired data.

The authorized next unit is to implement a whitelist-only atomic downloader, acquire the active manifest assets inside Apptainer, verify all provider metadata and checksums, freeze raw inventories, and inspect archives/formats safely. It will not build labels or train a model.

No expert-group decision is needed before that raw-acquisition unit.
