# Frozen competitors on test2

This experiment applies the previously evaluated, frozen predictors to the
unchanged test2 C1/C2/C3 partitions and compares them with selected 31k TUnA.
All new artifacts remain under this directory. No training, model selection,
original-result replacement, or changes to benchmark inputs are performed.

The 13 predictors comprise selected 31k, the three current frozen iPIN models,
original TUnA, original and retrained D-SCRIPT, original PLM-interact,
original and recovery RAPPPID, SPRINT, and the previously promoted cross-attention
and mean-pooling ensembles. Planning-only methods without completed predictors
and development-only unpromoted recipes are listed in `PROTOCOL.json`.

Test2 retains the frozen reconciled legacy and added cohorts. The primary metric
is the existing equal-cohort macro of design-weighted P-versus-U concordance,
with C3 primary and C1/C2 secondary. Paired component-bootstrap intervals use
2,000 common draws. The inherited C1 development-overlap sensitivity is retained.
U is unlabeled; test2 is a disclosed historical follow-up.

Archived predictions are verified and aligned by exact endpoint-pair identity
before reuse. New candidates receive scores from the unchanged predictors.
The selected and frozen PU-TUnA scores use the exact saved GP covariance.
SPRINT retains its original 16,799-positive training graph, with sequence-only
preprocessing extended to the frozen 17,583-protein corpus.

`INPUT_FREEZE.json` and `CATALOGUE.json` record inputs. Work logs are in `logs/`,
resumable GPU outputs in `shards/`, and completed comparisons in `results/`.

See [STATUS.md](STATUS.md) for the latest recorded progress. Refresh it with
`python3 -B scripts/status.py` from this directory. The final comparison runs
automatically after all scoring jobs succeed. Every job has a 12-hour allocation;
the PLM-interact and D-SCRIPT prediction arrays checkpoint every 512 rows.
