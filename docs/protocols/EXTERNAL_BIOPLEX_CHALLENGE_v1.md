# Locked external BioPlex co-association challenge v1

Date: 2026-09-11. Authority: DEC-0048.

## Question and lock

Does the small sequence pair head recover independently generated AP-MS
co-associations beyond unary propensity, direct similarity and interaction
transfer, on endpoints absent from its fitting data and normalization?
BioPlex is a Gygi/Harper laboratory programme using AP-MS rather than the HuRI
Y2H programme. It is not independent of all public biological knowledge or
ORFeome resources. Its two cell lines are related evidence, not two independent
laboratory replications. See the [published study](https://doi.org/10.1016/j.cell.2021.04.011)
and [official releases](https://bioplex.hms.harvard.edu/interactions.php).

Freeze this protocol/config, the DEC-0047 execution freeze, all eighteen
`purged20` checkpoints and the three normalization/fitting plans before
acquiring any external interaction rows. Source choice is informed by the
literature and prior internal outcomes, not new BioPlex model results. Reuse
the three seeds, two heads and raw-score ensemble without refitting. No model
selection or new encoder extraction. Freeze tested implementation, source hashes
and selected panels before scoring. This is a local computational preregistration,
not an external registration or previously unexposed protein test.

## Source, mapping and exposure

Only six published assets named in the config may be downloaded. Use HTTPS,
verified TLS, immutable project-local raw snapshots, headers, timestamps,
SHA-256 and a 40 MB/file ceiling. Record unavailable publisher checksums as
unavailable, not verified. Cite the published resource; do not redistribute
raw files or use unpublished quarterly releases.

Read official undirected rows for their accession/Entrez mapping, directed
rows for bait/prey orientation, and bait lists for experiment coverage. Map
only exact UniProt accessions from the frozen public endpoint metadata.
Reject ambiguous identifiers; do not strip isoform suffixes, infer mappings
from symbols, or acquire new sequences. This is reference-sequence mapping,
not proof of construct identity. Report unmapped/ambiguous/self/cross-fold/
previous-positive attrition. Validate directed edges against the same-cell
published undirected network and bait inventory; fail closed on inconsistency.
Schema-only inspection can precede the tested implementation freeze; no new
score may be inspected during development.

No development/protected package, evaluator ledger or key is read. Broader
downloaded source files are physically scanned in a constrained public-endpoint
projection; only public endpoint indices and aggregate counts leave it.
Existing released public P/U, folds, alignments, embeddings and prior reports
remain unchanged.

## Panels and comparisons

Evaluate 293T and HCT116 separately, never selecting the more favorable one.
For each original fold, both endpoints must belong to that fold. Score using
that fold's already fitted `purged20` heads and fitting-only transfer graph.
Verify zero detected direct >=20%-identity, >=80-residue-span, >=20%-both-coverage,
E<=1e-3 links between the heldout fold and its surviving fitting endpoints.
This is detected-link exclusion, not proof of nonhomology or new families.

Positives are mapped directed bait-to-prey BioPlex detections whose unordered
pair is absent from **all** 16,799 previously released public P. Count each
distinct directed reference edge once. An eligible anchor is a published bait;
candidate partners must have appeared as preys somewhere in that cell line's
directed network. These are ascertainment-matched identities, not evidence
that each bait/prey opportunity was attempted or evaluable.

U reuses only existing parent public U with both endpoints in the evaluation
fold. Orient each eligible row from bait to an observed prey. Exclude either
orientation of all current-cell observed positive pairs, including previously
known positives; do not call a reverse detection negative. Keep original exact
rational U weights. A pair can appear in both anchor directions, but a query
contains each partner once. No labels from the other cell line exclude U.
Source-union U curation and pre-explored endpoint support remain limitations.

Each cell/fold needs >=100 P, >=1,000 U, >=50 eligible anchors, and >=20 anchor
components. Failure in any fold makes that cell's anchor endpoint infeasible;
do not replace it or relax thresholds. U is unlabeled, not a negative.

Primary metric: equal-bait-macro design-weighted P-versus-U concordance. Report
the three-seed mean raw-score ensemble, every fold and every seed. Comparators
are linear unary, all four DEC-0047 exhaustive fitting-P transfer controls,
direct normalized 3-mer cosine, raw pooled cosine and length ratio. This
explicitly includes older controls that outperformed new transfer in DEC-0047.
No external network degree, source score or external edge enters model features
or interaction-transfer fitting graphs.

## Endpoint-balanced partner alternatives

Within each cell/fold enumerate distinct-endpoint directed P(A,B), P(C,D)
with both directed alternatives U(A,D), U(C,B) present. Do not reverse bait/prey
roles. Select in ascending SHA-256 order over the configured salt, cell, fold
and endpoint tuple, maximum 2,000 per fold, each P at most ten uses and each
endpoint at most twenty. No selection uses a prediction. Preserve selection
counts and panels; do not fill sparse folds by changing rules.

Swap credit is one for a summed-score advantage >1e-6, one-half within 1e-6,
zero otherwise. Additive unary scores cancel. Require >=30 quartets and >=20
contributing original components in each fold for a cell-level swap conclusion.
Otherwise report an inconclusive swap even if its anchor test is feasible.

## Uncertainty and decision

Use 2,000 shared Poisson(1) original-component multipliers, PCG64DXSM seed
20260917. Recompute within-bait P/U ratios with partner component weights and
weight each anchor by its component; for quartets multiply each distinct
endpoint-component weight once. This inherits the prior conditional multiplier
estimand, including ratio renormalization when partners receive zero weight.
Percentile 95% intervals require >=95% valid replicates. They condition on
locked heads, selected public support, source release and sampling design;
they do not include refitting, assay detection or new-source uncertainty.

A cell's anchor challenge passes only if the pair ensemble beats the largest
comparator macro by >=0.02, every paired 95% lower bound is >0, and every fold
and every seed beats linear unary. A supported swap passes only if the pair
lower bound is >0.5 and every paired lower bound versus non-unary controls is
>0. Overall external robustness requires both endpoints in both cells; retain
partial passes, failures and underpowered outcomes separately. These are
research triage rules, not population-calibrated hypothesis tests.

## Verification and claim ceiling

Test accession ambiguity, orientation, old-positive exclusion, other-cell
isolation, source-positive U exclusion, C3 disjointness, deterministic quartet
caps, numerical null cancellation and failure cases. Independently reconstruct
the source projection/panels, all learned forwards and all point estimates;
independently enumerate all fitting edges for deterministic transfer-score
samples; directly check 16 full anchor bootstrap replicates per cell and all
quartet replicates plus interval/decision arithmetic. Hash-bind execution and
closure evidence. Numerical verification is same-author, not external review.

Success supports transfer of released co-association ranking to an orthogonal
experiment source. AP-MS can capture indirect complex membership; failure can
reflect endpoint shift, biology, assay context, or absent signal. Neither
outcome identifies a causal mechanism. No biological accuracy, calibrated
binding probability, complete assay opportunity, independent-family or novel
architecture claim follows. Do not open protected evaluation after this run.
