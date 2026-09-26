---
title: "Endpoint exposure separates network shortcuts from sequence-derived interaction ranking in iPIN-OpenPPI"
bibliography: references.bib
link-citations: true
lang: en-GB
---

# Abstract

Protein–protein interaction prediction is often evaluated without distinguishing recognition of familiar proteins from generalization to new endpoints. We developed iPIN-OpenPPI, an evidence-aware positive–unlabeled ranking framework that separates these regimes using sequence-component partitions and C1/C2/C3 evaluation. A frozen ESM-2 encoder and a compact symmetric affine head achieved C3 concordance of 0.784 on development and 0.789 (95% component-bootstrap confidence interval, 0.708–0.846) on the original protected test, where neither endpoint was exposed to interaction-supervised training. The model exceeded all eleven prespecified fixed controls on protected C3, whereas network controls matched or exceeded it when training endpoints remained visible. Development 3-mer and interolog signals were concentrated in particular sequence-component and positive-pair patterns; removing influential components reduced these controls more than the affine model. Internal within-anchor ranking, endpoint-balanced partner swaps, homology purging and source-restricted refits supported pair-dependent signal beyond additive protein propensity, with one source-specific swap comparison remaining underpowered. A bounded search selected a residual head with approximately 0.5 million trainable parameters. Its C3 concordance reached 0.799 on development and 0.808 in a disclosed follow-up on the previously examined test; the incremental test gain remained inconclusive because its paired confidence interval included zero. These results support transferable interaction-associated sequence ranking while distinguishing it from evolutionary novelty, calibrated interaction probability and demonstrated direct-binding specificity.

# Introduction

Maps of protein–protein interactions connect molecular components to cellular organization. Yeast two-hybrid assays established a scalable route to detecting binary interactions, progressing from systematic yeast screens to proteome-scale human maps [@Fields1989; @Ito2001; @Rual2005; @Yu2008]. HI-II-14 and the Human Reference Interactome (HuRI) extended this resource substantially, providing systematic evidence that complements individually studied interactions [@Rolland2014; @Luck2020]. Yet an experimentally released interaction map records successful observations under particular assay and construct conditions. Assay sensitivity, technical evaluability and validation design influence what is observed, so missing edges cannot generally be interpreted as experimentally established noninteractions [@Venkatesan2009; @Braun2009]. This distinction becomes consequential when computational models are trained to recover released interactions from a much larger set of unreported pairs.

Sequence-based interaction prediction has advanced from engineered sequence descriptors to neural pair encoders and structure-aware sequence models [@Shen2007; @Chen2019; @Sledzieski2021]. In parallel, network methods exploit the organization of observed interactions, and hybrid approaches combine sequence and graph information [@Kovacs2019; @Singh2022]. These are different sources of predictive information. A model that ranks pairs involving well-studied or highly connected proteins can perform well without learning which partner is compatible with a particular protein. More fundamentally, random pair withholding can leave both proteins represented in the training graph. Park and Marcotte showed why pair-input evaluation must distinguish cases with two, one or no previously observed endpoints [@Park2012]. Subsequent analyses have demonstrated how degree information, sequence similarity and data leakage can dominate apparent performance in deep PPI prediction [@Bernett2024]. Methods for reducing similarity across partitions likewise emphasize that the split determines which generalization claim is being tested [@Joeres2025].

Protein language models offer a potentially useful sequence-derived signal in the most restrictive endpoint regime. Representations learned without interaction labels encode information relevant to protein structure and function [@Rives2021; @Elnaggar2022; @Lin2023]. However, a useful protein representation does not itself demonstrate pair specificity. Homology-based interaction transfer is already a substantial source of biological information, and evolutionary profiles can improve interaction prediction [@Yu2004; @Hamp2015]. A successful language-model predictor must therefore be examined against both sequence-similarity controls and tests that hold protein propensity approximately or exactly constant. Residue-level interface prediction addresses a related but distinct problem: identifying a binding surface is not equivalent to separating globally sampled observed and unreported pairs [@Fout2017].

The evidence status of the comparison set creates a second challenge. Positive–unlabeled learning distinguishes observed positives from a mixture whose latent class membership is unknown [@Elkan2008; @Kiryo2017]. Recovering biological probabilities requires assumptions about observation and sampling that are not guaranteed by an interaction catalogue. Even curated negative resources preserve heterogeneous experimental or structural evidence rather than a common population-wide assay denominator [@Negatome2014]. Recent experimental assessment of AI-based interactome mapping reinforces the importance of evaluating computational predictions against explicit laboratory evidence [@Lambourne2026].

Here we ask whether a compact scorer built on frozen protein-language-model representations retains interaction-associated ranking signal after both endpoints are withheld from interaction supervision. iPIN-OpenPPI combines reference-sequence evidence reconciliation, component-based partitions, explicit C1/C2/C3 tasks, weighted positive–unlabeled concordance and controls targeted at alternative explanations. We first examine the original affine ensemble and its protected validation, then characterize development cohort structure, internal partner specificity and homology/source robustness. Finally, a bounded comparison of head architectures and encoder sizes tests whether modest nonlinear capacity improves ranking. The contribution is an empirical separation of information regimes and claim levels, rather than a claim that architectural complexity alone establishes a better binding predictor.

# Results

## An evidence-aware benchmark separates endpoint-exposure regimes

