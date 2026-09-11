# Why do simple controls weaken from development C3 to test C3?

Date: 2026-09-11. Completed, post-hoc diagnostic. No model change or new test
evaluation. Both ensembles retain their frozen definitions and roles.

## Bottom line

**The development control signal is concentrated in particular sequence-group
and positive-pair patterns. We found no scoring discrepancy.** These patterns
provide a concrete reason not to expect the simple controls' development scores
to transfer uniformly to a different protein cohort. The PLM baseline is much
less dependent on the particular concentration examined here.

This is a measured explanation of **development performance**, not a complete
causal attribution of the test-side drop: no protected test pairs, labels,
predictions or keys were opened. The exact test-side composition remains
unmeasured. Do not describe this investigation as proving a single cause for
every control's dev/test difference.

## 1. What actually changed?

Metric throughout: HT-weighted positive-versus-unlabeled concordance; 0.5 is
chance ranking, not 50% biological classification accuracy. The matched controls
below are **fixed formulas**, not trained neural competitors. The 650M neural
architecture rivals were not evaluated on the final test.

| Frozen scorer | Development C3 | Original test C3 |
|---|---:|---:|
| Within-pair 3-mer cosine | 0.644683 | 0.493970 |
| Training-edge 3-mer interolog | 0.635701 | 0.484037 |
| Sequence-length ratio | 0.660880 | 0.549302 |
| Sequence-length sum | 0.520454 | 0.327235 |
| Affine PLM ensemble | 0.784142 | 0.789249 |
| Deterministic hash sentinel | 0.494233 | 0.491139 |

The development 3-mer 95% component interval already includes chance:
[0.498094, 0.726463]. Its test interval is [0.413882, 0.565829]. Interolog intervals
are [0.525749, 0.754754] and [0.425706, 0.574571]. These are marginal intervals;
their overlap neither proves nor disproves a dev/test difference. We did not
calculate a formal difference interval, and did not treat different dev/test
proteins as paired observations. A million sampled U rows does not create a
million independent biological validation units.

## 2. Scoring parity passed

Across **all 1,002,265 development C3 rows** (2,265 P; 1,000,000 U), recomputed
length, 3-mer and CUDA interolog controls exactly matched the saved development
scores: maximum absolute difference **0**. The actual frozen protected CPU
scorer, exercised only on development data, also matched all five checked
deterministic controls exactly over **10,457 rows**: all positives plus 8,192
fixed, evenly spaced U rows. This includes the hash/identity sentinel.

All six published development point estimates were reproduced within
1.44e-11. The original five component-bootstrap intervals were reproduced
within 1e-12. Endpoint order, component indices and input hashes were checked.
This strongly argues against a CPU/GPU/formula mismatch as the explanation;
it is not an independent re-audit of private test truth joins.

## 3. The largest-component hypothesis did not hold up

Development's largest frozen sequence component has 643 proteins; test's has
111. That initially looked like the obvious explanation. It was not supported
by the removal sensitivity: removing **both P and U pairs** touching the
643-protein component increased every investigated control's point estimate.

| Development-only sensitivity | P retained | 3-mer | Interolog | Length ratio | Affine PLM |
|---|---:|---:|---:|---:|---:|
| Original full C3 | 2,265 | 0.644683 | 0.635701 | 0.660880 | 0.784142 |
| Exclude pairs touching largest component (643 proteins) | 1,167 | 0.664688 | 0.695720 | 0.692719 | 0.823112 |
| Exclude pairs touching third-largest component (61 proteins) | 1,573 | 0.605088 | 0.567174 | 0.618482 | 0.778008 |
| Exclude pairs touching either of those components | 582 | 0.535518 | 0.562986 | 0.592514 | 0.776618 |
| Between-component pairs only | 1,440 | 0.534520 | 0.592286 | 0.595428 | 0.740051 |

Every exclusion applies to **both P and U**. These are changed-population
sensitivities, not replacement benchmark scores. The first removal was planned
before this analysis; the other three were explicitly data-informed follow-ups.
The full results retain all component influences, not just favorable examples.

## 4. What does explain the development signal?

### 3-mer: within-component positives dominate its excess over chance

Within-component pairs make up **825/2,265 positives (36.4%)**, but only
**6.61% of HT-weighted U mass**. Against the same full U reference, 3-mer
concordance is **0.873516** for these positives and only **0.513580** for the
remaining 1,440 between-component positives.

The exact positive-group decomposition is:

`0.644683 = (825/2265 × 0.873516) + (1440/2265 × 0.513580)`.

Consequently, within-component positives account for **94.0% of development's
3-mer excess over 0.5**. This is an arithmetic contribution, **not** 94% of the
dev/test gap, a causal effect, or an explanation of 94% of individual predictions.
When both P and U are restricted to between-component pairs, 3-mer scores
0.534520 [0.467170, 0.590161], versus affine PLM
0.740051 [0.697786, 0.799655].

"Component" means the repository's frozen sequence-similarity graph group.
It need not be a single biological family or imply that every member is
directly homologous to every other member. Concentration inside a held-out
component is not itself train/test leakage. This analysis does not strengthen
the graph's homology-detection guarantees.

### Interolog: a smaller, interaction-rich component matters much more

The third-largest component contains only **61 of 2,550 development proteins
(2.39%)**, but **692 positives (30.55%)** touch it, versus **4.72% of U mass**.
Of these, 372 positives have both endpoints inside it; only 430 sampled U pairs
do. Positives touching this component score **0.811331** against the full U
reference, compared with **0.558438** for all other positives.

