# iPIN-OpenPPI project status and execution checkpoint

**Checkpoint date:** 2026-08-19

**Execution environment:** NAISS Arrhenius node `n180`; accepted data/model
containers; at most one NVIDIA GH200 120 GB

**Scientific programme state:** `DEC-0032` authorizes bounded development-only
release and exact frozen-scorer evaluation; implementation and independent
pre-release validation must pass before decryption

The authoritative gate is `governance/gates/gate_status_v31.yaml`.

## Accepted preconditions

The exact `RESUME-004` preflight passed at clean, synchronized commit
`dc6dbb2cf938bcc19c1b1dd423af92a0ed94b067`. All authority, protocol, runtime,
training-registry, evidence-sidecar, public-input, and sealed-ciphertext hashes
matched. The complete unit suite passed 260 of 260 tests.

Stage 1 remains frozen: 30 selected checkpoints and 10 arithmetic three-seed
ensembles are fixed by training registry SHA-256
`11d7a92d6dd42ca78434783844cbba2ffb05ac789b76eca4399528d0d19ab318`.
No further training, checkpoint selection, recipe, seed, model, or embedding
change is authorized.

## Authorized development package

The active work package may implement and independently validate only the code
needed to release development, score the nine mandatory deterministic controls,
all 30 selected checkpoints, and all 10 frozen ensembles, and calculate the
unchanged development metrics and diagnostics.

Only after that pre-release validation passes may the development ciphertext be
decrypted with the development key into the private workspace. Protected
candidates, protected truth, and their private keys must remain untouched and
sealed.

Evaluation must report C3, then C2, then C1, using exact HT concordance and the
frozen paired 2,000-replicate component bootstrap. Degree/hub strata,
HI-II-14/HuRI-exclusive cells, seed stability, and C1 novel-U are mandatory.
Selection and the partner-gate/fallback/model-kill rules are exactly those in
`DEC-0028`; diagnostics cannot alter selection.

## Required return

Production outputs and a complete registry must be frozen before a clean-room
independent validator is implemented. Governance must then record one clear
disposition: advance a frozen scorer toward separately authorized protected
evaluation, retain only the simpler eligible fallback, or stop the complex-
model claim. No protected action is authorized by `DEC-0032`.

## Continuing boundary

Negatives or pseudo-negatives, benchmark changes, retraining, tuning, adaptive
criteria, new architectures or ablations, external panels, structural or
residue/interface work, protected access, and probability/prevalence/
calibration or unsupported transfer/exposure claims remain prohibited.
