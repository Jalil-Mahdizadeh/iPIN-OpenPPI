# TP53 biological partner panel

Prepared 2026-09-18T22:00:00.668375+00:00. Input only: no model inference or training was run.

[tp53_ipin_panel.csv](tp53_ipin_panel.csv) contains **3 P + 300 U = 303 pairs**. Its five columns exactly match ../ire1_ipin_panel2.csv:

`query_gene,query_uniprot,partner_gene,partner_uniprot,class`

The query is human TP53 (P04637); the gene/accession pairs were checked against UniProt 2026_03 (02-September-2026). Accessions refer to canonical sequences. [panel_manifest.json](panel_manifest.json) records the query and partner sequence SHA-256 values, sequence lengths, selection groups, source hashes, and overlap checks. The CSV itself intentionally contains neither sequences nor model scores.

## Positive partners

| Partner | UniProt | Pair type | Evidence / context |
|---|---|---|---|
| MDM2 | Q00987 | Heteromeric | [Evidence](https://www.uniprot.org/uniprotkb/P04637/entry) — Curated human TP53-MDM2 binary interaction. |
| MDM4 | O15151 | Heteromeric | [Evidence](https://www.uniprot.org/uniprotkb/P04637/entry) — Curated human TP53-MDM4 binary interaction. |
| EP300 | Q09472 | Heteromeric | [Evidence](https://www.uniprot.org/uniprotkb/P04637/entry) — Curated human TP53-EP300 binary interaction. |

These are nominated positives, not an exhaustive interaction catalogue. Experimentally supported homomeric interactions are eligible; identical endpoints are not automatically removed or automatically labelled positive. Canonical protein sequences do not encode phosphorylation, activation state, concentration, or experimental fragment boundaries.

## Unlabeled selection

U means **unlabeled/unknown**, never a verified non-interactor.

For each positive partner, 50 U proteins were matched to its declared broad cellular compartment and the presence/absence of a UniProt TRANSMEM feature; another 50 came from the broader eligible human background. Both groups were within 0.5-2 times that positive partner's sequence length. Absence of a TRANSMEM annotation does not establish solubility, and broad compartment matching is not cell-type-specific co-expression evidence.

The source pool was reviewed human UniProt proteins with protein-level evidence, a primary gene name, at least 30 residues, and supported amino-acid characters. Identical eligible sequences were deduplicated by SHA-256. U entries are unique within this target; a U protein may recur in another target's panel.

Conservative exclusions covered nominated positives, the query itself, IntAct human-human partner identifiers (including complex-association records and secondary/isoform identifiers), partner mentions in target and reciprocal UniProt subunit annotations, explicit literature exclusions, and all prior TRAIN/development pairs involving this query, whether P or U. Matching sequence duplicates were also excluded. This is a database/literature-screened U pool, not a claim that the interaction literature is exhaustive.

Selection was deterministic and did not use model scores. Salt: `ipin-six-target-panel-v1-20260918`. Candidates were ranked by the SHA-256 rule in the manifest. Context groups were allocated first, most constrained first, followed by background groups. All quotas were met without widening the twofold length window.

The following are one-based **data-row numbers, excluding the CSV header**. Each block contains 50 U rows.

| Positive anchor | U group | Data rows | Context requirement |
|---|---|---|---|
| MDM2 | context | 4-53 | nucleus; TRANSMEM=false |
| MDM2 | background | 54-103 | No compartment/TM restriction |
| MDM4 | context | 104-153 | nucleus; TRANSMEM=false |
| MDM4 | background | 154-203 | No compartment/TM restriction |
| EP300 | context | 204-253 | nucleus; TRANSMEM=false |
| EP300 | background | 254-303 | No compartment/TM restriction |

## Exposure and interpretation

No nominated P pair was found in the checked frozen TRAIN-P, TRAIN-U, or development P/U arrays, using accession and exact-sequence matching.

The TRAIN/development audit used the unchanged frozen TUnA input copies inherited from the matched iPIN data; exact sources and SHA-256 values are in the manifest. U pairs found in those arrays were excluded. Protected test truth was not opened. This does not establish absence of previous test exposure, homologous exposure, or language-model pretraining exposure.

Treat this as a biological partner-retrieval case study. Compare ranks or P-versus-U concordance across identical candidate lists; raw scores from different models are not on a common probability scale. Report context and background U groups separately. Do not reuse the historical benchmark's sampling weights for this differently sampled panel.

Before later inference, fetch/retain a sequence snapshot matching the manifest hashes, or explicitly record any sequence-version change. Use unchanged frozen model weights, preprocessing and ensemble rules.

## Sources

- [UniProt target record](https://rest.uniprot.org/uniprotkb/P04637.json)
- [UniProt reviewed human protein-level source pool](https://rest.uniprot.org/uniprotkb/stream?query=reviewed%3Atrue+AND+organism_id%3A9606+AND+existence%3A1&format=tsv&fields=accession%2Cgene_primary%2Clength%2Ccc_subcellular_location%2Cft_transmem%2Csequence%2Ccc_subunit%2Cprotein_existence)
- [IntAct interaction query](https://www.ebi.ac.uk/Tools/webservices/psicquic/intact/webservices/current/search/query/id%3AP04637%2A?format=tab25&firstResult=0&maxResults=2500)
- Per-positive evidence is linked above; additional exclusions and source-response hashes are in the manifest.
