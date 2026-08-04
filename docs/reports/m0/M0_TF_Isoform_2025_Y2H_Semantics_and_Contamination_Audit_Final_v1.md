# M0 final report: 2025 human TF-isoform Y2H semantics and contamination audit

**Report date:** 2026-08-04

**Study:** Lambourne et al., *Widespread variation in molecular interactions
and regulatory properties among transcription factor isoforms*, Molecular
Cell (2025), DOI `10.1016/j.molcel.2025.03.004`

**Frozen human reference:** UniProt `2026_02`

**Controlling decision:** `governance/decisions/DEC-0015-authorize-tf-isoform-y2h-audit.md`

## Executive conclusion

The bounded audit is technically complete and independently validated. The
recommended disposition is **external-only diagnostic candidate**. The panel
is useful as a provenance-rich, assay-specific research object, but it is not
currently suitable for a protected benchmark and cannot estimate population
PPI prevalence.

The decisive reasons are:

- the public pairwise Y2H table and all 1,260 blank outcomes are exactly
  reconstructable from archived raw data;
- the 1,260 blanks are all technical outcomes, not assay negatives;
- the reported 3,509-row analysis is reproduced exactly, but its selection
  explicitly conditions on prior positives and therefore destroys prevalence
  representativeness;
- exact AD clone sequences are preserved, but only 444 of 693 match a frozen
  UniProt sequence and the source archive provides no exact DB plasmid
  sequence for the 753 partner ORFs;
- 848 fixed-partner, positive-versus-negative evaluable isoform-contrast groups
  exist, but only 149 have complete frozen pair mappings and **zero** are
  protected from current future-training exposure at the exact-endpoint or
  UniRef90-endpoint level; and
- N2H is a continuous, selected validation panel with substantial score
  overlap and weak rank association with Y2H (`rho = 0.1001`); no defensible
  binary N2H label is identified or authorized.

No study outcome was used as a training label, merged with Negatome, converted
into a universal nonbinding claim, thresholded, or integrated into a benchmark.
No model or split was built and the primary PU-R design was unchanged.

## 1. Governed sources and licensing

The audit acquired exactly five assets authorized by
`PREACQUISITION_tf_isoform_y2h_2025_v1.yaml`:

| Asset | Frozen version | Audit use | License/redistribution |
|---|---|---|---|
| Article methods PDF | Author-hosted 2025 PDF | Internal methods interpretation only | Elsevier copyright; no redistribution |
| Code and supplement archive | Zenodo `14969075`, v2.1.0; archive root commit `92a466e` | Public clone, Y2H, N2H tables and archived loader logic | CC BY 4.0; attribution required |
| Code-record metadata | Zenodo `14969075` | Machine license/version verification | CC BY 4.0 metadata |
| Input archive | Zenodo `14968584`, v2 | Raw Y2H/N2H, selection, clone accessions, nucleotide FASTA | CC BY 4.0; attribution required |
| Input-record metadata | Zenodo `14968584` | Machine license/version verification | CC BY 4.0 metadata |

Both Zenodo records independently report `cc-by-4.0`. The article PDF remains
outside Git. Generated record-level artifacts retain the conservative tier
`internal_governance_bounded_audit_only`; any public release requires a
separate governance and licensing review.

The five acquired assets total 3,785,127,047 bytes. Their immutable acquisition
manifest has SHA-256
`1c163f8cafaad152a49cc002af66a26a0779e9387a7cc9c3fca6bfaa56f60e96`;
the independent raw-verification report has SHA-256
`59c4536b3ed07f2c78349a7adbd52dce48c9ddd4e2b609d0a8440b6656ba9bf2`.

## 2. Exact source universes

The archived public and raw universes are:

| Source object | Rows | Reconstruction result |
|---|---:|---|
| Public clone table | 693 | Every public CDS exactly matches its archived nucleotide FASTA record |
| Screen-selection table | 5,213 | Unique ordered AD→DB pairs with explicit screen flags |
| Raw pairwise Y2H | 10,332 | 9,562 public rows plus 770 excluded raw rows |
| Public pairwise Y2H | 9,562 | Exact one-to-one raw crosswalk; zero outcome disagreements |
| Raw N2H | 901 | Complete and incomplete records retained separately |
| Public N2H | 765 | Exactly the complete, non-vignette raw records |

The screen-selection flags comprise 2,596 focused-only pairs, 2,242
ORFeome-only pairs, and 375 pairs appearing in both. Of the 9,562 public Y2H
rows, 1,872 are exact screen-hit pairs and 3,447 have a TF-gene/partner selected
through at least one isoform.

All 693 public CDS strings equal the matching raw FASTA sequence. Independent
translation reproduces the reported amino-acid string for 615 clones; 78 are
discordant or have a non-codon-length CDS. The audit preserves both source
sequences and the concordance flag and does not silently repair either string.

## 3. Pair-level Y2H semantics and the 1,260 blanks

