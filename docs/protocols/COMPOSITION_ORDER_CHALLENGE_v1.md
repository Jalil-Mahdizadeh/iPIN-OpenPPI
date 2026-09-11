# Composition, sequence order and matched-partner diagnostic v1

2026-09-11 · DEC-0049 · Design informed by the completed DEC-0048 results.
This is a prospectively frozen **analysis of spent diagnostic evidence**, not
fresh validation or an external preregistration. It cannot change earlier gates.

## Question and scope

Does the successful direct 3-mer baseline require native residue order, and
does the locked pair head discriminate among composition/length/similarity-
matched partners? Use exactly the six existing BioPlex panels, original folds,
public 11,900 endpoint sequences, existing scores and component draws. Do not
refit, re-embed, reacquire sources, open development/protected data, reconstruct
an opportunity universe, or treat U as experimentally verified noninteraction.

AAC has predicted PPI benchmarks before; this is a needed control, not proposed
novelty. Published composition results do not establish causation or generalize
automatically to our split/assay. [Roy et al., 2009](https://doi.org/10.1371/journal.pone.0007813).
BioPlex detects co-association, including complexes, rather than exclusively
direct binary binding. [Huttlin et al., 2021](https://doi.org/10.1016/j.cell.2021.04.011).

## Fixed scores

Map residues to the parent 21-symbol alphabet, including X; other residues map
to X. Verify every original sequence SHA and length against public metadata.
Use FP64 counts, normalization, accumulation and pair products.

1. `aac_cosine`: cosine between 21-dimensional residue-frequency vectors.
2. `shuffle_kmer3`: mean cosine after independent, composition-preserving
   permutations of each endpoint. Generate exactly 64 permutations per endpoint
   with PCG64DXSM, using the first 16 SHA256 bytes (big endian) of
   `salt:endpoint_sha:replicate` as the seed. Start from sorted mapped residues.
   Normalize **each** 3-mer count vector before averaging; never normalize the
   average vector. Dotting the two endpoint means averages all 64-by-64 cross-
   replicate cosines; these are not 4,096 independent samples. This preserves
   length and composition, with fixed finite-Monte-Carlo noise, but destroys
   native order. It is not the cosine of expected counts.
3. `order_excess`: original frozen 3-mer cosine minus `shuffle_kmer3`, without
   refitting, scaling or clipping. This descriptive contrast is not a purified
   binding score or a variance decomposition.

Retain halves 0–31 and 32–63 separately and score their mean-vector dots.
The maximum absolute difference between their cell-level anchor concordances
must be <=0.01 for an order-increment interpretation. Otherwise call the shuffle
diagnostic Monte-Carlo-inconclusive; no additional replicates in this version.
Half stability is a coarse sensitivity check, not a confidence bound for the
shuffle expectation. Resampling intervals condition on the fixed permutations.

The IID expected-triplet frequency vector is a tensor cube of AAC. Its cosine
is AAC cosine cubed (identical anchor ranking), so do not count it as an
independent additional baseline. Native and shuffled 3-mers include finite-
length sparsity/normalization effects that AAC cosine does not.

Retain locked `pair_linear`, `endpoint_linear`, `kmer3_cosine`, `pooled_cosine`
ensembles. No learned scores change. Report both cell lines separately.

## Matched panels (both frozen, no tuning)

For each existing directed positive A–B, enumerate **all** existing U A–C
within the same panel, preserving the bait A. B and C must satisfy:

- `composition_length`: max(length B, length C)/min(length B, length C) <=1.25
  and total variation of their 21-residue frequencies <=0.10.
- `also_direct_similarity`: the above, plus absolute differences between
  A–B and A–C <=0.01 for **each** of frozen 3-mer and pooled-embedding cosine.

Inclusive calipers admit <=1e-12 roundoff. Keep a positive only with at least
five eligible U. Do not choose nearest neighbours, use learned scores to select,
subsample matches, alter U weights, or generate pairs. U reuse is allowed and
retained in dependence-aware resampling. Publish P/anchor/component attrition,
number of comparisons and empirical caliper summaries per fold/tier/cell.
Support is adequate only if **each fold** has >=100 retained P, >=50 baits,
and >=30 original bait components. Underpowered tiers remain in the report;
calipers and floors cannot change after outcomes.

For every retained positive, compute weighted concordance against its eligible
U, using original num/den U weights and exact score ties at 0.5. Average equally
over retained positives of a bait, then equally over baits. This is a new
conditional recovery estimand, not the parent full-panel AUC. Also report
unmatched-U point estimates using the **same retained positives and baits**,
to expose selection versus comparison-set changes. This restricted-support
reference is descriptive; do not attach the parent's all-bait interval to it.

## Uncertainty and interpretation rules

Reuse the parent's exact 2,000 original-component Poisson draws. For matched
comparisons, recompute each positive's U-weighted ratio with U-component
multipliers, then its bait mean with positive-partner-component multipliers,
then the bait macro with bait-component multipliers. Partner multipliers in
the bait's component are one (the bait multiplier already represents it).
Drop empty positive ratios and empty baits within a draw. Scores share draws.
Report percentile 95% paired intervals, requiring >=95% finite draws. These
intervals are conditional on trained heads, match sets, permutations and source
support; they do not include retraining, selection or assay uncertainty.

On full panels report anchor and original endpoint-balanced quartet metrics
for all new scores. Reuse previously verified bootstrap totals for old scores.
Quartets keep the existing 1e-6 tolerance and distinct-component product weights;
no new quartet selection. All matched scores are shown, including order excess.

Diagnostic flags (not confirmatory claims or new architecture gates):

- Order-free recovery is supported if shuffled anchor lower bounds exceed 0.5
  in both cell lines and half stability passes.
- A material native-order increment requires native-minus-shuffled anchor point
  >=0.02 and paired lower bound >0 in both cells, plus half stability. Failure
  does not establish equality or that order carries no information.
- A matched tier supports incremental learned ranking only if support passes
  in both cells, pair lower >0.5, pair point >=0.02 above the largest of the
  five locked comparator points, and all five pair-minus-control lower bounds
  >0 in both cells. Comparators: unary, native 3-mer, pooled cosine, AAC and
  shuffled 3-mer. Report every comparison, not only a winning baseline.

No p-values, fraction-of-signal-explained estimate, causal adjustment claim or
claim that composition is a nonbiological shortcut. Matching selected summary
variables does not match localization, complex membership, domains, expression,
detectability or opportunities. No direct-binding, family-generalization,
equivalence, superiority-on-new-data, or new-model-novelty claim follows.

## Execution and verification

Register config/protocol/authority and all reused input hashes before deriving
new features or match counts. After synthetic/unit tests, freeze execution
code/dependencies/tests. Complete all feature/score/match tables before metrics.
Use pinned ARM64 data Apptainer only, eight threads; no GPU is needed for this
study. Store large arrays locally, publish aggregate JSON and hashes only.

Independent same-author reference arithmetic must check every AAC vector,
every new pair-score value using saved features, all match membership and
retained-support points, all interval/flag arithmetic, 16 full anchor and
matched bootstrap draws per cell, and all quartet draws. Reconstruct shuffle
features independently using string counters for 64 evenly spaced endpoint
indices, all 64 permutations each. Validate exact finite-permutation mean-dot
semantics on tiny synthetic sequences and adversarial ties/weights/empty draws.
This is numerical auditing, not external scientific review. Preserve every
prior study closure; close only after passing post-execution tests/reference.
