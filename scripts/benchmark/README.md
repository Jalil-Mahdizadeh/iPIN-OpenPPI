# Benchmark-design utilities

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