The public outcome census is:

| Outcome class | Count | Evaluable? | Biological interpretation allowed? |
|---|---:|---|---|
| Positive Y2H observation | 2,563 | Yes | Positive in the reported construct, AD→DB orientation, host, and media |
| Explicit negative Y2H observation | 5,739 | Yes | Assay-specific negative observation only |
| Sequence-confirmation failure | 1,065 | No | None |
| Mating or spotting failure | 157 | No | None |
| Assay-measurement failure | 31 | No | None |
| Autoactivation | 7 | No | None |
| Unknown unresolved | 0 | No | None |

Thus all 1,260 public blanks are resolved from explicit raw technical fields:
1,065 sequence-confirmation failures, 157 mating/spotting failures, 31 missing
or failed measurements, and 7 autoactivation outcomes. All 1,260 remain
technically unevaluable and none becomes a negative.

The archive contains no expression measurement from which an expression-
failure category could be identified. The expression-failure count is
therefore **not identifiable**, rather than inferred to be zero. No negative
record is interpreted as universal nonbinding.

The preserved assay context is pairwise Y2H in *S. cerevisiae*: the TF isoform
is the Gal4 activation-domain prey and the hORFeome partner is the Gal4
DNA-binding-domain bait. Pair growth is evaluated on SC-Leu-Trp-His with 1 mM
3AT, with SC-Leu-Trp mating control and an AD-null autoactivation control.

## 4. Reconstructed selection and analysis filters

The archived default analytical logic is reproduced exactly:

| Step | Input | Output | Excluded |
|---|---:|---:|---:|
| Eligible non-reference-control categories | 9,562 | 9,562 | 0 |
| TF-gene/partner has at least one positive | 9,562 | 4,615 | 4,947 |
| Clone has at least one evaluable test | 4,615 | 4,456 | 159 |
| Clone has at least one positive | 4,456 | 3,843 | 613 |
| TF gene has at least two isoforms | 3,843 | 3,622 | 221 |
| TF-gene/partner has at least two evaluable isoforms | 3,622 | 3,593 | 29 |

The last row is a 3,593-attempt universe. Removing 84 technical outcomes gives
the reported 3,509 evaluable rows: 2,330 positive and 1,179 explicit negative
Y2H observations across 936 positive TF-gene/partner groups.

This mechanism is not prevalence-representative. Candidates begin with
positive first-pass screens plus HuRI and Lit-BM positives; partners found for
one isoform are expanded across cognate isoforms; groups without any positive
are removed; retained clones must have a positive; and multiple evaluable
isoforms are required. Neither the 2,330/1,179 ratio nor any ratio in the full
public table estimates arbitrary human-pair prevalence.

## 5. Construct and frozen-reference mapping

Exact TF clone sequence and DB partner identifier are deliberately distinct
mapping problems:

| Mapping result | Count |
|---|---:|
| TF clone sequences | 693 |
| Exact clone matches in frozen UniProt `2026_02` | 444 |
| Clone sequences absent from the frozen reference | 249 |
| Unique DB ORF identifiers | 753 |
| Exact source DB construct sequences present | 0 |
| Unique indirect HuRI/hORFeome frozen mappings | 706 |
| Ambiguous indirect mapping | 1 |
| Unmapped DB ORF | 46 |

Canonical-protein candidates are retained separately from exact clone
mappings. A DB mapping based on the same ORF identifier in frozen HuRI
reconciliation is marked `B_unique_indirect_orfeome_mapping`; it is never
reported as an exact plasmid-sequence match.

Both sequence endpoints are usable for 5,338 of 9,562 public rows, 4,694 of
8,302 evaluable rows, and 1,978 of the 3,509 reported-analysis rows.

## 6. Existing-evidence and future-training exposure

The overlay uses the already validated, permitted HuRI/IntAct direct evidence
and HuRI-family pair views. It does not relabel Y2H outcomes.

| Universe | Rows | Reference-usable | HuRI positive | Permitted positive / exact future pair | UniRef90 pair | Exact endpoint | UniRef90 endpoint |
|---|---:|---:|---:|---:|---:|---:|---:|
| All public Y2H | 9,562 | 5,338 | 489 | 677 | 1,718 | 5,338 | 5,338 |
| All evaluable Y2H | 8,302 | 4,694 | 387 | 549 | 1,513 | 4,694 | 4,694 |
| Reported 3,509 analysis | 3,509 | 1,978 | 311 | 458 | 1,112 | 1,978 | 1,978 |

Every reference-usable panel pair has at least one endpoint already exposed in
the current permitted positive-evidence snapshot, both exactly and at
UniRef90. This follows from the discovery and selection design, not from a
post-hoc data leak. It nevertheless prevents an unseen-endpoint or
family-generalization claim against a future model trained on that evidence.

## 7. Matched isoform contrasts

The fixed-partner grouping preserves TF gene, exact clone, DB ORF, and AD→DB
orientation.

