# iPIN-OpenPPI project status: local-representation diagnostic authorized

**Date:** 2026-08-19

The accepted `DEC-0039` development result remains frozen: the pooled
partner-gated claim is stopped and no model advances to protected evaluation.
Development is spent and protected candidates/truth remain sealed.

`DEC-0040` opens one separate prospective work package to test the specific
global-pooling bottleneck on public training data only. The exact protocol and
executable configuration are:

- `docs/protocols/PUBLIC_TRAINING_LOCAL_REPRESENTATION_DIAGNOSTIC_v1.md`
- `configs/public_training_local_representation_diagnostic_v1.yaml`

The primary test is a label-free ESM-2 150M segment late-interaction oracle in
a deterministic nested C3 component holdout. It compares top-four local
segment cosine against the matched global mean reconstructed from the same
forward pass and retains length, 3-mer, interolog, and hash controls. A
permissive frozen trigger may activate one low-capacity, no-search linear
feature comparison trained on nested C1.

No development/protected access, parent-benchmark change, negative or pseudo-
negative, encoder tuning, interface target, structure/external input, or
probability claim is authorized. A validated result must return through a new
numbered governance decision.

The authoritative execution ledger is `governance/gates/gate_status_v39.yaml`.
