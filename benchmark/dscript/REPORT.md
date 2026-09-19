# D-SCRIPT benchmark report

## Current stage: matched-data retraining and automatic testing

The user authorized D-SCRIPT retraining and subsequent C1/C2/C3 evaluation. The native SIF and full-residue cache are qualified, and the training/selection/test protocol is frozen. **All three fresh PPI heads are training healthily on distinct GPUs** in job **2342911**: at least 9,472 comparisons per seed, finite losses/gradients, declining early loss, and verified recovery checkpoints. Eight epochs are planned; C3-DEV alone chooses epoch 4 or 8 for the three-seed ensemble. Four two-epoch Slurm stages each have a 72-hour limit, followed by 24-hour selection and test jobs. The final test job is **2342916**. Monitoring is paused as requested; the job chain continues.

See [RETRAINING_REPORT.md](RETRAINING_REPORT.md) for the declared PU objective, native regularizer, qualification, timing estimate, job chain and startup status. Original D-SCRIPT results below are preserved; no retrained test metric is available yet.

## Completed stage: original-checkpoint test comparison

**Completed and verified: original D-SCRIPT evaluation on C1/C2/C3, before any retraining.** Job 2338739 completed successfully on 2026-09-12, with finite predictions for all 3,019,012 requested pairs and no cropping or row exclusion. The length-safe adapter preserves the original `human_v1` learned weights and native Bepler–Berger embeddings.

| Model | C1 | C2 | C3 |
| --- | ---: | ---: | ---: |
| Original D-SCRIPT | 0.462863 | 0.439297 | 0.498680 |
| Baseline iPIN | 0.843493 | 0.805299 | 0.789249 |
| Optimized iPIN | 0.916037 | 0.851301 | 0.807948 |

Metric: design-weighted positive-versus-unlabeled concordance, not confirmed-positive-versus-confirmed-negative AUROC. Original D-SCRIPT shows poor off-the-shelf transfer here: its primary C3 difference from optimized iPIN is **−0.309268**, paired 95% component-bootstrap interval **[−0.390123, −0.207965]**. Both iPIN models are ahead in all three panels. This does not establish how a D-SCRIPT model retrained on iPIN TRAIN would perform.

See [ORIGINAL_EVALUATION_REPORT.md](ORIGINAL_EVALUATION_REPORT.md) for all intervals, interpretation, full-coverage checks, native-score fidelity, runtime and the external-training exposure caveat. Full-precision [scores](results/original-v1/scores.csv) and [paired differences](results/original-v1/paired_differences.csv) are saved. Historical iPIN reference metrics reproduced exactly; 24 post-run native end-to-end spot checks matched the saved predictions exactly. The frozen-artifact and repository-scope audits passed.

That earlier stage stopped after original-model reporting. The newly authorized retraining stage is recorded above and does not alter these original results.

## Earlier stage: native container qualification

The remainder records the earlier container-only checkpoint; its stop point and then-unimplemented next steps are historical. The current authorized stage is described above.

Date: 2026-09-12. Scope: build and test the dedicated SIF, then report before proceeding. No retraining, benchmark embedding extraction, or C1/C2/C3 evaluation is authorized by this stage.

## Status

**SIF built and container qualification passed on the Arrhenius GH200.** All nine qualification checks completed, including characterization of a known upstream length limit; **98 selected upstream unit tests passed, with zero failures or skips**. This is installation/numerical qualification, not evidence of predictive performance on iPIN.

**Not yet ready for unrestricted full-length benchmarking:** the unmodified predictor fails when a protein exceeds 2,000 residues. No patch, cropping or row exclusion has been applied. Work stops here for the user's review.

Image size: **11,045,695,488 bytes** (approximately 10.29 GiB). SHA-256:

```text
bfcee514eeb908a05bde701f230066baca9fb45fab2a811732f8e16a14a3912c
```

## Native model identity and environment