We defined eligible human endpoints by mapping HuRI Space III membership to unambiguous frozen reference sequences. The resulting universe contained 17,000 distinct sequence endpoints and 58,049 qualifying released-positive sequence pairs from the HI-II-14/HuRI evidence union. Unreported eligible pairs were retained as unlabeled (U), rather than assigned negative labels. The reference-sequence unit intentionally separates this benchmark from claims about exact experimental constructs or isoforms (Methods).

A frozen sequence-similarity graph grouped the endpoints into 7,782 connected components, allocated as whole units to training, development and test partitions containing 11,900, 2,550 and 2,550 endpoints, respectively (Fig. 1; Supplementary Table S1). C1 evaluates withheld pairs between two endpoints exposed through training-positive edges; C2 evaluates one exposed training endpoint paired with a development or test endpoint; C3 evaluates two endpoints from the corresponding held-out partition. Thus, all three tasks withhold evaluation-positive pairs, but only C3 withholds both endpoints from interaction-supervised training. Component disjointness is defined by the frozen graph, not by an exhaustive guarantee of nonhomology.

The training set contained 16,799 released-positive pairs and 2,000,000 sampled U pairs. Each primary evaluation cell contained a positive census and 1,000,000 sampled U pairs (Table 1). We evaluated the probability that a released-positive pair received a higher score than a design-weighted U pair, with half credit for ties. This concordance measures P-versus-U ranking; neither the large U sample nor a high concordance supplies an estimate of biological precision or interaction prevalence.


**Table 1 | Primary benchmark cells**

| Cell | Positive pairs | U population | Sampled U |
| --- | --- | --- | --- |
| Training | 16,799 | 10,902,230 | 2,000,000 |
| C1 development | 3,259 | 10,902,230 | 1,000,000 |
| C1 test | 3,187 | 10,902,230 | 1,000,000 |
| C2 development | 11,327 | 11,909,923 | 1,000,000 |
| C2 test | 13,446 | 11,907,804 | 1,000,000 |
| C3 development | 2,265 | 3,247,710 | 1,000,000 |
| C3 test | 2,379 | 3,247,596 | 1,000,000 |

P denotes released-positive evidence; U denotes unlabeled pairs. Evaluation-positive pairs are excluded from interaction-supervised training. Counts describe pair rows, not independent biological replicates.


## Endpoint exposure changes which predictors appear strong

The original iPIN model combines frozen ESM-2 150M representations with an affine function of symmetric pair features. It therefore has only 1,922 trainable parameters per head, although its absolute-difference, product and cosine features already permit pair-dependent scoring. Three independently initialized heads contribute equally to the ensemble.

In C1 development, degree sum and preferential attachment achieved concordances of 0.907 and 0.907, respectively, compared with 0.849 for affine iPIN (Fig. 2). In C2 development, degree sum reached 0.839 compared with 0.800 for iPIN. These controls use training-positive topology alone. Their performance demonstrates that interaction recovery can be strongly associated with endpoint exposure and observed network connectivity.

The information available to these controls changes sharply in C3. Both held-out endpoints have zero training-positive degree, and the topology controls give tied scores, with concordance 0.500. Affine iPIN retained development C3 concordance of 0.784 (95% confidence interval (CI), 0.743–0.853). Length ratio, 3-mer cosine and a training-edge 3-mer interolog control also showed positive point estimates, at 0.661, 0.645 and 0.636. However, the 3-mer interval, 0.498–0.726, included chance ranking. The endpoint regimes therefore distinguish strong network recovery on exposed proteins from sequence-derived ranking on held-out proteins; a single pooled evaluation would obscure this distinction.

## The original model transfers to protected C3 while shallow controls weaken

The original protected evaluation fixed the affine ensemble and eleven deterministic controls before scoring and separated prediction generation from access to test truth. On C3, affine iPIN achieved concordance 0.789 (95% CI, 0.708–0.846), close to its development estimate of 0.784 (Fig. 3). All eleven paired model-minus-control intervals excluded zero in the positive direction (Supplementary Fig. S1). Against the strongest control by observed C3 point estimate, length ratio at 0.549, the difference was 0.240 (95% CI, 0.128–0.313).

Several simple controls transferred poorly. The 3-mer cosine estimate changed from 0.645 on development C3 to 0.494 on test C3; the interolog estimate changed from 0.636 to 0.484. Length ratio decreased from 0.661 to 0.549, and length sum changed from 0.520 to 0.327. Protected-test composition cosine and raw pooled-ESM cosine achieved 0.414 and 0.494, respectively. The latter two controls have no corresponding primary development estimates in the final result records and are shown as test-only comparisons. Control directions were fixed; below-chance test results were not reversed after inspection. Development and test involve different endpoint cohorts, so these trajectories are descriptive comparisons, not paired estimates of a development-to-test difference.

The protected C1/C2 findings retained the exposure-dependent pattern. Affine iPIN scored 0.843 on C1, below preferential attachment at 0.913: the paired difference was −0.069 (95% CI, −0.083 to −0.054). On C2, iPIN scored 0.805 versus 0.811 for degree sum; the difference of −0.005 (95% CI, −0.044 to 0.029) did not meet the prespecified 95% criterion for an advantage. This is not evidence of equivalence. The C3 finding is therefore the clearest protected evidence for sequence-derived signal beyond these fixed controls.

## Sequence-component composition explains much of the development control signal

To investigate the controls’ development strength, we examined positive-pair composition and component-removal sensitivities using development C3 only. These post hoc analyses changed the evaluated populations and were not used to replace benchmark scores or select a new model. The optimized ensemble was not evaluated in this investigation.

