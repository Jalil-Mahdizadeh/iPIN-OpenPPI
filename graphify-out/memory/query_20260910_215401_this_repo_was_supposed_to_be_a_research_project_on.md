---
type: "query"
date: "2026-09-10T21:54:01.240204+00:00"
question: "this repo was supposed to be a research project on developing a model for protein-protein interaction prediction. However, in the end it became a dead end. explore it, understand it, and brainstorm and let me know if you beleive that it is actually a dead end."
contributor: "graphify"
outcome: "corrected"
correction: "Verified correction complete: the selected small affine model has C3 concordance 0.784142 instead of the invalid original 0.491608. All 329 tests, 9 production checks and 17 standalone independent checks pass. Useful development ranking signal exists, but all gated configurations still fail original complexity/stability gates. Protected evaluation remains sealed and unauthorized. See PROJECT_STATUS_v45 and the 2026-09-10 reassessment report."
source_nodes: ["align_embedding_matrix()", "_storage_rows_from_manifest()", "score_cell()"]
---

# Q: this repo was supposed to be a research project on developing a model for protein-protein interaction prediction. However, in the end it became a dead end. explore it, understand it, and brainstorm and let me know if you beleive that it is actually a dead end.

## Answer

Priority #1 is complete under the user's DEC-0045 authorization. The repository is not established as a general scientific dead end, although the current partner-gated complexity claim still fails its original rules. Graph vocabulary expansion used in the initial investigation: [protein, interaction, model, results, diagnostic, benchmark, identifiability, leakage]. Graph navigation was followed by direct source/artifact checks and a fully audited correction.
Development had indexed length/hash-ordered ESM matrices with SHA-only endpoint coordinates, mismatching 16,999/17,000 proteins in each encoder. Production now joins manifest identity to row_index explicitly (src/ipin_openppi/development_evaluation/embedding_identity.py). The standalone v2 validator retains storage-order matrices and translates pair coordinates instead, imports no production modules, and checks all raw vector hashes and normalization values.
Corrected frozen 150M affine lr3e-4 ensemble: C3=0.784142246349548, C2=0.7997974202182104, C1=0.8485650687614544. Its invalid original C3 was 0.49160758476715566. Its C3 95% component-bootstrap interval is [0.7428201383689814,0.8527162689983394]. Best C3 gated ensemble=0.7595539108084669; gated-minus-simple difference=-0.024588335541081086, paired interval [-0.07051158965192768,0.033186882384296755]. All gated configurations fail seed stability and incremental-benefit gates. Original selected candidate is now the small affine ensemble, but unchanged scientific disposition remains stop_complex_model_claim_and_stop_before_protected_evaluation.
Full original development scope: 9 cells, 9,026,108 rows, 49 scorers including 30 checkpoints and 10 ensembles; 2,000 paired component bootstrap replicates. Original rows, weights, scorer definitions, bootstrap draws and scientific rules preserved. 329 unit tests, 9/9 production audit checks and 17/17 standalone independent checks passed. All 270,783,240 learned values reproduced exactly, maximum difference zero. Source/evidence commits: 5548baa / 1bae702 / bcebdca / 37c030b. No training, checkpoint change, repeat decryption, protected plaintext/key access or push. Protected ciphertext hashes unchanged.
Authoritative report: docs/reports/m1/M1_Research_Reassessment_and_Embedding_Identity_Findings_2026-09-10.md. Current status/ledger: governance/PROJECT_STATUS_v45.md and governance/gates/gate_status_v45.yaml. Validated artifact registry: artifacts/validation/development_evaluation/development_embedding_identity_correction_v2/INDEPENDENT_VALIDATION_ARTIFACT_REGISTRY.json.
These are released-positive-versus-unlabeled ranking results, not biological interaction accuracy or calibrated probability. The unrelated coarse-local diagnostic remains negative; its top-four segment cosine heuristic was not an information upper bound. A recommended future question is partner-specific retrieval versus endpoint/assay propensity, prospectively defined on public-training/internal-validation data. No additional architecture, training or protected evaluation was authorized.

## Outcome

- Signal: corrected
- Correction: Verified correction complete: the selected small affine model has C3 concordance 0.784142 instead of the invalid original 0.491608. All 329 tests, 9 production checks and 17 standalone independent checks pass. Useful development ranking signal exists, but all gated configurations still fail original complexity/stability gates. Protected evaluation remains sealed and unauthorized. See PROJECT_STATUS_v45 and the 2026-09-10 reassessment report.

## Source Nodes

- align_embedding_matrix()
- _storage_rows_from_manifest()
- score_cell()