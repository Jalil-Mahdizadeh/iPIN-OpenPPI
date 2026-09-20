---
type: "query"
date: "2026-09-20T17:37:23.031777+00:00"
question: "how possible the original tuna is so good? investigate it."
contributor: "graphify"
outcome: "useful"
source_nodes: ["tuna", "adapter.py", "metrics"]
---

# Q: how possible the original tuna is so good? investigate it.

## Answer

Expanded from the original query using graph vocabulary: tuna original exposure training validation comparison metrics scores frozen adapter audit concordance. Investigation: example/original_tuna_investigation_v1/REPORT.md. Original versus retrained macro PU is 0.804221 versus 0.780305 on twelve targets; omit EGFR and it is 0.786557 versus 0.783026. EGFR contributes 86.5 percent of the net PU gap and 90.5 percent of the MAP gap; eight PU wins but six AP wins; descriptive paired-target intervals include zero. Original native authors-checkpoint inference agrees within 1.79e-7 on fifty fixtures including all thirty-seven positives; all saved scores replay exactly and all original/runtime state tensors are identical. Replacing queries with the other eleven targets lowers original PU to 0.534064, and EGFR to 0.513805 from 0.998519, supporting query-dependent ranking. Exact original TRAIN/validation exposure is absent for EGFR GRB2 SHC1 CBL, but the best local TRAIN sequence matches are ERBB3 GRAP2 SHC4 CBLB; original TRAIN contains positive ERBB3-GRAP2 ERBB3-SHC4 and ERBB3-CBLB pairs, all absent from retrained TRAIN/development. EGFR, ERBB3, SHC1 and SHC4 have zero actual retraining TRAIN rows by accession despite sequence catalogue membership. EGFR-ERBB3 local alignment has 47.4 percent identity, query coverage 83.0 percent and reference coverage 74.8 percent; the strict 80-percent-both-coverage filter misses it, so do not interpret that filter as no related-protein exposure. Family transfer is plausible but causality and checkpoint complete training history are not established. GP adjustment changes PU only 0.000563; simple partner degree reaches 0.6098. Context U is harder than low-plausibility U. Completed main benchmark C3 favors retrained 0.815875 over original 0.695658; read only published aggregates. No model tuning, protected test pairs, or changes to previous scientific records.

## Outcome

- Signal: useful

## Source Nodes

- tuna
- adapter.py
- metrics