Within-component pairs accounted for 825 of 2,265 development positives (36.4%), but only 6.61% of weighted U mass. Against the same full U reference, 3-mer concordance was 0.874 for within-component positives and 0.514 for between-component positives. Their weighted contributions imply that within-component positives supplied 94.0% of the overall 3-mer excess above 0.5 (Fig. 4). When both P and U were restricted to between-component pairs, 3-mer concordance was 0.535 (95% CI, 0.467–0.590), whereas affine iPIN retained 0.740 (0.698–0.800).

The interolog control was particularly sensitive to a smaller interaction-rich component. The third-largest development component contained 61 endpoints, but 692 positives touched it. Those positives contributed 70.1% of the interolog excess above chance against the full U reference. Removing pairs touching this component from both P and U reduced interolog concordance from 0.636 to 0.567 (95% CI, 0.502–0.620), while iPIN changed from 0.784 to 0.778 (0.736–0.813). Removing both this component and the largest development component retained only 582 positives: 3-mer and interolog estimates were 0.536 and 0.563, with intervals including 0.5, whereas iPIN retained 0.777 (0.729–0.824).

Component size alone was insufficient to explain the pattern. Removing only the largest, 643-endpoint component increased all four displayed predictors’ point estimates. Coarse length-stratified comparisons also retained the simple-control signal (Supplementary Methods). The evidence instead implicates the distribution of particular positive-pair relationships across sequence components. A component is a connected group under an operational similarity rule, not necessarily one biological family. These decompositions quantify development performance; without protected pair-level composition analysis they do not identify the precise cause, or the fraction explained, of the test-side decreases.

## Internal partner tests support signal beyond additive protein propensity

Global P-versus-U concordance may reward broadly interaction-prone proteins without distinguishing their partners. We therefore refit the affine pair head and matched additive unary controls in three component-held-out folds within the public training partition. Each evaluation query fixed an anchor protein and ranked its released-positive partners against its available sampled U partners. This analysis used separate diagnostic fits, not the final protected-test checkpoints.

Across 3,072 eligible anchors, the pair head achieved equal-anchor concordance 0.664, compared with 0.584 for a linear unary control and 0.558 for a nonlinear unary control (Fig. 5a). The prespecified comparison against the nonlinear unary control gave a difference of 0.106 (95% CI, 0.094–0.140). Its direction was positive in every fold and seed. The advantage also remained positive when P/U partner comparisons were restricted to the same propensity bin. These results argue against a wholly additive endpoint explanation on the evaluated internal panels.

Endpoint-balanced swaps provide a complementary test. For two observed pairs involving four distinct proteins, we compared their summed scores with the summed scores of two alternative pairings already present in U. An additive protein score cancels exactly because both sides contain the same endpoints. The pair head preferred observed pairings in 72.8% of 6,000 selected quartets, compared with 63.1% for direct 3-mer cosine. The paired difference versus 3-mer was 0.097 (95% CI, 0.033–0.152). This supports pair-dependent ranking, but the alternative pairings remain unlabeled, and quartet selection conditions the estimand on available alternatives. No residue-level interface or physical binding specificity follows from this test alone.

## Homology and source challenges retain a bounded pair-dependent advantage

We next challenged the same internal framework with exhaustive interaction-transfer controls, a more sensitive sequence search, homology-purged refits and source-restricted refits. The transfer controls examined every fitting-positive edge in both orientations using 3-mer, pooled-embedding or alignment-based endpoint similarities.

A sensitive public-sequence search identified cross-fold links absent from the frozen component graph, including 344 undirected links at at least 30% identity satisfying the local span/coverage criteria. This establishes an empirical limit on interpreting component disjointness as evolutionary novelty. Removing entire fitting components connected to held-out endpoints by the stricter purge rule reduced the fitting endpoint sets substantially while leaving evaluation panels fixed. Pair-head anchor concordance changed from 0.664 to 0.657, and its advantage over linear unary scoring remained 0.073 (95% CI, 0.064–0.107; Fig. 5b). The purge changes training size and composition simultaneously and is not an isolated estimate of the contribution of homology.

Source-restricted fits retained positive anchor-ranking advantages in both directions. Training on HI-II-14-visible evidence and evaluating HuRI-exclusive positives gave pair-head concordance 0.593 and a difference versus linear unary scoring of 0.048 (95% CI, 0.032–0.089; 2,657 anchors). Training on HuRI-visible evidence and evaluating HI-II-14-exclusive positives gave 0.623 and a difference of 0.040 (0.016–0.087; 716 anchors). Each arm exceeded the four prespecified transfer controls with positive paired lower bounds. These are internal source-exclusive recovery tests: the sources share a broader experimental programme, the upstream benchmark used their union, and both sources informed earlier development choices.

The swap results were less uniform (Fig. 5c). Preference remained 0.725 after homology purging and 0.663 for HI-II-14-to-HuRI transfer. The reverse source direction retained only 66 quartets and yielded 0.561 (95% CI, 0.159–0.952), below the required support floor and inconclusive. Thus, anchor evidence survived every specified challenge, whereas partner-swap evidence did not meet the criterion in one sparse arm. Homology restriction and source restriction were evaluated separately; their joint effect remains unknown.

## A bounded nonlinear search improves the ensemble point estimate

