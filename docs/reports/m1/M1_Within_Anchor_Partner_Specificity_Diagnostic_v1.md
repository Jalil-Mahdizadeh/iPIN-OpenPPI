# Within-anchor partner-specificity diagnostic: results

Date: 2026-09-11. Authority: DEC-0046.

## Bottom line

The prospectively specified internal test passes all eight frozen signal
checks. The small pair-dependent head ranks released partners better than both
endpoint-only controls, and prefers observed pairings in an endpoint-balanced
swap test. This is evidence against calling the entire research direction a
dead end. It does **not** establish physical binding specificity, external
generalization, or a benefit from the stopped partner-gated architecture.

The frozen readout is numerically verified. All 357 unit tests, the separate
reference validator, and the supporting arithmetic audit pass. Protected
evaluation remains sealed and unauthorized.

## What was frozen and executed

The user's instruction, "act according to your recommendations", authorized
this bounded study. The protocol/configuration were hashed before the census;
the complete execution implementation, tests, inputs and prepared panels were
hashed before any public-data head fit. This is a **local prospective
specification**, not an external registry or a previously untouched dataset.
Earlier development findings motivated the question and pair-head choice.

Three whole-component folds partition the 11,900 public-training endpoints.
For each fold, fitting excludes every P/U pair incident to its components;
evaluation uses only pairs with both endpoints in that fold (C3). Mean and
standard deviation are refit on the other folds' endpoints. Raw frozen 150M
vectors are joined by manifest sequence identity and storage row, with every
used vector hash verified. No old head checkpoint or all-training normalizer
is reused.

Three heads, three seeds, three folds: 27 fits, five complete passes each,
fixed AdamW recipe and final-pass checkpoints. All fits finished before any
heldout scoring. Total fitting time was 93.19 seconds on the qualified GH200
runtime; no encoder extraction or fine-tuning was necessary.

The paired head is affine over sum, absolute difference, elementwise product,
and cosine features: 1,922 parameters. Controls are an additive linear unary
head (641 parameters) and additive 64-hidden-unit GELU unary network (41,089
parameters). All have matched fitting data, row order, objective and budget.

## Coverage and feasibility

| Fold | Heldout endpoints | Eligible anchors | C3 P | C3 U | Selected quartets |
|---|---:|---:|---:|---:|---:|
| 0 | 3,967 | 1,075 | 2,012 | 225,651 | 2,000 |
| 1 | 3,967 | 928 | 1,641 | 196,223 | 2,000 |
| 2 | 3,966 | 1,069 | 2,145 | 246,003 | 2,000 |
| Total | 11,900 | 3,072 | 5,798 | 667,877 | 6,000 |

Every frozen census minimum passed. Anchors need at least one released P and
one released U partner. The 8,828 excluded endpoints have no C3 released
positive; this is not evidence that they lack interactions. No positive-bearing
anchor was excluded for lacking a U partner. Panels contain 223–362 candidates,
depending on anchor/fold. Coverage is 25.8% of public endpoints, not the whole
proteome.

Fold 0 is concentrated: one leakage component contains 36.09% of its eligible
anchors. Effective component counts based on anchor shares are 7.63, 242.31,
and 111.48 across folds. The frozen split was not changed in response. The
feasibility report includes assumption-based power sensitivity, not a claim
that thousands of pairs are independent experiments.

## Primary and endpoint-balanced results

Primary metric: equal-anchor mean of design-weighted released-positive-versus-U
concordance. Larger is better; 0.5 is the tie/chance reference. Original rational
U weights are retained. It is not biological accuracy or calibrated probability.

| Scorer | Within-anchor concordance | Observed-pairing preference in swap panel |
|---|---:|---:|
| Pair-dependent affine head | **0.663612** | **0.727833** |
| Endpoint-only linear | 0.584203 | 0.500000 |
| Endpoint-only nonlinear, prespecified primary comparator | 0.557894 | 0.500000 |
| Length-ratio control | 0.542660 | 0.537500 |
| 3-mer cosine control | 0.547136 | 0.631000 |
| Raw pooled-embedding cosine | 0.550293 | 0.618833 |

The primary paired gain over the nonlinear endpoint comparator is **0.105718**,
with a conditional 95% component-multiplier interval of **[0.093729, 0.139639]**.
All 2,000 primary replicates are valid. The interval for the pair head itself
is [0.652630, 0.695833].

The additive linear control actually generalizes better than the larger unary
network. We do not present the nonlinear comparator as the empirically strongest
null: the pair head also beats the linear control by **0.079409**. That is a
prespecified secondary point comparison; its paired interval was not part of
the frozen primary calculation.

| Fold | Pair head | Linear unary | Nonlinear unary | Pair minus primary comparator |
|---|---:|---:|---:|---:|
| 0 | 0.650518 | 0.572590 | 0.556589 | +0.093928 |
| 1 | 0.693756 | 0.605428 | 0.584280 | +0.109476 |
| 2 | 0.650612 | 0.577457 | 0.536300 | +0.114312 |

Seed-wise primary gains are +0.107183, +0.104567 and +0.113132. Within fixed
partner-propensity bins, the gain is +0.128169, with all 3,072 anchors retaining
at least one comparable positive. This sensitivity is a different estimand,
not a replacement for the primary one.

For P edges (A,B), (C,D), the swap contrast is
`s(A,B) + s(C,D) - s(A,D) - s(C,B)`.
All four proteins are identical on both sides, so any additive unary score
cancels. Both crossed edges must already be released U rows. Selection and
reuse caps were frozen without inspecting scores. The swap statistic gives
half credit for numerical ties; 0.5 for the unary models is algebraic
cancellation, not an estimated biological performance.

