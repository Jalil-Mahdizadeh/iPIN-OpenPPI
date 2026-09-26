---
title: "Supplementary Information: iPIN-OpenPPI"
bibliography: references.bib
link-citations: true
lang: en-GB
---

# Supplementary Methods

## S1. Evidence interpretation and benchmark population

The primary endpoint is recovery of released-positive reference-sequence pairs from eligible unlabeled pairs. Positive evidence came from the frozen HI-II-14/HuRI release, while endpoint sequence mapping used UniProt 2026_02. This distinction between evidence date and sequence-reference version matters: the task is not a temporal prediction challenge. Canonical sequence projection does not establish an assay-specific result for every isoform or construct sharing a gene identifier. The eligible universe comprises distinct sequence endpoints, not an assertion that every possible pair was experimentally attempted.

The negative-evidence review preserved manual experimental observations separately from structure-derived noncontacts. Its bounded conditional subset contained 1,163 unique reference-sequence pairs from 315 publications, but did not establish a shared sampling population, complete construct/evaluability information or an identifiable biological class prior. These observations were not used as training negatives. This is a limitation of their suitability for the present estimand, rather than a claim that experimentally reported noninteractions are uninformative [@Negatome2014]. Similarly, a selected validation-panel non-detection can support an assay-conditional statement without becoming a universal nonbinding label. No external direct-binary panel was qualified and scored as independent confirmation in this study.

All detailed evidence records projecting to the same unordered sequence pair were grouped before role assignment. The positive ledger contained 58,049 pairs; 5,387 were quarantined because they were outside the permitted training/evaluation roles. The primary training and evaluation counts are in Table 1. Source membership was not additive because some pairs appeared in both sources. The actual retained training positives comprised 1,970 HI-II-14-only, 13,547 HuRI-only and 1,282 shared pairs.

## S2. Operational sequence disjointness

The sequence graph was a union of accepted full-length and local-domain similarity edges at the selected identity threshold. Components were connected components of this graph: transitivity can group sequences that do not directly align to every other member. At 30% identity, the allocation placed each whole component in one partition. The candidate search included evidence-opportunity and source-balance constraints before any model fitting; it was not chosen using model scores. Of 4,096 deterministic candidates, 2,653 met the frozen criteria, and the selected allocation had the exact 70%/15%/15% endpoint counts.

The criteria included at least 500 positive opportunities and 50 participating components in each C1/C2/C3 opportunity pool, plus source and degree-balance constraints. The lexicographic ordering considered endpoint balance, minimum normalized evidence retention, development/test opportunity balance, source composition, degree mass and hub placement, followed by deterministic ties. The public configuration provides the exact thresholds and salts. These constraints support feasibility, but their use of aggregate positive evidence should be distinguished from a completely label-blind partition.

A subsequent public-training-only MMseqs2 search identified additional cross-fold alignments. In particular, 344 links crossed folds at at least 30% identity under the original local span/coverage thresholds. This finding limits the scientific interpretation of the initial heuristic graph. It does not authorize an unseen-family claim for C3. The later purge is a separate internal sensitivity, not a replacement primary split.


**Supplementary Table S1 | Endpoint and component partitions**

| Partition | Endpoints | Components | Singletons | Largest component |
| --- | --- | --- | --- | --- |
| Train | 11,900 | 5,427 | 3,992 | 1,624 |
| Development | 2,550 | 1,071 | 796 | 643 |
| Test | 2,550 | 1,284 | 931 | 111 |




## S3. Sampling, evidence visibility and source-specific cells

Unlabeled sampling was performed without full pair-universe materialization. Cell-specific, salted SHA-256 ordering selected the smallest hashes within each stratum. Allocation used fixed caps and deterministic proportional allocation across nonempty degree strata, with exact rational inclusion probabilities. C1 used 36 strata, C2 eight, and C3 one. The fitting graph alone defined training degrees. Positive rows were never admitted to U in their governing cell.

Independent cell sampling did not impose U-pair exclusivity across cells. The 20,000,000 sampled cell rows across training and primary/source-specific evaluation represented 15,536,850 distinct pair identifiers. This reuse is permitted by the design; it should not be interpreted as independent repeated observations. In particular, training and C1 evaluation can reuse unlabeled pairs because both draw from the same exposed-endpoint universe. The primary C3 endpoint boundary prevents direct training-pair reuse for that regime. Intervals quantify component dependence within the evaluated cells, not between-cell independence.

