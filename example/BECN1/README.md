# BECN1 biological partner panel

Human BECN1 (Q14457), selected for autophagy regulation.
The [input CSV](becn1_ipin_panel.csv) contains **3 P + 300 U = 303 pairs**.
Current inference and all retrieval metrics: [RESULTS_v2.md](RESULTS_v2.md).

## Nominated positives

| Partner | Accession | Evidence and context |
| --- | --- | --- |
| ATG14 | Q6ZNE5 | [Human ATG14 coiled-coil interaction with Beclin 1; mutually exclusive with UVRAG-containing complexes.](https://pmc.ncbi.nlm.nih.gov/articles/PMC2592660/) |
| UVRAG | Q9P2Y5 | [Direct Beclin 1-UVRAG coiled-coil heterodimer.](https://www.rcsb.org/structure/5YR0) |
| BCL2 | P10415 | [Curated human BECN1-BCL2 interaction through the Beclin 1 BH3 domain; structural support in PDB 5VAX uses an engineered BCL2/BCL2L1 construct.](https://www.uniprot.org/uniprotkb/Q14457/entry) |

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
| ATG14 | context | 4-53 | endoplasmic reticulum | False |
| ATG14 | background | 54-103 | Unrestricted | Unrestricted |
| UVRAG | context | 104-153 | endoplasmic reticulum | False |
| UVRAG | background | 154-203 | Unrestricted | Unrestricted |
| BCL2 | context | 204-253 | endoplasmic reticulum | True |
| BCL2 | background | 254-303 | Unrestricted | Unrestricted |

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

ATG14: TRAIN_P; UVRAG: TRAIN_P

The checks use accessions and exact sequences. Protected-test pair labels were
not opened. Homology, prior examples, and sequence pretraining are separate
exposure questions. Results and exposure sensitivities are retained in the
[twelve-target report](../twelve_target_comparison_v1/REPORT.md).
