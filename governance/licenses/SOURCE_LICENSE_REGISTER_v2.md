# Source and license register v2

**Status:** Primary-source acquisition approved with source-specific conditions  
**Decision date:** 2026-08-03  
**Supersedes:** `governance/licenses/SOURCE_LICENSE_REGISTER.md`  
**Scope:** HuRI/CCSB maps, UniProt human reference proteome, IntAct/IMEx, and PDB/SIFTS

This is an operational research-data decision, not legal advice. It records what the project may acquire, process, and later redistribute. No scientific payload had been downloaded when this register was issued.

## Decision summary

| Source/material | Frozen source identity | Terms decision | Internal acquisition | Raw redistribution | Scientific conditions |
|---|---|---|---|---|---|
| Interactome Atlas published data | Published portal files, observed 2026-08-03; payload metadata dated 2020-03-09 | CC BY 4.0 | Approved | Approved with attribution | Positive records do not define a complete attempted or negative universe |
| HuRI Nature supplements | DOI `10.1038/s41586-020-2188-x`, version of record 2020-04-08 | Publisher/author copyright; not covered by the portal declaration | Approved for internal reconstruction audit | Not approved without separate permission | Preserve only provenance/checksums and non-extractive derived metadata in public releases |
| UniProt human reference proteome | Release `2026_02`, proteome `UP000005640`, taxon 9606 | CC BY 4.0 | Approved | Approved with attribution | Verify release metalink and provider MD5; retain canonical and additional sequences separately |
| IntAct/IMEx | Release 252, immutable archive `2026-01-09` | CC BY 4.0 for data | Approved | Approved with attribution | PSI-MI XML 3.0 is primary; expanded binary views are not direct-evidence labels |
| PDB archive and RCSB APIs | Entry-revision snapshot at retrieval | CC0 1.0 | Approved | Approved; attribution encouraged | Experimental results only; save query and per-entry revision/checksum |
| PDBe/SIFTS | Rolling weekly files observed with 2026-07-12 modification dates | CC0 under PDBe public-data statement | Approved | Approved; attribution encouraged | Freeze raw bytes because public files are rolling rather than immutable releases |

## 1. HuRI and earlier CCSB maps

Official records:

- Portal/download terms: <https://interactome-atlas.org/download>
- Method and search-space description: <https://interactome-atlas.org/about/>
- Publication: <https://doi.org/10.1038/s41586-020-2188-x>
- IntAct dataset cross-reference: `IM-25472`
- PubMed/PMC: PMID `32296183`, PMCID `PMC7169983`

The portal explicitly places its data and web portal under CC BY 4.0 and requests citation of the portal and HuRI paper, or the appropriate original paper for non-HuRI datasets. The page's moratorium language is directed at preliminary, unpublished, registered-user material. This project is restricted to already-published, unauthenticated files; it will not register for, acquire, or analyze moratorium data.

The portal exposes HuRI (52,569 interactions), Test-space screens-19 (1,159), Lit-BM (13,441), and earlier maps as interaction lists. HuRI's documented Space III covers roughly 17,500 genes and was screened nine times using three Y2H assay versions. That description is not equivalent to a complete pair-level attempt log.

The HuRI supplementary-table guide was examined before acquisition. It documents:

- ORF-to-Ensembl mappings and the three assay-vector systems;
- pairwise PRS/RRS tests in both orientations with `negative`, `positive`, `invalid`, and `autoactivator` states;
- positive Test-space and HuRI interactions with screen/assay information;
- selected MAPPIT/GPCA validation and random-control experiments; and
- a structurally known subset with assay-version detection outcomes.

It does **not** describe a complete attempted/evaluable pair matrix across all nine Space III screens. The published methods also show screen/run-specific candidate selection and pairwise retesting. Consequently:

1. absence from HuRI is unknown, not negative;
2. the Space III Cartesian product is not assumed attempted or technically evaluable;
3. invalid tests, autoactivators, and technical failures are not negatives;
4. explicit supplementary negatives can be stored only with their original assay/control scope; and
5. the primary model remains positive–unlabeled or latent-label until the attempted universe is defensibly reconstructed.

The Nature supplementary files are separately controlled. The portal's CC BY declaration cannot be presumed to license publisher-hosted PDF/XLSX/ZIP files. They may be frozen internally for reproducibility and evidence reconstruction, but raw redistribution is disabled in the project manifest.

