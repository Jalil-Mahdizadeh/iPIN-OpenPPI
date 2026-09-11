# Benchmark and protected-evaluation utilities

## Fixed-ensemble follow-up (DEC-0053)

The [follow-up protocol](../../docs/protocols/MODEL_OPTIMIZATION_FOLLOWUP_v1.md)
authorizes one comparison of the existing development-selected residual-MLP
ensemble against the original baseline ensemble, without further fitting.

- `prepare_model_optimization_followup_v1.py` checks historical integrity,
  qualifies exact frozen checkpoint replay on the GPU and CPU using development
  data, and freezes an allowlisted scorer bundle before test-pair access.
- `run_model_optimization_followup_v1.sh` exposes the separate stages
  `preflight`, `open`, `score`, `import-baseline`, `freeze-predictions`, `reserve`,
  `evaluate`, and `publish`. The frozen bundle's copy is the executed operator.
- `model_optimization_followup_core_v1.py` scores only the fixed candidate,
  imports the original baseline predictions byte-for-byte, and reuses the
  unchanged original paired component-bootstrap implementation.
- `publish_model_optimization_followup_v1.py` permits only aggregate metrics
  and a separate follow-up receipt/completion record; it sees no row data or keys.
- `audit_model_optimization_followup_v1.py` checks the completed lineage,
  historical hashes, stored bootstrap arithmetic and document consistency
  without another decryption or scoring pass.
- `normalize_followup_guard_log_v1.py` preserves raw UCX-prefixed probe stdout
  and extracts its unchanged JSON attestation. This is a logging-only adapter,
  not a change to the frozen guard or scientific evaluator.

These are one-attempt study operators, not instructions to rerun a completed
evaluation. A reservation consumes the follow-up even after failure. Never
delete custody markers, overwrite frozen records, rerun the spent original
`run_protected_final_test_v1.sh`, or invoke legacy development audits as current
authorization checks. Their historical no-follow-up assertions are superseded
only by the explicit DEC-0053 amendment; their sources and records stay intact.

Protected scoring uses the original restricted CPU Apptainer boundary; the GPU
is required for the pre-access model replay. Larger artifacts, checkpoints and
all protected rows remain private. See the
[completed report](../../docs/reports/m1/M1_Model_Optimization_Followup_v1.md).

## Historical label-free benchmark-design stage

These thin CLIs support the label-free benchmark-design stage. Reusable logic
lives under `src/ipin_openppi/benchmark/` and
`src/ipin_openppi/validation/`.

- `audit_systematic_screen_metadata.py` inventories the frozen HuRI and
  control-panel metadata without constructing labels or splits.
- `validate_systematic_screen_metadata_audit.py` independently recomputes
  the production audit metrics from immutable staged Parquet.
- `validate_estimand_policy_proposal.py` checks that the PU-ranking
  proposal, blueprint amendment, blockers, and review gate remain internally
  consistent and non-effective pending expert approval.
- `audit_benchmark_eligibility_and_sequence_components_v1.py` executes the
  governance-bounded Space III reference-sequence eligibility audit, algebraic
  candidate count, and deterministic 40%/30%/20% component construction.
- `validate_benchmark_eligibility_and_sequence_components_v1.py` independently
  recomputes eligibility, parses the raw MMseqs2 output, reconstructs every
  component, and validates aggregate positive-evidence coverage. It emits no
  biological pair rows, labels, C1/C2/C3 assignments, or splits.
- `audit_pre_split_feasibility_and_leakage_v1.py` performs the bounded,
  aggregate-only positive-network, allocation-opportunity, full-length
  sensitivity, and local/domain leakage stress-test authorized by `DEC-0019`.
- `validate_pre_split_feasibility_and_leakage_v1.py` independently reparses both
  raw searches, rebuilds all nine 40%/30%/20% leakage graphs, repeats the
  ephemeral allocation trials, and enforces the no-pair/no-label/no-split
  boundary.
- `construct_final_benchmark_component_split_v1.py` executes the model-free,
  preregistered `DEC-0021` allocator and freezes endpoint/component partitions
  under 30% `local_domain_union`, using 30% `sensitive_fl80_union` only after
  an explicitly recorded zero-valid-primary result.
- `validate_final_benchmark_component_split_v1.py` independently rebuilds both
  graphs, repeats all 4,096 deterministic candidates and the frozen objective,
  and verifies every assignment and aggregate opportunity/source/hub count.
- `audit_pair_level_pu_r_benchmark_protocol_v1.py` freezes and aggregate-checks
  the model-free pair-level PU-R protocol authorized by `DEC-0023`, including
  information visibility, deterministic C1/C2/C3 withholding, candidate-count
  algebra, unlabeled-sampling probabilities, metrics, uncertainty, metadata
  holdout support, degree/hub strata, and claim boundaries. It emits no pair or
  candidate rows and realizes no sample.
- `validate_pair_level_pu_r_benchmark_protocol_v1.py` independently reconstructs
  the released-positive union and reimplements the pair hash, exposure guards,
  cell assignments, source-exclusive diagnostics, candidate algebra, sampling
  allocation, and degree/hub summaries.

