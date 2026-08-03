# M0 final primary-source reconciliation and construct-mapping report

**Project:** iPIN-OpenPPI
**Date:** 2026-08-03
**Run family:** `primary_reconciliation_v1`
**Executor:** Codex
**Runtime:** Accepted Apptainer data SIF on NAISS Arrhenius
**Result:** **PASS WITH FOUR DOWNSTREAM SCIENTIFIC WARNINGS**

## Executive result

The frozen primary staging layer was reconciled successfully into an immutable,
provenance-preserving canonical mapping layer at
`data/canonical/primary_reconciliation_v1`. The production run used no override
flags, reverified all 152 staged Parquet files by SHA-256, ran from a clean Git
commit, and published atomically.

The independent production validator reports **152 passed checks, zero failed
checks, and four warnings**. The warnings are deliberate scientific
constraints, not integrity failures:

1. zero records can honestly receive construct confidence A or B because exact
   experimental construct sequences and boundaries are not available;
2. ISSUE-0003 still prevents treating unreported HuRI pairs as negatives;
3. ISSUE-0004 is now quantitatively reconciled but retained as a public-source
   limitation because the provider headline transformation cannot be reproduced
   exactly; and
4. ISSUE-0005 still blocks exact structural mappings because the SIFTS and
   UniProt releases differ.

The result establishes that high-coverage reference-sequence reconciliation is
computationally feasible. It also establishes, just as importantly, that a
strict construct-aware benchmark is not feasible from the frozen public sources
alone. The scientifically viable route is therefore a clearly named
reference/canonical-sequence estimand with positive-unlabeled or latent
observation modelling, not a conventional positive-versus-unreported classifier
and not a claim about exact experimental constructs.

## Production disposition

| Item | Result |
|---|---:|
| Canonical tables | 5 |
| Parquet files | 46 |
| Rows across canonical tables | 4,297,000 |
| Parquet payload bytes | 366,537,644 |
| Validation checks passed | 152 |
| Validation checks failed | 0 |
| Validation warnings | 4 |
| Canonical reconciliation accepted | Yes |
| Benchmark and estimand design authorized | Yes |
| Strict construct benchmark authorized | No |
| Label construction authorized | No |
| Structural mapping authorized | No |
| Model training authorized | No |

Rows across tables are an engineering inventory, not a unique-PPI count. The
tables represent participant mappings, evidence-level mapping summaries, HuRI
evidence projections, HuRI representation reconciliation, and SIFTS chain-mapping
audits.

## Canonical table inventory

| Table | Rows | Purpose |
|---|---:|---|
| `participant_sequence_mappings` | 2,213,524 | One deterministic mapping and construct-confidence assessment per staged participant |
| `evidence_mapping_summaries` | 773,376 | Mapping coverage and ordered/unordered sequence-pair projections per evidence record |
| `huri_evidence_gene_pair_projections` | 220,934 | Trace from HuRI participant identifiers and ORFs to ordered and unordered Ensembl-gene representations |
| `huri_pair_reconciliation` | 81,469 | Union of detailed-evidence gene pairs and provider pair-view gene pairs, with multiplicity and membership state |
| `sifts_chain_mapping_audit` | 1,007,697 | Taxonomy-, interval-, frozen-sequence-, and release-aware audit of each SIFTS chain mapping |
| **Total** | **4,297,000** | |

## Binding reconciliation policy

Candidate routes are evaluated in frozen precedence order and stop after the
first route that yields at least one candidate:

1. exact frozen UniProt sequence identifier;
2. explicit canonical `-1` alias;
3. Ensembl protein cross-reference;
4. Ensembl transcript cross-reference; and
5. Ensembl gene cross-reference.

Conflicts within the selected route are retained. Multiple identifiers with the
same sequence hash are represented as sequence-equivalent candidates; multiple
sequence hashes remain ambiguous unless they project to one canonical parent,
in which case only the canonical projection is usable. A canonical projection
is never called an exact construct mapping.

