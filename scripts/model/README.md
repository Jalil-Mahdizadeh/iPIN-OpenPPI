# Model-governance utilities

This directory contains the governed model-runtime entry points. Stage 1 model
acquisition, frozen embedding extraction, public-only training, and training
validation are closed under `DEC-0031`. Development execution is separately
bounded by `DEC-0032`; protected evaluation remains prohibited.

- `audit_model_governance_and_baseline_training_protocol_v1.py` verifies the
  binding protocol configuration, immutable parent hashes, and 24 frozen
  scientific and custody rules.
- `validate_model_governance_and_baseline_training_protocol_v1.py` independently
  verifies the production audit and reconstructs 20 consequential rule groups
  without importing production protocol code or a model framework.

The development-only commands are:

- `audit_development_prerelease_v1.py`, which validates the release boundary,
  exact scorer census, model algebra, metrics, bootstrap, and policy fixtures
  without resolving any private key;
- `release_development_for_evaluation_v1.py`, which is disabled until a later
  committed activation gate records passing production and independent
  pre-release reports, and then resolves only the development key;
- `run_development_scoring_v1.py`, which scores the nine released-development
  cells with nine controls, 30 selected checkpoints, and ten frozen ensembles;
  and
- `evaluate_development_v1.py`, which applies the frozen metrics, diagnostics,
  model selection, complexity gates, and kill rules without training.

Run model-bearing commands inside the checksum-pinned ARM64 model SIF. Private
development identities and score rows stay below `.private/`; public outputs
contain aggregates and hashes only. None of these commands can authorize or
open protected candidates, protected truth, or either protected private key.
