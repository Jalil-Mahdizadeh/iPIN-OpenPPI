# Selected 31k model on the fixed 12-target panel

Inference-only comparison of the selected 31,188-positive, epoch-1, three-seed
TUnA ensemble against the four archived predictors on
`example/twelve_target_comparison_v2`: 5,587 pairs, 37 P and 5,550 U.

Read [the report](output/REPORT.md), [primary metrics](output/primary_comparison.csv),
or [the comparison plot](output/comparison.png). Full scores, positive ranks,
per-target comparisons, and exposure sensitivities are in `output/`.

All new files are confined to this experiment. Original panel data, models,
results, and the scaling study remain unchanged. The historical residue
embeddings are reused after hash validation; model-specific features are
recomputed for each selected checkpoint. The exact saved GP covariance is
preserved by setting its fitted flag before evaluation mode.

`INPUT_FREEZE.json` records dependencies; `output/SCORING_RUN.json` and
`output/VALIDATION.json` record scoring and metric checks. `PRESERVATION.json`
records the final input-hash verification and output inventory.

The archived panel is not an independent benchmark. Its original exposure
sensitivities remain available, with additional common exclusions for pairs
present in the 31k training or selection-development data. U is unlabeled.

Run phases are `bash run.sh prepare`, `bash run.sh score`,
`bash run.sh compare`, and `bash run.sh verify`. Completed outputs are
exclusive-create; the commands intentionally refuse to overwrite this run.
