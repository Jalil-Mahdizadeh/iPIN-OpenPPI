# Frozen iPIN transfer to six non-human organisms

Started 2026-09-20, following the user's request to investigate the three frozen
iPIN models and explicit choice of broad transfer with interactions **within
each species**. This is a new external, descriptive evaluation of already
selected models. The prior human results informed the question. No model is
trained, selected, calibrated, or modified here; the historical human tests and
examples remain unchanged.

## Question and scope

Can the original affine iPIN, optimized pooled iPIN, and TUnA-retrained rank
released-positive partners above unlabeled candidates in mouse, fly, worm,
budding yeast, Arabidopsis, and E. coli K-12? Report species separately and give
each species equal weight in any overall summary. This measures transfer from
human PPI supervision; it does not establish absence from ESM pretraining.

## Evidence and sequence identity

Use the six original PSI-MI XML species archives in IntAct release 252,
2026-01-09. The source is archived rather than a changing API. Download URLs,
HTTP identity, local checksums, archive member names, and XML provenance are
retained. IntAct data attribution: https://www.ebi.ac.uk/intact/about (CC BY 4.0).
No data from human protected test pair/truth files are required.

Primary positives require exactly two protein participants (MI:0326), direct
interaction (MI:0407) or a binary two-hybrid experiment (MI:0018 descendants)
annotated as MI:0407/MI:0915/MI:0914, no negative flag, no modelled or intramolecular flag, no
expansion, matching organism taxids from `config.json`, UniProt identities,
explicit reference sequences, and **no recorded non-tag participant features**.
Only MI:0507 tag descendants are allowed; annotated mutants/fragments and other
feature-bearing records are excluded. It does not prove that unannotated experimental
constructs were full-length wild type. Results concern the archived reference
sequence projection of that evidence. This rule was adjusted after a metadata-
only feasibility audit and before any model scoring; see
[the adjustment record](PRE_SCORING_EVIDENCE_ADJUSTMENT.md).
Negative records remain separate and
are not promoted to universal biological negatives.

Sequence eligibility is 50–2,000 residues, the 20 standard amino acids only.
The upper bound controls full-context inference cost and must be reported as a
coverage limitation. Never truncate or change a frozen model's preprocessing.
Conflicting sequences for an accession are excluded. Deduplicate by exact
sequence within each species; exclude self-pairs and identical-sequence pairs.
All positively reported co-participant pairs, including broader associations
and complex co-membership, are excluded from U; complex expansion is used only
for exclusion, never to create P. Also exclude explicitly negative pairs from
the U pools so that U denotes unreported evidence in this source snapshot.

## Panels, selected before model inference

Within each species, uniformly choose up to 50 eligible targets by a seeded
SHA-256 ordering. Each must have at least two eligible positive partners and
enough distinct candidates. Include up to ten P per target, also by seeded
hash; unselected known partners never become U. Targets are selected by source
eligibility and the hash, never by a model score, sequence similarity to human,
or a preferred biological function. Fewer than 50 targets is reported without
changing the rule. Candidate proteins come from the same archived species
evidence universe, so this is not a whole-proteome or uniformly sampled
proteome claim.

Select 100 background U per target by hash. Select a disjoint 100 matched U by
cycling over the selected P and prioritizing the same observed association-
degree bin (0–2, 3–9, 10–29, 30+) and length within 0.5–2 times the P length.
If a matched pool runs out, relax degree before length and record the tier.
Tie-break using seeded hashes. This controls simple length/study-degree cues;
it is not a claim of biological context matching or noninteraction. Counts are
**per target**, not per P. Freeze selected sequences, panels, source evidence,
metric code, and scoring code before inference.

Evaluate P+background U, P+matched U, and P+all 200 U. This independent design
does not inherit the human example's low-plausibility compartment rules.

## Frozen scoring

Use the unchanged v2 model registry and the pinned iPIN and TUnA Apptainer
images. Fresh embeddings are computed from the frozen external sequences.
Preserve the pooled models' TRAIN normalizer, residue windows, member ordering,
and FP64 ensemble mean. Preserve TUnA's full-context representation, frozen GP
covariance, epoch-4 members, and mean adjusted logits. No sigmoid, threshold,
temperature, species normalization, or covariance refit is introduced.
Verify checkpoint/source hashes, finite complete outputs, pair-order symmetry,
and native TUnA agreement on species-spanning fixtures and the longest pair.

## Metrics and uncertainty

Primary: equal-target P-versus-U concordance within each species for matched U.
Also report AP/MAP, expected first-P rank, reciprocal rank/MRR, positive ranks,
recovered P, recall, known-positive precision, enrichment factor, NDCG, and
target success at K=5,10,20 for all three candidate sets. Use the existing
example's threshold-group AP and fractional/expected tie conventions. U is
unlabeled: accuracy, specificity, F1, MCC, biological precision, and calibrated
interaction probabilities are not identified by this design.

Compute paired model differences with 10,000 seeded target-bootstrap draws
within species; resample the same targets for every model. These exploratory
intervals are conditional on the selected panels and fixed models. Related
targets, reused partners, studies, and overlapping reversed pairs mean they are
not a full account of biological sampling uncertainty. Report target/pair
reuse, study concentration, and coverage. Equal-species summaries resample
targets within all species, not a mixture of cross-species pairs. Human C3 and
this external panel have different candidate designs; do not treat their raw
metric difference as a controlled estimate of the species effect.

## Training exposure and similarity

Read only frozen human TRAIN and development inputs and the public sequence
catalogue. Audit exact sequence/pair exposure; a different taxid is not proof
of unseen sequence. Search external sequences against actual TRAIN endpoint
sequences with pinned MMseqs2 (sensitivity 7.5, E<=0.001). Report best local
matches and matches with >=80% coverage of both sequences, plus bins of the
best qualifying identity (<30%, 30–50%, 50–80%, >=80%; no qualifying hit is
separate). Summarize target retrieval by target similarity and P-versus-U
concordance by both-endpoint homology status. Include a sensitivity excluding
any pair with an exact TRAIN/development endpoint match. No hit under these
settings does not prove absence of remote homology or shared domains.

## Completion

Independently validate labels, taxids, source evidence, deduplication, exclusion
rules, frozen identities, and metrics with scikit-learn and separate rank
oracles. Publish the selected panel, score and metric tables, coverage and
exposure audit, figures, report, reproducible scripts, and checksum manifest.
Large source archives and inference caches stay local and are checksum-bound.