We compared 24 prespecified recipes spanning affine, multilayer-perceptron, residual and low-rank bilinear heads over frozen ESM-2 150M and 650M representations. Each recipe received an initial three-epoch single-seed screen; four recipes were promoted to three-seed eight-epoch fits, with ensemble selection at epochs four or eight (Fig. 6; Supplementary Table S3). This search selected the 150M residual head at epoch four. The head adds a width-256 nonlinear branch to an affine branch, with 498,053 trainable parameters per member (Table 2).

The selected ensemble reached development C3 concordance 0.799419, compared with 0.784142 for the original affine ensemble: a gain of 0.015277 (95% paired CI, 0.002942–0.034460). This is a post-selection development interval, not confirmatory evidence. The nearly tied 150M MLP ensemble reached 0.799379, and the promoted 650M MLP reached 0.794405. The search therefore provides no clear advantage for the larger encoder or a distinctive benefit attributable specifically to the residual connection. Learning rate, regularization and training schedule also differ from the original affine model.

The gain was ensemble-specific: two of three matched individual-seed gains were negative, and the candidate seed range of 0.0212 exceeded the original 0.02 requirement. The fixed ensemble was accepted for a separately specified follow-up after development selection. That follow-up reused the already examined protected test; it is not an independent replication or a previously untouched test of the optimization procedure.

On protected C3, optimized iPIN achieved 0.807948 (95% CI, 0.740480–0.852013), compared with 0.789249 for the original affine ensemble. The paired gain was 0.018699 (−0.001358 to 0.050000), so the primary incremental comparison did not meet the prespecified 95% criterion. Secondary C2 and C1 gains were 0.046002 (0.031561–0.061559) and 0.072544 (0.063093–0.081869), respectively. These secondary results do not establish primary C3 superiority. Although optimized C1/C2 point estimates exceeded the highlighted network controls, the follow-up did not perform paired comparisons against those controls. We retain both models: the affine ensemble as the original confirmatory reference and the optimized ensemble as the highest observed scoring model among the two evaluated ensembles.


**Table 2 | Final model specifications**

| Property | Original affine | Optimized residual |
| --- | --- | --- |
| Frozen encoder | ESM-2 150M | ESM-2 150M |
| Head parameters per member | 1,922 | 498,053 |
| Ensemble members | 3 | 3 |
| Hidden width | — | 256 |
| Training dropout | 0.0 | 0.3 |
| Initial learning rate | 3e-04 | 1e-04 |
| Weight decay | 0.0001 | 0.01 |
| Comparisons per batch | 4,096 | 8,192 |
| Selected pass / epoch | 5 | 4 |
| Scheduled passes / epochs | 5 | 8 |

Both models use the same 640-dimensional standardized embeddings and 1,921-dimensional symmetric pair features. Optimization changes the training recipe as well as the head. The optimized epoch-four checkpoint comes from an eight-epoch schedule.


# Discussion

iPIN-OpenPPI identifies a useful sequence-derived ranking signal while making its evidential limits explicit. The strongest result is the original affine ensemble’s protected C3 performance: two interaction-training-naïve endpoints can be ranked using frozen language-model representations substantially better than the prespecified fixed controls. This finding concerns interaction-associated sequence information under the constructed P/U benchmark. It does not establish that a high-scoring pair binds directly, that the score is calibrated, or that the endpoints are evolutionarily novel.

Endpoint exposure materially changes the comparison. Network topology is biologically informative, and successful network predictors need not be dismissed as artefacts [@Kovacs2019; @Singh2022]. The problem arises when recovery of links between already exposed proteins is interpreted as generalization to unfamiliar endpoints. Our C1/C2 controls illustrate this distinction directly, in line with previous warnings about pair-input evaluation and degree-associated performance [@Park2012; @Bernett2024]. C3 removes a particular source of training-network information by construction; it does not eliminate all correlations between sequence, ascertainment and interaction propensity.

The development control-shift analysis adds a complementary caution. Even a deterministic sequence formula, with no fitted parameters to overfit, can benefit from cohort-specific positive-pair composition. The concentration of 3-mer signal within components and interolog signal around an interaction-rich component explains why a development score alone is an unreliable measure of transportability. These are changed-population sensitivities rather than a repaired benchmark. They support the comparative robustness of the original model on the examined subsets without proving a complete causal account of test behavior.

The language-model result is compatible with, but does not resolve, several biological explanations. Protein language models encode broad structural and functional regularities [@Rives2021; @Elnaggar2022; @Lin2023]. Those regularities may support transferable complementarity, membership in interaction-relevant protein classes, or more complex homology-based transfer than captured by simple controls [@Yu2004; @Hamp2015]. The within-anchor and endpoint-balanced tests exclude a purely additive propensity account on their panels. Homology-purged and source-restricted fits further reduce specific alternative explanations. Nevertheless, the additional cross-fold alignments demonstrate that sequence generalization must be described relative to the actual search and split procedure [@Steinegger2017; @Joeres2025]. No-hit status in one search does not prove nonhomology, and transitive sequence components are not universal family definitions.

Architecture contributes less decisively than the representation and evaluation design. The bounded search favored a modest head on the smaller encoder, but the residual and non-residual MLP ensembles were almost tied. The protected C3 interval includes no improvement, and the follow-up used a previously examined test. These results justify retaining the optimized scorer as a practical candidate while withholding a statistically conclusive claim of incremental C3 superiority. They also argue for comparing stronger modern sequence and network methods under the same information boundary before asserting broad model leadership [@Chen2019; @Sledzieski2021; @Singh2022]. Such retrained head-to-head comparisons were not performed here.

