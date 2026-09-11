# DEC-0052: Development-only optimization and one conditional follow-up

Date: 2026-09-11. Authority: explicit user request to de-emphasize BioPlex,
prospectively amend the one-shot protocol, optimize architectures/parameters on
training/development, and retest the development winner if improved. The user
specified **at most two GPU-hours** and **a stable multi-seed gain with a paired
95% interval above zero, without a fixed minimum effect size**.

Authorize only the bounded experiment in
[MODEL_OPTIMIZATION_v1](../../docs/protocols/MODEL_OPTIMIZATION_v1.md). This
supersedes DEC-0050's model-development stop and DEC-0051's prohibition on future
development and another evaluation, to the exact extent stated here. All
original decisions, protocols, data, results, receipts and spent ledgers remain
immutable. This is a new prospective authorization, not a retroactive rewrite.

The existing 150M baseline has strong positive-unlabeled C3 ranking evidence.
BioPlex AP-MS is secondary cross-assay association evidence, not an appropriate
decisive direct-binary panel or a gate on this benchmark. Retain its negative
results and provenance without using them for model selection. Partner-specific
and direct-binding generalization remain unresolved.

No new split, labels, negatives, source acquisition, encoder inference, PLM
fine-tuning, quarantine access, or test-informed model selection is authorized.
The same already-examined test may be used once more only after the frozen
development gate passes and one exact scorer bundle is sealed. A separate
append-only follow-up ledger must link to the immutable original spent ledger;
it must not reset, replace, or masquerade as the original first evaluation.
No second follow-up, adjustment after test feedback, or automatic continuation.

This is local prospective freezing, not independent preregistration. Report
test reuse and all search attempts, including failures. Any resulting test
comparison is a follow-up on an existing benchmark, not a new unseen test or
independent replication. No commit/push or external coordination is requested.
