# CTNNB1 biological partner panel

Human CTNNB1 (P35222), selected for cell adhesion and wnt transcription.
The [input CSV](ctnnb1_ipin_panel.csv) contains **3 P + 300 U = 303 pairs**.
Current inference and all retrieval metrics: [RESULTS_v2.md](RESULTS_v2.md).

## Nominated positives

| Partner | Accession | Evidence and context |
| --- | --- | --- |
| CDH1 | P12830 | [Curated human beta-catenin-E-cadherin interaction; E-cadherin cytoplasmic tail binds beta-catenin. Homologous structural support: PDB 1I7X (murine proteins).](https://www.uniprot.org/uniprotkb/P35222/entry) |
| CTNNA1 | P35221 | [Curated human beta-catenin-alpha-E-catenin interaction; distinct from alpha-N-catenin (CTNNA2).](https://www.uniprot.org/uniprotkb/P35222/entry) |
| TCF7L2 | Q9NQB0 | [Direct beta-catenin-TCF4 (TCF7L2) binding supports Wnt-dependent transcription.](https://www.rcsb.org/structure/1JDH) |

These are supported nominated partners, not an exhaustive catalogue. Canonical
sequences do not encode biological state, modifications, cleavage, or experimental
fragment boundaries. Evidence may concern particular domains or conditions.

## Unlabeled controls

Each positive anchors 50 compartment/TRANSMEM-matched and 50 background U
proteins, all within 0.5-2 times its length. All quotas were met without widening.
U means unlabeled, not verified noninteraction. The source pool contains reviewed
human UniProt proteins with protein-level evidence, primary gene names, and
supported canonical sequences of at least 30 residues. Controls are deduplicated
by sequence and sampled without replacement within this target.

| Anchor | U group | Rows | Compartment | TRANSMEM |
| --- | --- | --- | --- | --- |
| CDH1 | context | 4-53 | cell membrane | True |
| CDH1 | background | 54-103 | Unrestricted | Unrestricted |
| CTNNA1 | context | 104-153 | cytoplasm | False |
| CTNNA1 | background | 154-203 | Unrestricted | Unrestricted |
| TCF7L2 | context | 204-253 | nucleus | False |
| TCF7L2 | background | 254-303 | Unrestricted | Unrestricted |

Rows are one-based data rows, excluding the CSV header. Broad compartment matching
uses UniProt location text; the declared positive context can also be supported
by UniProt GO cellular-component annotation. Absence of TRANSMEM does not prove
solubility. Context groups are allocated first, most constrained first. Selection
uses SHA-256 ordering with salt `ipin-twelve-target-panel-v1-20260920` and no model scores.

Exclusions include the query, all nominated partners, IntAct human-human partner
identifiers, target/reciprocal UniProt subunit annotations, TRAIN/development P
and U neighbors, and identical excluded sequences. The [manifest](panel_manifest.json)
retains source URLs and hashes, exact row identities, matching groups, and exposure
records. Public raw responses are retained locally in the comparison's ignored
`sources/` directory.

## Exposure

No nominated P exact pair was found in the checked TRAIN/development P/U arrays.

The checks use accessions and exact sequences. Protected-test pair labels were
not opened. Homology, prior examples, and sequence pretraining are separate
exposure questions. Results and exposure sensitivities are retained in the
[twelve-target report](../twelve_target_comparison_v1/REPORT.md).