The pair model favors the observed pairing in 72.78% of the selected,
tie-adjusted quartet comparisons; the conditional interval is
**[68.12%, 78.39%]**. It beats the 3-mer control by 9.68 percentage points
(paired interval [3.35, 15.21]) and the length control by 19.03 points
([12.13, 25.02]). Quartets are uniformly weighted in the selected panel;
parent pair inclusion weights do not provide their joint sampling probability.

The previous corrected 0.784 development concordance is a different pooled
metric on different data and training exposure. It must not be directly
compared with this 0.664 equal-anchor internal result as a performance change.

## Frozen decision

All eight checks pass: useful primary margin, positive paired lower bound,
positive gains in every fold and seed, gains over all frozen controls, positive
propensity-stratified sensitivity, swap lower bound above 0.5, and swap gains
over the length and 3-mer controls.

Disposition: `useful_internal_partner_specific_signal_not_external_confirmation`.

The defensible scientific wording is **internal pair-dependent partner-ranking
signal beyond the tested endpoint-only and simple similarity controls**.
The result does not resurrect the old gating/complexity claim.

## Verification and operational record

- 357 unit tests pass, including 28 new tests for this diagnostic.
- Preparation verified 11,900 raw vector hashes and all 2,016,799 public pair
  joins; C3 evaluation covers 673,675 pair rows and 15 score columns.
- The separate NumPy/SciPy reference validator passed all 14 checks. It checked
  all 7,616,000 used embedding values, all 2,016,799 input pair joins, all
  6,063,075 learned scores, every anchor/quartet point, and direct P-by-U
  recomputation of 16 complete primary bootstrap replicates. All 2,000 draws
  and primary paired interval arithmetic were reproduced. Maximum FP64
  reference-forward difference was 0.00000603702, below the frozen 0.0001
  tolerance. This is same-author numerical validation, not external review
  or replication.
- A post-readout supporting arithmetic audit passed. It independently
  recomputed all 2,000 quartet replicates for six scorers, all propensity bins
  and matched-anchor metrics, panel recalls, reported supporting intervals,
  checkpoint freeze identities, fitting row counts and 45 matched training
  order groups. This additional validator was written after the readout; it
  adds no new estimands or decision rules and does not modify frozen evidence.
- The complete unit suite also passed after execution: 357/357.
- The first preparation attempt failed closed because the loader expected
  shorthand P/U instead of the existing `released_positive`/`unlabeled` schema
  values. This was corrected before any census result or model fit. The
  original preregistration was preserved; the restart is recorded in
  `PREPARATION_RESUME.json`. No design change or outcome-driven retry occurred.
- The initial whole-suite invocation in the model-only image could not collect
  tests requiring DuckDB/OpenPyXL. The accepted data-test image ran all 357
  tests successfully. The failed collection log is retained as `unit_tests.xml`;
  the passing pre-execution evidence is `unit_tests_data_runtime.xml`.
- All public parent inputs and frozen execution hashes are rechecked at every
  phase. No development rows, protected candidates/truth, or keys were accessed.

## Limits and recommended next decision

This result answers a narrower question than physical interaction specificity.
The public package omits source memberships and assay opportunity/batch data.
The controls do not exhaust interolog transfer, richer homology effects,
co-complex membership, or pair-dependent assay ascertainment. U remains
unlabeled. Sampled-panel Recall@10/100 is reported only as panel recovery, not
full-universe recall or biological precision.

The intervals use paired component multipliers, conditional on trained heads,
fixed folds and released panels. They do not capture refitting uncertainty or
between-source sampling; component concentration particularly matters in fold
0. The seeds and folds are robustness views, not independent new datasets.

**Next priority: validate the signal, rather than expand the architecture.**
A separately scoped source/assay-aware challenge with stronger interolog or
homology controls, followed by an independently assembled or prospectively
measured evaluation, would test the remaining explanations. Freeze that design
before accessing new outcomes. This work does not authorize opening the current
protected test, external data acquisition, or another architecture sweep.

## Artifacts and navigation

- Protocol: `docs/protocols/WITHIN_ANCHOR_PARTNER_SPECIFICITY_v1.md`.
- Executable config: `configs/within_anchor_partner_specificity_v1.yaml`.
- Entry point: `scripts/model/run_within_anchor_partner_specificity_v1.py`.
- Public aggregate evidence: `artifacts/results/within_anchor_partner_specificity_v1/`.
- Numerical/test evidence: `artifacts/validation/within_anchor_partner_specificity_v1/`.
- Local arrays/checkpoints: `artifacts/runs/within_anchor_partner_specificity_v1/`
  (ignored by Git, consistent with the existing artifact policy).
- Current status: `governance/PROJECT_STATUS_v46.md`; gate ledger:
  `governance/gates/gate_status_v46.yaml`.
- Closure registry: `artifacts/results/within_anchor_partner_specificity_v1/ARTIFACT_REGISTRY.json`.
- Execution-freeze SHA-256:
  `6f43af31884dd263adf3d2f9cf4c4dd23031f852592b2f786cd9f2c8f67607e0`.
- Readout SHA-256:
  `f6e0c83cdee51dab99a1c7abe5b9c59deaa0970b30455f5b5e64200f3eefea7e`.

Graphify led to the existing public-training split, model features, and PU
evaluation machinery. Its final required AST-only update produced 3,544 nodes,
8,445 edges and 276 communities without LLM/API use. It warned that 112 sources
produced no AST nodes; this update does not semantically index the new reports
or result JSON. Existing graph/cache changes were preserved. The protocol,
frozen manifests and verified readout are authoritative, not inferred graph
relationships.
