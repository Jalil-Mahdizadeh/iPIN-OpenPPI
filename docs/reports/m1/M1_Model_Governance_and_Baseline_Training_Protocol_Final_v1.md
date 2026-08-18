# M1 model-governance and baseline/training-protocol report v1

**Protocol ID:** `model_governance_and_baseline_training_protocol_v1`

**Date:** 2026-08-18

**Authority:** `DEC-0027`

**Parent acceptance:** `DEC-0026` and `RESUME-002`

**Result type:** governance design; no model experiment or model result

## Executive disposition

The first modelling stage is specified as a bounded, frozen-encoder,
sequence-only diagnostic. It contains two ESM-2 candidates, a mandatory
shortcut/baseline ladder, one primary partner-gated pooled-pair head, two
scientifically necessary 650M ablations, an exact design-weighted P-versus-U
ranking objective, a finite 30-run search, and fail-closed development and
protected-test custody.

This report does not authorize implementation or execution. No weight or
tokenizer was downloaded, no model cache or image was created, no embedding or
feature was extracted, no baseline or neural model was implemented, no job was
submitted, and no model was trained, scored, selected, or evaluated.
Development and protected packages remain encrypted and inaccessible.

The machine-binding specification is
`configs/model_governance_and_baseline_training_protocol_v1.yaml`; the full
scientific procedure is
`docs/protocols/MODEL_GOVERNANCE_AND_BASELINE_TRAINING_PROTOCOL_v1.md`.

## 1. Resume and immutable-parent check

The work resumed from Git commit
`55be4cd4f43659acf32423580b94732aa7e38041`, with local `main` equal to freshly
fetched `origin/main` and divergence `0 0`. The accepted 17,000-sequence
universe, 7,782-component hard graph, 11,900/2,550/2,550 endpoint split,
16,799-row public training-P census, 2,000,000-row public training-U sample,
36-row sampling-strata table, and three encrypted held-out packages all
matched the hashes recorded by `RESUME-002` and `DEC-0026`.

The checkpoint-prescribed safety suite passed 26 tests in the checksum-pinned
ARM64 data container. No sealed package or private key was opened. These checks
established continuity; they did not reconstruct, resample, or reinterpret any
benchmark artifact.

## 2. PLM freeze and exposure boundary

The admitted public model set contains exactly:

- `facebook/esm2_t30_150M_UR50D` at revision
  `a695f6045e2e32885fa60af20c13cb35398ce30c`, safetensors SHA-256
  `c3f1da8aea53bddd32c246c86168c23b9fd72341fb9db9a94436f855f5053566`;
  and
- `facebook/esm2_t33_650M_UR50D` at revision
  `08e4846e537177426273712802403f7ba8261b6c`, safetensors SHA-256
  `a08adabb949fa67ad3c14b509d04fd60368b35007b0095e3358f81200c4f4db0`.

The 150M model is the lightweight mandatory PLM baseline; 650M is the primary
frozen encoder candidate. Only safetensors is admissible, remote code and
pickle weights are prohibited, and all repository files must later be
revision- and hash-pinned in project-local offline custody.

Provider records describe masked-language-model training on UR50/D associated
with UniRef `2021_04`, but do not expose an exact dynamic sequence-draw log.
The project has not completed exact or homologous exposure auditing for the
17,000 endpoints. Exposure is therefore unknown and possible. C3 must not be
called PLM-unseen, family-unseen, temporally clean, or an exposure experiment.

The future ARM64 model-runtime recipe is version-frozen, but neither built nor
qualified. Container construction and model acquisition require a later
numbered authorization and independent validation.

## 3. Frozen embedding rule

Both backbones remain in evaluation mode, FP32, with autograd disabled. The
final residue layer is pooled without BOS/EOS/padding. Exact frozen sequences
are neither truncated nor replaced. A sequence longer than 1,022 residues is
covered with 1,022-residue windows, overlap 128, stride 894, and an appended
terminal start at `length - 1022` when needed. Overlapping residue vectors are
averaged before whole-protein averaging.

All 17,000 vectors may later be extracted label-blindly. Only the 11,900
training endpoints define normalization statistics. Completeness, uniqueness,
finiteness, manifest hashes, and a deterministic 1% repeat-extraction tolerance
of `1e-6` are hard prerequisites. No residue-level output is retained.

## 4. Mandatory diagnostic ladder

Every candidate is compared on identical governed rows, weights, and tie
rules against:

- the frozen deterministic hash score;
- endpoint-degree sum, preferential attachment, component degree-mass, and
  training-graph common-neighbor controls;