The central remaining limitation is the absence of an ideal dense, independent direct-binary benchmark qualified for this study. Released systematic interaction data and selected experimental non-detections answer different questions [@Rolland2014; @Luck2020; @Braun2009; @Venkatesan2009]. Curated negative evidence is useful when its assay and selection context are retained, but does not by itself identify a population class prior [@Negatome2014; @Elkan2008]. Our evidence review did not establish the common attempted/evaluable denominator needed to convert the primary analysis to calibrated binary classification. Precision–recall quantities also depend on the comparison population and prevalence, so sampled P/U performance cannot be read as proteome-wide precision [@Davis2006; @Saito2015]. The weighted concordance deliberately avoids making that conversion.

Future validation should preserve this distinction while bringing computational and experimental endpoints closer together. Extracellular interaction programmes provide examples of direct measurement designs with construct and expression information, although their molecular scope and selected follow-up processes require separate qualification [@Shilts2022; @Wojtowicz2020]. A convincing specificity challenge would contain sufficient observed interactions and technically evaluable alternatives for the same anchors, document construct and homology exposure, and test a locked scorer. Recent experimental interactome assessment and interface-prediction work emphasize why pair recovery, residue-level recognition and laboratory validation should be evaluated as complementary endpoints [@Lambourne2026; @Fout2017]. The present results motivate that next validation step: frozen protein representations support interaction-associated ranking beyond elementary sequence and network controls, while the stronger claim of transferable physical partner specificity remains open.

# Methods

## Evidence unit and endpoint eligibility

The primary evidence snapshot comprised published-2020 HI-II-14/HuRI releases. HuRI Space III gene membership was mapped through the frozen human UniProt release 2026_02 [@Rolland2014; @Luck2020; @UniProt2025]. An endpoint was admitted only when its mapping resolved to one distinct canonical reference-sequence hash; sequence-equivalent accessions could represent the same endpoint. Unmapped or sequence-ambiguous cases were excluded. The pair unit was an unordered pair of distinct exact reference sequences. Reverse orientations, repeated evidence and source memberships were grouped at this unit, and self/same-sequence pairs were excluded. This projection preserves reference-sequence identity without claiming exact equivalence to every assayed clone.

Released-positive evidence defined P. Eligible pairs outside the applicable positive set defined U. Complete selected, attempted and technically evaluable pair-level opportunities could not be reconstructed from the inspected public release. Independently curated experimental non-detections and structural noncontacts were consequently not pooled into training negatives. The conceptual latent-state distinction is $S_{AB}=1$ for a released positive and $S_{AB}=0$ for U; the latter does not imply a latent biological state $Y_{AB}=0$. The score targets observed P/U ordering rather than estimating $\Pr(Y_{AB}=1)$.

## Component partitions and pair assignment

The frozen primary graph joined full-length similarity edges with accepted sensitive full-length and local-domain edges. At the primary 30% identity threshold, full-length edges required at least 80% coverage of both endpoints; added local-domain edges required at least 80 aligned residues on each endpoint, at least 20% coverage of each endpoint and E-value at most $10^{-3}$. Connected components were allocated intact. A deterministic search over 4,096 allocations balanced endpoint counts, evidence opportunities, source composition and graph-degree summaries before model fitting. The selected split contained 5,427 training, 1,071 development and 1,284 test components. The split was evidence-balanced rather than a completely outcome-agnostic random allocation.

Training–training positive pairs received deterministic hash roles with nominal fractions 70% training, 15% development and 15% test. An exposed training endpoint had degree at least one in the retained training-positive graph. C1 withheld-positive pairs required both training endpoints to be exposed. C2 required exactly one exposed training endpoint and one endpoint in the relevant held-out partition. C3 required both endpoints in that held-out partition. Development–test cross-pairs and pairs failing the exposure guards were quarantined without reassignment. All evidence for a withheld positive pair was withheld from interaction supervision. Source-specific diagnostic cells are described in Supplementary Methods.

## Unlabeled sampling and ranking estimand

Within each cell, U sampling used deterministic bottom-hash selection without replacement, with degree-based strata for exposed endpoints and fixed cell-specific allocations. The inclusion probability in stratum $h$ was $\pi_h=n_h/N_h$, where $n_h$ is the sample count and $N_h$ the eligible U population. The design weight was $w_u=1/\pi_h$. Positive pairs were a census of the cell’s released positives. Inverse-inclusion weighting follows the finite-population sampling principle of Horvitz and Thompson [@Horvitz1952].

Let $s(p)$ and $s(u)$ be the scores of positive pair $p$ and sampled unlabeled pair $u$. The implemented concordance was

$$
\widehat C
=
\frac{\displaystyle\sum_{p\in P}\sum_{u\in U_s}w_u\,\psi\!\left(s(p)-s(u)\right)}
{|P|\displaystyle\sum_{u\in U_s}w_u},
\qquad
\psi(t)=\mathbf{1}\{t>0\}+\tfrac12\mathbf{1}\{t=0\}.
$$

(1)

Here $U_s$ is the sampled U set. A value of 0.5 denotes tied or chance ordering. The normalization uses the total represented U weight, not the raw P:U sampling ratio. This is not an estimate of the area under a biological positive-versus-negative ROC curve, although the same ranking algebra applies to the observed P/U states.

## Frozen embeddings and symmetric heads

