# M0 negative-evidence discovery audit

**Version:** 1.0

**Date:** 2026-08-04

**Status:** Final; production audit complete and independently validated

**Execution owner:** Codex

**Platform:** NAISS Arrhenius through the pinned ARM64 Apptainer image

**Scientific scope:** Evidence discovery, mapping, reconciliation, provenance,
and feasibility only; no labels, candidate universe, splits, or model were built

## Executive judgment

The additional negative-evidence work package is technically complete and has
produced a useful but deliberately bounded evidence resource. All four
Negatome 2.0 pair files were acquired, versioned, parsed, mapped to the frozen
human UniProt release, reconciled with all 939 frozen IntAct negative records,
and checked against current permitted positive evidence. An independent
validator passed all 43 checks with no failures or warnings.

The most important scientific conclusion is that the evidence does **not**
justify changing the project's primary positive–unlabeled design into a
population-calibrated positive–negative–unlabeled design.

There is enough mapped manual evidence for a protected, source- and
assay-stratified conditional diagnostic: 1,188 records, representing 1,163
unique frozen sequence pairs and 315 publications, survive the deliberately
conservative diagnostic filter. That is numerical adequacy, not
identifiability. Negatome lacks the selected population and much of the
construct, orientation, condition, and technical-evaluability context needed
for population calibration; IntAct's explicit negatives are heterogeneous
curated observations without a common sampling denominator. The biological
class prior and the source-specific detection processes therefore remain
unknown.

The recommended programme remains:

1. retain reference-sequence positive–unlabeled ranking (PU-R) as the primary
   design;
2. reserve qualifying manual negative observations for protected conditional
   diagnostics only;
3. keep structure-derived non-contact pairs in a separate evidence family;
4. preserve positive conflicts rather than deleting inconvenient records; and
5. never describe any audited record as a universal nonbinding pair.

The project remains feasible as an evidence-aware sequence-ranking and
prioritization programme. It is not presently feasible as a calibrated binary
binding classifier, a universal positive/negative benchmark, or a source of
experimentally validated biological conclusions.

## 1. Authority, scope, and claim ceiling

Blueprint Amendment 001 and `DEC-0011` authorized this audit. The work package
was required to:

- acquire the complete Negatome manual, manual-stringent, PDB, and
  PDB-stringent datasets;
- determine their licensing and redistribution boundary;
- map every participant against frozen human UniProt `2026_02`, retaining
  isoform and mapping confidence;
- calculate exact overlap with the 939 existing IntAct negative records;
- reconcile mapped pairs with current permitted HuRI, IntAct, and other direct
  PPI evidence;
- preserve available assay, construct, orientation, species, publication, and
  experimental-condition provenance;
- keep manually observed experimental negatives separate from
  structure-derived non-contact pairs;
- classify reliability rather than create a single negative class;
- survey additional public systematic non-detection sources; and
- assess whether a positive–negative–unlabeled design is statistically and
  scientifically supportable.

This report contains only non-extractive aggregate findings. Record-level
Negatome outputs remain internal because the database payload license is not
explicitly stated. Nothing in this audit authorizes negative labels, candidate
pairs, pseudo-negatives, split construction, model implementation, or model
training.

## 2. Reproducibility and independent validation

The production run began from clean implementation commit
`30220bd5e0fec5f6c259ba369f14b62a71530f3f`. All scientific execution used:

- image: `containers/images/ipin-data-arm64_0.1.2.sif`;
- image SHA-256:
  `72e4a13299df1c7036dbf5c8845f3a1d9d02bf6143bd2e4ee675aabd03112629`;
- architecture: `aarch64`;
- Python `3.12.3`, PyArrow `19.0.1`, and DuckDB `1.5.5`; and
- frozen human UniProt release `2026_02`.

