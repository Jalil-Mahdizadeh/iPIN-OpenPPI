# Canonical data schemas

Canonical tables contain deterministic, auditable mappings derived from immutable staging records. They never overwrite source-native identifiers, silently select among conflicting candidates, or authorize a biological label.

The active identifier/construct reconciliation contract is `primary_reconciliation_v1.yaml`.

`benchmark_eligibility_and_sequence_component_audit_v1.yaml` governs the
preconstruction Space III eligibility and sequence-component audit. Its tables
contain endpoint eligibility, distinct reference sequences, component
memberships, and aggregate feasibility only; candidate-pair rows, interaction
labels, and split assignments are outside the contract.

`pre_split_feasibility_and_leakage_stress_test_v1.yaml` governs the
aggregate-only child audit authorized by `DEC-0019`. Its six summary tables
contain positive-network distributions, source composition, similarity-search
sensitivity, leakage-graph effects, ephemeral allocation-opportunity
distributions, and claim boundaries. Endpoint, component, pair, trial,
C1/C2/C3-label, and split-assignment rows are prohibited.