The strongest permitted construct confidence is C:

- **C** means a frozen reference sequence or canonical projection is available,
  while the experimental construct sequence and boundaries remain unreported;
- **D** means the identifier, taxon, entity type, or sequence mapping is
  ambiguous or unresolved;
- `unmapped` and `not_applicable` remain explicit states; and
- **A/B are prohibited** without source-supported exact construct information.

No source-native pair view, contact annotation, absence, or technical state is
authorized as a project label in this layer.

## Participant mapping results

### Coverage by source

| Source | Participants | Reference sequence usable | Coverage | Canonical projection usable | Coverage |
|---|---:|---:|---:|---:|---:|
| HuRI | 441,868 | 432,557 | 97.89% | 441,056 | 99.82% |
| IntAct/IMEx | 1,771,656 | 1,621,466 | 91.52% | 1,622,916 | 91.60% |
| **Total** | **2,213,524** | **2,054,023** | **92.79%** | **2,063,972** | **93.24%** |

Reference-sequence and canonical coverage are both high enough for a
sequence-level derived view. Neither percentage is a construct-mapping rate.

### Mapping states

| Source | Mapping state | Construct confidence | Participants |
|---|---|---:|---:|
| HuRI | Direct identifier unique | C | 264,888 |
| HuRI | Canonical `-1` alias unique | C | 159,053 |
| HuRI | Cross-reference unique | C | 8,547 |
| HuRI | Sequence-equivalent candidates | C | 69 |
| HuRI | Canonical projection only | C | 8,685 |
| HuRI | Ambiguous | D | 45 |
| HuRI | Unmapped | `unmapped` | 581 |
| IntAct/IMEx | Direct identifier unique | C | 1,609,261 |
| IntAct/IMEx | Canonical `-1` alias unique | C | 9,222 |
| IntAct/IMEx | Cross-reference unique | C | 2,346 |
| IntAct/IMEx | Sequence-equivalent candidates | C | 637 |
| IntAct/IMEx | Canonical projection only | C | 2,355 |
| IntAct/IMEx | Ambiguous | D | 170 |
| IntAct/IMEx | Unmapped | `unmapped` | 40,252 |
| IntAct/IMEx | Unresolved | D | 738 |
| IntAct/IMEx | Nonhuman/out of scope | `not_applicable` | 57,023 |
| IntAct/IMEx | Nonprotein/not applicable | `not_applicable` | 49,652 |

Across all 2,213,524 participants, **zero** have construct confidence A or B,
**zero** are strict-construct eligible, and **zero** authorize a label. This is
the correct result for the available inputs, not a mapping failure.

## Evidence-level sequence-pair results

| Source | Evidence records | Binary two-human-protein records | Reference pair usable | Canonical pair usable |
|---|---:|---:|---:|---:|
| HuRI | 220,934 | 220,934 | 211,785 | 220,137 |
| IntAct/IMEx | 552,442 | 442,454 | 408,505 | 409,822 |
| **Total** | **773,376** | **663,388** | **620,290** | **629,959** |

Across all evidence records, 80.21% have a usable reference-sequence pair and
81.46% have a usable canonical-sequence pair. The more relevant denominator for
pair mapping is the 663,388 binary two-human-protein records: 93.50% have a
reference pair and 94.96% have a canonical pair.

These pair identifiers are deterministic derived views. They do not collapse
assays, publications, orientations, observations, or repeated measurements, and
they are not consensus interaction labels.

## HuRI representation reconciliation

### Deterministic transition audit

