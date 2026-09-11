# DEC-0051: Authorize one final protected evaluation, not further development

Date: 2026-09-11. Authority: explicit user instruction, "conduct the model's
performance on the final test."

Authorize one final evaluation of the development-selected frozen 150M affine
three-seed ensemble against prespecified controls. This narrowly supersedes the
stop-before-protected-access disposition; DEC-0050's stop on model development
and all source quarantine restrictions otherwise remain in force. No fitting,
encoder inference, model/seed selection on test, resplitting, or new labels.

Before any candidate opening, freeze the exact scorer bundle, dependencies,
features, implementation, metric rules and synthetic validation records under
`docs/protocols/PROTECTED_FINAL_TEST_v1.md`. Check all upstream hashes and the
embedding identity join. The original protected package's one-first ledger is
binding; no new ledger namespace or multiple per-baseline truth evaluations.
The versioned comparison harness may submit a fixed bundle of separate exact
two-column prediction files in one attempt, with paired uncertainty. It must
retain the original privacy, prediction-freeze and fail-closed requirements.

The host disables network namespaces and PID virtualization. A CPU-only
restriction-increasing alternative may be qualified before access: pinned
Apptainer, no checkout/home/proc/sys/hostfs mounts, only allowlisted read-only
frozen inputs and account-private stage outputs, closed inherited descriptors,
no_new_privs and inherited native-ABI seccomp denial of networking, io_uring,
cross-process access and namespace/mount escape calls. Test enforcement and
child inheritance before accessing any protected input. Do not merely set an
offline environment flag. No elevated privileges or host settings changes.
If qualification fails, stop with the candidate/truth packages still sealed.

Stage candidate key, scorer and truth key separately. Close scoring, validate
and hash every prediction, and exclusively reserve the existing package ledger
before providing the truth key to the metric process. An attempt is consumed
irrevocably at reservation, even on failure. Release aggregate metrics only;
all identities, row predictions, errors and logs remain private. A final test
result must not trigger tuning or a repeat evaluation of this split.

This is local prospective freezing, not independent external preregistration.
Implementation checks by the same author are not independent replication.
No commit/push, source publication, resource purchase, or external coordination
is authorized by this instruction.
