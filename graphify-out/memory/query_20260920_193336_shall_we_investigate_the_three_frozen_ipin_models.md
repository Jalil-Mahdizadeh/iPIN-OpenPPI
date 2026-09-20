---
type: "query"
date: "2026-09-20T19:33:36.627434+00:00"
question: "shall we investigate the three frozen ipin models on non-human protein space?"
contributor: "graphify"
outcome: "useful"
source_nodes: ["score_models.py", "parse_sources.py", "analyze.py", "FROZEN_PAIR_MODELS_v2.md"]
---

# Q: shall we investigate the three frozen ipin models on non-human protein space?

## Answer

Expanded from original query via graph vocabulary: frozen, human, training, benchmark, sequence, homology, transfer, model, scorer, evidence, organism, protein. User selected broad transfer across model organisms, testing interactions within species. Completed benchmark/nonhuman_transfer_v1 with all three unchanged frozen iPIN ensembles: mouse (10090), fly (7227), worm (6239), budding yeast S288C (559292), Arabidopsis (3702), E. coli K-12 (83333). Fifty targets/species, 300 targets, 1,385 P rows +60,000 U rows, 30,497 distinct sequences, 14,492,932 residues. Per target 2-10 P, 100 background U plus disjoint 100 length/degree-matched U, not U per P. All 30,000 matched U met primary tier. Archived IntAct release252 2026-01-09 original XML; direct or binary two-hybrid evidence, no negative/modelled/expansion/intramolecular flags, only tag participant features. Initial MI:0407/no-feature feasibility left too few fly/worm targets; documented metadata-only adjustment before panel selection/scoring, preserving initial audits and exact initial parser/protocol. No scores used in eligibility or target choice. Fixed hash sampling. 50-2000 standard-AA sequences; source-evidence universe rather than whole proteomes. Independent XML parser verified 1,753 supporting evidence records and no selected U was a reported co-participant pair.
Matched-U equal-target PU concordance in model order affine/optimized/TUnA-retrained: mouse .726431/.717685/.714149; fly .643592/.629230/.678287; worm .563160/.595613/.598281; yeast .595237/.633215/.623678; Arabidopsis .618747/.670103/.715148; Ecoli .551783/.560494/.557380. Equal-species .616492/.634390/.647821. Retrained-minus-optimized .0134306, paired target-bootstrap95%[-.0045416,.0317502], 10,000 draws. Highest point estimate is not established superiority; intervals conditional on fixed panels, shared targets/partners/studies and residual homology not fully captured. Ecoli is weakest and 83.9% of unique P supported by one paper. TUnA Ecoli recall@10 .080905 versus optimized .117762 and analytical random-order expectation .096438; point references, no tested below-random claim. Ranking by concordance and early retrieval differs: affine leads mouse PU but retrained leads mouse MAP/recall; optimized leads yeast PU but retrained leads yeast recall. Equal-species matched MAP .148566/.158203/.166412; recall10 .189618/.203049/.224489.
Actual human TRAIN has 4,675 pair endpoints, development pair endpoints 7,225. External sequences include53 exactTRAIN and82 exactDEV matches (overlap possible); no external P pair exactly in TRAIN/DEV; two mouse U rows match prior sampled human U. Exact endpoint-exclusion sensitivity retains similar overall PU .616056/.633637/.648320. Pinned MMseqs18-8cc5c s7.5 E<=.001, local-best and max-identity both80%coverage matches, target and both-endpoint homology strata. No qualifying hit does not prove no homology or ESM pretraining exposure. Human C3 and external candidate designs are not numerically comparable as a controlled species effect.
All previous retrieval metrics at K5/10/20 for background/matched/allU; 5,373 target metric rows and126macro rows independently checked using sklearn ROC/AP/NDCG and combinatorial tie oracles. Fresh embeddings, no training/refit/calibration; full model input hashes and symmetry pass. All three TUnA native oracle errors <=6.199e-6 (tolerance1e-5), buffers unchanged. Data/iPIN/TUnA SIFs pinned. iPIN pooled pipeline317.18s for both ensembles; retrained TUnA450.37s; not a fair per-model speed comparison. REPORT.md, README, PROTOCOL, input and final manifests, complete score/metric/audit tables, PNG/PDF/SVG figure. Root README, benchmark README, model/report indexes updated. Existing human examples, protected test pairs/truth, versioned model cards, registry and weights untouched. No universal industrial recommendation for bacterial screening from this evidence.

## Outcome

- Signal: useful

## Source Nodes

- score_models.py
- parse_sources.py
- analyze.py
- FROZEN_PAIR_MODELS_v2.md