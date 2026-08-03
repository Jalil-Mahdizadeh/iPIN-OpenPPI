# iPIN-OpenPPI novelty claim matrix

**Version:** 0.1  
**Date:** 2026-08-03  
**Status:** Preliminary prior-art freeze; a formal scoping review is still required before manuscript claims.

## Claim policy

iPIN-OpenPPI is not described as a newly pretrained protein foundation model. Its intended contribution is an evidence-generation-aware direct-PPI inference and evaluation system. “First”, “unique”, and equivalent priority claims are prohibited until a documented scoping review supports them.

| Candidate contribution | Current assessment | Prior art or constraint | Permitted wording now |
|---|---|---|---|
| ESM-2 sequence backbone | Not novel | Public pretrained protein language models are standard | Reference implementation choice |
| Joint encoding of two sequences | Not novel | PLM-interact, PPLM, and MINT jointly model protein pairs | Existing architectural family |
| Partner-conditioned cross-attention | Not novel alone | Partner-aware interface models already use cross-attention | Component reused and tested |
| Local/sliding interaction windows | Not novel alone | SWING and other local-interface methods exist | Baseline or routing ingredient |
| Positive-unlabelled learning | Not novel alone | Established statistical methodology | Comparator in statistical ladder |
| Leakage-reduced two-entity splitting | Not novel alone | DataSAIL and earlier strict PPI benchmarks address dependency leakage | Required evaluation control |
| Explicit separation of selection, evaluability, contextual binding, and observed assay outcome | Potentially strong | Individual assay-bias and latent-variable ideas exist; integrated sequence-PPI use requires scoping audit | Intended evidence-model contribution |
| Construct- and orientation-aware evidence records with symmetric biological and asymmetric assay heads | Distinctive integration | Experimental studies establish tag, orientation, and assay-version effects | Intended integrated modelling contribution |
| Joint patch-pair router followed by sparse high-resolution cross-attention | Conditional architectural contribution | Partner-aware attention and window models exist; exact router requires prior-art audit and gate success | Candidate architecture, not yet a demonstrated advance |
| Unified C1/C2/C3, 30% clustering, full temporal freeze, assay/source/species/interface and PLM-exposure audit | Strong benchmark contribution if completed | Individual controls exist separately | Integrated leakage-controlled benchmark |
| Calibrated hypothesis retrieval with uncertainty and evidence provenance | System contribution | Retrieval, calibration, and uncertainty exist separately | Integrated prioritization workflow |
| Arrhenius/Apptainer implementation | Engineering, not scientific novelty | Reproducible HPC containerization is established | Reproducibility contribution only |

## Current defensible project statement

> The intended novelty of iPIN-OpenPPI is an evidence-generation-aware framework for sequence-based direct-PPI prioritization that explicitly models non-random testing, technical evaluability, assay sensitivity and specificity, construct-level provenance, and conditional negative evidence, and evaluates partner-aware sequence models under strict biological, temporal, and pretraining-exposure controls.

## Architectural continuation rule

Sparse routing is promoted to a core contribution only if oracle regions help, the learned joint router captures at least half of the oracle gain, strict C3/interface-family gains survive, and the efficiency thresholds in `configs/gates_v3.yaml` pass. Otherwise the project uses the simpler joint encoder and makes no routing novelty claim.

## Preliminary primary references

- PLM-interact: <https://doi.org/10.1038/s41467-025-64512-w>
- Protein Pair Language Model (PPLM): <https://doi.org/10.1038/s41467-026-70457-5>
- MINT, “Learning the language of protein-protein interactions”: <https://doi.org/10.1038/s41467-025-67971-3>
- SWING: <https://doi.org/10.1038/s41592-025-02723-1>
- DataSAIL: <https://doi.org/10.1038/s41467-025-58606-8>
- PLM pretraining-leakage analysis: <https://doi.org/10.1038/s42256-025-01176-7>
- Binary-assay version and orientation study: <https://doi.org/10.1038/s41467-019-11809-2>
- Experimental assessment of AI-based interactome mapping: <https://doi.org/10.1038/s41467-026-70942-x>