We used frozen ESM-2 150M and 650M encoders [@Lin2023]; both final models use `esm2_t30_150M_UR50D`, revision `a695f6045e2e32885fa60af20c13cb35398ce30c`. For a sequence $S_A$ of length $L_A$, windows contained at most 1,022 residues, with overlap 128 and stride 894; the terminal window ensured full coverage. Special tokens were excluded. If $\mathcal W_A(r)$ is the set of windows covering residue $r$ and $\mathbf h^{(w)}_{A,r}$ is its final-layer representation in window $w$, pooling was

$$
\mathbf e_A=\frac{1}{L_A}\sum_{r=1}^{L_A}
\frac{1}{|\mathcal W_A(r)|}\sum_{w\in\mathcal W_A(r)}\mathbf h^{(w)}_{A,r},
\qquad
\mathbf z_A=\frac{\mathbf e_A-\boldsymbol\mu_T}{\max(\boldsymbol\sigma_T,10^{-6})}.
$$

(2)

The maximum and division act coordinatewise. The mean $\boldsymbol\mu_T$ and population standard deviation $\boldsymbol\sigma_T$ were computed over all 11,900 training-partition endpoints, without development or test endpoints. The dimensions were 640 and 1,280 for the 150M and 650M encoders. Encoder outputs and standardized vectors were stored in FP32; normalization statistics used FP64. For the internal folds, normalization was recomputed over the permitted fitting endpoints.

The pair representation was

$$
\mathbf x_{AB}=\left[
\mathbf z_A+\mathbf z_B,\;
|\mathbf z_A-\mathbf z_B|,\;
\mathbf z_A\odot\mathbf z_B,\;
\frac{\mathbf z_A^\top\mathbf z_B}{\|\mathbf z_A\|_2\|\mathbf z_B\|_2}
\right].
$$

(3)

Zero-norm vectors were prohibited. For 150M embeddings, $\mathbf x_{AB}$ has dimension 1,921 and is invariant to endpoint exchange. The original affine head was $s_{\rm aff}(A,B)=\mathbf w^\top\mathbf x_{AB}+b$. At inference the selected residual head was

$$
s_{\rm res}(A,B)=\mathbf w^\top\mathbf x_{AB}+b
+\mathbf v^\top\operatorname{GELU}\!\left(\mathbf W\operatorname{LN}(\mathbf x_{AB})+\mathbf c\right)+d.
$$

(4)

$\operatorname{LN}$ is learned LayerNorm with $\epsilon=10^{-5}$, and the hidden width is 256. Training inserted dropout with probability 0.3 after GELU; inference disabled it. Each final ensemble averaged three FP32 member scores after casting them to FP64:

$$
\overline s(A,B)=\frac13\sum_{k=1}^{3}s_{\theta_k}(A,B).
$$

(5)

The fixed seeds were 20260803, 20260817 and 20260831. No sigmoid, rank transformation or calibration was applied. The ensemble is the prediction unit; averaging member concordances is not equivalent to evaluating the averaged scores.

## Training and model selection

Training paired each sampled U observation with a cyclically repeated, deterministically permuted positive observation. Every U row was used once per complete pass, and positive repetitions differed by at most one within a pass. For a batch $B$ of comparisons $(p_i,u_i)$, the implemented objective was

$$
\mathcal L_B(\theta)=\frac1{|B|}\sum_{i\in B}
\frac{w_{u_i}}{\overline w_U}
\log\!\left[1+\exp\!\left(-\{s_\theta(p_i)-s_\theta(u_i)\}\right)\right],
$$

(6)

where $\overline w_U$ is the mean design weight over the fitting U set. This is a weighted P-versus-U ranking surrogate, not a class-prior-corrected binary PU risk estimator [@Elkan2008; @Kiryo2017]. Positive and U pairs in a training comparison need not share an anchor.

The original affine model used AdamW, learning rate $3\times10^{-4}$, weight decay $10^{-4}$, 4,096 comparisons per batch and five complete passes. The selected checkpoints were the fifth-pass states. The bounded optimization used 8,192 comparisons per batch and the finite recipe grid described above. Both schedules used warm-up and cosine learning-rate decay with gradient norm clipping at 1. The optimized recipe used learning rate $10^{-4}$ and weight decay 0.01. Development C3 selected the ensemble; supplementary material specifies promotion and tie rules. The original member-consistency conditions were not met, so the follow-up tested a subsequently accepted fixed-ensemble criterion rather than presenting the earlier rule as satisfied.

## Fixed controls

Training degree $d_A$ counted only retained fitting-positive edges; held-out endpoints had degree zero. The implemented degree, preferential-attachment and common-neighbor scores were $\log(1+d_A)+\log(1+d_B)$, $\log(1+d_A d_B)$ and $\log(1+|\mathcal N_A\cap\mathcal N_B|)$, respectively. Component degree mass summed these degrees within the frozen sequence component, with pair score $\log(1+m_A m_B)$. Length controls were $\log(1+L_A)+\log(1+L_B)$ and $-|\log(1+L_A)-\log(1+L_B)|$; “length ratio” denotes the latter monotone length-matching score.

Overlapping 3-mer counts used a 21-symbol alphabet comprising the 20 standard amino acids and X, with other residues mapped to X. L2-normalized count vectors $\mathbf q_A$ defined direct similarity $K_3(A,B)=\mathbf q_A^\top\mathbf q_B$. Composition cosine used analogous normalized single-residue counts. Pooled-ESM cosine used raw, unstandardized pooled vectors. These direct pair similarities are distinct from the standardized cosine feature in Eq. (3). For endpoint similarity $K$, exhaustive fitting-edge transfer was