- Published D-SCRIPT Python package **0.3.1**, installed from its SHA-256-pinned PyPI wheel. Upstream model source is not patched.
- Original predictor **`human_v1`**, not the package default `human_v2` / Topsy-Turvy. The original state dictionary and the authors' Hugging Face export are both bundled for offline loading and equivalence testing.
- Native **Bepler–Berger `lm_v1`** encoder: 6,165 FP32 features per residue from the three-layer bidirectional SkipLSTM `transform` output. No ESM substitution or pooled embeddings.
- ARM64 image derived read-only from `containers/images/ipin-model-arm64_0.1.0.sif`, whose verified SHA-256 is `c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91`.
- Runtime retains Python 3.12, NVIDIA PyTorch 2.8.0a0 and NumPy 1.26.4. Added packages: `dscript==0.3.1`, `biotite==1.2.0`, `biotraj==1.2.2`, `h5py==3.14.0`, `loguru==0.7.3`, `seaborn==0.13.2`, `packaging==24.2`.
- Biotite and biotraj require local ARM64 wheel builds. Their upstream-required NumPy 2 headers are confined to the build virtual environment; NumPy 2 is not installed into the runtime. Resolved build dependencies are archived in a SHA-256-verified offline lock.

Primary sources: [D-SCRIPT 0.3.1 on PyPI](https://pypi.org/project/dscript/0.3.1/), [release source](https://github.com/samsledje/D-SCRIPT/tree/0b3f7363b7d62fb99f5c8bfc6780833f088b8d84), [native pretrained loaders](https://github.com/samsledje/D-SCRIPT/blob/0b3f7363b7d62fb99f5c8bfc6780833f088b8d84/dscript/pretrained.py), [authors' original human predictor](https://huggingface.co/samsl/dscript_human_v1/tree/907ea0b745b1a555b19f2b3e73f2d98963caf365).

## Reproduction and artifacts

From the repository root:

```bash
bash benchmark/containers/build_dscript.sh
bash benchmark/dscript/test_container.sh
```

The build refuses to overwrite an existing SIF. The test command creates a new output directory and fresh scope snapshot each time; it does not reuse the old build snapshot to judge later legitimate repository changes. Rebuilding needs the unchanged parent image, recipe, downloads and wheel lock; rebuilt compressed-image hashes need not be bit-for-bit identical because build timestamps can change.

- Image: `../containers/images/dscript-native-arm64-v1.sif`.
- Build recipe: [dscript-native-arm64-v1.def](../containers/dscript-native-arm64-v1.def).
- Build script: [build_dscript.sh](../containers/build_dscript.sh).
- Build log: `../containers/logs/dscript-native-v1-build.log`.
- Download identity: [dscript-downloads.json](../containers/manifests/dscript-downloads.json).
- Compiler dependencies: [dscript-build-requirements.lock](../containers/manifests/dscript-build-requirements.lock), [wheel provenance](../containers/manifests/dscript-build-wheels.json).
- Runtime wheels and image: `../containers/manifests/dscript-runtime-wheels.sha256`, `../containers/manifests/dscript-sif.sha256`, `../containers/manifests/dscript-inspect.json`.
- Tests: [test_container.sh](test_container.sh), [qualify_native.py](scripts/qualify_native.py).
- Completed qualification: [machine-readable results](qualification/sif-test-FK64Hy78/qualification.json), [upstream test log](qualification/sif-test-FK64Hy78/upstream-tests.log), [synthetic diagnostic scores](qualification/sif-test-FK64Hy78/synthetic-scores.csv).
- Repository preservation: [build-scope audit](provenance/repository-sif-audit.json), [unchanged parent image checksum](provenance/parent-image-after.sha256).

PyPI artifacts are checked against pinned registry SHA-256 values. Original model files were downloaded over official HTTPS endpoints; their hashes were recorded locally and pinned for reuse. Those local hashes are not represented as independently published author checksums. The Hugging Face export is revision-pinned. This is a local research image, not a licensing/redistribution clearance.

## Tests and limitations

Qualification uses three deterministic synthetic sequences and synthetic boundary probes. It does not mount the repository's datasets, iPIN models or test labels. Python TCP/IP connections are actively denied during the qualification, including native CLI subprocesses. This tests offline Python execution; it is not an OS-wide network security boundary.

Qualification ran on 2026-09-12, 19:29:43–19:30:04 UTC. CUDA 13.0 / NVIDIA PyTorch `2.8.0a0+34c6371d24.nv25.08` recognized the GH200. TF32 was disabled for these numerical checks. The main qualification process peaked at **1.006 GiB of allocated GPU memory**; this does not include subprocess peaks and is not a full-training or worst-case pair-memory estimate.

| Check | Result |
| --- | --- |
| ARM64/GPU and declared added dependencies | Passed |
| Installed upstream Python source vs published wheel | All **34 files byte-identical** |
| Original `.pt` vs authors' Hugging Face export | All **21 state entries bit-identical**; predictor settings matched |
| Native embeddings, synthetic lengths 32/47/101 | `[1, L, 6165]`, finite; CPU/GPU maximum absolute difference **2.43 × 10⁻⁶** |
| Direct encoder `transform` vs native convenience API | Bit-identical CPU output |
| Original predictor, four synthetic pair rows | Finite scores in [0,1]; CPU/GPU maximum absolute difference **4.66 × 10⁻¹⁰** |
| Legacy/Hugging Face inference, repeated GPU inference | Bit-identical on tested inputs; reversed-pair score difference zero |
| Offline native `embed` + `predict_serial` | All **4/4** requested rows retained, including reversal and self-pair |
| Offline native blocked `predict`, single GPU | **3/3** unique non-self pairs, matching direct inference |
| Encoder length probes | 2,000, 2,001 and **7,570 residues** succeeded without cropping |
| Native predictor boundary | 2,000 × 32 residues succeeded; **2,001 × 32 failed** with positional-array size mismatch |
| Selected upstream unit suite | **98 passed**, zero failures/errors/skips |
| Repository preservation | **1,842 files outside `benchmark/` unchanged**, plus parent-SIF checksum unchanged |

The selected upstream suite covers alphabets, embedding/contact/interaction modules and the original checkpoint builders. The full upstream command/training suite was intentionally not run: it includes training and other model variants outside this request. Gradient-flow unit tests do not perform optimizer steps. Synthetic score CSVs are installation diagnostics, not biological validation or performance estimates.

The current upstream predictor contains a 2,000-element positional array (`xx`). The boundary probe produced: `The size of tensor a (2001) must match the size of tensor b (2000) at non-singleton dimension 2`. This is an implementation limitation of the pinned release, not a claim that the scientific architecture fundamentally requires short proteins. The Bepler–Berger encoder itself produced full-length embeddings at 7,570 residues. No native source was changed.

Recommended next step, **not implemented**: a separately documented length-safe compatibility adapter that generates/extends this positional index for the actual sequence length, with exact-agreement tests on all supported short sequences and full-length resource tests before deployment. Avoid silent cropping or removing long-protein pairs, which would change the comparison. Encoder success at 7,570 residues does not prove that a 7,570 × 7,570 contact-map prediction or its training backward pass fits memory.

The newer blocked `dscript predict` command canonicalizes/deduplicates pair inputs and its ordinary self-block loop excludes self-pairs. Its writer expects the original input row count. Therefore duplicate/reversed or self-pair input is not qualified for that route; the serial CLI is tested separately for row preservation. This is based on source inspection, not a deliberate hang test. Any later benchmark adapter must enforce complete row coverage and reject missing/non-finite predictions.

## Stop point

Stopped after qualification for the user's review. The next stage would require a declared long-sequence strategy, a row-safe benchmark adapter, embedding/cache planning, and TRAIN/DEV-only retraining configuration before any final test scoring. No such work is started here. No new Slurm job was submitted, no iPIN model or dataset was changed, and no benchmark training/evaluation process remains running.

Build notes: the initial dependency-fetch attempt needed an explicit read-only host DNS configuration bind inside the contained build environment; the retry succeeded. Apptainer completed the SIF and its build-time tests, but an edit to the running shell wrapper interrupted its subsequent checksum-export step. The manifests were generated separately, the saved script passed `bash -n` and ShellCheck, and the completed SIF then passed its checksum and all runtime qualification checks. Build-time Matplotlib cache warnings were nonfatal; qualification uses a dedicated writable cache under its output directory. These packaging issues did not involve model training or benchmark evaluation.