Those 692 positives contribute **70.1% of the interolog control's development
excess over chance**. Removing their component from both P and U reduces
interolog from 0.635701 to **0.567174 [0.501577, 0.619920]**. The affine PLM
changes much less: 0.784142 to **0.778008 [0.736049, 0.813064]**.

After excluding both the 643- and 61-protein components, 3-mer and interolog
intervals include chance: [0.460097, 0.606912] and [0.482505, 0.635072]. Affine
PLM remains at **0.776618 [0.728600, 0.823923]**. This supports differential
robustness on these development sensitivities, not universal PLM superiority.

## 5. Length and source checks prevent an overly simple story

**Length alone is not an adequate demonstrated explanation.** Matching P/U
comparisons within ten fixed, unordered endpoint-length bins (boundaries 200,
500 and 1,000 residues; 100% P coverage) does not remove the control signal:
3-mer is 0.676796, interolog 0.665245 and affine PLM 0.778967. Coarse binning is
not exact adjustment, and these values use a different, conditional estimand.
The test length-sum reversal to 0.327235 is evidence of changed score/label
association; whole-partition protein-length summaries alone cannot explain it.

**Source mixture alone is also insufficient.** The decline occurs inside the
published HuRI-exclusive stratum: 3-mer 0.652732 → 0.471040; interolog
0.627836 → 0.472572. Within development, 652/1,677 HuRI-exclusive positives are
within-component, compared with 54/312 HI-II-14-exclusive positives. Of the
372 positives internal to the 61-protein component, 310 are HuRI-exclusive,
13 HI-II-14-exclusive and 49 shared. Thus source labels conceal substantial
component-level composition; holding the source name constant need not hold
the protein/pair population constant.

The matched controls are much steadier on C1: 3-mer 0.517473 → 0.524181 and
interolog 0.620921 → 0.633114. Their larger C3 changes are consistent with
cohort-dependent sequence shortcuts, not ordinary overfitting of fitted
parameters in these deterministic controls. Sampling variation and residual
cohort differences remain part of the explanation, especially for interolog
and length ratio, whose development signal does not disappear completely.

## 6. Interpretation and unchanged project status

The useful conclusion is **not** that development was invalid or the controls
are broken. It is that their apparent strength is sensitive to which sequence
groups and positive interactions occupy a held-out cohort. The earlier
"one huge component explains it" conjecture should be replaced with the
measured within-component and smaller-component concentration findings.

These diagnostics support confidence that the affine result is not simply the
same narrow control shortcut, but do not establish genuine partner specificity,
direct binding, absence of residual homology, or generalization to every future
protein distribution. Do not repair this benchmark by deleting difficult groups
or flipping length-score directions after seeing test performance.

The optimized three-seed ensemble remains the **best-performing model by
observed benchmark score**; the affine ensemble remains the **original
confirmatory baseline**. Neither was refit or selected here. The optimized
ensemble was not rescored in this investigation. Existing test outcomes,
including the inconclusive C3 superiority interval, remain unchanged.

## Evidence and reproducibility

- [Initial scope](../../protocols/C3_CONTROL_SHIFT_INVESTIGATION_v1.md) and
  [explicit data-informed supplement](../../protocols/C3_CONTROL_SHIFT_COMPONENT_SUPPLEMENT_v1.md).
- [Initial results](../../../artifacts/results/c3_control_shift_investigation_v1/RESULTS.json)
  and [component supplement](../../../artifacts/results/c3_control_shift_investigation_v1/COMPONENT_SUPPLEMENT.json),
  including every one of the 353 positive-participating development components.
- [Analysis](../../../scripts/analysis/c3_control_shift_v1.py),
  [supplement](../../../scripts/analysis/c3_control_shift_components_v1.py), and
  [allowlisted-mount runner](../../../scripts/analysis/run_c3_control_shift_v1.sh).
- [Artifact registry](../../../artifacts/results/c3_control_shift_investigation_v1/ARTIFACT_REGISTRY.json)
  and [validation directory](../../../artifacts/validation/c3_control_shift_investigation_v1).

Both analyses used an actual NVIDIA GH200 with the checksum-pinned ARM64 model
image (`c4bddf5f…aad91`), CUDA 13 and FP64 control/metric arithmetic. Core analysis
times were 18.10 and 13.90 seconds, including 2,000 component-bootstrap replicates
per reported sensitivity. Original component draws are retained across subsets;
intervals are descriptive, component-conditional and not multiplicity-adjusted.
No test-pair, truth, prediction archive or key mount was provided to either
analysis. Separate read-only integrity checks verify both model bundles and
the 210 historical registered entries before and after.

Reproduce into a **new** output directory from the repository root:

```bash
task_output=$(mktemp -d)
bash scripts/analysis/run_c3_control_shift_v1.sh first "$task_output"
bash scripts/analysis/run_c3_control_shift_v1.sh supplement "$task_output"
```

Private development caches and the pinned image must already be present.
The supplement is bound to the recorded initial result; timestamps and elapsed
times differ on replay. Existing outputs are never overwritten. Qualification
includes synthetic weighted ties, endpoint-access guards, component retention,
length-bin coverage, frozen scorer tests and aggregate/source-hash consistency.
The final targeted suite passed **38 tests**. An initial invocation named a
nonexistent test file and ran zero tests; its empty `UNIT_TESTS.xml` is retained
alongside the successful intermediate and final records.
