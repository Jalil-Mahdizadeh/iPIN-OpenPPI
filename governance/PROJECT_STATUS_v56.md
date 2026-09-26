# Project status v56 — iPIN-TUnA-31k is the primary iPIN model

Date: 2026-09-26. Authority: [DEC-0056](decisions/DEC-0056-designate-ipin-tuna-31k-primary-model.md).

The current four-model catalogue is [Frozen pair models v3](../docs/models/FROZEN_PAIR_MODELS_v3.md).
**iPIN-TUnA-31k** (`ipin_tuna_31k_ensemble`) is the primary/default human PPI
predictor. It is the unchanged 31,188-P, epoch-1 ensemble of seeds 20260803,
20260817 and 20260831, retaining the saved GP covariance and published TUnA
architecture attribution. The original affine, optimized pooled and 17k
PU-TUnA models remain historical references with unchanged identities.

The completed 13-predictor test2 comparison covers 3,774,966 candidate rows.
Primary-model C1/C2/C3 macro concordances are 0.886903 / 0.827113 / 0.786652.
The paired C3 gain over historical 17k PU-TUnA is +0.042781
[0.019768, 0.070150]. All 12 paired C3 intervals are positive, pointwise and
unadjusted for multiplicity. PLM-interact leads added C3 alone. Test2 is a
historical follow-up; the twelve-target application also has training exposure.
See the [promotion report](../docs/reports/m1/M1_iPIN_TUnA_31k_Promotion_v1.md).

The new local read-only bundle preserves exact selected states, endpoint
features, sequence order, code and provenance. The public registry, aggregate
evidence and validation records are under `artifacts/models/frozen_pair_models_v3/`
and `artifacts/validation/frozen_pair_models_v3/`. Weights and pair-level data
remain local. The v3 verifier checks v2 and v1 preservation as well.

This promotion performs no new training, benchmark evaluation, metric
recomputation or test access. Prior decisions, benchmark results and spent
ledgers remain unchanged. Previous numbered status records retain their
historical scope; [status v55](PROJECT_STATUS_v55.md) records the preceding
three-model release. Current gate: [v56](gates/gate_status_v56.yaml).
