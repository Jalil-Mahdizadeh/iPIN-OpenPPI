# Risk register

**Last updated:** 2026-08-03

| ID | Risk | Likelihood | Impact | Current mitigation | Owner | State |
|---|---|---:|---:|---|---|---|
| R-001 | Primary systematic search space or evaluability metadata cannot be reconstructed | Certain for current public release | Critical | Validated audit complete; PU ranking amendment proposed; never impute unsupported negatives | Codex | Realized; amendment awaiting approval |
| R-002 | Latent sensitivity/specificity model is not identifiable | High | High | Keep latent probability inactive; use prior-sensitivity diagnostics and a non-probabilistic compatibility score | Codex | Open |
| R-003 | Public PLM pretraining leaks test-sequence information | High | High | Exposure audit, strict clustering, similarity reporting, and cautious causal claims | Codex | Open |
| R-004 | Partner-aware router adds complexity without signal | Medium | Medium | Oracle-first gate; remove router if oracle or learned-routing criteria fail | Codex | Open |
| R-005 | ARM64 dependency or GPU-container incompatibility | Medium | High | Minimal SIF qualification first; pinned definitions, checksums, repeat fixtures, checkpoint test | Codex | Mitigating |
| R-006 | Four-GPU or multi-node communication underperforms | Medium | Medium | Single-GPU default; separate four-GPU gate; no multi-node requirement at month six | Codex | Open |
| R-007 | Storage becomes disordered or irreproducible | Medium | High | Fixed tree, immutable versioning, project-local caches, manifests, checksums, and no overwrites | Codex | Mitigating |
| R-008 | No laboratory validation weakens biological discovery claims | Certain | High | Enforce computational-hypothesis claim ceiling; use frozen temporal and independent evidence validation | Expert group | Accepted |
| R-009 | Source licensing prevents redistribution | Medium | High | Source/license register before ingestion; release manifests or derived summaries when raw redistribution is prohibited | Codex / sponsor | Open |
| R-010 | Candidate-universe prevalence makes calibration misleading | High | High | No probability claim in PU-R; freeze candidate sampling and class-prior sensitivity; defer calibration to TU-C | Codex | Open |
| R-011 | PU ranking is misreported as biological classification or precision | High | High | Machine-readable claim ceiling, metric-name controls, data/model cards, and expert approval of public wording | Codex / expert group | Open |