- `construct_pair_level_pu_r_benchmark_artifacts_v1.py` realizes the exact
  `DEC-0024` positive and sampled-unlabeled rows authorized by `DEC-0025`, writes
  only the public training layer, and encrypts development, protected
  candidates, and protected truth under distinct keys.
- `validate_pair_level_pu_r_benchmark_artifacts_v1.py` independently decrypts
  and reconstructs the packages, positive/source roles, candidate populations,
  bottom-hash thresholds, probabilities, weights, protected union, hashes, and
  evidence-leakage checks.
- `evaluate_pair_level_pu_r_benchmark_v1.py` implements the gated development
  release and scorer-hash-before-candidate, prediction-hash-before-truth,
  one-first protected evaluator procedure. Construction does not invoke it.

All scientific execution must use the pinned project Apptainer image on
Arrhenius. Smoke outputs must be written only to explicitly named
`_smoke_*` directories and removed after qualification. Production reports are
immutable and written under `artifacts/validation/benchmark_design/`.

Prepare the checksum-pinned ARM64 MMseqs2 binary, then execute and validate from
a clean committed tree:

```bash
apptainer exec --cleanenv --containall --bind "$PWD":"$PWD" --pwd "$PWD" \
  containers/images/ipin-data-arm64_0.1.2.sif env PYTHONPATH=src \
  python scripts/platform/prepare_mmseqs2_v1.py
apptainer exec --cleanenv --containall --bind "$PWD":"$PWD" --pwd "$PWD" \
  containers/images/ipin-data-arm64_0.1.2.sif env PYTHONPATH=src \
  python scripts/benchmark/audit_benchmark_eligibility_and_sequence_components_v1.py
apptainer exec --cleanenv --containall --bind "$PWD":"$PWD" --pwd "$PWD" \
  containers/images/ipin-data-arm64_0.1.2.sif env PYTHONPATH=src \
  python scripts/benchmark/validate_benchmark_eligibility_and_sequence_components_v1.py
```

After `DEC-0019`, execute its child audit and validator from clean commits:

```bash
apptainer exec --cleanenv --containall --bind "$PWD":"$PWD" --pwd "$PWD" \
  containers/images/ipin-data-arm64_0.1.2.sif env PYTHONPATH=src \
  python scripts/benchmark/audit_pre_split_feasibility_and_leakage_v1.py
apptainer exec --cleanenv --containall --bind "$PWD":"$PWD" --pwd "$PWD" \
  containers/images/ipin-data-arm64_0.1.2.sif env PYTHONPATH=src \
  python scripts/benchmark/validate_pre_split_feasibility_and_leakage_v1.py
```

After `DEC-0021`, construct from a clean implementation commit, commit the
production artifacts, and then validate from that clean production commit:

```bash
apptainer exec --cleanenv --containall --bind "$PWD":"$PWD" --pwd "$PWD" \
  containers/images/ipin-data-arm64_0.1.2.sif env PYTHONPATH=src \
  python scripts/benchmark/construct_final_benchmark_component_split_v1.py
apptainer exec --cleanenv --containall --bind "$PWD":"$PWD" --pwd "$PWD" \
  containers/images/ipin-data-arm64_0.1.2.sif env PYTHONPATH=src \
  python scripts/benchmark/validate_final_benchmark_component_split_v1.py
```

After `DEC-0023`, produce the protocol audit from a clean implementation commit,
commit that report, and validate it independently from the resulting clean
production-evidence commit:

```bash
apptainer exec --cleanenv --containall --bind "$PWD":"$PWD" --pwd "$PWD" \
  containers/images/ipin-data-arm64_0.1.2.sif env PYTHONPATH=src \
  python scripts/benchmark/audit_pair_level_pu_r_benchmark_protocol_v1.py
apptainer exec --cleanenv --containall --bind "$PWD":"$PWD" --pwd "$PWD" \
  containers/images/ipin-data-arm64_0.1.2.sif env PYTHONPATH=src \
  python scripts/benchmark/validate_pair_level_pu_r_benchmark_protocol_v1.py
```


After `DEC-0025`, qualify only in explicitly named `_smoke_*` roots. Then commit
the implementation, construct production from that clean commit, commit the
construction report, and independently validate from the resulting clean
production-evidence commit:

```bash
apptainer exec --cleanenv --containall --bind "$PWD":"$PWD" --pwd "$PWD" \
  containers/images/ipin-data-arm64_0.1.2.sif env PYTHONPATH=src \
  python scripts/benchmark/construct_pair_level_pu_r_benchmark_artifacts_v1.py
# Commit CONSTRUCTION_REPORT.json before validation.
apptainer exec --cleanenv --containall --bind "$PWD":"$PWD" --pwd "$PWD" \
  containers/images/ipin-data-arm64_0.1.2.sif env PYTHONPATH=src \
  python scripts/benchmark/validate_pair_level_pu_r_benchmark_artifacts_v1.py
```

Development release and protected scoring/evaluation remain separately gated;
construction must not invoke `evaluate_pair_level_pu_r_benchmark_v1.py`.
