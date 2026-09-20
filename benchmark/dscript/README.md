# D-SCRIPT benchmark

Status: **original and retrained C1/C2/C3 evaluations are complete**. The retrained
three-seed ensemble selected epoch 4 using C3 development and completed evaluation
on 18 September 2026. Its C1/C2/C3 concordance is
**0.504429 / 0.481321 / 0.511437**. All seeds are reported, including the weak
third seed. See [retrained results](results/retrained-v1/RESULTS.md),
[paired comparisons](results/retrained-v1/paired_differences.csv), and the
[cross-method index](../README.md). [RETRAINING_REPORT.md](RETRAINING_REPORT.md)
preserves the frozen recipe and dated startup/job history.

Original `human_v1` evaluation remains completed and verified (job 2338739; 2026-09-12): all 3,019,012 rows retained, with weighted P-versus-U concordance **0.462863 / 0.439297 / 0.498680**. See [original report](ORIGINAL_EVALUATION_REPORT.md) and [original comparison CSV](results/original-v1/scores.csv). These original results are unchanged.

Read [REPORT.md](REPORT.md) for the earlier native-image qualification: **98 selected upstream tests passed**. The unmodified released predictor fails above 2,000 residues. The separately qualified compatibility adapter extends its nonlearned positional array and tiles contact-map computation without cropping, row exclusion, or changes to learned parameters. The SIF and its upstream source remain unchanged.

Image: `../containers/images/dscript-native-arm64-v1.sif`. Native model identity: original **`human_v1`**, with **Bepler–Berger `lm_v1`** embeddings (6,165 features per residue). Native CLI prediction must explicitly set `--model /opt/dscript/weights/human_v1_hf`; its upstream default is Topsy-Turvy, not the original D-SCRIPT.

Re-run the synthetic-only image tests with `bash benchmark/dscript/test_container.sh` from the repository root. Each new run has its own output directory and scope snapshot; the original build-scope audit is preserved separately.

Upstream: [official repository](https://github.com/samsledje/D-SCRIPT).

Required comparison: authors' original released predictor and a separately identified predictor retrained on iPIN TRAIN, each evaluated on the identical C1/C2/C3 test cells against the frozen baseline and optimized iPIN ensembles. Development data alone determine retraining choices. Original-checkpoint interaction exposure is disclosed; an original training objective is not an original pretrained model.

All candidate-specific code, configurations, downloads, data, weights, runs, logs, and reports belong in this directory. Shared containers belong in `../containers/`; reuse of an existing read-only repository SIF requires recorded dependency and numerical qualification. Existing repository data/models are read-only inputs.

If an original checkpoint is unavailable or cannot be reproduced faithfully, report that limitation explicitly rather than substituting a newly trained model under the original label.
