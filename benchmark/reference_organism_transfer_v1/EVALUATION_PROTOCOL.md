# Frozen-model evaluation of published human–yeast assay confirmation

Defined on 2026-09-21 before viewing model scores. This evaluation follows the
accepted reference-organism scope and the completed source preparation.

## Primary question and data

Do the three frozen human PPI ensembles rank published human–S288C pairs that
were confirmed by an orthogonal assay above pairs that were not confirmed?
Use the authors' `Call` field and `Final score` from Table EV7 of Zhong et al.
(2016), [PMID 27107014](https://pubmed.ncbi.nlm.nih.gov/27107014/).
The outcome concerns this published LUMIER assay. A `no` call does not establish
a biological noninteraction: these pairs were selected from the Y2H-positive
network, and detection depends on assay context. The positive versus random
control task from the earlier broad proposal is not the endpoint here.

Map Table EV7 gene pairs through Table EV2's original IntAct identifiers to the
already verified reference-sequence pairs. Union all matching evidence before
assessing uniqueness. Keep a row only if that mapping resolves to exactly one
published sequence pair and the reported call and score are valid. Apply the
same rule to both outcomes; do not resolve ambiguous isoforms by model score.
Record every excluded row, its call, and the reason. Freeze the result before
inference. Initial metadata inspection found 91 assay rows, with 75 uniquely
mapped rows (36 `yes`, 39 `no`). Recompute these counts in the builder.

Score all 1,555 verified published positive pairs, using only archived human
(9606) and S288C (559292) reference sequences. The primary performance analysis
uses only the retained Table EV7 rows. Remaining scores are descriptive outputs.
Do not generate new candidate pairs or reuse missing pairs as negative labels.

## Models and execution

Use the registered frozen baseline affine iPIN, optimized residual iPIN and
TUnA-retrained ensembles. Keep all three members of each registered ensemble,
normalization, selected epochs, and TUnA GP covariance unchanged. Use fresh
embeddings in the accepted pinned Apptainer images. Reuse the qualified existing
inference implementation with a loader bound to this study's input freeze.
Verify model hashes and pair-order symmetry; retain TUnA's native-path numerical
qualification and checks that parameters and buffers are unchanged.

The input freeze binds source preparation, comparison mapping, evaluation
protocol, scoring and analysis implementations, source/model registries and
exposure results. No training, calibration, parameter selection, or tuning on
the evaluation outcomes is allowed. Scores are ranking values, not binding
probabilities. Registered model identities remain fixed regardless of results.

## Exposure and uncertainty

Audit exact endpoint and pair exposure against actual human TRAIN and
development files only. Do not open protected human test-pair identities or
truth. Run the pinned MMseqs2 comparison to actual TRAIN endpoints, reporting
local similarity and identity with at least 80% coverage of both proteins.
Describe the similarity of yeast and human endpoints separately.

Report the primary full-cohort result and the fixed sensitivity excluding
either exact TRAIN or development endpoint. If a sensitivity has no examples
of either outcome, report that it is not estimable. Protein-language-model
pretraining exposure is outside this supervised PPI exposure audit.

Primary metric: AUROC for the authors' assay-confirmation call, with half credit
for tied scores. Secondary: average precision for that same call and Spearman
correlation with the authors' continuous final assay score. Report class counts
and the prevalence reference for AP. These metrics do not estimate performance
against biological noninteractions or precision in an unselected proteome.

For exploratory uncertainty, use 10,000 paired bootstrap draws with seed
20260921. Construct connected components of the assayed pair graph, linking
observations that share either sequence endpoint. Resample these components,
keeping all records in each component together and using the same draws for all
models. Report percentile 95% intervals for AUROC, AP and paired differences;
report the number of components, largest component and valid draws. Reject draws
missing either outcome. If fewer than two components or inadequate valid draws
prevent an interval, explicitly mark it unavailable. Report Spearman as a
descriptive point estimate. All pairs originate from one publication; these
intervals cannot establish replication across studies or assay platforms.

Independently check metric implementations against library results and explicit
pair comparisons, including ties. Report mapping attrition by assay outcome,
reference-sequence projection, shared endpoints, source concentration and
supervised/pretraining exposure limitations. A successful result supports only
this narrower retrospective assay-confirmation question; a null result should
be reported without changing the cohort or metrics.