Source-exclusive evaluation cells retained target-source-exclusive positives and the cell-specific U set. They are secondary recovery diagnostics. The learned original and optimized protected scorers remained their union-trained frozen ensembles; these cells did not perform new source-purged training. They must be distinguished from the separate internal source-restricted refits in Fig. 5. In the latter, fitting positives carried the visible source, shared evidence remained visible, and target-only public positives outside the evaluation fold were restored to U with weight one. This restoration avoids using target evidence merely to remove difficult U pairs, but does not make the upstream union-based sampling design independent of the source union.

## S4. Head families and bounded optimization

The final heads use Eq. (3) in the main text. The affine head has one coefficient per pair feature and one bias. The MLP head is LayerNorm → linear hidden layer → GELU → dropout → scalar. The residual head sums this branch and an affine branch. The low-rank bilinear candidate adds

$$
\frac{1}{\sqrt r}\boldsymbol\alpha^\top\left[(\mathbf P\mathbf z_A)\odot(\mathbf P\mathbf z_B)\right]
$$

(S1)

to the affine score, where $\mathbf P\in\mathbb R^{r\times d}$ and $\boldsymbol\alpha\in\mathbb R^r$ are learned without projection/output biases in this branch. All families are symmetric in the endpoints. The recipe grid, per-member parameter counts and all evaluated checkpoints are supplied in Supplementary Table S3 and its CSV.

Both encoders were frozen. The 24 initial recipes received three complete epochs using seed 20260803. Promotion ranked development C3 concordance, then smaller head size and recipe identifier. Four recipes were refit from initialization using the three fixed seeds for eight epochs. Ensemble candidates were defined at epochs four and eight; selection ranked ensemble concordance, then parameter count, earlier epoch and recipe identifier. The experiment comprised 24 initial fits and 12 promoted fits, with 168 total training epochs across fits. Epoch-four selection does not mean that the eight-epoch learning-rate schedule was shortened to four epochs: the checkpoint was taken from the prescribed eight-epoch schedule.

AdamW used $(\beta_1,\beta_2)=(0.9,0.999)$ and $\epsilon=10^{-8}$, with global gradient-norm clipping at 1. Warm-up occupied approximately 5% of steps, followed by cosine decay to 10% of the initial learning rate. The initial affine schedule used 123 warm-up steps in 2,445 steps. Nonlinear optimization changed batch size, weight decay and learning rate as well as architecture. Consequently, the final difference is between specified training recipes, not an isolated causal effect of the nonlinear branch.

The development comparison’s original requirements included a positive ensemble gain and paired lower bound, positive matched gains in every seed, and a candidate seed range no greater than 0.02. The last two requirements were not met. A fixed-ensemble follow-up criterion was specified after development inspection and before the follow-up test. The original requirements were not retrospectively represented as passed. The test reuse limits inference about the optimization procedure even though the follow-up scorer was fixed before its own evaluation.

## S5. Within-anchor estimand and endpoint-balanced alternatives

Internal folds contained 3,967, 3,967 and 3,966 public-partition endpoints. Only pairs with both endpoints outside a fold were used to fit its models; only pairs wholly inside that fold were evaluated. Fitting normalization used all permitted fitting endpoints. The three diagnostic seeds were 20260911, 20260912 and 20260913, distinct from the final ensemble seeds. Each diagnostic model used five complete passes and its final checkpoint, with no fold-specific architecture search.

For eligible anchor $a$, let $P_a$ and $U_a$ denote the released positive and sampled unlabeled partners available in the panel. The anchor-level statistic and equal-anchor average were

$$
\widehat C_a=
\frac{\sum_{b\in P_a}\sum_{c\in U_a}w_{ac}\,
\psi\!\left[s(a,b)-s(a,c)\right]}
{|P_a|\sum_{c\in U_a}w_{ac}},
\qquad
\widehat C_{\mathrm{anchor}}=
\frac{1}{|\mathcal A|}\sum_{a\in\mathcal A}\widehat C_a,
$$

(S2)