$$
s_{\rm transfer}(A,B)=\max_{(u,v)\in P_T}
\max\!\left\{
\min[K(A,u),K(B,v)],\;
\min[K(A,v),K(B,u)]
\right\}.
$$

(7)

$P_T$ denotes fitting-positive edges. The primary interolog control used $K_3$ and the full fitting edge set. Here “interolog” is operational shorthand for representation-based within-species interaction transfer, not established orthology. A deterministic hash scorer provided an identity-based chance sentinel. All directions were frozen before test evaluation.

## Partner, homology and source diagnostics

Internal diagnostic folds used only the 11,900 public training-partition endpoints. Three component folds were formed by assigning size-ordered components to the fold with the smallest endpoint count. Evaluation pairs had both endpoints inside the held-out fold; fitting pairs had both endpoints outside it. Separate three-seed five-pass fits compared the symmetric affine pair head with additive $g(\mathbf z_A)+g(\mathbf z_B)$ controls, using either an affine $g$ or a width-64 GELU MLP. Within-anchor concordance applied Eq. (1) to each eligible anchor’s observed P/U partners and averaged anchors equally.

For a selected quartet $(A,B,C,D)$, the swap contrast was

$$
D_{ABCD}=s(A,B)+s(C,D)-s(A,D)-s(C,B).
$$

(8)

Both original edges were released positives and both alternatives belonged to the sampled U panel. Preference assigned one, one-half or zero according to whether the contrast exceeded $10^{-6}$, lay within $\pm10^{-6}$ or fell below $-10^{-6}$. Quartets used four distinct endpoints with deterministic selection and reuse caps (Supplementary Methods).

The homology search used MMseqs2 18-8cc5c at sensitivity 7.5 on public training sequences only [@Steinegger2017]. Accepted alignments required at least 20% identity, E-value at most $10^{-3}$ and spans of at least 40 residues. Purging required spans of at least 80 residues and at least 20% coverage of both endpoints; entire fitting components linked to held-out endpoints were removed. Source-restricted fitting retained positives visible in the fitting source, including shared positives. Target-only released positives outside the evaluation fold were inserted into fitting U at unit weight. Evaluation used target-exclusive positives and the parent U panel. Neither analysis used primary development or protected-test pair rows.

## Uncertainty and protected evaluation

Primary benchmark intervals used 2,000 paired component-resampling replicates, motivated by dependence among pairs sharing biological units [@Owen2007]. Components were sampled with replacement. For counts $n_c^{(b)}$ in replicate $b$, a pair joining distinct components $c_A,c_B$ received multiplier $n_{c_A}^{(b)}n_{c_B}^{(b)}$; a pair within one component received $n_{c_A}^{(b)}$. Multipliers reweighted both P and U, retaining U design weights. The 2.5th and 97.5th percentiles defined the interval. Differences used common draws, and a positive lower bound defined the prespecified 95% criterion for an advantage. Internal partner/source studies instead used paired independent Poisson(1) component multipliers with anchor-aware ratio recomputation; quartet weights were products over unique endpoint components. These intervals condition on fitted models, fixed folds and available panels, and do not incorporate refitting or independent laboratory sampling uncertainty. Secondary comparisons were not multiplicity-adjusted.

For the original protected test, the model, controls and scoring bundle were frozen before candidate opening; predictions were completed and hashed before truth access. Only aggregate outcomes were released. The optimized follow-up fixed a new ensemble and paired comparison before its evaluation but reused the same previously examined test. We therefore distinguish original confirmatory evidence, development-selected estimates, internal stress tests and the disclosed follow-up throughout. Manuscript figures reproduce existing aggregate outputs; no protected scoring or model fitting was repeated.

# Data availability

