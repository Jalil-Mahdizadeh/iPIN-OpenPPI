---
type: "query"
date: "2026-09-20T11:13:41.535698+00:00"
question: "in the 'example' folder where i conducted a real six-target benchmark, what else matrics we can calculate besides the P-vs-U concoedance?"
contributor: "graphify"
outcome: "useful"
source_nodes: ["six_target_comparison_v1/README.md", "six_target_comparison_v1/REPORT.md", "run_comparison.py"]
---

# Q: in the 'example' folder where i conducted a real six-target benchmark, what else matrics we can calculate besides the P-vs-U concoedance?

## Answer

Expanded from original query via vocab: [six, target, comparison, metrics, recall, precision, rank, positive, unlabeled]. Graph sources confirmed by reading example/six_target_comparison_v1/{README.md,REPORT.md,run_comparison.py,per_target_metrics.csv,macro_metrics.csv,positive_partner_ranks.csv,all_six_targets_scores.csv}. The panels contain 19 nominated positives and 1900 unlabeled pairs across six targets, with 3-4 positives per target. Already saved: P-versus-U concordance by target/U stratum and exposure/homomer subset, positive rank intervals and midranks, tie-fractional top-10 recovery, and comparisons with each positive's own context/background controls. Recommendation, not computed new results: extend known-positive recall and recovered counts to K=5,10,20; calculate per-target average precision and equal-target MAP; NDCG@10/20 with binary known-positive relevance; first-positive rank and mean reciprocal rank; number of targets recovering at least one known positive at each K. Optional known-positive enrichment EF@K=(recovered_P/K)/(P/N) rescales recall by N/K, so is not independent evidence. Ordinary ROC-AUC with P=1 and U=0 equals existing concordance. AP and NDCG describe retrieval of the nominated positives only; U remains biologically unknown, so these do not establish true interaction precision. Do not report accuracy, specificity, F1, MCC, or calibration as biological performance from these labels. Scikit-learn official AP/NDCG definitions and Jain, White, Radivojac AAAI 2017 (doi:10.1609/aaai.v31i1.10937) support this interpretation. Example already documented: optimized iPIN BCL2 concordance 0.972 with positive ranks 7,9,15, giving 0/3 recovered at K=5 and 3/3 at K=20. Calculate within each target, equal-weight macro average, retain tie handling, context/background and exposure/homomer sensitivities; 3-4 positives per target limits precision and requires displaying all six target results. Existing scored CSVs suffice; no model inference needed. No new scientific metrics computed in this query turn.

## Outcome

- Signal: useful

## Source Nodes

- six_target_comparison_v1/README.md
- six_target_comparison_v1/REPORT.md
- run_comparison.py