| Record | Result | SHA-256 |
|---|---:|---|
| `AUDIT_REPORT.json` | Complete | `ccefebc920ec5c3d1a04d271babbdee044608662ef88d87615a274d82f6e6315` |
| `VALIDATION_REPORT.json` | Pass: 43 pass, 0 fail, 0 warning | `e3b7b8da6fbb9d6361278e9d89ab1cdd070c087279a8a821dc852cfd5f4fc155` |
| Staging manifest | 12,720 source rows | `4b4c4cd9679f8bd6e6f207bbe067df75da30b38d900bc0214dcc1303095f3ec9` |
| Canonical audit manifest | 6,568 parent records plus audit tables | `593b1b45ef579f4f4f403f8567510c28b0ac84b8818ac82d3b27a6d2dce9be24` |
| Acquisition manifest | Complete source acquisition | `c628c960590b046293f286038574138fda2d4ecfd5b351e15d8dc21b65151dc5` |
| Raw verification report | All source hashes reverified | `2a18393601997da4e662adb0a2c6739dbe734d4214df7551861fdc822ed31d0e` |

The independent validator did not merely compare the report with itself. It
re-read immutable raw and Parquet artifacts, checked manifest sidecars and file
hashes, recomputed subset relationships, mapping counts, current-positive
conflicts, all 939 IntAct records, overlap, reliability tiers, and the PNU
feasibility result. It also verified read-only output permissions and the
fail-closed authorization fields.

## 3. Acquisition, versioning, and licensing

The four provider files were frozen as the provider snapshot last modified on
2021-09-15 and acquired on 2026-08-04.

| Negatome dataset | Physical rows | Bytes | SHA-256 |
|---|---:|---:|---|
| Manual | 2,171 | 123,362 | `f05410c9ba1748e0d36a13e9b873a67e61bdcef2446904735fc3e172ca78aa16` |
| Manual stringent | 1,991 | 113,757 | `6391316c19abaf8a677ef65878891e9ae6fd9346dff53e2c0617cb34516f578c` |
| PDB | 4,397 | 305,645 | `85232908f1b993b9bb54abc0547a2566cc99930538d134faec8db56f303df182` |
| PDB stringent | 4,161 | 279,096 | `61026a6147d5729980efc80f84e85d92bbd9424b11a586332c8ebf193011cc3c` |