HI-II-14/HuRI evidence is available through the [Interactome Atlas downloads](https://www.interactome-atlas.org/download); reference sequences are from [UniProt](https://www.uniprot.org/). Machine-readable source data for every figure and the tabulated aggregate results accompany this manuscript. The exact split and analysis manifests are retained in the project repository. Protected pair-level truth, row-level predictions and model states are not included in this manuscript package.

**[Submission placeholder: insert the permanent repository/archive accession, accessible split and checkpoint deposit locations, and the final access terms for protected pair-level materials. No public deposit is asserted here.]**

# Code availability

The iPIN-OpenPPI repository contains the benchmark construction, model implementations, evaluation code and versioned runtime definitions. This manuscript package includes the scripts and aggregate snapshots required to regenerate all figures and tables without accessing protected pairs or running models. Production analyses used dedicated ARM64 Apptainer environments; model work used `ipin-model-arm64_0.1.0.sif`.

**[Submission placeholder: insert the permanent code URL, archived release DOI and release identifier, and confirm the code licence for that release.]**

# References

::: {#refs}
:::


# Main figures

## Figure 1 | Evidence, endpoint exposure and the iPIN scoring framework

![Figure 1](figure-1.png){width=7in}

**a,** The benchmark distinguishes released-positive interactions (P) from eligible unlabeled pairs (U). A frozen sequence-component graph partitions 17,000 reference-sequence endpoints into training, development and protected-test cohorts; the component and endpoint counts refer to the partition skeleton, not independent observations. **b,** C1 evaluates a withheld pair with both endpoints exposed in training-positive edges, C2 has one exposed endpoint, and C3 has neither. Filled and open symbols denote exposed and held-out endpoints, respectively; gold, purple and teal encode C1, C2 and C3 throughout. **c,** A shared frozen ESM-2 encoder produces residue-mean protein representations, standardized with training endpoints only. Symmetric pair features feed an affine branch and the optimized nonlinear branch; their sum is averaged across three seeds. The original model uses the affine branch alone. Arrows denote data flow, not retraining on development or test endpoints. Source data: `figure-1.csv`.

## Figure 2 | Endpoint exposure changes the apparent strength of fixed controls

![Figure 2](figure-2.png){width=7in}

HT-weighted released-positive-versus-unlabeled concordance on **a,** development and **b,** the original protected test. Values are shown directly; darker teal denotes stronger ranking and pale purple denotes below-chance ranking. The original affine ensemble is compared with training-topology and simple sequence controls. Topology is computed only from fitting-positive edges. Held-out endpoints have zero training degree, so several C2 controls and all displayed topology controls in C3 produce constant scores and concordance 0.500. C1/C2/C3 contain 3,259/11,327/2,265 development positives and 3,187/13,446/2,379 test positives; each cell uses 1,000,000 sampled U pairs. Corresponding marginal 95% intervals are included in the CSV and Supplementary Table S2; paired protected differences appear in Supplementary Fig. S1. The panels should not be read as independent replications across exposure regimes. Source data: `figure-2.csv`.

## Figure 3 | Original iPIN retains C3 ranking while several shallow controls weaken

![Figure 3](figure-3.png){width=7in}

Open symbols show development C3 and filled symbols show protected C3, with connecting segments identifying the same scorer across cohorts. Small vertical offsets distinguish their whiskers. Whiskers represent marginal 95% component-bootstrap intervals from 2,000 replicates; the optimized development point has no marginal interval reported in the frozen aggregate record. Development and test contain 2,265 and 2,379 P pairs, respectively, each compared with 1,000,000 sampled U pairs. The test values are directly labelled. Composition and raw pooled-ESM cosine appear as test-only controls because corresponding primary development metrics were not available. Optimized iPIN was evaluated in a disclosed follow-up on the already examined test set. Connecting segments are descriptive cohort comparisons, not paired development–test difference intervals. The dashed line marks concordance 0.5; U does not denote confirmed noninteraction. Source data: `figure-3.csv`.

## Figure 4 | Development control performance depends on sequence-component composition

![Figure 4](figure-4.png){width=7in}

**a,** Full development C3 and four changed-population sensitivities for affine iPIN, 3-mer cosine, training-edge 3-mer interolog and length ratio. Removal excludes both P and U pairs touching the indicated components. Rows retain 2,265, 1,167, 1,573, 582 and 1,440 positive pairs, respectively; retained sampled-U counts are 1,000,000, 559,080, 952,824, 524,006 and 933,856. Whiskers are descriptive 95% component-bootstrap intervals using 2,000 original development component draws. The largest-component removal was specified before the initial diagnostic; the other subsets were data-informed follow-ups. **b,** Exact positive-group decomposition of concordance above 0.5 against a common full U reference. Within-component positives supply 94.0% of the 3-mer excess; positives touching the third-largest component supply 70.1% of the interolog excess. Gray segments represent the remaining positives. Each row is a separate disjoint positive partition. These percentages do not quantify the development-to-test decrease or establish its test-side cause. Source data: `figure-4.csv`.

## Figure 5 | Internal tests support pair-dependent ranking with bounded robustness

![Figure 5](figure-5.png){width=7in}

**a,** Equal-anchor P-versus-U concordance across 3,072 anchors in three component-held-out folds within the public training partition. The affine pair head is compared with additive linear and nonlinear unary scorers and direct sequence controls. Whiskers show available 95% component-multiplier intervals; fixed controls without reported intervals are points only. Pair-head and nonlinear-unary intervals use the original partner study, and the linear-unary interval uses the later union-arm readout; the annotated paired comparison uses the original common draws. **b,** Paired advantage over the linear unary scorer in the union, homology-purged and two source-restricted arms (3,072, 3,072, 2,657 and 716 anchors). **c,** Preference for two observed pairs over two U alternatives with identical four endpoints. Counts denote selected quartets; intervals use 2,000 Poisson component-multiplier draws, except the sparse reverse-source arm with 1,998 finite draws. The 66-quartet reverse-source result is inconclusive and fails the support floor. Internal fits are distinct from the final protected-test models. Source data: `figure-5.csv`.

## Figure 6 | A bounded search favors modest nonlinear capacity on the smaller encoder

![Figure 6](figure-6.png){width=7in}

**a,** All 24 initial three-epoch, single-seed recipes, plotted against trainable head parameters. Color identifies frozen ESM-2 encoder size and symbol identifies head family. **b,** All eight three-seed ensemble candidates from four promoted recipes, assessed at epochs four and eight of eight-epoch fits. Filled circles denote epoch four and open squares epoch eight. The selected 150M residual ensemble scores 0.799419, nearly tied with the 150M MLP at 0.799379. **c,** Matched individual-seed development gains and ensemble gains relative to the original affine model. Individual-seed points have no inferential interval. Ensemble whiskers are paired 95% component-bootstrap intervals from 2,000 draws. The development interval is a post-selection screen; the protected interval comes from a follow-up on the previously examined test. The protected C3 interval crosses zero and does not meet the prespecified 95% criterion for improvement. All comparisons use 2,265 development or 2,379 protected P pairs and 1,000,000 sampled U pairs per cell. Source data: `figure-6.csv`.

