# Prospective human PPI model comparison

Authorized by the user's 24 September 2026 request to create a new study,
initiate training, select promising models, and compare them with the three
frozen iPIN models on C1/C2/C3. GPU/SLURM execution is explicitly authorized.

## Scientific question

Does retaining several learned residue summaries, and allowing those summaries
to attend to the partner protein, improve positive-versus-unlabeled ranking?
This is not an interface-supervised or binding-affinity study.

## Inputs and models

Reuse the qualified full-context, layer-30 ESM-2 150M FP32 residue cache for all
17,000 human endpoints. Reuse the exact 16,799 TRAIN P and 2,000,000 TRAIN U
pairs, design weights, sequence-hash ordering, and frozen component partitions.
TRAIN contains 11,900 endpoints, development 2,550, and test 2,550. U remains
unlabeled; it is never called experimentally verified noninteraction.

Every recipe has the same residual MLP global branch, using the full-context
residue mean standardized with TRAIN endpoints only. This mean differs from
historical windowed means for long sequences, so the new mean control is needed.

The three advanced recipes add a learned residue branch. Shared learned queries
pool contextual residue vectors into 8 or 16 latent tokens. The pooling control
summarizes these tokens without cross-protein attention. The two cross-attention
recipes use one or two shared bidirectional cross-attention blocks before final
pooling. Both branches use symmetric pair features, so swapping A/B preserves
the evaluation score. A zero-initialized final local projection initially gives
the global branch's score. All PPI parameters are freshly initialized; no PPI
weights are transferred from the comparators. ESM remains frozen.

Training uses at most 512 stratified-random residue positions per endpoint per
batch, spanning the full sequence; short proteins use every residue and masked
padding. The full-sequence mean is always retained. Evaluation computes latent
tokens from every residue with no sequence truncation. This is latent-token
cross-attention, not a dense all-residue contact map. Local residue sampling is
an approximation during training and will be disclosed in results.

## Fitting and selection

Four recipes, three fixed seeds each, eight epochs. Each epoch visits every
TRAIN U pair once with balanced cycling of positives and the historical
PCG64DXSM ordering convention. Optimize weighted `softplus(score_U-score_P)`;
normalize U design weights by their TRAIN mean. AdamW, fixed learning rate
1e-4, weight decay 0.01, gradient norm clipping at 5, batch 256 comparisons.
FP32 model/cache/attention and FP64 loss weighting and ensemble accumulation;
AMP and TF32 disabled. Use no BatchNorm or statistics fitted to development/test.

Evaluate each member on full C3 development at epochs 1, 2, 4, 6 and 8. Select the
best three-seed mean-score ensemble for each recipe; ties choose earlier epochs.
Retain all three seeds. No test information selects checkpoints, recipes or
ensemble weights. This is a finite development search, not a confirmatory
development hypothesis test.

Promote at most two advanced recipe ensembles whose C3-development concordance
strictly exceeds frozen PU-TUnA's 0.8044558035378994. Order by descending
development concordance, then recipe name. If any qualify, also test the selected
mean control as a prespecified diagnostic comparator. If none qualify, publish
all development results and the no-promotion disposition without opening test
truth. No fallback to a lower promotion threshold or extra search is automatic.

## Final comparison

Freeze selected weights, full-length per-endpoint latent features, normalizer,
source code, selection and scorer identities before opening candidate test
pairs. Score the unchanged C1/C2/C3 panels: respectively 3,187 / 13,446 / 2,379
P and 1,000,000 U each (3,019,012 candidate rows total). Freeze all finite,
identity-aligned predictions before test truth is mounted. Reuse byte-identical
historical predictions for original iPIN, optimized iPIN and PU-TUnA.

Primary comparison: the advanced ensemble ranked first by C3 development versus
PU-TUnA on C3 test. Report every promoted ensemble and the mean control against
all three references on all three cells, with the historical design-weighted
PU concordance and 2,000 paired component-bootstrap draws. Other contrasts and
individual member results are secondary/descriptive; intervals are pointwise.
Do not choose a new winner by test performance or claim multiplicity-adjusted
superiority from secondary contrasts. These are previously examined test panels;
the study is a disclosed follow-up, not a fresh unseen confirmatory evaluation.

Use separate allowlisted runtime mounts for training, candidate scoring,
reference import, prediction freeze, truth evaluation and aggregate publication.
The existing qualified restriction-only GPU guard is reused unchanged. Create
a new one-attempt study-local truth-access reservation; never reset historical
ledgers or overwrite historical artifacts. Report failures and finite coverage.

## Qualification, execution and limits

Qualify padding invariance, endpoint identity, swap symmetry, finite gradients,
partner-dependent cross-attention, cached/direct score agreement, resume-state
recovery and independent brute-force metric agreement before formal training.
Use only synthetic/TRAIN fixtures for throughput and numerical qualification;
discard pilot fits. Record input and execution hashes before formal fitting.

Use the interactive GH200 for qualification and to start the mean control while
a four-GPU SLURM job queues for the four recipes (three sequential seeds per
recipe). A shared per-recipe file lock prevents duplicate concurrent workers;
the batch worker reuses completed control fits. Reserve eight hours for training
and four hours for selection/comparison, with runtime pilots supporting this
margin. Selection and final comparison follow only successful completion.
Preserve resumable optimizer/RNG state. The unused initial pre-fit snapshot is
retained under `runs/prefit_v0/`; see [PREFIT_AMENDMENT.md](PREFIT_AMENDMENT.md).
Measure head-scoring throughput for a few thousand pairs with cached embeddings;
report it separately from encoder cost. Do not infer physical interface contacts,
calibrated interaction probabilities, or binding energies from these scores.
