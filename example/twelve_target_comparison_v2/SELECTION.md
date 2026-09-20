# Low-plausibility U selection, fixed before inference

Add **50 U per nominated positive**, preserving all original P, context U and
background U. Twelve targets contain 37 P and 1,850 U in each of three strata:
5,587 pairs. ERN1 has four positive anchors; other targets have three.
Candidates remain **unlabeled**, not true negatives.

The user explicitly chose **“Keep 50 with explicit evidence tiers”** after being
told strict separation cannot fill EGFR's quotas. Feasibility used annotations
and exclusion records only. No new scores or embeddings were read in selection.
Previously examined targets make this a descriptive follow-up; score-independent
new sampling does not make the whole study blind.

## Sources and identity

Use newly retrieved UniProt reviewed human, protein-level-evidence entries with
primary genes and canonical sequences of at least 30 residues. Search alternative
locations, including notes, for conservative vetoes. URLs, retrieval times,
releases and hashes are in `PANEL_BUILD.json`; raw snapshots remain in `sources/`.

The [Human Protein Atlas subcellular data](https://www.proteinatlas.org/humanproteome/subcellular/data)
provide imaging locations and evidence levels. Its landing page describes HPA
25.1 / Ensembl 109. Identify actual unversioned downloads by exact hashes and
HTTP headers, rather than assuming every archive has the landing page's release.
HPA's protein table maps UniProt accessions to Ensembl genes; require a unique
ID and matching primary gene name. Ambiguous mappings supply no HPA support.
All HPA locations, including approved and uncertain alternatives, veto an
incompatible single-compartment claim. Only enhanced/supported locations count
as support. No HPA predicted localization embeddings are used.

## Evidence tiers

**A — compartment separation:** affirmative curated location and membrane-side
annotations make encounter with the mature target less plausible in its usual
cellular setting. Restricted matrix/peroxisomal/nuclear candidates must lack
alternative cytoplasmic, surface, secretory or other incompatible locations.
Secreted/luminal candidates also require an annotated signal peptide and no
transmembrane segment. Secretory transit is compatible with secretion, not
evidence of cytoplasmic access. Missing location is never negative evidence.

| Target | Candidate classes admitted to A |
|---|---|
| ERN1, TNFRSF1A | Restricted nuclear, mitochondrial matrix, peroxisomal |
| TP53, BRCA1 | Secreted, secretory lumen, peroxisomal |
| EGFR | Peroxisomal |
| BCL2, KEAP1, KRAS, CDK2, HIF1A, CTNNB1, BECN1 | Secreted, secretory lumen, mitochondrial matrix, peroxisomal |

Both faces and secretory trafficking of ERN1/EGFR/TNFRSF1A are considered.
Nuclear/mitochondrial U are not called strictly separated from EGFR. TP53's
annotated matrix location excludes matrix candidates. BRCA1 is conservatively
handled without mitochondrial candidates. BECN1's HPA nuclear location excludes
nuclear candidates. BCL2's mitochondrial outer membrane location does not imply
matrix access; generic mitochondrial candidates are not admitted to its tier A.

**B — dominant-location mismatch with known secondary overlap (EGFR only):**
restricted mitochondrial/nuclear candidates require experimental UniProt location
evidence and concordant enhanced/supported HPA staining, without contradictory
HPA locations. Prefer explicit matrix, then other non-membrane mitochondrial,
then nuclear candidates. This is a weaker prior only: EGFR has documented
mitochondrial and nuclear locations, so tier B is **not compartment incompatibility**.
See primary studies on [mitochondrial EGFR](https://pmc.ncbi.nlm.nih.gov/articles/PMC2794774/)
and the [subcellular EGFR interactome](https://www.nature.com/articles/s41389-020-0225-0).
Report all tiers and a separate equal-target analysis of the eleven targets
whose additions contain only A. Neither tier establishes noninteraction.

Annotation quality is recorded separately: 0 = UniProt experimental plus HPA
enhanced/supported; 1 = UniProt experimental only; 2 = HPA enhanced/supported
plus reviewed UniProt; 3 = reviewed UniProt without either extra support.
`ECO:0000269` must occur in the location annotation before its note. Protein-level
evidence establishes existence, not location confidence. Quality 3 is a disclosed
annotation-based fallback, never relabeled experimental evidence.

## Exclusions, matching and allocation

Exclude the query, all existing P/U and identical sequences; current IntAct
human–human neighbors in either orientation (including complexes, isoforms and
alternate identifiers); preserved historical exclusions; target and reciprocal
UniProt SUBUNIT/INTERACTION annotations; all frozen iPIN TRAIN/development pairs
of either label; and documented original-TUnA Bernett training/validation pairs
of either label. Exposure is checked by accession and exact sequence in both
orientations. No protected test files or quarantined negative evidence are read.
These checks do not establish homology or sequence-pretraining independence.

Each candidate is 0.5–2.0 times its **positive anchor's** sequence length.
The encounter screen concerns the **target–candidate pair**, not similarity to
the positive. Deduplicate canonical sequences and use a candidate at most once
per target. Cross-target reuse is allowed and reported. Absence of a transmembrane
annotation alone does not prove solubility; affirmative location is also required.
Unlike context U, new U do not match the positive's transmembrane status.

Assign all anchors' quotas together with SciPy's minimum-cost linear assignment
to protect scarce long-anchor pools. Edge cost is
`1e9*tier_B + 1e6*tier_B_location_priority + 1000*annotation_quality
+ abs(log2(candidate_length/anchor_length)) + 1e-6*deterministic_hash`.
Salt: `ipin-twelve-target-low-plausibility-20260920-v2`; hash inputs also include
target, anchor accession and candidate accession. Prefer tier A, the declared
EGFR location order, annotation quality, then length closeness. No fitted weights
or model scores enter selection. Insufficient quota stops the builder; neither
length windows nor exclusions silently widen.

## Interpretation

These priors concern usual cellular encounter, with no assay/cell type specified.
Import, shuttling, cleavage, stress, lysis and incomplete annotation can defeat
them. The new group changes candidate difficulty and composition, including
secretion signals. Improved retrieval would not establish a globally better
model or a measured lower interaction rate in this U stratum.
