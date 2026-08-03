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

All scientific execution must use the pinned project Apptainer image on
Arrhenius. Smoke outputs must be written only to explicitly named
`_smoke_*` directories and removed after qualification. Production reports are
immutable and written under `artifacts/validation/benchmark_design/`.
