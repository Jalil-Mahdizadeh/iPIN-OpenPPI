# Composition/order challenge: concise findings

2026-09-11 · DEC-0049 · Executed and numerically verified.

## Bottom line

**The project is not disproved, but the present learned head still has no
demonstrated advantage over elementary sequence controls.** Composition-only
similarity is competitive. Native order helps the 3-mer anchor-ranking statistic,
so “it is all composition” is also too strong. The intended matched-partner
test is inconclusive because the frozen candidate support is extremely sparse.
The next investment should be better experimental comparison sets, not a larger
head or another architecture sweep.

## What was frozen and tested

Reused the six already-examined BioPlex panels and locked homology-purged scores.
Registered the design at 06:55:52 UTC and froze tested execution at 07:06:20 UTC,
before new features, matching counts or outcomes. This is diagnostic reuse,
**not fresh validation or external preregistration**. No fits, encoder extraction, new
interaction acquisition, development evaluation or protected/key access.

Computed AAC cosine and 64 composition/length-preserving permutations for each
of 11,900 public sequences: 761,600 permutations. The shuffle comparator averages
individually normalized 3-mer vectors, without renormalizing their mean. Also
tested native-minus-shuffled similarity (`order_excess`). AAC is an established
control, not methodological novelty. [Roy et al., 2009](https://doi.org/10.1371/journal.pone.0007813).

## Full-panel results

Bait-macro weighted P-versus-U concordance; larger is better:

| Fixed score | 293T | HCT116 |
|---|---:|---:|
| Learned pair head | 0.6171 | 0.6094 |
| Additive endpoint head | 0.4494 | 0.4469 |
| Native 3-mer cosine | 0.6415 | 0.6134 |
| Pooled-embedding cosine | 0.6142 | 0.6209 |
| **AAC cosine, no residue order** | **0.6273** | **0.6128** |
| Composition-preserving shuffled 3-mers | 0.6027 | 0.5784 |
| Native-minus-shuffled similarity | 0.5820 | 0.5612 |

Native-minus-shuffled **concordance differences** are +0.0389
[0.0302, 0.0709] and +0.0350 [0.0208, 0.0761]. Both pass the prespecified
0.02-point/positive-lower-bound diagnostic rule. Shuffle-half concordances
differ by only 0.000060 / 0.000731, below the frozen 0.01 sensitivity ceiling.
However, AAC is itself stronger than the shuffled statistic: order's benefit
to that particular statistic does not establish superiority over composition.

Pair-minus-AAC differences are −0.0101 [−0.0334, +0.0171] and −0.0035
[−0.0292, +0.0287]. No superiority, inferiority or equivalence is established.
Shuffling did not re-embed proteins, so this does not identify what the learned
head itself uses. Intervals reuse 2,000 original-component draws and condition
on fixed models, source support and permutations; they exclude retraining,
assay and Monte Carlo uncertainty.

On the original 3,832 / 2,231 endpoint-balanced quartets, even order-free AAC
scores 0.6628 / 0.6333, with lower bounds above 0.5. Native-versus-shuffled
quartet differences remain uncertain: intervals [−0.0529, +0.0817] /
[−0.0968, +0.1003]. Passing swaps alone therefore does not establish an
order-dependent binding mechanism. All scores and contrasts remain in JSON.

## Matching failed feasibility—not a specificity falsification

Required partner length ratio <=1.25, composition total variation <=0.10 and
at least five eligible existing U per positive. A second tier additionally
required both direct similarities within 0.01. No learned-score selection.

| Support | 293T | HCT116 |
|---|---:|---:|
| Positives entering original bait rankings | 4,082 | 2,705 |
| Composition/length-matched positives / baits | 22 / 22 | 3 / 3 |
| Matched P-versus-U comparisons | 122 | 17 |
| Also direct-similarity-matched positives | 0 | 0 |

Every fold fails the frozen support floors. The tiny matched estimates,
same-support unmatched references and attrition are retained, not promoted as
findings; HCT116 has only 1,561/2,000 valid matched draws, so no interval is
reported. Calipers were not relaxed. The original panels contain 9,599 / 6,477
positive edges overall; many have no eligible U for bait ranking.

## Research decision and next step

Prioritize an **opportunity/construct and matched-support feasibility audit**
for an independently generated, dense direct-binary candidate panel. Require
pair-level attempted/evaluable/failed assay records and enough matched alternatives
before model scoring; separate pilot feasibility from untouched confirmation.
Carry AAC, native 3-mer, pooled cosine and the fixed head forward as mandatory
comparators. Do not manufacture experimental negatives from missing pairs.

BioPlex measures co-association, including complexes; localization, expression,
within-pair homology, complex membership, detectability and construct identity
remain unresolved.
[Huttlin et al., 2021](https://doi.org/10.1016/j.cell.2021.04.011).
Composition may encode real biology. Neither this diagnostic nor its sparse
matching establishes causal confounding or direct binding. The original
architecture stop and DEC-0048 failed superiority gates remain unchanged.

Verification: 451 CPU tests before/after execution plus the separate existing
GPU regression; 36 new tests. Independent same-author arithmetic checked all
1,706,845 new score values (maximum error 1.17e−15), every AAC vector and match
membership, 4,096 sampled-endpoint permutations, all points/intervals/flags,
16 full anchor/matched draws and all quartet draws per cell. This is not external
review. All three preceding study closures remain hash-identical.

Evidence: [protocol](../../protocols/COMPOSITION_ORDER_CHALLENGE_v1.md),
[readout](../../../artifacts/results/composition_order_challenge_v1/RESULTS.json),
[reference audit](../../../artifacts/validation/composition_order_challenge_v1/REFERENCE_VALIDATION.json).
