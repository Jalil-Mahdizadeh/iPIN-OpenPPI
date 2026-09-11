# External BioPlex challenge: concise findings

2026-09-11 · DEC-0048 · Executed and numerically verified.

## Bottom line

**The ranking signal transfers, but the learned head's added value does not
clear the external challenge.** Simple sequence similarities match or exceed
its anchor-ranking point estimates. This is not evidence that the entire
research project is a dead end; it is evidence against claiming a generally
better predictor from the present head. No architecture sweep is justified.

## Locked test and results

Before downloading interaction rows, locked the 18 existing homology-purged
checkpoints, protocol and eight comparators. No refitting, tuning, new embeddings,
development evaluation or protected-package/key access. Tested the published
BioPlex AP-MS releases separately in 293T and HCT116, preserving bait/prey
direction. AP-MS measures co-association, including indirect complex membership,
not necessarily direct binding. [Huttlin et al., 2021](https://doi.org/10.1016/j.cell.2021.04.011).

Both endpoints are held out from the corresponding fit and normalization;
zero detected qualifying homology links remain to fitting endpoints. Targets
exclude every previously released public positive. Existing U is restricted
to published baits/observed preys and excludes current-cell detections in either
orientation. Missing pairs remain **unlabeled**, not biological negatives.

Metric: equal-bait, design-weighted P-versus-U concordance.

| Cell | Baits | Pair head | Direct 3-mer | Pooled cosine | Pair minus best baseline, paired 95% interval |
|---|---:|---:|---:|---:|---|
| 293T | 1,196 | 0.617146 | 0.641533 | 0.614187 | −0.024387 [−0.049219, +0.003584] |
| HCT116 | 694 | 0.609358 | 0.613400 | 0.620852 | −0.011494 [−0.040744, +0.021782] |

The pair head beats unary (0.449422 / 0.446946) and all four interaction-transfer
controls with positive paired lower bounds in both cells. Nevertheless, neither
cell passes the frozen ≥0.02 advantage over **every** comparator. The intervals
do not establish statistical inferiority or equivalence to direct similarities;
they establish no demonstrated incremental advantage here.

Balanced swaps also retain signal: **72.76%** on 3,832 quartets in 293T
(95% interval 64.81–78.58%) and **72.34%** on 2,231 in HCT116
(63.25–80.58%). Unary cancels to 50%. Both cells meet support floors, but paired
intervals against direct 3-mer and pooled cosine cross zero. Thus both swap
superiority gates fail too—not because their panels lack the prespecified size.

## Scope and confidence

Strict public-endpoint/accession projection retained 27,059 of 129,687 directed
293T edges and 18,473 of 77,184 HCT116 edges before C3/novelty filtering. Final
panels contain 9,599 / 6,477 positive directed edges. This substantial attrition
limits generalization. We reuse explored endpoints and source-union-curated U;
the two cell lines share a programme, and complete attempted/evaluable pair
logs are absent. Reference accessions do not certify construct identity.
These are newly used external experimental labels, not an independently built
proteome-wide benchmark, a wet-lab prospective study, or an unseen-family test.

All intervals use the frozen 2,000 conditional component-multiplier draws;
all have 2,000 valid replicates. They omit refitting and assay/source uncertainty.
The study cannot distinguish shared composition, localization, complex membership
or direct compatibility as the explanation for its residual ranking signal.

Verification passed: **416 distinct tests**, all **2,048,214 learned values**
(maximum reference error 1.72e−6, tolerance 1e−4), all 341,369 directed panel rows
and quartet selections, all point estimates, 24,576 sampled exhaustive-transfer
values, 16 complete anchor-bootstrap draws per cell and all 2,000 swap draws.
Checks are same-author numerical auditing, not external peer review. Scoring
produced 5,120,535 values in 8.53 seconds; zero new fits. Prior two study closures
remain unchanged. Unpublished releases and raw redistribution were excluded.

## Next decision

Treat BioPlex as spent diagnostic evidence from now on. Prioritize explaining
what the direct similarities capture with composition-/localization-/complex-
matched controls; freeze any new rules before a **fresh direct-binary source**
challenge with auditable opportunities. Do not tune to recover these BioPlex
gates, open protected evaluation, or revive the gated-architecture claim.

[Protocol](../../protocols/EXTERNAL_BIOPLEX_CHALLENGE_v1.md) ·
[Full readout](../../../artifacts/results/external_bioplex_challenge_v1/RESULTS.json) ·
[Numerical audit](../../../artifacts/validation/external_bioplex_challenge_v1/REFERENCE_VALIDATION.json) ·
[Status v48](../../../governance/PROJECT_STATUS_v48.md).

Graphify traced the prior source-opportunity audit and checkpoint machinery;
the AST-only refresh produced 3,751 nodes and 9,027 edges. It warned that 134
sources produced no AST nodes and some community labels are hub-derived;
no semantic/LLM indexing was run. Frozen manifests and numerical evidence,
not graph relationships, are authoritative.
