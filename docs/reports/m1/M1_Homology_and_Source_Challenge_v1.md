# Homology/interolog and source-aware challenge: findings

Date: 2026-09-11. Authority: DEC-0047.
Status: execution complete; numerical reference and supporting audits pass.

## Judgment

The internal partner-ranking signal survives all four prespecified anchor
challenges. It remains after a substantial remote-homology purge and transfers
in both directions between HI-II-14 and HuRI. None of the four new interaction-
transfer controls explains away the pair head's advantage on these panels.

That strengthens the case that this is **not a dead end as a ranking research
project**. It does not establish biological binding specificity, independent
source/assay generalization, unseen-family prediction, or a novel architecture.
The entire protocol is **not** a pass: the HuRI-to-HI-II-14 swap panel is too
small and inconclusive. The original gating/complexity stop remains unchanged.

## What was actually run

This is a follow-up on previously explored public training data, not an
external preregistration or untouched test. The protocol/config were frozen
before new source counts or sequence-search results; implementation, passing
tests, input similarities and panels were frozen before any new fit/score.
The prior study, its checkpoints, public pair rows and three component folds
were preserved. No development or protected package/key was accessed.

The study added four exhaustive interaction-transfer controls: normalized
3-mer similarity, raw pooled-embedding similarity, local alignment similarity,
and coverage-aware alignment similarity. Each candidate score takes the best
minimum endpoint similarity over **all fitting positive edges and both
orientations**, not just a top-k neighbor shortlist. "Interolog" here is
shorthand for within-species homology/representation-based transfer, not a
claim of evolutionary orthology. These controls are stronger explanatory
challenges than direct pair cosine alone, but were not empirically stronger
rankers than all older controls.

