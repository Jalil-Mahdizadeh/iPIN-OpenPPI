# Frozen pair models v1

Date: 2026-09-11. Decision: [DEC-0054](../../governance/decisions/DEC-0054-freeze-and-designate-both-models.md).

Both evaluated models are frozen. The optimized ensemble is the project's
**best-performing model by observed benchmark score**; the affine ensemble
is retained as the **original confirmatory baseline**. This changes model
designation and preservation, not weights, predictions or scientific results.

| | Best-performing model | Original confirmatory baseline |
|---|---|---|
| Exact ID | `esm2_150m__residual_wide__epoch04_ensemble3` | `lightweight_esm2_150m_linear__linear_lr3e-4` |
| Head | Affine branch + LayerNorm → 256 → GELU → dropout → scalar | Affine scalar head |
| Selected checkpoint | Epoch 4 of the completed eight-epoch schedule | Pass 5, global step 2445 |
| Parameters per head / three heads | 498,053 / 1,494,159 | 1,922 / 5,766 |
| C3 development concordance | 0.799419 | 0.784142 |
| C3 test concordance (primary) | 0.807948 | 0.789249 |
| C2 test concordance | 0.851301 | 0.805299 |
| C1 test concordance | 0.916037 | 0.843493 |
| Evidence role | Development-selected, disclosed follow-up under DEC-0053 | Original protected confirmatory evaluation under DEC-0051 |

The optimized ensemble has higher point scores in all nine reported test cells.
Its C3 gain is **+0.018699 [−0.001358, +0.050000]**: the paired 95% interval
includes zero, so primary C3 superiority is not statistically established.
“Best-performing” is scoped to observed scores of these two evaluated PLM
ensembles, not an assertion of state-of-the-art or confirmed superiority.
Secondary C2/C1 gains have positive paired intervals; they do not substitute
for the primary comparison. The full unchanged results are in the
[follow-up report](../reports/m1/M1_Model_Optimization_Followup_v1.md) and
[original report](../reports/m1/M1_Protected_Final_Test_v1.md).

## Exact prediction definition

Both models use the same frozen `facebook/esm2_t30_150M_UR50D` encoder at
revision `a695f6045e2e32885fa60af20c13cb35398ce30c`. The original extraction
uses final-layer residue-mean pooling with 1,022-residue windows, overlap 128,
stride 894, and FP32 outputs. Standardization uses only the 11,900 training
endpoints; the recorded standard-deviation floor is 1e-6. The preserved 17,000 ×
640 matrix is identity-aligned by sequence hash to the endpoint manifest, not
assumed to share an independently sorted row order.

For standardized endpoint vectors `a, b`, the shared 1,921-dimensional symmetric
features are `concat(a+b, abs(a-b), a*b, exact_cosine(a,b))`.
The optimized head sums its affine and MLP branches; LayerNorm epsilon is 1e-5,
width 256 and training dropout 0.3. Dropout is disabled at inference.
The optimization recipe also used learning rate 1e-4 and weight decay 0.01;
this is not an isolated architecture-only causal comparison.

For **each model**, seeds 20260803, 20260817 and 20260831 are fixed, in order.
Run members in evaluation/inference mode with FP32 parameters and operations,
cast their raw scores to FP64, and take their equal arithmetic mean. There is
no sigmoid, calibration, ranking transform, seed omission, reweighting, or
averaging of member performance metrics. The three-member ensemble is the
prediction unit. Individual-member results remain diagnostics.

## Preservation and verification

The machine-readable [MODEL_REGISTRY.json](../../artifacts/models/frozen_pair_models_v1/MODEL_REGISTRY.json)
is authoritative for IDs, aliases, checkpoint SHA-256 hashes, seed order,
ensemble definition, shared inputs, exact metrics and historical provenance.
Its [artifact registry](../../artifacts/models/frozen_pair_models_v1/ARTIFACT_REGISTRY.json)
also freezes the new versioned code/docs and validation records.

The local preservation bundle is `.private/frozen_pair_models_v1/bundle/`.
It holds six byte-identical safe NPZ head states, encoder weights/tokenizer,
the normalizer and aligned feature identities, and source snapshots. Files
are mode 0400 and directories 0500. These permissions plus SHA-256 checks
prevent accidental edits and detect drift; they are not hardware WORM storage
or an off-site backup. Original training checkpoints remain separately
hash-registered in their original locations. Neither old evaluation bundle is
modified. Public and private copies of the registry are byte-identical.

No weights, protein identities, pair rows, predictions or private keys are
committed. A fresh Git clone contains the public audit trail, not the private
weights. This is a local preservation package, not a standalone arbitrary-
sequence scoring API; the checksum-pinned Apptainer runtime and original
pipeline dependencies remain required. Do not run a spent evaluation operator
to verify preservation.

The read-only verifier can be repeated inside the pinned model image:

```bash
PYTHONPATH=/project/src python /project/scripts/model/freeze_pair_models_v1.py /project
```

Mount the repository read-only as `/project` using the existing Arrhenius
Apptainer procedure and image `ipin-model-arm64_0.1.0.sif` (SHA-256
`c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91`).
`--create` was used once to construct this release and now fails closed.
Verification checks exact copies, shapes/dtypes/finite states, six member hashes,
read-only custody, the closed evidence records and both spent ledgers.
See the [freeze audit](../../artifacts/validation/frozen_pair_models_v1/FREEZE_AUDIT.json)
and [synthetic tests](../../artifacts/validation/frozen_pair_models_v1/UNIT_TESTS.xml).
All 38 targeted tests passed in the checksum-verified model image with the real
GH200 GPU available, including synthetic GPU ensemble checks and the existing
protected-evaluation/follow-up safety tests. These tests do not use test pairs.
The preservation audit also verifies 210 registered historical entries across
eight studies (entries can share files), plus both spent ledgers and completions.

No new training, benchmark scoring, truth access or test evaluation is performed
for this release. Earlier protocols, failed gates, amendments and evaluations
remain immutable. Any later model changes need a new version and appropriate
authorization; neither frozen model is silently updated.

## Claim boundaries

These models rank positives against sampled unlabeled pairs under the protected
PU benchmark. Unlabeled pairs are not verified noninteractions. C3 describes
interaction-training-naïve proteins under the frozen component split, not
proteins necessarily absent from PLM pretraining or free of all homology.
Direct binding, genuine partner specificity and absence of network/source
shortcuts remain unresolved. The optimized follow-up used the previously
examined test and is not independent replication. BioPlex remains secondary
AP-MS association evidence, not a decisive direct-binary panel.
