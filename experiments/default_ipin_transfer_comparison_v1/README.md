# Default iPIN transfer comparison

This experiment applies the registered **iPIN-TUnA-31k** default to the existing
six-species and human–laboratory-yeast PU panels. All historical inputs remain
unchanged. The directory contains everything new from this request.

Read [REPORT.md](REPORT.md) for results, [PROTOCOL.md](PROTOCOL.md) for the fixed
comparison, and `PRESERVATION.json` / `FINAL_MANIFEST.json` for completion and
checksums. The model is the immutable v3 three-seed, 31,188-P, epoch-1 ensemble.

## Reproduction

On the allocated ARM64 GPU node with the existing private model bundles,
archived studies, expanded training/development data and pinned TUnA image,
copy only `scripts/`, `run.sh`, `PROTOCOL.md` and this README to a new sibling
directory under `experiments/`. Each phase refuses to overwrite its outputs.
From the repository root, replacing the directory name with that new sibling:

```bash
bash experiments/default_ipin_transfer_comparison_v1/run.sh prepare
bash experiments/default_ipin_transfer_comparison_v1/run.sh score
bash experiments/default_ipin_transfer_comparison_v1/run.sh compare
bash experiments/default_ipin_transfer_comparison_v1/run.sh verify
```

The numerical phases use the pinned `tuna-arm64-v1.sif`, one GPU, FP32 with
TF32/autocast disabled, and no network access within the guarded runtime.
The repository is mounted read-only, with only this experiment writable.
The original ESM residue caches are reused after full checksum verification;
learned TUnA endpoint features are recomputed for every seed.

## Outputs

- `primary_comparison.csv`, `primary_paired_differences.csv`, `REPORT.md`, and
  `comparison.png` / `comparison.pdf`: direct comparisons with the three old models.
- `nonhuman_transfer_v1/` and `reference_organism_pu_transfer_v1/`: all member and
  ensemble scores, learned features, per-target/per-P metrics, rank tables,
  paired intervals, exposure/coverage audits and historical replay validation.
- `INPUT_FREEZE.json`, `PREDICTION_FREEZE.json`, `METRIC_VALIDATION.json`,
  `ANALYSIS_COMPLETE.json`, `PRESERVATION.json`, `FINAL_MANIFEST.json`: provenance
  and completion evidence. Runtime caches and temporary files stay here too.

The default has already been selected; this experiment makes no model,
checkpoint, threshold or species-specific tuning decision. U is unlabeled,
not confirmed negative. Original metric weighting and the two original
exposure cohorts are preserved. A third cohort applies the same expanded
exact-exposure exclusions to every predictor. See the protocol for limitations.