| Matched-group property | All public grouping | Reported analysis subset |
|---|---:|---:|
| Groups with at least two public isoforms | 2,750 | — |
| Groups with at least two evaluable isoforms | 2,342 | — |
| Positive-versus-negative evaluable contrast | 848 | 708 |
| All evaluable pairs reference-usable | 149 | 74 |
| Exact-pair protected | 90 | 45 |
| UniRef90-pair protected | 83 | 45 |
| Exact-endpoint protected | 0 | 0 |
| UniRef90-endpoint protected | 0 | 0 |

Among the 848 contrast groups, 699 have incomplete pair mapping, 59 are
exact-pair exposed, 7 add UniRef90-pair exposure, and the remaining 83 protect
the pair signature but not the endpoint family. No group supports a strict
unseen-endpoint diagnostic under the current future-training exposure.

## 8. N2H remains a separate continuous assay

The 765 public N2H rows exactly equal complete, non-vignette raw rows. Exactly
276 have the ordered ORF pair in public Y2H. The two study-designated isoform
strata contain 131 Y2H-positive and 131 Y2H-negative observations; each stratum
crosswalks exactly to its source Y2H state.

N2H `log2 NLR` is independently reproduced as
`log2(score_pair / max(empty-N1, empty-N2))` for every row. For the 262 isoform
validation rows, the Y2H-negative stratum has mean 0.6423 and median 0.7710;
the Y2H-positive stratum has mean 1.3774 and median 0.4711. The Spearman
association between a Y2H-positive indicator and continuous N2H is 0.1001.
The distributions overlap substantially. No N2H threshold was published or
authorized here, so N2H remains continuous and does not relabel Y2H.

## 9. Identifiable and non-identifiable claims

The audit identifies only:

- conditional Y2H outcome frequencies within the selected, technically
  evaluable panel;
- matched within-panel isoform contrasts for a fixed DB partner and fixed
  AD→DB orientation;
- continuous N2H distributions for the published selected validation strata;
  and
- overlap with the frozen evidence snapshot where both references map
  uniquely.

It does not identify:

- population PPI prevalence or calibrated probability for arbitrary pairs;
- orientation-invariant interaction probability;
- universal nonbinding from a negative Y2H observation;
- endogenous, cell-type-specific, or physiological binding;
- binary N2H outcomes without a separately governed threshold;
- exact DB construct effects when DB plasmid sequences are absent; or
- family-generalizing or unseen-protein performance.

## 10. Reproducibility and independent validation

Production ran from clean commit
`9de608ddc301d0af548d043c9fbd57b5c7e1b7f2` in
`containers/images/ipin-data-arm64_0.1.2.sif` with image SHA-256
`72e4a13299df1c7036dbf5c8845f3a1d9d02bf6143bd2e4ee675aabd03112629`,
ARM64, Python 3.12.3, and frozen UniProt `2026_02`.

| Artifact | Result | SHA-256 |
|---|---|---|
| Production audit report | Pass; external-only diagnostic candidate | `9235569bd40adc4114c0b1f4387e57fb4fcabc823a28a3509676607ef809a281` |
| Independent validation report | 26 pass, 0 warning, 0 fail | `af9297e54203b7486a883eaa555d006dfac57da232f475f165395cf888f42327` |
| Staging manifest | 18,476 rows across five tables | `49221d602c1f2d966c451985604538c045fa9ffa8744363c35824aade7a9bffc` |
| Canonical manifest | 14,529 rows across six tables | `c71de2354bacfdef43b35d7f0ecbe07851568ab4abeb6a23df7065f1d8c39b68` |
| Acquisition manifest | Five assets | `1c163f8cafaad152a49cc002af66a26a0779e9387a7cc9c3fca6bfaa56f60e96` |
| Independent raw verification | Five assets passed | `59c4536b3ed07f2c78349a7adbd52dce48c9ddd4e2b609d0a8440b6656ba9bf2` |

The independent validator re-reads the ZIP and 3.77 GB compressed input TAR,
reconstructs all Y2H and N2H semantics and analytical filters without using
the production classifiers, recomputes exact and canonical mappings, rebuilds
positive and UniRef90 exposure in independent SQL, verifies every matched-
group protection flag, and checks schemas, file hashes, sidecars, permissions,
table sets, and row-level governance guards.

The final targeted Apptainer test suite passed 25 of 25 tests covering this
audit's acquisition policy, semantics, source parsing, independent validator,
positive-evidence overlap, and frozen reconciliation dependencies.

## 11. Governance recommendation

Accept the audit as technically complete, retain the study in a quarantined
external-only diagnostic-candidate role, and reject current benchmark
integration. Any future use requires a new expert-approved protocol, a newly
frozen training-exposure snapshot, explicit leakage estimands, and claims
limited to the reported assay. Current authorization remains: no labels,
splits, threshold, integration, model work, Negatome merge, PU-R change, or
universal-nonbinding interpretation.