## 2. UniProt

Official records:

- License: <https://www.uniprot.org/help/license>
- Release notes: <https://www.uniprot.org/release-notes>
- Human reference-proteome directory: <https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/reference_proteomes/Eukaryota/UP000005640/>

UniProt places copyrightable database components under CC BY 4.0. Attribution is required; patent and third-party-rights caveats remain. The acquisition is bound to release `2026_02` through `RELEASE.metalink`, not merely to the mutable `current_release` URL.

The immediate payload is the canonical FASTA, additional/isoform FASTA, canonical DAT annotations, identifier mapping, and release metalink. Provider MD5 values from the metalink will be verified, and SHA-256 will be computed locally. UniRef and UniParc are legally compatible but deliberately deferred until clustering and identifier-history requirements are concrete; this prevents an unnecessary bulk download.

## 3. IntAct and IMEx

Official records:

- IntAct license/about page: <https://www.ebi.ac.uk/intact/about>
- Immutable archive: <https://ftp.ebi.ac.uk/pub/databases/intact/2026-01-09/>
- Production service base: <https://www.ebi.ac.uk/intact/ws>
- EMBL-EBI terms: <https://www.ebi.ac.uk/about/terms-of-use/>

The specific IntAct data-license statement distinguishes CC BY 4.0 data from Apache-licensed software. A legacy sentence on the downloads presentation can be read as applying Apache broadly; because the specific data statement is clearer, this register applies CC BY 4.0 to data and records the discrepancy rather than silently resolving it.

Release 252's immutable `2026-01-09` archive is preferred over a mutable current-release URL. The primary file is human PSI-MI XML 3.0, because XML 3.0 can retain original n-ary records. MITAB and search-result binaries may represent spoke expansion and cannot be treated as experimentally observed direct binary interactions. The parser must preserve stable `EBI-*` evidence identifiers, IMEx dataset accessions, participant roles, negative flags, interaction/detection method, host organism, constructs, and original n-ary structure.

The HuRI dataset cross-check `IM-25472` produces multiple screen/detection-stage records, not a one-row-per-consensus-pair map. It is therefore a provenance cross-check, not an alternative ground-truth label file.

## 4. PDB and SIFTS

Official records:

- RCSB PDB usage policy: <https://www1.rcsb.org/pages/usage-policy>
- RCSB Search API: <https://search.rcsb.org/index.html>
- PDBe public-data statement: <https://www.ebi.ac.uk/pdbe/about/public-data-access-statement>
- SIFTS documentation: <https://www.ebi.ac.uk/pdbe/docs/sifts/>
- SIFTS files: <https://ftp.ebi.ac.uk/pub/databases/msd/sifts/>

PDB archive files and RCSB API data are CC0 1.0; original authors and RCSB should still be credited. PDBe states that its primary and derived structural data are provided under CC0, which covers SIFTS-derived mappings under this operational decision.

The RCSB query must explicitly request `experimental` content, excluding computed structure models. The exact query request and response will be frozen. Coordinate files will receive child manifests carrying PDB ID, entry revision, method, resolution, assembly ID, HTTP metadata, and SHA-256. Interfaces will be recalculated from those frozen biological assemblies. SIFTS mappings must be used to audit engineered mutations, tags, chimeras, isoforms, and unobserved residues before an interface-derived label can exist.

## 5. Deferred sources

Systematic yeast and *E. coli* binary sources remain potential external-transfer evaluations. They have not yet received release, assay-universe, or license audits and remain prohibited from `data/raw/`.

## Frozen policy evidence

Six official policy pages were fetched inside the qualified Apptainer image on 2026-08-03. Byte counts, redirect targets, HTTP metadata, and SHA-256 values are recorded in:

- `governance/licenses/snapshots/2026-08-03/SNAPSHOT_MANIFEST.json`

The UniProt and IntAct sites are client-rendered applications; their raw HTML snapshots contain application shells rather than the rendered license text. The operative findings above were therefore human-reviewed against the rendered official pages, while the raw endpoint responses are retained as timestamped provenance.

## Attribution requirements for eventual outputs

Any distributed dataset card or release note must cite the relevant original publications and providers, include CC BY 4.0 attribution for Interactome Atlas, UniProt, and IntAct data, and identify PDB/PDBe/SIFTS provenance. Raw Nature supplementary files may not be packaged in a release under this decision.
