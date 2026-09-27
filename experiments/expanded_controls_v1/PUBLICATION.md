# Publication and reproduction scope

This experiment records a follow-up specified after the expanded benchmark had
already been evaluated. The original eleven deterministic formulas predate
test1; their dev2/test2 evaluation and the direct partner diagnostics are new.
The selected 31k model remains frozen. Two additive endpoint architectures are
newly fitted with three seeds each, using the fixed historical
architecture/optimizer/pass recipe and the expanded train2 P/U population.

## Included evidence

- Protocol, its source-based pre-execution clarification, executable scripts
  and independent synthetic tests.
- Input and implementation freezes with parent identities and phase boundaries.
- Aggregate development/test results, both constituent cohorts, paired
  differences, C1 overlap sensitivity, C3 anchor and quartet diagnostics.
- Compact feature, alignment, training, scoring and final validation manifests.
- PNG, PDF and SVG figures and machine-readable aggregate CSV/JSON.

[PUBLICATION_MANIFEST.json](PUBLICATION_MANIFEST.json) inventories these compact
review files, including the completion record. This is a local deliverable;
no commit, remote deposit or manuscript modification is implied.

## Local artifacts

Sequence metadata, train2 pairs, human development/test candidates and truth,
embeddings, homology kernels, model weights, pair predictions, selected quartet
identities and bootstrap arrays remain local. The experiment's ignore rules
exclude those artifacts from Git. Their hashes and public aggregate support
counts are retained; publication of aggregates does not release protected rows.
Runtime images and original trained models are external prerequisites already
recorded in INPUT_FREEZE.json.

## Phase order and verification

The runner uses isolated Apptainer mounts for preparation, sequence features,
sequence-only alignment search, qualification, endpoint-control fitting,
candidate-only scoring, evaluation, diagnostics and final validation. Training
has no evaluation-pair or truth mounts. Scoring has candidate identities but no
labels or design weights. Evaluation requires the complete prediction freeze.

The executed order was preparation; sequence_features and alignment;
qualification; a source-based clarification of the pooled-transfer kernel;
final qualification and implementation freeze; train_unary; score; evaluate;
diagnostics; initial validation; independent numerical audit; final validation.
All completed result writes refuse replacement.

For a fresh reproduction, provision the exact parents named in INPUT_FREEZE.json
and use a clean experiment directory under the same repository's experiments
directory. Copy the scripts, tests and run.sh. Start with protocol_archive/
initial.json as PROTOCOL.json for preparation and sequence preprocessing, then
restore the clarified PROTOCOL.json and copy PRE_EXECUTION_CLARIFICATION.json
before final qualification and scripts/freeze.py. This preserves the recorded
preprocessing/clarification lineage. Run the named runner phases in the order
above, with the validation clarification below. A fresh run creates its own
timestamped input and execution manifests; it must not overwrite the recorded
scientific run. The scripts/freeze.py utility is invoked directly in the
study directory after qualification; it is not a run.sh phase.

The first synthetic-test invocation hit an installed pytest plugin's localhost
lookup during collection. Automatic plugin loading was disabled before any
tests, fitting or candidate scoring completed; the subsequent initial and final
qualifications passed. The failed invocation is retained in the local logs.
The kernel clarification preserves the historical nonnegative pooled-cosine
transfer kernel found during source review. It does not use observed outcomes.

The frozen initial validator stopped on a full-panel point comparison because
FP64 weight-summation order differed by at most 1.49e-11 between the published
metric and an independent oracle. The retained audit explains the difference
to within 4.3e-14 and confirms it with higher-precision arithmetic. The original
scientific implementation, predictions, results and validator remain unchanged.
A separately hashed final validator passed using a documented 1e-10 tolerance
only for that comparison, retaining 1e-12 elsewhere. Its audit, exact invocation
and fresh-output readback instructions are in
[validation/README.md](validation/README.md). The frozen run.sh still invokes
the original validator; the final readback uses scripts/validate_final.py.

## Interpretation boundaries

Global estimates use the existing equal-cohort design-weighted P/U concordance.
Anchor means give each eligible anchor equal weight within a cohort; their
macro gives each cohort equal weight. Selected quartets have deterministic caps
and are not a population-weighted sample. Raw score scale is retained for swap
contrasts because a nonlinear transformation can change summed-score preferences.

Intervals are pointwise and conditional on fitted models and the frozen corpus.
They do not incorporate refitting, model selection or a new laboratory sample.
The endpoint controls are historical small-head alternatives, not
capacity-matched TUnA ablations. Homology transfer exhausts training interaction
edges under the declared kernels, but its alignment search is still heuristic.
This study does not repeat internal homology-purged or source-restricted refits,
as agreed with the user. U remains unlabeled throughout.
