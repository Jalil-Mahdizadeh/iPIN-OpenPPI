# Model-governance utilities

This directory currently contains design-only static governance entry points.
It contains no model acquisition, embedding, baseline, training, development,
or protected-evaluation command.

- `audit_model_governance_and_baseline_training_protocol_v1.py` verifies the
  binding protocol configuration, immutable parent hashes, and 24 frozen
  scientific and custody rules.
- `validate_model_governance_and_baseline_training_protocol_v1.py` independently
  verifies the production audit and reconstructs 20 consequential rule groups
  without importing production protocol code or a model framework.

Both commands must run from clean committed states inside the checksum-pinned
ARM64 data SIF. Production outputs are immutable and written beneath
`artifacts/validation/model_governance/`. Passing either command does not
authorize model files, embeddings, implementation, training, development
release, or protected access.
