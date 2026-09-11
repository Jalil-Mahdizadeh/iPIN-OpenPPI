# Project status v52 — optimization completed; conditional test not triggered

Date: 2026-09-11. Decision: [DEC-0052](decisions/DEC-0052-development-only-optimization-and-conditional-followup.md).
Previous frozen status: [v51](PROJECT_STATUS_v51.md).

The project retains strong evidence for simple frozen-PLM C3 PU ranking in the
existing benchmark. The original development/test concordances are 0.784142 /
0.789249; these are not binding accuracy. Partner-specific/direct-binding
generalization remains unresolved, and network shortcuts remain competitive or
dominant with previously exposed endpoints. BioPlex is secondary cross-assay
evidence, not the decisive test of this result.

The prospectively frozen train/development-only optimization completed all
24 preliminary recipes and 12 three-seed-stage fits, totaling 168 epochs on the
GH200 GPU. The selected 150M residual-MLP ensemble at epoch 4 reached 0.799419
C3 development concordance, gain 0.015277, paired 95% interval
[0.002942, 0.034460]. Its individual seed gains were +0.018326, −0.003437,
−0.005677; seed range 0.021207 exceeded the frozen 0.02 limit.

Thus the ensemble improvement conditions passed but the seed-stability
conditions failed. **No follow-up test, new test ledger, fallback selection,
extra search or baseline replacement.** The original test remains an already
evaluated panel, not a newly unused test. DEC-0052's conditional follow-up
authorization was not triggered; original records remain immutable.

All 148 registered earlier-study files and original custody records verified
unchanged. Eleven GPU fixtures and 68 CPU regression tests passed (one GPU
case skipped only in the CPU invocation); full-panel paired-bootstrap CPU/GPU
agreement was within 3.07e-12. The search used 175.4 GPU-process seconds against
the two-hour cap. A pre-fit plugin failure and numerical reference-rounding
distinction are transparently recorded without changing the scientific rules.

See the [concise report](../docs/reports/m1/M1_Model_Optimization_v1.md),
[protocol](../docs/protocols/MODEL_OPTIMIZATION_v1.md), and
[gate record](gates/gate_status_v52.yaml). The new ensemble is promising
development evidence, not a stable validated replacement or a dead-end verdict.
No further experiment, quarantine access, external coordination or commit/push
has been performed or automatically authorized by this status update.
