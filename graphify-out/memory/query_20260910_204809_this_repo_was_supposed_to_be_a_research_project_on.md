---
type: "query"
date: "2026-09-10T20:48:09.601548+00:00"
question: "this repo was supposed to be a research project on developing a model for protein-protein interaction prediction. However, in the end it became a dead end. explore it, understand it, and brainstorm and let me know if you beleive that it is actually a dead end."
contributor: "graphify"
outcome: "corrected"
correction: "The DEC-0039 near-chance learned-model development results cannot support a scientific dead-end conclusion: scoring and its independent validator index length/hash-ordered embedding matrices with SHA-only endpoint indices, mismatching 16,999 of 17,000 proteins in both encoders. Training uses the correct identity map. Corrected performance remains unknown. The separate coarse local diagnostic is unaffected by this specific bug."
source_nodes: ["load_endpoint_universe()", "score_cell()", "ordered_records()", "M1 development release and evaluation final report v1", "local_diagnostic/pipeline.py"]
---

# Q: this repo was supposed to be a research project on developing a model for protein-protein interaction prediction. However, in the end it became a dead end. explore it, understand it, and brainstorm and let me know if you beleive that it is actually a dead end.

## Answer

Review conclusion: this repository has not established that its learned PPI models are a scientific dead end. A confirmed development-scoring identity defect invalidates the principal near-chance learned-model results underlying DEC-0039.

Graph query expansion from actual vocabulary: [protein, interaction, model, results, diagnostic, benchmark, identifiability, leakage]. The graph led to the blueprint, PU-R design, Stage 1 reports, DEC-0039, and the separate local diagnostic. Direct source and frozen-artifact checks then revealed the defect.

Project understanding: the initial scope was evidence-aware, sequence-based direct human heteromeric PPI prioritization, with calibrated assay prediction conditional on reconstructing a tested/evaluable universe. The frozen HuRI public-data audit could not recover that denominator, so the project adopted positive-versus-unlabeled ranking of released evidence. It constructed 17,000 endpoints, 30% local_domain_union component separation, 16,799 public training positive pairs, 2,000,000 public training U rows, and frozen C1/C2/C3 evaluation. Stage 1 trained 30 runs of small affine or nonlinear symmetric heads over frozen mean-pooled ESM-2 150M/650M embeddings. It did not train a residue joint encoder, cross-attention model, or adapted PLM.

Confirmed bug:
- src/ipin_openppi/stage1/embeddings.py:89-110 orders embedding records by (sequence_length, sequence_sha256).
- src/ipin_openppi/stage1/embeddings.py:281-326 standardizes without reordering rows; its manifest records sequence_sha256 and row_index.
- src/ipin_openppi/stage1/preparation.py:90-91 and :164-170 maps training pairs to this length/hash order.
- src/ipin_openppi/development_evaluation/scoring.py:98-123 instead creates endpoint indices in SHA256-only order.
- deterministic_scores at :255-257 returns these hash-order pair indices.
- score_cell at :460-477 loads the original standardized matrix without a row permutation and uses those indices for every learned scorer.
- scripts/model/run_development_scoring_v1.py:95-105 supplies the original frozen standardized matrix paths.
- scripts/model/validate_development_completed_independent_v1.py:1617-1644 builds the same hash-order endpoint indices and :1133-1144 loads the original matrices unchanged. Its separate implementation reproduces the same identity error.
- Current production scoring.py SHA256 874b84270be2fe47211a3936907762ebb6442052eb6928adbdcda50ace60ca5f matches the frozen independent validation report, confirming this is the evaluated code.

Read-only verification in pinned containers/images/ipin-data-arm64_0.1.2.sif on Arrhenius, with repository bound read-only:
- Read public eligible endpoint Parquet, both actual ESM embedding manifests and matrices, normalization artifacts, and public training positive arrays.
- Both models: 16,999 / 17,000 SHA-order indices point to a different protein's stored vector; only 1 index agrees.
- Both standardized matrix hashes match the frozen manifests.
- Checked raw vector hashes and exact standardized reconstruction on nine spread-out rows per model.
- Example: evaluation index 0 expects a 2,137-residue protein; the actual matrix row 0 belongs to a 25-residue protein. The intended protein is in matrix row 16,801.
- All 16,799 public training positive pairs have endpoint indices consistent with the actual embedding identity order.
- No development or protected pair package was opened, no scores or metrics were recomputed, and no code/frozen scientific artifact was changed.

Scope: all 30 learned-model columns and ten derived ensembles in all nine development cells use the mismatched lookup. Consequently learned-model metrics, learned-versus-control comparisons, candidate selection and scientific kill decisions cannot establish performance on the intended proteins. The bug does not establish that corrected models will perform well. Deterministic degree, length, k-mer and interolog controls use their own consistently keyed universe and are not affected by this specific mismatch.

The separate public-training local diagnostic creates records and pair lookup in the same length/hash order (src/ipin_openppi/local_diagnostic/pipeline.py:283-287 and :677-690); this particular bug does not invalidate its result. Its primary coarse top-four segment cosine scored 0.553171 versus matched global cosine 0.568759 on 650 nested-C3 positives, delta -0.015588, missing the +0.01 trigger. This is evidence against that coarse similarity heuristic, not a learned interaction-information upper bound or an impossibility result for token-aware models. Phase B was not run.

Research assessment:
1. Highest-value next action is an explicitly scoped evaluation correction using the already frozen models and original rules, without retraining or architecture selection. Join every scored protein to embedding rows by sequence hash, validate against manifest vector identity, test invariance to endpoint-table permutation, and independently validate training/evaluation score agreement on public pairs. Then repeat development scoring, all dependent metrics/intervals and frozen decisions in new versioned artifacts, preserving original evidence and sealed protected test.
2. If corrected models show useful gains, focus on evidence-aware partner prioritization and query-level retrieval beyond length, sequence-similarity and degree explanations. Positive-versus-U concordance is evidence recovery, not biochemical binding probability.
3. If they fail, a single prospective learned local/partner-aware comparison may be justified, but the 30 pooled-head runs did not exhaust architecture possibilities. Published PPLM (https://www.nature.com/articles/s41467-026-70457-5) and MINT (https://www.nature.com/articles/s41467-025-67971-3) demonstrate existing pair-aware architectural families; this reduces architectural novelty and requires rigorous pretraining interaction-exposure auditing before comparison.
4. A narrower isoform/partner-effect task is biologically coherent: the TF audit found 848 contrast groups, only 149 fully reference-mapped, and no exact/UniRef90 endpoint-protected group under the audited exposure snapshot. It is a separate research design with construct and exposure limitations, not a ready-made strict C3 benchmark.
5. The evidence semantics and benchmark infrastructure retain value independent of model success. A resource/methodology contribution requires a clear question, usable artifacts and substantive comparisons; generic leakage warnings alone are established prior art.

Immediate decision: fund the identity correction and a valid frozen-model evaluation before retiring the project or committing to a replacement architecture. Corrected development performance is currently unknown.

## Outcome

- Signal: corrected
- Correction: The DEC-0039 near-chance learned-model development results cannot support a scientific dead-end conclusion: scoring and its independent validator index length/hash-ordered embedding matrices with SHA-only endpoint indices, mismatching 16,999 of 17,000 proteins in both encoders. Training uses the correct identity map. Corrected performance remains unknown. The separate coarse local diagnostic is unaffected by this specific bug.

## Source Nodes

- load_endpoint_universe()
- score_cell()
- ordered_records()
- M1 development release and evaluation final report v1
- local_diagnostic/pipeline.py