MMseqs2 18-8cc5c searched only the 11,900 public sequences, at sensitivity 7.5,
without adaptive first-hit termination. Exact integer postfilters retained
>=20% identity, E-value <=1e-3 and >=40-residue spans; the search had no coverage
floor. The stricter purge uses >=80-residue spans and >=20% coverage of both
endpoints. Identity and coverage semantics follow the
[official MMseqs2 guide](https://github.com/soedinglab/MMseqs2/wiki).

The three new refit arms each used the original two small heads, three seeds,
three folds, five complete passes and final checkpoints: **54 new fits**.
All fits completed before any new heldout scoring. Fit time was 126.17 seconds;
scoring took 24.42 seconds, producing 40,420,500 score values across 12 tables.
No encoder extraction, fine-tuning, model search, or new scientific data download
was needed.

## Anchor-ranking results

Metric: equal-anchor, design-weighted released-positive-versus-U concordance.
It is neither biological accuracy nor calibrated probability. Intervals below
are paired, conditional 95% component-multiplier intervals, with 2,000 draws.

| Challenge | Anchors | Pair head | Linear unary | Best new transfer control | Pair minus unary, 95% interval |
|---|---:|---:|---:|---:|---:|
| Original union, new controls | 3,072 | 0.663612 | 0.584203 | 0.521385, embedding | +0.079409 [0.070839, 0.109922] |
| Remote-homology-purged refit | 3,072 | 0.657382 | 0.583893 | 0.516907, embedding | +0.073490 [0.064369, 0.107007] |
| HI-II-14 → HuRI-only | 2,657 | 0.593449 | 0.545761 | 0.506298, embedding | +0.047688 [0.032103, 0.089457] |
| HuRI → HI-II-14-only | 716 | 0.623196 | 0.583384 | 0.566169, 3-mer | +0.039812 [0.015602, 0.087462] |

All four arms meet the frozen >=0.02 margin over the strongest **primary
comparator** (linear unary plus four transfer controls); every paired lower
bound against those five comparators is positive. Every fold and every seed
beats its linear-unary comparator. All anchor intervals have 2,000 valid draws.

Do not confuse "strongest primary comparator" with "best of every descriptive
score": in HI-II-14→HuRI, direct pooled cosine scores 0.551945, above unary
0.545761. The pair head still exceeds it by 0.041503, but a paired interval for
that descriptive comparison was not prespecified here. Likewise, direct 3-mer
swap preference is stronger than every new transfer control in some arms. All
these older controls remain visible in `RESULTS.json`; no favorable comparator
is substituted after the readout.

The alignment-based transfer controls are close to 0.5. This limits what their
failure can establish: the absence of usable detected transfer paths is not
proof that richer sequence/structure, domain, orthology or network methods
cannot explain the score. The homology-purged refits are the more consequential
robustness result.

## Remote-homology stress test and a newly documented limitation

The new search finds **344 undirected links crossing the original folds at
>=30% identity**, despite satisfying the earlier local span/coverage criteria;
507 cross original components. Nine links cross components/folds at >=40%.
At >=20%, 7,843 links cross folds and 11,085 cross components. These counts are
for public endpoints only, not the protected benchmark.

This does not invalidate historical metric arithmetic. It exposes the
distinction between disjointness under a frozen heuristic graph and absence of
every alignment satisfying a nominal threshold. Search settings and database-
size-dependent significance differ; this study does not identify their separate
contributions. The limitation is recorded in
`governance/issues/ISSUE-0015-residual-homology-in-frozen-component-folds.md`.

| Evaluation fold | Original fitting endpoints | Endpoints after purge | Fitting P after purge | Detected cross-links before / after |
|---|---:|---:|---:|---:|
| 0 | 7,933 | 5,270 | 3,595 | 5,861 / 0 |
| 1 | 7,933 | 4,619 | 3,090 | 4,565 / 0 |
| 2 | 7,934 | 4,601 | 2,905 | 5,260 / 0 |

Removing an outside endpoint removes its whole original component from fitting
and normalization. Both endpoints of every fitting edge must survive. The
evaluation panels are unchanged. This removes 2,663–3,333 fitting endpoints per
fold, but the pair-head point estimate changes only from 0.663612 to 0.657382.
This is a robustness comparison, not a causal decomposition: less data, fewer
optimization steps and changed normalization accompany the purge. No matched
random-removal arm was run.

The frozen "no detected hit" sensitivity retains 1,271 anchors, 965 components,
1,729 P and 203,992 U. The pair head scores 0.669584, versus unary 0.567170 and
best transfer control 0.547154. This is a descriptive subset without its own
success gate or interval. It excludes detected >=40-span hits to fitting
endpoints; it does not establish nonhomology or unseen families.

## Source-aware validation: useful, explicitly bounded

The original public training package omits memberships. DEC-0047 authorized a
narrow join from frozen pre-benchmark source archives to the exact public-P
allowlist. Only source bits for those 16,799 already released pairs leave the
projection; no new positive identity, evaluator role or protected outcome is
recovered. The archive files are physically scanned inside this constrained
join, so this is not a claim that no broader archive was read.

| Public P membership | Pairs |
|---|---:|
| HI-II-14 only | 1,970 |
| HuRI only | 13,547 |
| Both | 1,282 |

For each source direction, fitting positives carry the visible source, including
shared evidence. Target-only public positives outside the evaluation fold are
reinserted into fitting U with unit weight, rather than excluded using hidden
source knowledge. This reintroduces 5,754–6,407 P per fold when fitting HI-II-14
and 766–1,041 when fitting HuRI. Original sampled U and rational weights remain.
Evaluation uses target-exclusive positives and the parent C3 U panel; shared
positives are excluded from targets, not relabeled negative.

The union-trained descriptive strata are also positive: pair/unary concordance
is 0.637404/0.602780 for HI-II-14-only, 0.665789/0.580521 for HuRI-only, and
0.681982/0.584926 for shared positives. These use different anchor cohorts and
must not be interpreted as a causal source effect.

Transfer is not lossless. On the matched HuRI-only cohort, the union-trained
pair head scores 0.665789 versus 0.593449 when trained on HI-II-14 evidence.
On HI-II-14-only targets, the corresponding union/HuRI-trained scores are
0.637404/0.623196. This asymmetry deserves attention: source coverage and the
amount of fitting evidence both change, so it is not an isolated causal source
effect. A positive residual advantage does not mean source invariance.

The source-limited fits are not independent source validation in the strongest
sense. Upstream pair-role selection and U sampling used the source union;
both sources informed prior model choice. Reinsertion corrects source visibility
only on the available public support. The datasets belong to the same research
programme and related Y2H methods; HuRI itself used multiple versions/screens.
[Luck et al., 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7169983/).

The frozen release in this repo lacks complete pair-level attempted/evaluable
logs. Source labels do not supply that denominator, batch independence, or
assay-specific negatives. The existing systematic-screen metadata audit remains
the basis for this limit. These are **internal source-exclusive recovery
stress tests**, not laboratory-independent replication or a complete assay-aware
validation. Source restriction and homology purging were tested separately,
not jointly.

## Endpoint-balanced swap results

Quartets compare P(A,B)+P(C,D) against released U(A,D)+U(C,B), with identical
four endpoints. Additive unary scores cancel to 0.5 tie-adjusted preference.
All panels inherit the original frozen quartet selection; source arms only
filter it, with no replacement sampling. Reported intervals condition on these
selected panels, not a population quartet sampling design.

| Challenge | Quartets | Pair preference | 95% interval | Frozen swap conclusion |
|---|---:|---:|---:|---|
| Union | 6,000 | 0.727833 | [0.680154, 0.782976] | Survives all new transfer controls |
| Homology-purged | 6,000 | 0.725167 | [0.678886, 0.779694] | Survives all new transfer controls |
| HI-II-14 → HuRI-only | 3,876 | 0.662539 | [0.604439, 0.734627] | Survives all new transfer controls |
| HuRI → HI-II-14-only | 66 | 0.560606 | [0.158668, 0.952464] | Inconclusive; insufficient frozen support |

The last direction has just 29, 17 and 20 quartets per fold, below the frozen
minimum of 30 in every fold. Two bootstrap draws have zero effective quartet
mass, leaving 1,998 valid draws; its broad interval cannot support specificity.
The count floor was not weakened. Direct 3-mer preference is 0.575758 in that
tiny panel, above the pair head's point; this is not hidden behind the other
controls' lower points. It also is not a well-powered disproof of the signal.

Thus all four anchor tests and three swap tests survive, while the fourth swap
test remains unresolved. The machine-readable conservative disposition is
`mixed_or_explained_internal_signal_inspect_each_challenge`; in this actual
readout, it means **mixed evidence from an unresolved swap arm**, not that the
transfer controls have explained away the anchor-ranking signal.

## Verification and operational record

The separate numerical reference audit passes. It checks all 16,799 public
source annotations, all 566,440,000 similarity entries, all 171,433 purge edges,
every fitting mask and normalizer, all training row orders and complete passes,
and **all 16,168,200 learned score values**. Maximum reference-forward difference
is 0.00000429523, below the frozen 0.0001 tolerance. It independently enumerates
every fitting edge for 24,576 deterministically sampled transfer-score values,
checks every anchor and quartet point estimate, recomputes 16 complete direct
anchor-bootstrap replicates per arm and all 2,000 quartet replicates, and checks
all reported primary interval arithmetic. It does not independently recompute
every transfer score or every anchor-bootstrap replicate.

All four full similarity matrices had also passed before fitting. The
supporting readout audit passes all source/no-hit strata and decision rules.
The complete 390-test set passes across the qualified runtimes: 389 CPU tests
plus the separately run CUDA test, before and after fitting/scoring. This adds
33 tests to the prior 357-test suite.

One issue was caught **before execution freeze or any new fits/scores**: FP32
sparse 3-mer multiplication exceeded the unchanged 2e-6 tolerance, with a
1.49e-5 discrepancy in the first failing block. The original matrix and
feasibility manifest are retained. FP64 accumulation followed by FP32 storage
produced a separate corrected matrix; the final maximum difference is
2.9782e-8. The preregistration, tolerances, scientific rules and data splits did
not change. The operational correction and transcribed failure are retained.

The edge-count and supporting decision/stratum audits were written after
execution freeze. They add numerical checks and label-free context only, not
new metrics, fitting choices or scientific success rules. All validation here
is same-author numerical auditing, not external review.

## Next decision

The sensible next investment is a **fresh, externally assembled challenge with
auditable source/assay opportunities and stronger homology exclusions**, using
a locked pair head and locked competing baselines. If a full opportunity log
cannot be obtained, use a genuinely independent source with an explicitly PU
endpoint and do not upgrade it to biological specificity. Include enough
source-specific balanced partner alternatives to make the sparse-direction
swap test meaningful.

An offline joint source-plus-homology purge could be a modest additional stress
test, but it would still reuse spent data and would not solve the main remaining
evidence gap. Do not launch an architecture sweep or open the current protected
test because this internal result is encouraging. Richer profile/domain,
structure-informed, network-transfer and co-complex controls also remain
unexcluded. The concern about homology/degree shortcuts is well motivated by
[Bernett et al., 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC10939362/); passing
these particular controls does not settle that broader problem.

## Artifacts and execution

- Protocol: `docs/protocols/HOMOLOGY_SOURCE_CHALLENGE_v1.md`.
- Config: `configs/homology_source_challenge_v1.yaml`.
- Main CLI: `scripts/model/run_homology_source_challenge_v1.py`.
- Supporting audit: `scripts/model/audit_homology_source_support_v1.py`.
- Closure verifier: `scripts/model/close_homology_source_challenge_v1.py`.
- Aggregate phase records: `artifacts/results/homology_source_challenge_v1/`.
- Numerical and test evidence: `artifacts/validation/homology_source_challenge_v1/`.
- Local matrices, plans, checkpoints and score tables:
  `artifacts/runs/homology_source_challenge_v1/` (ignored by Git).
- Execution freeze: `d62147bcb4f0f10170575161cb2b9cc016894e656aa210c0e65bc24c2fb1d08b`.
- Readout: `6ff6e42efeb78e0368e37b67f012cda934240201586f3db08c86f79787ec40d6`.
- Numerical reference report:
  `5b601d9527e057d15113a6cfdc38233adb79e9c3bf7f8a8e940f174247975608`.
- Closure registry: `artifacts/results/homology_source_challenge_v1/ARTIFACT_REGISTRY.json`.

The CLI phases are `register`, `annotate`, `search`, `prepare`, `freeze`,
`train`, `score`, `evaluate`, and `validate`. Source annotation uses the data
image; training/scoring use the model image with `--nv`, clean offline
environment, `CUBLAS_WORKSPACE_CONFIG=:4096:8`, and eight CPU/BLAS threads.
Freeze requires passing full-suite/GPU XML and the label-free reference report
generated by `reference_similarities`. The historical `correct_precision` phase
records this run's pre-freeze correction; current fresh preparation already
uses FP64 accumulation. Completed namespaces refuse overwrite; these are
auditable frozen experiments, not commands to rerun over their own evidence.

Graphify led to the existing source-completeness audit, provenance projection,
component safeguards and ranking machinery. The required AST-only updates
completed without LLM/API use; the final graph has 3,657 nodes, 8,766 edges and
282 communities. The tool warned that 126 sources produced no AST nodes and
that some communities received hub-derived labels. This does not semantically
index the new report/result JSON or validate its scientific relationships.
Pre-existing graph/cache changes were preserved. The frozen manifests and
checked readout, not graph inference, are authoritative. No commit or push was
performed for this work package.
