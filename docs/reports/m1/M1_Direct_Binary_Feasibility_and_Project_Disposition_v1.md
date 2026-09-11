# Direct-binary feasibility and project disposition

2026-09-11 · DEC-0050 · bounded source triage, not a model experiment.

## Decision

**Stop the current learned-head development track. A separate extracellular
specificity study remains plausible, but is not evaluation-ready.** The search
found a concrete candidate, SAVEXIS; it did not establish sufficient matched
support or clean confirmation. Do not call this either a rescued model or proof
that protein-interaction prediction is a dead end.

The preceding [composition/order study](M1_Composition_Order_Challenge_v1.md)
found no established incremental learned-head value over simple composition,
and its matched-partner comparison lacked support. Those findings are preserved;
there is no reason to launch another architecture sweep.

## What the bounded check found

Two new experimental programmes were followed up, alongside existing aggregate
audits. This was an informed shortlist, not an exhaustive literature review.

| Source | Relevant evidence | Disposition |
|---|---|---|
| [Shilts 2022 SAVEXIS](https://doi.org/10.1038/s41586-022-05028-x), Wright/Sanger programme | Direct extracellular measurements, construct and expression metadata; selected secondary screen | Best candidate for a separate data-reconstruction pilot; not qualified for scoring |
| [Wojtowicz 2020 apECIA](https://doi.org/10.1016/j.cell.2020.07.025), Garcia/Zinn/Novartis programme | 564-protein library with constructs/QC; primary screen pooled, positive wells deconvoluted | Not a ready-made dense individual-pair P/N dataset |
| Earlier Negatome/IntAct, Lambourne 2026 and TF-isoform 2025 audits | Conditional/selected evidence with previously documented opportunity, construct or exposure limitations | No new qualification; quarantined pair data not reopened |

For apECIA, the supplement describes Data S4 as observed-interaction readouts,
and the [Dryad inventory](https://doi.org/10.5061/dryad.xsj3tx9bd) supplies that
table plus alignments. Coverage of 318,096 combinations in pooled screening
must not become 318,096 independently evaluated pair labels. This is a
limitation of the inspected release for our purpose, not of its biological value.

## SAVEXIS: promising data, concrete unresolved prerequisites

Acquired **11 files / 3,621,415 bytes** from upstream commit
`82442448e9440c9e847415173979871950e27d77`, with byte counts, Git blob hashes and
SHA256 verified. Raw files remain local; upstream scripts were not executed.

Our [structural inventory](../../../artifacts/results/direct_binary_feasibility_v1/SOURCE_STRUCTURE.json)
finds 363,456 primary numeric cells including controls. Exact metadata aliases
identify a **565 × 630** rectangle (355,950 cells), not a complete 630 × 630
orientation matrix. Secondary data contain 36,094 finite measurements and two
blanks including controls; the exact-alias 187 × 187 rectangle contains 34,967
finite cells. These are measurements, **not negative counts**. Unmatched axes,
expression failures, controls and selection require explicit reconciliation.

Metadata include 630 entries, 629 nonblank first-chain sequences and 36
two-chain entries. The 82 sequences initially flagged for noncanonical
characters all contain a single terminal stop marker; they are not 82 corrupt
constructs. Tags, maturation, multichain identity and QC joins still need a
documented assay-specific mapping. Both concentration and band measurements
are available, so this is substantially better than a positive-only network.

One reproduction detail needs clarification: the paper's Methods say
secondary measurements count "three times more", while the
[pinned processing script](https://github.com/jshilts/shilts-et-al-2022-immunoreceptors/blob/82442448e9440c9e847415173979871950e27d77/organized_code_screen_processing/leuk_screen_data_processing_tidy.R#L202)
uses 0.8 versus 0.2, a 4:1 ratio. The inspected
[2024 correction](https://doi.org/10.1038/s41586-024-07928-6) does not discuss this.
That wording is ambiguous: this is not a demonstrated numerical error or a
reason by itself to reject the source. Freeze an explicit interpretation and
reconcile it to published outputs before deriving assay labels.
The script also uses literature-reference indicators and sampled non-reference
pairs for benchmarking; these must not be imported as experimental negatives.
Neither observation establishes that the paper's conclusions are wrong.

## Reopening conditions—not another automatic experiment

First reconcile the assay transformation, construct/QC mapping and selected
follow-up, preserving failed/missing states. Then, **before any model scores**,
count matched positive-versus-evaluable-nondetection contrasts and independent
anchor/family support. Audit exposure against actual fitted training data;
independent laboratory provenance does not guarantee unseen pairs or homologs.
Freeze a precision-justified confirmation design isolated from pilot decisions.

These prerequisites are **not yet satisfied**. Matched support and current
training contamination were not calculated because the P/N semantics were not
qualified. No support failure or uncontaminated generalization is claimed.
A separate, explicitly scoped extracellular-study decision would be required;
this audit does not start that pivot or contact authors.

Verification: eight targeted tests pass; a separate pandas implementation
checks matrix/missingness/alias and numeric-QC counts, all 11 raw hashes, and
all 109 registered files across the four preceding study closures. This is
same-author checking, not external review. A strict text-decoding failure was
recovered with a recorded Windows-1252 fallback without altering raw bytes.
Zero fits, embeddings, model scores, P/N labels or protected/quarantine access.

**Bottom line:** preserve the project as a reproducible methodological result;
stop selling or developing the current head as a better PPI model. SAVEXIS is
a credible conditional pivot, not a reason to erase the stopping decision.
