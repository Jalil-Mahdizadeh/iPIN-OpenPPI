# Reading the corrected P/U results

This note was written after analysis and independent validation. It explains
the results; it does not change the frozen panels, metrics or model definitions.

Every one of the original **1,555 published P pairs** was retained. Each has
100 assigned U, and all **155,500 U pairs are globally distinct**. The models
scored all **157,055 pairs**. The 39 P not reconfirmed in the second laboratory
assay remain P and have no special role in selecting U.

## Concordance

Give every P equal weight and compare it only with its assigned 100 U:

| Model | P-vs-U concordance | Exploratory 95% interval |
|---|---:|---:|
| Baseline iPIN | 0.751871 | 0.729296–0.774156 |
| Optimized iPIN | 0.797524 | 0.772429–0.821539 |
| TUnA retrained | 0.816251 | 0.788643–0.842592 |

Scores are shown to six decimal places. These measure ranking of observed P
versus source-unreported U, not accuracy against verified biological negatives.
Full precision and the equal-target summaries are in `metrics.csv`.

All three exploratory paired concordance intervals for the ordered model
differences are above zero. TUnA minus optimized iPIN is **0.018727** with
interval **[0.005955, 0.031957]**. This supports the observed ordering within
this fixed panel and target-bootstrap scheme. It does not establish a general
model winner across independent studies or sampling designs.

## Metadata and exposure limits

Ranking by archived human-partner association degree alone gives concordance
**0.613367**, so the dataset retains source-metadata signal despite matching.
The model point estimates exceed this control. Matching bins and length ranges
are coarse; this comparison does not prove that study or sequence biases have
been removed. Reported fallback counts are **149,120 U matching both criteria**
and **6,380 matching length only**.

Excluding exact supervised TRAIN/development endpoint matches leaves a separate
sensitivity with **631 P and 38,898 U**. Its concordances are **0.754275**,
**0.783991** and **0.796067**, respectively. It has variable U counts per P and
does not replace the requested full 1:100 primary benchmark. Protein-language-
model pretraining exposure remains unaudited.

The 10,000 bootstrap draws preserve groups of panels sharing a yeast target.
Shared human proteins, homology and one publication still limit independence.
The conclusions concern human–S288C reference-protein ranking under this U
sampling design. U is unreported in the declared archived source and may
contain real interactions or interactions reported elsewhere.

The dataset was designed after the earlier positive scores had been inspected.
Its construction used no model scores, and the new U assignments, inference
code, models and metrics were frozen before new scoring. Treat this as an
exploratory follow-up, not a fully prospective evaluation.
