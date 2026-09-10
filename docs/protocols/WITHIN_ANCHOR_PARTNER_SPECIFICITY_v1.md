# Within-anchor partner-specificity diagnostic v1

Date: 2026-09-11. Authority: DEC-0046. Freeze before model performance is
inspected; this is a local prospective specification, not a public registry.
The YAML configuration is the executable specification.

## Question and interpretation

Does the corrected frozen-ESM-150M pair head rank a particular anchor's released
partners beyond endpoint propensity and simple sequence relationships?
The previous development result motivated this question and model choice.
Public training data have also been explored before. A new split does not
erase that history: this is an internal diagnostic, not external confirmation.
P denotes released positives; U is unlabeled, never a verified noninteraction.

Read only the frozen public tables and raw embeddings listed in the config.
Do not read development rows, evaluator source-membership artifacts, protected
packages, or keys. Training source memberships are omitted from the public
package, so source-stratified and assay-batch analyses are unavailable. A
positive result cannot establish source robustness or physical specificity.

## Split, census, and execution freeze

Assign the 5,427 whole public-training leakage components to three folds by
descending size, salted SHA-256 tie ordering, then greedy assignment to the
smallest endpoint-count fold (lowest fold index breaks ties). Labels and model
scores never choose a split. Every endpoint is evaluated in only one fold;
only same-fold edges enter primary C3 evaluation. Cross-fold edges are not
silently counted as C3. For each fold, fit only P and U edges with both
endpoints outside it. Report all row/endpoint/component counts and exclusions.

Before fitting, hash protocol/config/authority and produce the census,
deterministic quartet selection, and input-identity checks. Freeze the complete
implementation/test hashes and preparation artifacts before training. Reject
drift and refuse overwrites. No outcome-driven reruns or checkpoint selection.
Only a census meeting every configured minimum may proceed to fitting.

The coverage check includes anchor-count effective component sample size
1/sum(component anchor fraction squared). Show illustrative normal-approximation
80%-power minimum detectable effects (1.96 + 0.8416) * sigma / sqrt(N_eff) for
component-effect SD 0.05, 0.10, 0.20. These are assumptions, not measured power:
candidate dependence and fitted-model variability can make actual uncertainty
larger. Low precision must be reported as inconclusive, not scientific failure.

## Matched learning experiment

Reuse raw stored vectors, joined explicitly by sequence SHA and manifest row
index; verify all used raw vector hashes. Refit mean/population standard
deviation on the fold's fitting endpoints only. Never reuse the parent's
all-training normalizer or trained head checkpoints.

Fit three symmetric heads with the same fixed optimizer, row order, five
complete passes, three seeds, and final-pass checkpoint policy:

- endpoint_linear: u(a) + u(b), u a linear 640-to-1 map;
- endpoint_mlp64: u(a) + u(b), u = Linear(640,64), GELU, Linear(64,1), no dropout;
- pair_linear: the existing Linear(1921,1) over a+b, abs(a-b), a*b, cosine(a,b).

The strong endpoint comparator is intentionally nonlinear and has greater
capacity than the affine pair head. Only the last head has joint features.
Use the existing design-weighted global P-versus-U logistic objective, not
within-anchor negative mining, so all models have matched supervision.
All U rows occur once each pass. P rows cycle through a seeded permutation;
repetition counts differ by at most one. Training-only loss is logged; no
holdout scores are examined until all 27 fits finish. No encoder runs needed.

## Primary and supporting estimands

For anchor a with at least one P and one U partner, let C_a be the mean over
its P partners of the design-weighted fraction of U partners scored below
them, with half credit for ties. Primary C is the equal-anchor mean of C_a,
not a pooled edge metric. Original integer U weight numerators/denominators
are retained. Report eligible anchors and zero-P/zero-U exclusions.

