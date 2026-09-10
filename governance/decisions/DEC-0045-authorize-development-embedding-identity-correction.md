# DEC-0045: Authorize development embedding identity correction and reevaluation

Date: 2026-09-10

Status: effective user authorization for the bounded work below.

## Authority

The project user explicitly instructed: "save your findings in a file and
initiate the priority #1. Do your best." Priority 1 was the repair and complete
reevaluation of existing frozen models after correcting ISSUE-0014. This
decision records that direct instruction; it does not imply an additional
expert-group review or approval.

## Authorized work

- Save the findings, repair development protein-to-embedding identity joins,
  and add meaningful identity and ordering regression tests.
- Verify frozen inputs and public-training/inference agreement before scoring.
- Score the existing released development package again with all 49 frozen
  scorers, preserving every row, weight, model, ensemble, and score formula.
- Recompute all original metrics, 2,000-draw component bootstrap intervals,
  source/degree/hub/novel-U diagnostics, and selection/complexity/kill rules.
- Replace audit assertions tied to the previous observed result with checks of
  the result computed by the unchanged scientific rules. Scientific success or
  failure is not predetermined by an auditor.
- Freeze correction source and production evidence in local versioned commits;
  then implement and run a separate independent corrected validator. Do not
  push commits or publish results as part of this authorization.
- Record the corrected result and its limits in the report and current status.

## Preserved boundaries

Original source snapshots, trained checkpoints, embeddings, splits, old
development results and old validation records remain recoverable and
unchanged. New results use the `development_embedding_identity_correction_v2`
namespace. Existing development plaintext may be reused; no further
decryption or key access is authorized. Protected candidates and truth remain
sealed regardless of the development outcome. No retraining, tuning, model
selection rule change, new architecture, external panel, or new biological
claim is authorized.

The operational protected-evaluation hold is separate from the scientific
kill-rule result, which may change after correct scoring. DEC-0039's learned-
model performance interpretation is under correction; DEC-0044's separate
coarse-local diagnostic is unchanged.
