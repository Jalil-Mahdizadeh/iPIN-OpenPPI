# Human PPI data scaling study

Authorized by the user on 2026-09-25. This is a separate, versioned follow-up to
the frozen human iPIN benchmark. All earlier raw data, partitions, embeddings,
model weights, predictions, results, and evaluation ledgers remain unchanged.

Location: `experiments/human_ppi_data_scaling_v1/`. The study was moved out of
`benchmark/` on 2026-09-25 because its scope includes corpus construction and
training as well as evaluation. Historical benchmark paths are read-only inputs.

The question is whether expanding experimentally supported human binary PPI
training data improves PU-TUnA, on both the original evaluation population and
an expanded population. It is not a claim that more records necessarily mean
more information or that this study can establish a performance ceiling.

## Design fixed before fitting

- Retain train-1 positives and the complete original dev-1/test-1 panels.
- Deduplicate unordered pairs of exact frozen reference sequence hashes across
  sources, orientations, assays, constructs, and repeated records.
- Add human–human binary evidence with explicit provenance. Co-complex expansion,
  functional associations, ambiguous mappings, and explicit mutant-only evidence
  cannot create primary positives. Quantitative fragment screens need their own
  positive-call audit before admission; a database row alone is insufficient.
- Anchor all original protein/component assignments. New sequences may inherit
  one old partition; components bridging old partitions are quarantined. New
  components receive deterministic allocations. Preserve original C1 pair roles.
- Freeze expanded development and test populations before any model fitting.
  Reserve old candidate identities, including unlabeled candidates, from training.
- Use nested positive budgets beginning with exactly 16,799 original positives;
  add 25k, 50k, 70k and the eligible maximum only when those sizes are possible.
  Keep the architecture, optimizer, comparison budget, and seed list fixed.
- Report original, added-only, and combined evaluation panels separately. Keep
  unlabeled examples identified as U, never as confirmed non-interactions.
- Select a common epoch per three-seed ensemble and a training size using a
  prespecified C3 development objective. Test outcomes cannot choose either.
- Include the frozen PU-TUnA baseline on the expanded panels and a fresh 16,799-P
  control. Preserve comparisons with the other existing iPIN baselines.
- Freeze selected weights and test predictions before computing final test metrics.
  Test-2 contains historically examined test-1 by explicit user agreement; neither
  the combined test nor its added subset is advertised as independent replication.

The expansion can change source composition, protein coverage, and evidence
quality as well as size. Source/assay composition and fixed-panel curves will be
reported alongside performance. A volume-only causal conclusion is not warranted.

## Initial corpus and interpretation

The first frozen release supports **16,799, 20,000, 25,000 and 31,188** training
positives, with three fitting seeds per size. The maximum is for the declared
eligible, locally frozen sources; it is not the maximum available human PPI data.
The added sources are qualified IntAct binary evidence, Lit-BM, and the other
already frozen HuRI pair views. The source audit retains evidence identifiers,
methods, publications, source locators, and mapping decisions.

The eligible endpoint universe grows from 17,000 to 17,583. Another 220 candidate
new endpoints were quarantined because their similarity components would bridge
original partitions. Four new sequences exceed the previously qualified context
length; they are deferred rather than truncated. Existing residual homology from
the original heuristic graph remains a limitation.

Positive nesting is exact. All sizes use the same newly sampled 2M-U background,
after excluding the expanded positive evidence and every held-out candidate.
The original 2M-U training sample is preserved byte-for-byte in `data/legacy/`.
Thus comparisons along the new curve hold U fixed; comparison with the historical
frozen model also reflects the reconciled U/background population.

Version 2 retains every original dev/test candidate identity. Newly supported
original U rows become P only in the version-2 view. Exact dev-1/test-1 metrics
continue to use the original states and weights. The selection objective is the
equal-weight mean of C3 concordance in the reconciled original cohort and the
added cohort, computed from the mean scores of three members at a common epoch.

An inherited C1 exception requires explicit reporting: dev-1 and test-1 share
91,781 U candidate identities; reconciliation makes 57 of these P in both views.
C2/C3 have no such overlap. Complete C1 panels are retained as requested, and a
prespecified additional C1 test-2 view excludes every development candidate
identity. No held-out candidate, in either state, enters the new training fits.

The import criteria are informed by the [HuRI provider's evidence descriptions](https://interactome-atlas.org/about/)
and [IntAct's experiment-level data model](https://www.ebi.ac.uk/training/online/courses/intact-quick-tour/getting-data-from-intact/).
Rows from large quantitative fragment screens are deferred until their positive
calls and reference-sequence interpretation can be independently reconciled.

## Execution

`scripts/` holds the reproducible study code. `audit/` records source eligibility,
exclusions, parent hashes and split validation. `data/` contains training and
development inputs; `private/` holds curation and test artifacts and is excluded
from training mounts. `runs/` and `logs/` hold only this study's outputs.

Only the already frozen human sources are admitted in the initial release. A
later source release requires a new corpus version and freeze, not an in-place
addition after model selection.

Status and concrete execution records are written to `STATUS.md` as work proceeds.

The GPU entry point is `bash run_gpu.sh <stage>`. `scripts/submit.py` submits the
12 registered fits (up to four GPUs at once), followed by a dependent job that
selects on C3 development, freezes scorers and predictions, and evaluates C1/C2/C3
against the three existing frozen iPIN models. It refuses duplicate submission.
