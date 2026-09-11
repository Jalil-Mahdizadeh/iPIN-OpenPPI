# Development-only model optimization v1

2026-09-11 · [DEC-0052](../../../governance/decisions/DEC-0052-development-only-optimization-and-conditional-followup.md)
· [Prospective protocol](../../protocols/MODEL_OPTIMIZATION_v1.md)
· [Machine-readable results](../../../artifacts/results/model_optimization_v1/RESULTS.json)

## Outcome

The best three-seed ensemble improved C3 development PU concordance from
**0.784142 to 0.799419**: gain **0.015277**, paired 95% component-bootstrap
interval **[0.002942, 0.034460]**. This is a promising ensemble-level improvement.
However, it failed the prospectively fixed seed-stability rule. **No follow-up
test was run, no follow-up ledger was reserved, and the original baseline and
test records remain unchanged.** The baseline remains the test-evaluated reference;
the new ensemble is a development-selected candidate, not its validated replacement.

## What ran

Twenty-four fixed recipes crossed two existing frozen encoders (ESM-2 150M and
650M) with linear, MLP, residual-MLP and low-rank bilinear heads. Learning rates,
weight decay, hidden widths/ranks and dropout varied according to the frozen
configuration. The four highest three-epoch C3 scores advanced to new eight-epoch
fits with three seeds; selection compared raw-score ensembles at epochs 4 and 8.
All 36 fits and 168 epochs completed on an **NVIDIA GH200 120GB GPU**. The GPU
search process used **175.4 seconds**, comfortably within the two-hour cap;
cached encoder embeddings made these small heads inexpensive. This excludes
CPU data preparation, documentation and separate verification work.

Training used all 16,799 frozen P and 2,000,000 U rows, original design weights,
a P-versus-U ranking loss, manifest-based embedding identity joins, and no
development gradients. C3 development contained 2,265 P and 1,000,000 U rows.
The optimization process had no protected test packages, keys or predictions
mounted. No encoder inference, new data, split changes or negative labels.

| Promoted recipe | Parameters/head | Epoch 4 ensemble | Epoch 8 ensemble |
|---|---:|---:|---:|
| 150M residual MLP, width 256 | 498,053 | **0.799419** | 0.793845 |
| 150M MLP, width 256 | 496,131 | 0.799379 | 0.791192 |
| 650M MLP, width 64 | 253,635 | 0.794405 | 0.787535 |
| 150M retuned linear | 1,922 | 0.786004 | 0.784068 |

The selected residual MLP uses learning rate 1e-4, weight decay 0.01, dropout
0.3, and epoch 4 of the eight-epoch schedule. The plain MLP is only 0.000040
behind: this does **not** establish an advantage for the residual architecture.
Architecture and training recipe changed together; this is not a clean causal
architecture ablation. All four promoted recipes scored lower at epoch 8 than
epoch 4, supporting attention to regularization/training duration in any future
authorized study. The fixed search ended here despite unused compute budget.

## Why the retest gate failed

| Seed | Original baseline | Selected candidate | Gain |
|---|---:|---:|---:|
| 20260803 | 0.780285 | 0.798612 | +0.018326 |
| 20260817 | 0.784857 | 0.781421 | −0.003437 |
| 20260831 | 0.783082 | 0.777405 | −0.005677 |

The ensemble gain and its paired interval passed. All 2,000 bootstrap draws
were finite. But two individual seeds lost to their corresponding baseline,
and candidate seed range **0.021207** exceeded the predeclared **0.020000**
limit. Both stability conditions therefore failed. The highest-scoring group
was fixed before computing its gate; there was no fallback to another recipe,
extra seed search, revised threshold or test opening.

Ensembling can improve ranking even when some constituent fits are weaker.
That explains why the positive ensemble result and the failed individual-seed
rule can coexist. The development interval is a post-selection stability
screen, not multiplicity-adjusted confirmatory evidence. This experiment does
not invalidate the original baseline's positive test result, settle direct
binding, or show that further model development is a dead end.

## Protocol, validation and records

DEC-0052 prospectively permits one conditional follow-up on the existing,
already-examined test; it does not call that test fresh or reset its original
spent ledger. The condition was not met in this search. The six prior study
registries, their 148 registered files, original checkpoints, final-test result,
receipt, ledger and completion record are preserved.

The effective search freeze was recorded at **11:08:34 UTC**, before the first
fit at **11:09:27 UTC**. Its SHA-256 is
`c321841b6d79f4ca4256f14f9f7463a5bf3b5dc0085cfa554a1dc3ba4c906f67`.
A preceding pytest-plugin startup failure occurred before any fit or baseline
replay; its bundle and empty-result launch are retained under the documented
[pre-fit technical erratum](../../protocols/MODEL_OPTIMIZATION_v1_PREFIT_TECHNICAL_ERRATUM.md).
The repair disabled unrelated plugin autoload and changed no scientific rule.

Validation: 11/11 isolated GPU fixtures passed; the CPU regression suite had
68 passes and one intentionally skipped GPU case (which passed separately).
Original baseline GPU replay had zero concordance error and maximum score
error 2.74e-6. A separate frozen CPU implementation replayed the full C3 panel
and first 32 bootstrap draws: maximum bootstrap difference **3.06e-12**.
Serial-prefix versus direct-sum normalization explains the **1.47e-11** point
difference; the numerical audit documents this harmless rounding distinction.
All eight ensemble groups and their 24 seed metrics were replayed with zero
metric discrepancy; the full 36-fit/168-epoch census, fixed promotion rule,
source freeze and byte-identical aggregate publication also passed audit.
These are same-author implementation checks, not independent replication.

Artifacts: [selection](../../../artifacts/results/model_optimization_v1/SELECTION.json),
[gate](../../../artifacts/results/model_optimization_v1/DEVELOPMENT_GATE.json),
[search freeze](../../../artifacts/validation/model_optimization_v1/SEARCH_FREEZE.json),
[completed audit](../../../artifacts/validation/model_optimization_v1/COMPLETED_SEARCH_AUDIT.json),
[full-census audit](../../../artifacts/validation/model_optimization_v1/FULL_CENSUS_AUDIT.json).
Private checkpoints, row scores, bootstrap draws and prepared arrays remain in
`.private/model_optimization_v1/`. The prepare module, guarded GPU launcher and
aggregate publisher are versioned separately from every original frozen script.

## Scientific framing

The strongest established result remains the simple frozen-PLM model's C3 PU
ranking on interaction-training-naïve proteins; network shortcuts remain strong
when endpoints have prior interaction exposure. Partner specificity and direct
binding remain open questions. BioPlex is now secondary cross-assay evidence,
not a binary-binding verdict or an optimization gate: AP-MS includes both
direct and indirect co-complex associations, as the original
[BioPlex study](https://pmc.ncbi.nlm.nih.gov/articles/PMC8165030/) explicitly
demonstrates. Its historical negative findings have not been erased.

Recommendation: preserve the baseline and this candidate. If further work is
authorized, focus a prospectively defined study on reproducible ensemble gains
and regularization, rather than interpreting the near-tied architecture ranking
as a mechanistic discovery. No additional search or test is queued automatically.