The counts reproduce the provider's published Negatome 2.0 inventory. The
[Negatome 2.0 paper](https://academic.oup.com/nar/article/42/D1/D396/1048129)
also makes the essential semantic distinction: manual records represent
reported experimental non-interactions, whereas the PDB set is generated from
chains in structural complexes that do not meet the historical contact rule.
The paper explicitly cautions that absence from interaction reporting is not
itself evidence of noninteraction.

The manual-stringent file is a normalized multiset subset of manual, and the
PDB-stringent file is an exact multiset subset of PDB. For manual, 24 stringent
rows fail raw byte-for-byte row matching solely because of boundary whitespace
in an assay field; trimming only boundary whitespace restores the complete
subset relationship. This normalization is recorded explicitly and did not
alter identifiers or scientific values. Manual contains 10 duplicate rows and
manual-stringent contains 9 under this normalization; the PDB files contain no
duplicates. The canonical layer represents the 2,171 manual and 4,397 PDB
parent rows once and stores stringent membership as provenance rather than
double-counting the stringent files.

### License decision

The official Negatome download page and the four payload files do not state a
database license, database-right waiver, redistribution grant, or commercial
use grant. The article's CC BY-NC 3.0 notice is not assumed to license the
separately served database payload. The resulting boundary is:

- internal computational research and audit: approved;
- citation and non-extractive aggregate reporting: approved;
- raw or record-level redistribution: not authorized without explicit provider
  permission; and
- commercial use: unresolved and not authorized.

IntAct states that its data exports and services are available under CC BY 4.0
on the [IntAct About page](https://www.ebi.ac.uk/intact/about). That license does
not turn an IntAct source-asserted negative into a universal biological claim.
This is a conservative project compliance determination, not legal advice.

## 4. Source semantics and retained provenance

Two evidence families are intentionally immutable and separate:

| Family | Parent rows | Meaning permitted by this audit | Meaning not permitted |
|---|---:|---|---|
| Manual experimental negative | 2,171 | A reported conditional experimental non-detection or negative observation, with the source assay and publication retained | Universal inability of the proteins to bind |
| Structure-derived non-contact | 4,397 | Two chains in a specific structural entry did not meet Negatome's historical direct-contact criterion | Experimental noninteraction, assay negative, or universal nonbinding |

For every source record, the staging layer preserves the original identifiers,
source row, file membership, order, publication identifier, assay value, PDB
entry/chain fields where applicable, and all actually supplied context. A
manual publication recorded as `PMC1717011`, rather than a numeric PubMed ID,
is retained as a PMC identifier rather than rejected or silently coerced.

The source does not supply complete construct sequences, orientation, species,
experimental conditions, or technical-evaluability state at row level. Those
fields are retained as null with an explicit missing-provenance state. They are
never inferred from the frozen reference sequence or from a different source.
Consequently, every construct-level mapping confidence remains reference-only,
not an exact construct mapping.

## 5. Frozen human reference mapping

Each accession was resolved independently and deterministically against the
frozen UniProt `2026_02` human release. Isoform suffixes were preserved. Unique
secondary-accession and canonical isoform-1 routes were allowed only when the
frozen reference made the resolution unambiguous.

### Participant-level results

| Mapping state | Participants |
|---|---:|
| Exact primary canonical | 3,666 |
| Exact isoform | 38 |
| Unique frozen secondary accession | 32 |
| Canonical isoform-1 alias | 9 |
| Ambiguous frozen accession | 38 |
| Not in frozen human reference | 9,353 |
| **Total** | **13,136** |

| Confidence | Definition | Participants |
|---|---|---:|
| A | Exact frozen primary or isoform identifier | 3,704 |
| B | Unique frozen secondary accession | 32 |
| C | Explicit canonical isoform-1 alias | 9 |
| D | Unmapped or ambiguous in the frozen human reference | 9,391 |

“Not in the frozen human reference” is intentionally broader than “known
nonhuman.” The project has not imputed a species merely because an accession is
absent from the human release.

### Pair-level results

| Pair state | Parent records |
|---|---:|
| Both participants uniquely mapped to frozen human sequences | 1,630 |
| Exactly one participant uniquely mapped | 485 |
| Neither participant uniquely mapped | 4,453 |
| **Total** | **6,568** |

Of the fully mapped records, 1,408 are manual and 222 are structural
non-contact. The much lower human-reference coverage in the structural family
is not repaired through speculative cross-species mapping.

## 6. Reconciliation with current positive evidence

Every one of the 1,630 fully mapped Negatome parent records was checked against
a frozen positive index constructed from permitted direct binary HuRI/IntAct
evidence and the HuRI, HI-II-14, Lit-BM, and Test-space pair views.

| Positive index component | Rows or unique pairs |
|---|---:|
| Mapped positive evidence rows | 619,837 |
| Unique mapped positive evidence pairs | 194,277 |
| Mapped permitted pair-view rows | 79,386 |
| Unique permitted pair-view pairs | 71,044 |
| Combined unique positive sequence pairs | 212,732 |

Current positive evidence conflicts with 237 fully mapped Negatome parent
records. Of these, 153 have a qualifying direct conflict (`CF-D`) and 183 have
a broader IntAct physical/association conflict (`CF-B`). Those overlays can
co-occur and therefore must not be added together.

This result is important: historical stringent membership is not a guarantee
that a pair is conflict-free against the current frozen evidence base.
Conflicts remain in the audit as provenance. They are not deleted, relabelled,
or resolved by a vote between sources. A conditional negative observation and
a positive observation under another construct, orientation, method, species,
or condition can both be valid evidence.

## 7. Exact overlap with the 939 IntAct negative records

All 939 frozen IntAct source-asserted negative records were enumerated. Of
these, 453 resolve to a usable unordered pair of frozen human reference
sequences. Records with n-ary structure, nonhuman participants, missing
mappings, or ambiguous mappings remain in the audit and are not dropped from
the denominator.

The exact overlap is zero under every prespecified matching route:

| Matching route | Links |
|---|---:|
| Exact ordered source accessions | 0 |
| Exact unordered source accessions | 0 |
| Unordered frozen sequence-hash pair | 0 |
| Negatome parent records with any IntAct-negative overlap | 0 |
| IntAct negative records with any Negatome overlap | 0 |

This is an exact source-reconciliation result under the frozen matching rules.
It does not prove that the resources are biologically independent, that either
source is complete, or that any pair is universally nonbinding.

## 8. Reliability tiers

The audit assigns reliability tiers only to the evidence actually supported by
the frozen mapping and source provenance. It does not create a universal
negative target.

| Tier | Records | Operational meaning |
|---|---:|---|
| ME-1 | 1,216 | Manual-stringent, both participants uniquely mapped to human, and no current qualifying direct-positive conflict |
| ME-2 | 192 | Other fully mapped manual records, including direct-conflicted manual records |
| SN-1 | 154 | PDB-stringent and both participants uniquely mapped to human |
| SN-2 | 68 | Other fully mapped PDB non-contact records |
| MX | 4,938 | One or both participants missing, ambiguous, or outside the frozen human reference |
| **Total** | **6,568** | Families remain separate in every tier |

The `ME` and `SN` prefixes are scientifically substantive, not cosmetic. ME
records represent manual experimental-negative evidence; SN records represent
structural non-contact evidence. They may not be pooled into a common negative
class. Current-positive status is an independent overlay. A broader `CF-B`
conflict does not silently rewrite the base tier, but it excludes a record from
the conservative conditional-diagnostic set.

There are zero label-authorized rows and zero universal-nonbinding rows.

## 9. Additional public non-detection survey

Nine source categories were systematically reviewed. The source inventory and
per-source disposition are frozen in
`governance/source_surveys/PUBLIC_EXPERIMENTAL_NONDETECTION_SURVEY_v1.yaml`.

| Source category | What is publicly useful | Audit disposition |
|---|---|---|
| Negatome 2.0 | Manual conditional negatives and separate structural non-contacts | Acquired and audited; internal record-level use only |
| IntAct explicit negatives | 939 curated source-asserted negative records | Fully audited; conditional evidence without a sampling denominator |
| HuRI/HI-II screens | Positive maps and selected control/non-detection panels | Full-screen absent pairs remain unlabeled; selected panels diagnostic only |
| Lambourne et al. 2026 human AI-prediction Y2H panel | A bounded selected set with reported Y2H outcomes, NA handling, and sequence confirmation | Highest-priority follow-up candidate; not yet acquired or authorized for use |
| Lambourne et al. 2026 yeast/YeRI | Larger systematic methodological evidence in yeast | Transfer-method candidate, not primary human evidence |
| Trabuco et al. likely-tested negatives | Computationally inferred likely-tested pairs | Exclude from observed-negative class |
| hsPRS/hsRRS multi-assay panels | Small, carefully selected assay reference panels | Conditional assay sensitivity/calibration only |
| DULIP, LuTHy, and related panels | Study-specific selected reference outcomes | Conditional control panels; source-specific audit required |
| Positive-only AP-MS, proximity, and curated maps | Detected or curated edges | Absence is unlabeled, never negative |

The 2026 human Y2H study is the strongest follow-up candidate because its
methods distinguish scored pairs from technical `NA` outcomes within a defined
selected panel. The [open-access article](https://www.nature.com/articles/s41467-026-70942-x)
reports a sample of 4,100 prediction pairs, narrowed to 3,222 after alignment
to the later prediction release, and points to IMEx entry `IM-30553`, source
data, code, and an archive. It is still a selected AI-prediction panel rather
than a proteome-population sample. Before any use, it needs a new source policy
and acquisition manifest, payload-license confirmation, immutable pair-level
acquisition, row-level attempted/evaluable/NA and sequence validation, frozen
mapping, positive-conflict reconciliation, and a sampling-selection audit.

The survey found no complete public human pair-level
selected/attempted/evaluable population and no universal-nonbinding source.

## 10. Positive–negative–unlabeled feasibility

### 10.1 What is numerically feasible

Applying the conservative diagnostic filter—manual family, ME-1, and no current
positive conflict of either overlay—leaves:

- 1,188 conditional manual records;
- 1,163 unique frozen sequence pairs; and
- 315 publications.

This exceeds the prespecified descriptive minimum of 100 records and 10
independent publications. A protected, source-/assay-stratified diagnostic can
therefore be designed after a later gate freezes its exact estimand and
sampling rules.

### 10.2 What is not statistically identified

A population-calibrated P+N+U design is not currently feasible because:

1. there is no complete human pair-level selected, attempted, and evaluable
   population;
2. Negatome manual records lack complete construct, orientation, condition,
   and technical-evaluability provenance;
3. IntAct negatives are heterogeneous curated records without a common
   sampling denominator;
4. source selection mechanisms and assay sensitivities are unknown; and
5. the biological class prior is not identified.

Adding more negative rows cannot repair these missing design variables. A
binary classifier trained on observed positives versus these curated negatives
would primarily learn source, assay, publication, organism, and curation
differences unless those mechanisms were explicitly identified. Its output
could not honestly be called a binding probability or a calibrated
proteome-population probability.

### 10.3 Binding statistical recommendation

| Design | Feasibility | Role |
|---|---|---|
| Reference-sequence PU ranking | Feasible subject to the next eligibility/component audit | Retain as primary |
| Manual-negative conditional diagnostic | Numerically feasible, semantically bounded | Protected diagnostic only; no training role authorized |
| Structure non-contact diagnostic | Potentially useful for a distinct structural question | Separate family; never pooled with manual negatives |
| Population-calibrated P+N+U | Not identified from current public data | Do not implement |
| Universal positive/negative classifier | Unsupported | Prohibited |

## 11. Overall feasibility and programme effect

The audit strengthens rather than weakens the existing PU-R programme. It adds
an independently mapped challenge resource that can later test whether a
sequence-ranking model separates released positives from narrowly defined,
conditional experimental non-detections. It also exposes 237 current-positive
conflicts that would have contaminated a simplistic negative class and shows
why evidence provenance is central to the model design.

The viable project claim is therefore:

> A provenance-aware computational model can prioritize symmetric human
> sequence pairs for compatibility and can be evaluated against released
> positives, unlabeled candidates, and protected source-scoped conditional
> diagnostics.

The project may not claim:

- that an unreported pair is negative;
- that a Negatome or IntAct negative never binds;
- that structural non-contact is experimental noninteraction;
- that its score is an absolute binding probability;
- that a P+N+U population is calibrated from these sources; or
- that any prediction has been experimentally validated by this project.

## 12. Governance disposition and next step

This audit subgate should pass with the Negatome redistribution constraint
remaining active. The primary PU-R design should remain unchanged. The
conditional manual-negative set should be registered as a future protected
diagnostic candidate, not as training labels.

The next previously queued technical unit is
`benchmark_eligibility_and_sequence_component_audit_v1`. It may compute only
aggregate reference-sequence eligibility, exclusions, candidate counts without
pair materialization, and 40%/30%/20% sequence-component feasibility. It must
return to governance before candidate rows, evidence indicators, pseudo-negative
samples, C1/C2/C3 assignments, structural labels, splits, or models are built.

The Lambourne 2026 panel remains a separately gated follow-up candidate. This
report does not authorize its acquisition or use.

## Final assessment for the expert group

The work package is complete, reproducible, and scientifically valuable. The
data support conditional negative-evidence diagnostics, but not a universal
negative class and not a calibrated P+N+U primary model. Retaining PU-R while
adding carefully protected negative-evidence diagnostics is the most defensible
and feasible design. It uses the new evidence without making a stronger claim
than the public experimental record can support.
