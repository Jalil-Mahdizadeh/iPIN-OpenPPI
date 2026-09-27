# Controls on the expanded human benchmark

**Completed on 2026-09-27.** Start with the
[interpretation](results/INTERPRETATION.md), [complete control results](results/RESULTS.md),
and [within-anchor and partner-swap results](results/diagnostics/RESULTS.md).
The [control figure](results/control_scores.png) and
[diagnostic figure](results/diagnostics/partner_diagnostics.png) also have PDF/SVG
versions. Machine-readable scores and paired intervals accompany both reports.

Authorized by the user on 2026-09-27 to fill the missing evaluations before
repository simplification. This follow-up evaluates the manuscript's eleven
fixed controls, two fitted additive endpoint controls, and three additional
homology-transfer controls against the frozen selected 31,188-P TUnA ensemble.
The four transfer kernels include the original 3-mer control.

All new work and results stay in this experiment. Historical data, models,
predictions, evaluation ledgers, results and manuscript files remain unchanged.

The complete C1/C2/C3 development-2 and test-2 panels are evaluated, with the
reconciled legacy and added cohorts reported separately and through the existing
equal-cohort macro. C1 test also excludes development-overlapping identities in
the established sensitivity view. C3 within-anchor ranking and endpoint-balanced
partner swaps compare the same frozen scores.

This is a newly specified follow-up on previously examined data. The eleven
formulas were specified in the original study; their expanded-data evaluation
was not part of the original test2 protocol. U remains unlabeled, and neither
global concordance nor partner swaps establishes direct-binding specificity.
Direct evaluation does not reproduce the historical internal source-restricted
or homology-purged refitting studies.

Read PROTOCOL.json for the frozen definitions. INPUT_FREEZE.json records
verified parents; IMPLEMENTATION_FREEZE.json records executed code; phase
manifests chain features, fitted controls and candidate-only predictions before
test truth is mounted. Aggregate results and validation are published under
results/ and validation/. Pair-level human benchmark artifacts remain local.

[Final validation](validation/VALIDATION.json) passed: 7,547,402 candidate rows,
17 predictors, 1,089 interval/contrast checks, and preservation of all 54 frozen
historical parent files. Eleven synthetic tests passed; existing selected-31k
test2 points and all 2,000 paired draws replay exactly. The independent numerical
check and its documented rounding tolerance are explained in
[validation/README.md](validation/README.md).

See [publication and reproduction scope](PUBLICATION.md) for phase isolation,
local artifacts and reproduction instructions. [COMPLETE.json](COMPLETE.json)
records completion; [PUBLICATION_MANIFEST.json](PUBLICATION_MANIFEST.json)
inventories the compact files retained for review.