where $\mathcal A$ includes anchors with at least one P and one U partner. An unordered pair may contribute to queries at both endpoints, which is intentional. Pooling across folds retained equal anchor weight rather than equal fold weight. For propensity matching, quintile boundaries were estimated from the nonlinear unary scorer on fitting endpoints only. Comparisons were restricted to P/U partners in the same bin and averaged over supported positives and then anchors. This changes the conditional comparison; it is not a calibrated adjustment for all biological interaction propensity.

Quartets considered both alternative matchings of two positive edges with four distinct endpoints. Both cross edges had to occur in the released U panel. Deterministic hash selection retained at most 2,000 quartets per fold, with at most ten uses per positive edge and 50 uses per endpoint. The selected-quartet mean is not a Horvitz–Thompson population quartet estimate. For an additive scorer $s(A,B)=g(A)+g(B)$, Eq. (8) cancels algebraically. The nonlinear unary control therefore also ties in the swap test, despite having a flexible protein-level function.

Reported anchor counts exceed the number of effective independent groups. In fold 0, 1,075 eligible anchors occupied 598 components, but the largest component contained 36.1% of anchors. Its concentration-based effective component count was only 7.63, computed as $(\sum_c a_c)^2/\sum_c a_c^2$, where $a_c$ is the number of eligible anchors in component $c$. This is a descriptive measure of concentration, not the sample size of an independent binomial experiment. The component bootstrap and the limited external scope remain essential to interpretation.

## S6. Homology transfer, purging and source support

The sensitive search used exact postfilters on alignment counts. Identity $I_{uv}$ was the number of identical aligned residues divided by alignment columns, including gaps. With aligned spans $s_u,s_v$, and sequence lengths $L_u,L_v$, accepted alignments had identity at least 20%, E-value at most $10^{-3}$ and both spans at least 40 residues. The two alignment kernels were

$$
K_{\mathrm{local}}(u,v)=I_{uv}\min\!\left(1,\frac{\min(s_u,s_v)}{80}\right),
\qquad
K_{\mathrm{coverage}}(u,v)=I_{uv}\sqrt{\frac{s_u}{L_u}\frac{s_v}{L_v}}.
$$

(S3)

Nonqualifying alignments contributed zero. The kernels entered the exhaustive fitting-edge transfer score in Eq. (7), alongside 3-mer and raw pooled-embedding similarities. No top-neighbor shortlist replaced the full fitting edge set. The alignment controls’ near-chance performance cannot rule out more informative profile, domain, structural or network-transfer approaches.

The purge retained the same held-out P/U evaluation panels and removed whole fitting components linked to held-out endpoints by accepted alignments with spans at least 80 residues and coverage at least 20% on each endpoint. Normalization and fits were recomputed after removal. Fitting endpoint counts fell from 7,933/7,933/7,934 to 5,270/4,619/4,601 across folds, leaving 3,595/3,090/2,905 fitting-positive pairs. No matched random-removal experiment was performed. The inference is robustness to this removal rule, not a causal estimate of homology dependence.

Source restriction and homology purging were separate arms. Source-specific swaps were filtered from the original selected quartet panel without replacement sampling. The HuRI-to-HI-II-14 direction retained 29, 17 and 20 quartets per fold, below the minimum of 30 in each fold, and two bootstrap draws had zero effective quartet mass. Its interval used 1,998 finite draws. This result cannot meet the planned support criterion and remains inconclusive irrespective of its positive point estimate. Supplementary Table S4 retains the fitting and evaluation counts for all internal arms.

## S7. Resampling and sensitivity interpretation

For primary concordance, the same component counts reweighted both models in every paired comparison. A within-component pair received one component count, avoiding squaring a single biological group’s multiplicity. A between-component pair received the product of its two component counts. The procedure is a component-based, two-endpoint resampling adaptation; the general crossed-data bootstrap literature motivates dependence-aware resampling, but does not by itself establish exact coverage for this biological design [@Owen2007].

Internal anchor analyses used independent Poisson(1) multipliers for components. Within an anchor query, a partner received its component multiplier unless it belonged to the anchor’s component, in which case its within-query multiplier was one. The P/U ratio was recomputed, and the resulting anchor statistic received the anchor-component multiplier in the macro average. Queries with zero effective comparison mass were omitted within that draw. For quartets, each unique component among the four endpoints contributed its multiplier once. All reported intervals are conditional on the fitted scores and selected panel. They omit uncertainty from choosing a split, retraining, selecting a recipe and drawing independent experimental programmes.

