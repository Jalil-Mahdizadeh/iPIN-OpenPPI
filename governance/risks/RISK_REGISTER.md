# Risk register

**Last updated:** 2026-08-04

| ID | Risk | Likelihood | Impact | Current mitigation | Owner | State |
|---|---|---:|---:|---|---|---|
| R-001 | Primary systematic search space or evaluability metadata cannot be reconstructed | Certain for current public release | Critical | PU ranking amendment accepted; retain permanent source limitation and never impute unsupported negatives | Codex | Realized; mitigated by scope |
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
| R-012 | Heterogeneous negative evidence is collapsed into a universal nonbinding class | High | Critical | Separate manual experimental and structural non-contact families; preserve context; tier reliability; retain positive conflicts; universal class prohibited | Codex | Open |
| R-013 | Historical Negatome stringent filtering is mistaken for current conflict-free evidence | High | High | Reconcile every mapped pair against frozen current HuRI/IntAct/direct-PPI evidence and flag rather than discard conflicts | Codex | Open |
| R-014 | Negatome redistribution terms are assumed from public download or article license | Medium | High | Internal-only raw payloads; do not commit record-level data; publish only code, hashes, schema, and non-extractive aggregates pending permission | Codex / sponsor | Open |

