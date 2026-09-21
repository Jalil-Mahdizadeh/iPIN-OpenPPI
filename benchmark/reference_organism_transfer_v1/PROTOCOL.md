# Published interactions involving laboratory reference organisms

Scope revision accepted by the user on 2026-09-21, before model scoring.

## Question

Assess whether the registered frozen human PPI predictors retain useful signal
on published protein interactions between humans and nonpathogenic laboratory
reference organisms. The primary source is the human–yeast study by Zhong et al.
(2016), [PMID 27107014](https://pubmed.ncbi.nlm.nih.gov/27107014/).
Its experimental cross-species network supports a question about biophysical
transfer across evolutionary distance. It does not establish performance on
human pathogens, infection biology, or natural interactions in a human host.

## Organism eligibility

Use exact participant taxids, separately from the organism used to perform an
assay. The reviewed reference labels are *E. coli* K-12 (83333) and
*S. cerevisiae* S288C (559292). Species-only labels 562 and 4932 and all other
taxids are outside this scope. No automatic inclusion of descendants or other
strains is permitted. Human partners have participant taxid 9606.

ATCC lists [K-12 reference material](https://genomes.atcc.org/genomes/531534bd23a542ae)
and [S288C reference material](https://genomes.atcc.org/genomes/7a25fb7d25a24eb8)
at Biosafety Level 1. These records support the reference-strain choice. They
do not authenticate every historical construct or certify a computational
workflow. Here strain identity means the reference-sequence taxonomy recorded
in the archived interaction source, not independent authentication of a culture.

The primary dataset uses S288C and PMID 27107014. Source feasibility showed
1,555 distinct pairs involving 545 yeast and 466 human reference sequences.
K-12 has four pairs involving three nonhuman proteins; retain its eligibility
review but omit it from the primary dataset because coverage is too sparse for
a meaningful species-level comparison. The remaining yeast literature is also
outside the primary dataset to keep the assay source interpretable. These
decisions use source metadata, without inspecting model scores.

## Source and identity checks

Use the existing archived IntAct release 252 and its checksum-bound parsed
cache. Preserve the original study and source artifacts. Independently read
the relevant original XML to confirm every primary evidence record's two
participants, exact taxids, UniProt identities, reference-sequence digests,
publication, detection method, interaction type, and experimental host taxids.
Reject explicitly negative, modelled or intramolecular records. Verify that
recorded participant features are limited to the previously reviewed tag
vocabulary. Require a numeric PubMed identifier; retain nonnumeric legacy
publication aliases as provenance only.

Retain the source sequence filters: 20 standard amino acids, length 50–2,000,
no truncation, no identical-sequence endpoints. Source accession/sequence
conflicts have already been removed from the pinned input. Use archived
reference sequences, with the source's construct-projection limitations.
Collapse repeated evidence to distinct sequence pairs while retaining all
qualifying original evidence. Assay observations are not independent biological
replicates merely because they have different record identifiers.

## Evaluation readiness

Preparation produces a positive-only published dataset. Positive-only score
distributions cannot establish ranking performance, precision, specificity,
AUROC or average precision against noninteractions. Scan the archive's explicit
negative members for exact reference/human participant pairs and record the
result. A missing interaction is not a measured negative.

A subsequent evaluation must define and freeze an appropriate published
comparison set and its assay interpretation before inference. Random sampled
pairs and a new partner-discovery screen are not part of this preparation.
The paper's published comparison data can be assessed in a later source audit.
Before scoring, also complete the actual human TRAIN/development exposure audit,
sequence-similarity review, and a freeze binding inputs, scoring code and model
identities. Do not open protected human test-pair identities or truth.

All selected positives come from one publication. Shared endpoints and repeated
assays limit independence; a large pair count does not supply independent
replication across studies. Supervised PPI exposure and protein-language-model
pretraining exposure are separate questions. No training, calibration, model
selection or parameter changes are authorized by this preparation.

## Attribution

Interaction data: EMBL-EBI IntAct / IMEx, release 252 (2026-01-09), and the
original publication. IntAct data are provided under
[CC BY 4.0](https://www.ebi.ac.uk/intact/about). Original source paths and
checksums remain recorded in the preparation manifest.