The initial partner study and the later homology/source study used different fixed Poisson draws. The union point estimates are identical where they reuse scores, but their marginal intervals need not be. Fig. 5a uses the original partner study for the pair-head and nonlinear-unary intervals; its linear-unary interval comes from the union arm of the later challenge. Fig. 5b,c use the later challenge consistently. The displayed paired differences always use the common draws of their stated study, never subtraction of marginal confidence limits.

For the development component analysis, removal applied to both P and U and reused the original development component draws. Removing the largest component was specified before the initial diagnostic; the third-component, combined-removal and between-component analyses were data-informed follow-ups. The component decomposition holds the full U reference fixed and partitions P into disjoint groups $G$:

$$
\widehat C-\tfrac12
=\sum_G\frac{|P_G|}{|P|}\left(\widehat C_{G,\mathrm{full}\ U}-\tfrac12\right).
$$

(S4)

Consequently, a group’s percentage contribution to excess concordance is its summand divided by the total excess. The 94.0% and 70.1% values in Fig. 4 do not represent fractions of the development-to-test decrease. Contributions of overlapping component-touching groups cannot be summed. The two displayed decompositions each use their own disjoint positive partition.

Ten unordered endpoint-length bins used fixed boundaries at 200, 500 and 1,000 residues. Comparing P/U pairs within bins retained all development positives and gave concordances 0.677 for 3-mer, 0.665 for interolog and 0.779 for affine iPIN. This conditional statistic provides a sensitivity to coarse length differences, not exact length adjustment. The control decreases also occurred within HuRI-exclusive C3: 3-mer changed from 0.653 to 0.471, and interolog from 0.628 to 0.473. Source labels therefore do not hold component or pair composition constant. Neither check supplies a complete test-side causal explanation.

# Supplementary Tables


**Supplementary Table S2 | C3 performance and available marginal 95% intervals**

| Model/control | Development C3 | Protected C3 |
| --- | --- | --- |
| iPIN affine | 0.784 [0.743, 0.853] | 0.789 [0.708, 0.846] |
| iPIN optimized | 0.799 [not reported] | 0.808 [0.740, 0.852] |
| Degree sum | 0.500 [0.500, 0.500] | 0.500 [0.500, 0.500] |
| Preferential attachment | 0.500 [0.500, 0.500] | 0.500 [0.500, 0.500] |
| Common neighbors | 0.500 [0.500, 0.500] | 0.500 [0.500, 0.500] |
| Component degree mass | 0.500 [0.500, 0.500] | 0.500 [0.500, 0.500] |
| Length ratio | 0.661 [0.567, 0.742] | 0.549 [0.484, 0.607] |
| Length sum | 0.520 [0.418, 0.578] | 0.327 [0.250, 0.449] |
| 3-mer cosine | 0.645 [0.498, 0.726] | 0.494 [0.414, 0.566] |
| 3-mer interolog | 0.636 [0.526, 0.755] | 0.484 [0.426, 0.575] |
| ESM cosine | Not reported | 0.494 [0.431, 0.603] |
| Composition cosine | Not reported | 0.414 [0.347, 0.529] |
| Hash sentinel | 0.494 [0.473, 0.522] | 0.491 [0.472, 0.510] |

The CSV additionally includes C1/C2 and source-specific results with sample counts and exact provenance. Optimized test values are from the disclosed follow-up. Missing intervals/estimates are not imputed. The paired optimized-minus-affine interval, rather than overlap of marginal intervals, determines the incremental conclusion.



**Supplementary Table S3 | Complete bounded search**

