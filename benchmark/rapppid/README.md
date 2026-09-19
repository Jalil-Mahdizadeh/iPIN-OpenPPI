# RAPPPID benchmark

Status: original and user-selected latest-recovery C1/C2/C3 test evaluations completed on 17 September 2026. **Training remains stopped** after job 2578434 failed during epoch 8; the user chose not to restart it. The three unequal-position mid-epoch-8 checkpoints and their fixed mean-logit ensemble were evaluated on all 3,019,012 test pairs. Ensemble concordance is **0.775316 / 0.729804 / 0.700049** on C1/C2/C3, below both iPIN references. See the [latest test report](RECOVERY_TEST_REPORT.md) and [scores/intervals CSV](results/retrained-v1/recovery-test-v1/scores.csv). No further RAPPPID stages are queued.

The [latest recovery C3-development evaluation](results/retrained-v1/recovery-c3-dev-2578434-v2/RESULTS.md) remains unchanged: ensemble **0.699429**, versus **0.692744** at epoch 4. These recovery states are not completed epoch-8 or completed 20-epoch models. See [RETRAINING_REPORT.md](RETRAINING_REPORT.md) for the stopped training experiment and selection disclosures.

Upstream: [official repository](https://github.com/jszym/rapppid).

Completed original comparison: the authors' released `1690837077.519848_red-dreamy` multiplicative-head predictor against the unchanged baseline and optimized iPIN predictions on all 3,019,012 C1/C2/C3 rows. This release is not the paper's concatenation-head checkpoint. The matched-data retraining experiment is separate; original frozen artifacts and results remain unchanged.

Read [REPORT.md](REPORT.md) for the pinned model, native batch-dependence finding, fixed singleton inference policy, numerical qualification, scope and timing. The dedicated image is `../containers/images/rapppid-native-arm64-v1.sif`; its SHA-256 is `e853a89768c5351927f90fd0ccfb2ad899a15a6fc239a9014726af0c34442d48`.

The qualification, scorer freeze and run provenance are in `runs/original-v1/`. [Results](results/original-v1/RESULTS.md) and [scores/intervals CSV](results/original-v1/scores.csv) are in `results/original-v1/`; pair-level predictions remain under `private/original-v1/`. RAPPPID's weighted P-versus-U concordance is **0.5974 / 0.6002 / 0.6071** on C1/C2/C3, below both iPIN references. The scoring-to-publication pipeline took **74.66s on one GH200**, after image/qualification/session preparation. Do not rerun an already opened/completed protected evaluation or modify its frozen bundle.

All candidate-specific code, configurations, downloads, data, weights, runs, logs, and reports belong in this directory. Shared containers belong in `../containers/`; reuse of an existing read-only repository SIF requires recorded dependency and numerical qualification. Existing repository data/models are read-only inputs.

If an original checkpoint is unavailable or cannot be reproduced faithfully, report that limitation explicitly rather than substituting a newly trained model under the original label.
