# Project status v54 — both models frozen; optimized ensemble best-performing

Date: 2026-09-11. Decision: [DEC-0054](decisions/DEC-0054-freeze-and-designate-both-models.md).
Previous immutable status: [v53](PROJECT_STATUS_v53.md).

The **best-performing model** is the fixed three-seed residual-MLP ensemble
`esm2_150m__residual_wide__epoch04_ensemble3`. The affine ensemble
`lightweight_esm2_150m_linear__linear_lr3e-4` remains the **original confirmatory
baseline** from the original protected evaluation. Both retain all three seeds
and equal raw-score averaging. No weights or predictions have changed.

C3 development concordance improved 0.784142 → 0.799419; test C3 was
0.789249 → 0.807948, C2 0.805299 → 0.851301, and C1 0.843493 → 0.916037.
“Best-performing” means the higher observed primary C3 score of the two evaluated
PLM ensembles. All nine test cell point scores increased. The primary C3 paired
gain interval remains [−0.001358, +0.050000], so statistically conclusive C3
superiority is not established. This does not mean equivalence or no benefit.

A public dual-model registry and a read-only local preservation bundle freeze
the six exact state-only checkpoints, shared encoder/tokenizer, training-only
normalizer, identity-aligned embeddings, scoring definitions and provenance.
Weights/identities remain outside Git. Historical artifacts and both consumed
evaluation ledgers are unchanged; this action performs no new training, scoring,
truth access or metric recomputation. It is a post-follow-up designation,
not a new prospective or confirmatory selection procedure.

DEC-0052's failed individual-seed gate, DEC-0053's explicit ensemble amendment
and follow-up, and DEC-0051's original confirmatory record remain separate and
immutable. The test has been examined; no independent replication or calibrated
binding-probability claim. Genuine partner specificity, direct binding and
shortcut-free generalization remain unresolved. BioPlex stays secondary
cross-assay association evidence, not a binary binding gate.

See the [model cards and preservation record](../docs/models/FROZEN_PAIR_MODELS_v1.md),
[machine-readable registry](../artifacts/models/frozen_pair_models_v1/MODEL_REGISTRY.json)
and [gate v54](gates/gate_status_v54.yaml). No additional experiment, refit or test
evaluation is authorized or queued. Repository updates, commit and push are
user-authorized.