| Encoder / recipe | Head parameters | Screen, epoch 3 | Ensemble, epoch 4 | Ensemble, epoch 8 |
| --- | --- | --- | --- | --- |
| 150m / linear_slow | 1,922 | 0.7814 | — | — |
| 150m / linear_base_lr | 1,922 | 0.7902 | 0.7860 | 0.7841 |
| 150m / linear_fast | 1,922 | 0.7769 | — | — |
| 150m / linear_regularized | 1,922 | 0.7776 | — | — |
| 150m / mlp_small | 126,915 | 0.7897 | — | — |
| 150m / mlp_wide | 496,131 | 0.8021 | 0.7994 | 0.7912 |
| 150m / mlp_fast | 249,987 | 0.7527 | — | — |
| 150m / residual_small | 128,837 | 0.7761 | — | — |
| 150m / residual_wide | 498,053 | 0.8052 | 0.7994 | 0.7938 |
| 150m / residual_fast | 251,909 | 0.7397 | — | — |
| 150m / bilinear_small | 22,434 | 0.7845 | — | — |
| 150m / bilinear_wide | 83,970 | 0.7534 | — | — |
| 650m / linear_slow | 3,842 | 0.7787 | — | — |
| 650m / linear_base_lr | 3,842 | 0.7827 | — | — |
| 650m / linear_fast | 3,842 | 0.7791 | — | — |
| 650m / linear_regularized | 3,842 | 0.7792 | — | — |
| 650m / mlp_small | 253,635 | 0.7913 | 0.7944 | 0.7875 |
| 650m / mlp_wide | 991,491 | 0.7792 | — | — |
| 650m / mlp_fast | 499,587 | 0.7347 | — | — |
| 650m / residual_small | 257,477 | 0.7639 | — | — |
| 650m / residual_wide | 995,333 | 0.7810 | — | — |
| 650m / residual_fast | 503,429 | 0.7538 | — | — |
| 650m / bilinear_small | 44,834 | 0.7617 | — | — |
| 650m / bilinear_wide | 167,810 | 0.7430 | — | — |

Screen scores use one seed; promoted ensemble scores use three. Dashes indicate recipes not promoted. The CSV retains every individual-seed evaluation, exact hyperparameters and checkpoint identifiers. These development-selected comparisons are not protected head-to-head tests.



**Supplementary Table S4 | Internal challenge support**

| Arm | Fold | Fit endpoints | Fit P | Evaluation P | Anchors | Quartets |
| --- | --- | --- | --- | --- | --- | --- |
| Union | 0 | 7,933 | 7,367 | 2,012 | 1,075 | 2,000 |
| Union | 1 | 7,933 | 8,123 | 1,641 | 928 | 2,000 |
| Union | 2 | 7,934 | 7,107 | 2,145 | 1,069 | 2,000 |
| Homology purge | 0 | 5,270 | 3,595 | 2,012 | 1,075 | 2,000 |
| Homology purge | 1 | 4,619 | 3,090 | 1,641 | 928 | 2,000 |
| Homology purge | 2 | 4,601 | 2,905 | 2,145 | 1,069 | 2,000 |
| HI-II-14 → HuRI | 0 | 7,933 | 1,312 | 1,561 | 934 | 1,191 |
| HI-II-14 → HuRI | 1 | 7,933 | 1,716 | 1,385 | 817 | 1,398 |
| HI-II-14 → HuRI | 2 | 7,934 | 1,353 | 1,723 | 906 | 1,287 |
| HuRI → HI-II-14 | 0 | 7,933 | 6,601 | 275 | 273 | 29 |
| HuRI → HI-II-14 | 1 | 7,933 | 7,082 | 145 | 173 | 17 |
| HuRI → HI-II-14 | 2 | 7,934 | 6,281 | 243 | 270 | 20 |

The CSV also reports fitting/evaluation U counts, participating components, removed endpoints and target-only positives restored to fitting U. Folds and seeds are robustness views of the same public training evidence.


# Supplementary Figure

![Supplementary Figure S1. Paired original protected-test comparisons against every fixed control.](figure-s1.png)

Each point is affine iPIN concordance minus control concordance on the same evaluation cell. Whiskers are paired 95% component-bootstrap intervals from 2,000 common resampling draws; the dashed line denotes zero difference. C1, C2 and C3 retain their gold, purple and teal encoding. All eleven C3 lower bounds are positive. The degree-sum C2 interval crosses zero, and the C1 preferential-attachment difference is negative. Counts are 3,187, 13,446 and 2,379 P pairs for C1, C2 and C3, each compared with 1,000,000 sampled U pairs. Source data: `figure-s1.csv`.

# Supplementary References

Citations use the shared `references.bib`; all cited works also appear in the main manuscript bibliography.