Average raw model scores across the three seeds within each fold, then
aggregate anchor metrics across folds with equal anchor weight. Do not compare
raw logits between different fitted folds. Report each seed and fold too.
Show deterministic length-ratio, 3-mer cosine, and raw pooled-embedding cosine
controls. These do not exhaust homology/interolog confounding.

Secondary Recall@10/100 uses only the actual released P/U candidate panel and
is explicitly unweighted panel recall, never full-universe recall or biological
precision. Numeric canonical pair order breaks exact retrieval ties.

A prespecified propensity sensitivity fits five quintile boundaries to the
strong unary ensemble's fitting-endpoint scores. Within each anchor compare
P/U partners only in the same fixed bin; aggregate over comparable positives
then equally over eligible anchors. Report coverage; do not silently change
the primary estimand. No heldout degree is used as an input or fitting feature.

## Endpoint-balanced partner swaps

For two P edges (A,B), (C,D) with four distinct endpoints, enumerate both
cross-matchings. Retain a matching only when both cross edges are released U
rows in the same evaluation fold. Deterministic hashed selection caps counts
per fold, P edge, and endpoint, as configured. No new negative labels or unseen
candidate pairs are created. Report eligibility and selected-panel coverage.

Raw-score contrast D = s(A,B) + s(C,D) - s(A,D) - s(C,B) cancels every additive
endpoint score exactly in real arithmetic. Unary evaluation computes endpoint
scores once and sums in float64 to avoid spurious FP32 cancellation evidence.
The statistic is the fraction D > 1e-6, with half credit when abs(D) <= 1e-6.
Use sign/tie credit, not mean raw D, for comparisons across score scales.
Quartets are uniformly weighted in this selected panel: their complex joint
sampling probabilities are not the parent U pair weights. No population-wide
quartet inference is claimed. Pairwise similarity or assay confounding may
still explain success; compare length/3-mer controls explicitly.

## Paired uncertainty and decision

Generate 2,000 fixed independent Poisson(1) multipliers for every public leakage
component. The same draws apply to every model and fold. For a query anchor,
weight its final contribution by its component multiplier. Inside C_a, weight
each P/U partner by its component multiplier unless it shares the anchor's
component (already represented by the anchor multiplier). Recompute normalized
within-anchor metrics; skip a resampled anchor with zero P or U mass. For
quartets, multiply once per unique component among all four proteins.
Use percentile 95% intervals and paired differences. This is a prespecified
component multiplier sensitivity conditional on trained models, fixed folds,
and the sampled panel, not uncertainty from refitting or source sampling.
Record invalid replicates; require at least 95% valid replicates.

Useful signal requires ensemble macro gain >=0.02 over endpoint_mlp64 and a
paired 95% lower bound >0, positive gain in every fold and seed, positive gains
over the other frozen controls, positive propensity-stratified gain, and a
quartet lower bound >0.5 with positive gains over length and 3-mer controls.
The 0.02 margin is a research triage choice, not biological calibration.
If the primary upper bound is below 0.02, report that a useful incremental gain
was not demonstrated under this recipe; do not claim all representations fail.
Otherwise report inconclusive/mixed evidence. No outcome revives the old gating
claim or opens protected evaluation.

## Reproducibility and validation

Unit tests must cover identity permutations/duplicates, component isolation,
training-only normalization, brute-force weighted within-anchor metrics, ties,
shared-component weights, quartet enumeration/caps/cancellation, deterministic
repeats, and fail-closed path/freeze behavior. Validate frozen input hashes,
all prepared pair joins and fold assignments, selected quartet eligibility,
checkpoint completeness, finite scores, symmetry, and metric recomputation.
Retain compact public JSON reports plus hash-bound local arrays/checkpoints.

Background: [Bernett et al. (2024)](https://academic.oup.com/bib/article/25/2/bbae076/7621029)
and [Yilmaz et al. (2025)](https://doi.org/10.1073/pnas.2416646122) motivate
shortcut-aware controls and node-weighted evaluation. They do not establish
the outcome of this new experiment.
