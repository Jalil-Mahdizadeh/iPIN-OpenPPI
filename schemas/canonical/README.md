# Canonical data schemas

Canonical tables contain deterministic, auditable mappings derived from immutable staging records. They never overwrite source-native identifiers, silently select among conflicting candidates, or authorize a biological label.

The active identifier/construct reconciliation contract is `primary_reconciliation_v1.yaml`.

`benchmark_eligibility_and_sequence_component_audit_v1.yaml` governs the
preconstruction Space III eligibility and sequence-component audit. Its tables
contain endpoint eligibility, distinct reference sequences, component
memberships, and aggregate feasibility only; candidate-pair rows, interaction
labels, and split assignments are outside the contract.
