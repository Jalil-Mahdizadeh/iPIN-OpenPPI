---
type: "query"
date: "2026-09-20T13:26:44.851727+00:00"
question: "explain how P pairs are designed"
contributor: "graphify"
outcome: "useful"
source_nodes: ["build_panels.py", "twelve_target_comparison_v1/REPORT.md", "BECN1/README.md", "KRAS/README.md"]
---

# Q: explain how P pairs are designed

## Answer

Expanded from original query via graph vocabulary: [positive, pairs, panel, design, evidence, exposure, twelve].
For the twelve-target example, P means a manually nominated, evidence-supported target-partner interaction. The additional targets and three partners per target were chosen from literature and curated records before scoring; build_panels.py reads the fixed panel_config.json list, validates human UniProt gene/accession identity and canonical sequence hashes, and writes the P rows with evidence/context and prior-pair exposure. It does not derive P labels from model scores or apply a universal numerical evidence-confidence cutoff. The original six inputs were preserved.
The 37 positives are: ERN1 with ERN1, HSPA5, PDIA6, SEC61A1; TP53 with MDM2, MDM4, EP300; EGFR with GRB2, SHC1, CBL; BCL2 with BCL2L11, BAD, BBC3; KEAP1 with NFE2L2, CUL3, SQSTM1; BRCA1 with BARD1, PALB2, BRIP1; KRAS with RAF1, BRAF, ARAF; CDK2 with CCNA2, CCNE1, CDKN1B; HIF1A with ARNT, VHL, EP300; CTNNB1 with CDH1, CTNNA1, TCF7L2; TNFRSF1A with TNF, LTA, TRADD; BECN1 with ATG14, UVRAG, BCL2. ERN1 self-association has explicit supporting evidence; identical endpoints are not automatically positive. Eleven targets have three P and ERN1 four.
Each P partner anchors 100 U controls: 50 broad compartment/TRANSMEM-matched and 50 background proteins, both within half to twice its length. All those pairs retain the same target endpoint. U remains unknown.
Exact accession/sequence audits found BECN1-ATG14 and BECN1-UVRAG in TRAIN-P and KEAP1-SQSTM1 in DEV-P. Main panels retain these with flags; sensitivities exclude them (34 P), then the ERN1 homomer (33 P). These cases therefore are not a wholly unseen test set.
P evidence is heterogeneous (structures, experiments, curated interactions), sometimes domain-, modification-, or state-dependent. Canonical sequence input does not represent these conditions. Panels contain nominated references, not exhaustive catalogues; KRAS RAF partners are homologous. Sources: example/twelve_target_comparison_v1/panel_config.json:3; build_panels.py:193,267; example/ERN1/README.md:11 and other original target README positive tables; example/KRAS/README.md:21; twelve_target_comparison_v1/REPORT.md:63,96.


## Outcome

- Signal: useful

## Source Nodes

- build_panels.py
- twelve_target_comparison_v1/REPORT.md
- BECN1/README.md
- KRAS/README.md