| Metric | HuRI | HI-II-14 |
|---|---:|---:|
| Detailed PSI-MI evidence rows | 171,545 | 49,389 |
| Rows with one gene per participant | 170,621 | 49,107 |
| Rows with unresolved gene projection | 924 | 282 |
| Unique detailed gene pairs | 52,649 | 13,432 |
| Unique unordered ORF pairs | 51,842 | 15,654 |
| Unique ordered ORF pairs | 78,886 | 23,757 |
| Downloaded pair-view rows | 52,548 | 13,633 |
| Detailed/pair-view matched gene pairs | 51,961 | 13,432 |
| Detailed-only gene pairs | 688 | 0 |
| Pair-view-only gene pairs | 587 | 201 |
| Union gene pairs | 53,236 | 13,633 |
| Pair-view self-pairs | 480 | 518 |
| Provider-advertised pairs | 52,569 | 13,993 |
| Advertised minus pair-view rows | 21 | 360 |

Unique two-gene projection succeeds for 99.46% of HuRI detailed evidence and
99.43% of HI-II-14 detailed evidence. At the gene-pair level, the detailed and
pair-view representations overlap strongly but not perfectly: the Jaccard
overlap is 97.61% for HuRI and 98.53% for HI-II-14.

The audit explains why the source representations must not be equated:

- detailed evidence rows have assay/orientation multiplicity;
- ordered and unordered ORF-pair counts differ materially;
- ORF-to-gene projection is not one-to-one for every record;
- self-pairs are present in the pair views;
- HuRI has both detailed-only and pair-view-only gene pairs;
- HI-II-14's detailed unique gene pairs are contained in a larger pair view; and
- the downloaded pair-view row counts still differ from the provider headlines
  by 21 and 360, respectively.

All public transition layers requested by ISSUE-0004 are now preserved and
quantified, but the public records do not expose enough provider-internal logic
to reproduce the headline transformations exactly. ISSUE-0004 is therefore
classified as **reconciled and retained as a documented source limitation**.
No rows were added, removed, or collapsed to force agreement.

## SIFTS release and structural-mapping audit

| Metric | Result |
|---|---:|
| Chain-mapping rows | 1,007,697 |
| Rows on chains with human taxonomy | 252,678 |
| Distinct human-chain accessions | 9,812 |
| Primary canonical accessions | 8,946 |
| Primary field present without canonical sequence | 1 |
| Additional-sequence identifiers | 84 |
| Absent from frozen sequence corpus | 781 |
| Descending intervals | 72 |
| Frozen out-of-bounds ascending intervals | 0 |
| Exact sequence identity verified | 0 |
| Structural mapping authorized | 0 |
| Labels authorized | 0 |

The interval audit found no out-of-bounds interval among evaluable ascending
rows, which is useful quality evidence. It does not overcome the release
mismatch: SIFTS declares UniProt `2026.03`, while the frozen sequence corpus is
UniProt `2026_02`. Exact chain-to-sequence identity was not asserted, descending
intervals were preserved, and all structural mappings remain blocked under
ISSUE-0005.

## Independent validation coverage

The production validator independently checked:

- manifest and sidecar integrity, accepted SIF path/hash, ARM64 runtime, config
  hash, schema hash, clean production Git commit, and complete staging hashes;
- exact table and Parquet inventories, row counts, byte counts, file hashes,
  Arrow schemas, embedded provenance metadata, read-only permissions, and link
  absence;
- required fields, enums, primary keys, deterministic record identifiers, and
  uniform row-level provenance;
- one-to-one participant/evidence links back to immutable staging records and
  exact copied source fields;
- participant feature recounts, applicability logic, mapping-state logic,
  candidate-list cardinality, sequence referential integrity, and construct
  missingness semantics;
- evidence participant recounts, usability flags, and deterministic ordered and
  unordered sequence-pair identifiers;
- HuRI gene/ORF projection and pair-view membership reconstructed independently
  from staging inputs;
- the complete HuRI pair-union aggregation and multiplicities;
- SIFTS taxonomy, frozen-sequence match state, interval classification, release
  state, and structural authorization logic; and
- exact agreement among frozen expectations, recomputed Parquet metrics, and
  manifest metrics.