- sequence-length sum and ratio controls;
- exact within-pair contiguous 3-mer cosine;
- exact best training-interolog 3-mer similarity; and
- the frozen ESM-2 150M one-affine-head baseline.

The 650M linear head is also part of the strongest simple sequence baseline
set. Degree and graph features use only the 16,799 training-positive graph;
held-out endpoints have training degree zero. Approximate interolog search,
held-out/full-graph features, source metadata, and external panels are barred.

## 5. Primary objective and finite execution design

The only primary training objective is a design-weighted positive-versus-
unlabeled pairwise logistic ranking loss. Each of five passes uses every
2,000,000-row U observation once without replacement and the complete 16,799-P
census. Each positive is paired 119 or 120 times per pass; exactly 919
positives receive 120 comparisons. P and U orders are independently determined
by frozen full-SHA-256 keys.

Each U row retains its exact rational `N_h/m_h` design weight. The loss is
`softplus(-(s_p-s_u))`, normalized by mean U design weight, with an FP64
complete-pass monitor. U remains unlabeled: there is no U-as-zero BCE,
pseudo-negative, class-prior risk, calibration target, or prevalence estimate.

The sole primary architecture is a symmetric frozen-650M pooled-pair head with
a shared `1280 -> 256` projection, one shared bidirectional partner gate,
commutative pair features, and a `128 -> 1` scalar head. Trainable parameters
must remain below two million. Required ablations are a 650M affine head and a
650M nonlinear no-gate head; no other architecture enters stage one.

Three fixed seeds and two linear or three nonlinear recipes produce exactly 30
runs and at most 300,000,000 pairwise comparisons. Runs use one GH200, at most
100 GPU-hours and 100 GiB. Five complete passes, complete-pass checkpoints,
an exact single infrastructure resume, no performance early stopping, and
fail-closed numerical/reproducibility conditions are fixed in advance.

## 6. Release, selection, metrics, and diagnostics

Before any development release, every run and selected complete-pass
checkpoint must be complete or fail closed; code, container, config,
embeddings, inputs, checkpoints, and three-seed ensemble definitions must be
registered and hashed; the registry must be independently validated; and a new
numbered decision must authorize release.

Development selection uses the arithmetic mean of three seed scores. The
lexicographic order is quantized C3 concordance, then C2, then C1, followed by
lower model complexity and candidate ID. No pooled cell metric, seed picking,
post-release retraining, new candidate, or protected information is allowed.

The primary metric remains the frozen Horvitz-Thompson positive-versus-U
pairwise concordance with half credit for exact ties. Reporting order is C3,
C2, C1, separately for development and protected test, with the existing
two-endpoint-component pigeonhole bootstrap. Full-ranking measures remain
demoted until separately authorized exact streaming over the full universe.

Degree strata and nested top-1%, top-5%, and top-10% training hubs are frozen.
The prespecified C1 novel-U analysis is a view over already-frozen C1 rows:
retain only U pair IDs absent from public training U, retain every original
rational weight, do not resample, and never use the view for selection.

## 7. Complexity and kill gates

The partner gate is retained only with prespecified C3 gains over the strongest
simple sequence baseline and both 650M ablations, paired intervals excluding
zero, supported-source directionality, non-hub-only gain, and three-seed
stability. Otherwise the fallback removes the gate, then the nonlinear head,
then 650M scale, or terminates the learned line.

Any future complex residue/joint/routing proposal requires accepted results
from this simple stage, a qualifying C3 statistical gain, an unresolved error
pattern not explained by degree, length, 3-mer, interolog, or frozen-PLM
controls, a separate oracle/interface evidence study, a compute case, and a
new numbered decision.

The model line stops before protected test if no learned candidate achieves
the frozen qualifying C3 gain. A result explained by degree/graph/length is a
shortcut result; a result explained by interolog or frozen-PLM linear controls
rejects complexity. Integrity leakage, treating U as scientific negatives,
premature development release, or post-release retraining invalidates the
stage.

## 8. Validation and authority disposition

The production audit is required to emit exactly 24 passing static checks from
a clean commit in the pinned data SIF. A separately implemented validator,
which does not import production protocol code or any model framework, must
independently reconstruct path/hash guards, long-sequence coverage, P/U
repetition algebra, search budget, selection quantization, and the remaining
consequential rules.

Only an immutable passing audit, passing independent report, and a new numbered
acceptance decision may close this design gate. Even successful acceptance
does not authorize model acquisition, implementation, embeddings, training,
development release, or protected evaluation; each later boundary requires
its own numbered governance decision.
