# All published positives versus 100 distinct unlabeled pairs per positive

## User-directed correction

The user requires all **1,555 published human–S288C positive pairs** and
**100 U pairs for each P**, with **155,500 globally distinct U pairs**.
This creates 1,555 panels of one P and 100 U, or **157,055 total pairs**.
The organism scope remains human (9606) and laboratory reference S288C (559292).
The original 545 S288C sequences are retained; the human partner pool expands
to eligible human sequences already present in the checksum-bound archive.

The earlier 36-versus-39 comparison measured secondary-assay confirmation.
It did not complete a P-versus-U benchmark. All 39 previously reported P that
failed secondary confirmation remain P here, as do every other original P.
Secondary-assay results play no role in P/U construction or model selection.

This correction follows inspection of the earlier positive-pair model scores.
It is an exploratory follow-up, not a study designed before any model scores
were known. U selection uses source metadata and a fixed seed, never scores.
Freeze this protocol, data, scoring code and metric code before new inference.

## Positive and candidate identity

Copy the original verified `published_pairs.csv` byte for byte and include
every pair once. Preserve its reference sequences, aliases and evidence.
The positive evidence comes from one publication and the archived IntAct
release 252. It is reported experimental evidence, not error-free ground truth.

Human candidates come from the existing frozen source cache: taxid 9606,
unambiguous archived accession/sequence identity, 50–2,000 residues, and the
20 standard amino acids. Collapse identical sequences. These are archived
reference proteins/isoforms, not a claim of uniform whole-proteome coverage.
Keep each P's yeast endpoint fixed and replace its human partner to obtain U.

Before sampling, exclude every reported human/reference co-participant pair
in the source cache, including broad associations, complexes, explicitly
negative records and interactions outside the primary publication. Match
reference endpoints by exact sequence even when another taxid label appears
in an exclusion record. Also exclude all original P and identical-sequence
endpoints. This conservative rule is limited to the declared source snapshot;
unreported pairs may contain real interactions. U never means verified negative.

## Exactly 100 globally distinct U per P

The source association-degree field and length are metadata matching controls,
following the existing nonhuman benchmark. Degree bins are 0–2, 3–9, 10–29
and 30+. Relative to the P's human partner, prioritize (0) same degree bin and
length ratio 0.5–2, (1) length only, (2) degree only, (3) neither. Report all
fallback counts; metadata matching does not establish biological plausibility.

For each P, use a NumPy PCG64 permutation seeded from SHA-256 of the study seed
and positive pair ID to break ties within matching tiers. Within each yeast
target, order P by a seeded hash and allocate candidates in 100 rounds, one
unused candidate to every P in each round. Share a used-human set across all
P for that target. This prevents easy depletion by the first P and guarantees
global sequence-pair uniqueness. Different yeast targets may share a human
protein, but never the same complete U pair. Stop on shortage; do not drop P,
reduce the U ratio or reuse U. Validate the exact counts independently.

## Frozen models and exposure

Apply the same three registered ensembles unchanged: baseline iPIN, optimized
iPIN and TUnA retrained. Preserve preprocessing, human TRAIN normalization,
member weights/order, TUnA selected epochs and GP covariance. No fitting,
threshold choice, calibration or model selection uses this evaluation.
Use the accepted pinned containers and the qualified inference implementations.

Audit exact sequence/pair matches to actual human TRAIN and development inputs
and similarity to TRAIN using the existing qualified audit. Do not open
protected human test pairs or truth. ESM pretraining exposure is not audited.
Primary results retain every P, as requested. A separately labeled sensitivity
may remove exact TRAIN/development endpoint matches; report all resulting
counts and do not present it as the requested complete 1:100 benchmark.

## P-versus-U evaluation

Within each 101-pair panel, compute the fraction of its 100 U scores below
its P score, with half credit for ties. The primary summary averages the
1,555 per-P concordances equally. Also report equal-target concordance by
first averaging panels within each of the 545 yeast targets, then averaging
targets. Do not pool unrelated targets into a single AUROC.

Use the repository's existing tie-aware retrieval metrics: AP, expected P rank,
MRR, recall and NDCG at 5, 10 and 20. Report random-order references (concordance
0.5, recall at k = k/101). With one P per panel these are known-positive
retrieval measures; they do not identify biological specificity or precision.
Report a source-degree ranking control and matching coverage.

For exploratory uncertainty use 10,000 paired yeast-target bootstrap draws
with seed 20260921, keeping all panels for a sampled target together and using
identical draws across models. For equal-P estimates, resample sums and counts
and divide, preserving the chosen weighting. Intervals are conditional on
these fixed panels and one source study; shared human partners and homologous
proteins create residual dependence. They do not measure replication across
studies or establish performance on human pathogens.

## Completion

Independently verify preservation of all P, taxids, sequence hashes, per-P U
counts, global pair uniqueness, P/U disjointness and source exclusions before
inference. After inference verify score alignment and finite values, model
identity and symmetry, and per-panel concordance against an independent
implementation. Publish tables, provenance, exposure, results, limitations,
reproduction commands and final checksums. Report preparation and evaluation
completion separately. The previous assay analysis remains a historical study.