The validator returned 152 passes, zero failures, and four warnings. All four
warnings are represented in the gate decision below.

## Feasibility assessment

### Feasible now

- Reproducible identifier and reference-sequence reconciliation at full source
  scale is feasible inside Apptainer on Arrhenius.
- A high-coverage canonical human sequence view is feasible, provided it is
  explicitly described as a derived reference view rather than exact construct
  truth.
- HuRI representation differences can be carried forward without data loss via
  evidence-level records, ORF/gene projections, pair-view membership, and
  multiplicity fields.
- A computational, no-laboratory positive-unlabeled or latent-observation study
  remains feasible.

### Not feasible from the current frozen public sources

- The blueprint's strict evidence criterion of at least 80% construct confidence
  A/B is not met: the observed fraction is 0%.
- Exact experimental construct claims cannot be recovered from canonical
  UniProt identifiers alone.
- A complete HuRI negative/evaluable universe cannot be reconstructed, so
  unreported pairs cannot support ordinary supervised negative labels.
- Release-safe structural labels cannot be produced from the mismatched SIFTS
  and UniProt snapshots.
- Prospective wet-lab validation is outside project scope by instruction.

### Consequence for the model

The project should not stop, but the initial estimand must be narrowed. The
next model should target source-conditioned assay-positive evidence or latent
interaction propensity over the frozen reference/canonical sequence universe,
with explicit observation and selection uncertainty. Claims must remain at that
level. A universal direct-binding probability for exact experimental constructs
would not be supported by these data.

## Gate decision and next authorized unit

The source-reconciliation and identifier/construct-mapping subgate passes. The
overall evidence gate remains **in progress** because its strict A/B construct
coverage requirement is unmet and ISSUE-0003/ISSUE-0005 remain open.

The next authorized unit is **benchmark and estimand design without label
construction**. It must:

1. freeze the precise reference/canonical-sequence estimand and distinguish it
   from exact-construct binding;
2. define positive-unlabeled or latent-observation assumptions for HuRI without
   converting missing pairs to negatives;
3. define which explicit IntAct negatives or controls, if any, are conditionally
   admissible and for which evaluation only;
4. design entity/sequence-cluster and temporal leakage controls before any
   comparative modelling result is inspected; and
5. produce a formal benchmark-construction proposal and gate amendment for
   review before labels, splits, or training are created.

Label construction, strict-construct benchmark publication, structural mapping,
and model training remain unauthorized.

## Reproducibility record

- Production canonical root: `data/canonical/primary_reconciliation_v1`
- Reconciliation manifest: `data/canonical/primary_reconciliation_v1/RECONCILIATION_MANIFEST.json`
- Reconciliation-manifest SHA-256: `6408c6be771ac6a957e443d8c848b66789ca47230ae372b7ec3f3390ab7a6932`
- Validation report: `artifacts/validation/reconciliation/primary_reconciliation_v1/VALIDATION_REPORT.json`
- Validation-report SHA-256: `9d00b08bccb3620672ea6621cf3cb90c67de6bb1328d62b560712d65e4fa14d2`
- Reconciliation Git commit: `d66d990a16592eb469f1b58643d982cb936c9083`
- Reconciliation version: `0.1.0`
- Canonical schema SHA-256: `ae381c4e9dc94ebeb64f1ccb19f9ba2f3d86dfed5bff4fe8024625e38850fcf2`
- Apptainer image: `containers/images/ipin-data-arm64_0.1.2.sif`
- Image SHA-256: `72e4a13299df1c7036dbf5c8845f3a1d9d02bf6143bd2e4ee675aabd03112629`
- Run started: `2026-08-03T19:28:08.700330+00:00`
- Run completed: `2026-08-03T19:31:00.699286+00:00`
- Validation completed: `2026-08-03T19:32:45.372972+00:00`

The production root, production manifest and sidecar, validation report and
sidecar are read-only and link-free. No smoke or incomplete reconciliation
directory remains.
