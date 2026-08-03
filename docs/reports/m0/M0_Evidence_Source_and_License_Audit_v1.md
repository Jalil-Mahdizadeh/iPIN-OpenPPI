# M0 evidence-source and license audit

**Project:** iPIN-OpenPPI  
**Date:** 2026-08-03  
**Executor:** Codex  
**Platform:** NAISS Arrhenius, qualified Apptainer SIF  
**Result:** Source/license subgate **PASS WITH CONDITIONS**; evidence gate remains **IN PROGRESS**

## Executive conclusion

The project is feasible as a fully computational, provenance-first study using HuRI/CCSB, UniProt, IntAct/IMEx, and experimental PDB/SIFTS evidence. All four source families have official retrieval paths and terms compatible with internal research processing. The audited manifest set contains 20 assets, of which 19 are mandatory at this stage, plus a controlled query/child-manifest workflow for later PDB coordinates.

The most important scientific finding is negative: the public HuRI materials do not expose a complete pair-level attempted/evaluable universe for all nine Space III screens. HuRI can support high-quality positive and explicit-control evidence, but its complement cannot support negative labels. This does not make the project infeasible; it changes the statistically defensible first model to a positive–unlabeled or latent-observation design unless a fuller screen log is obtained.

Acquisition may now begin. Training-label construction and model training remain prohibited until the evidence audit quantifies mapping coverage, construct confidence, assay-state resolution, and the available explicit-negative/control scope.

## Audit questions and outcomes

| Question | Outcome | Effect |
|---|---|---|
| Is there an official, versionable source? | Yes for all four families; HuRI uses published-file metadata rather than a formal release | Local immutable snapshots and SHA-256 required |
| Are terms compatible with project use? | Yes, with attribution for HuRI portal, UniProt, and IntAct; PDB/SIFTS is CC0 | Acquisition approved |
| Can raw source files later be redistributed? | Generally yes under source terms, except Nature-hosted HuRI supplements | Nature raw supplements are internal-only |
| Is HuRI's full attempted/evaluable universe public? | No complete per-pair log was found | Missing pairs remain unknown; PU/latent design |
| Can IntAct provide direct evidence? | Yes, but only after preserving original PSI-MI evidence semantics | Spoke/matrix expansions excluded as direct labels |
| Can structure evidence be made experimental-only? | Yes | RCSB queries explicitly request experimental content; PDB child manifests required |
| Are release and integrity checks implementable? | Yes | Provider MD5 for UniProt; local SHA-256 and HTTP metadata for every asset |

## Source-by-source assessment

### HuRI / HI-III and earlier CCSB maps

Feasibility for positive evidence is high. The portal supplies 52,569 HuRI interactions and associated PSI-MI export, Test-space positives, Lit-BM, and earlier maps. The publication and supplements expose assay versions, constructs, validation/control experiments, and some explicit outcome states.

Feasibility for a conventional positive-versus-negative classifier is presently low. The public materials do not show that every Space III pair was selected, physically attempted, technically evaluable, and called negative when absent. The primary statistical route must therefore distinguish selection `s`, evaluability `e`, latent contextual binding `b`, and observed outcome `y`, as required by the blueprint.

The advertised Test-space PSI-MI URL returned HTTP 404 on the audit date; the TSV remains available. This is logged as an unavailable asset rather than silently substituted.

### UniProt

Feasibility is high. Release `2026_02` and human reference proteome `UP000005640` provide canonical sequences, additional/isoform sequences, annotations, and identifier mappings. `RELEASE.metalink` supplies release-aware provider checksums. The pipeline will never silently collapse isoforms to genes.

UniRef and UniParc access is license-cleared but deferred. Downloading large archives before the benchmark split/clustering design is fixed would add cost without improving the current evidence gate.

### IntAct / IMEx

Feasibility is high for evidence-level provenance and moderate for automatic direct-binary labeling. The immutable Release 252 archive supplies human PSI-MI XML 3.0. Its richer representation is essential because web/MITAB binary rows can be expansions of n-ary interactions. Direct interaction (`MI:0407`), physical association (`MI:0915`), and association (`MI:0914`) will remain distinct.

The HuRI IMEx dataset `IM-25472` is valuable as an independent curation and record-ID cross-check. It contains multiple evidence and detection-stage records rather than 52,569 consensus pair rows, so early collapsing would destroy needed information.

### PDB / SIFTS

Feasibility is moderate to high. Licenses and APIs are suitable, but structural evidence is biased toward tractable proteins and constructs. The project will explicitly request experimental entries, freeze query results, retrieve biological assemblies only through reviewed child manifests, and recalculate interfaces from frozen coordinates. SIFTS mappings and residue-level XML will be used to reject or qualify interfaces affected by mutations, tags, chimeras, isoform mismatch, or missing residues.

Computed models can later be useful as model inputs or hypotheses, but they are prohibited from the experimental-evidence layer.

## Feasibility judgment

| Component | Feasibility | Main limitation | Current response |
|---|---|---|---|
| Release-aware human sequence universe | High | Isoform/gene ambiguity | Preserve canonical, additional, accession, and version layers |
| Systematic positive assay evidence | High | Assay and construct heterogeneity | Evidence-record schema before pair consensus |
| Complete systematic negative universe | Low at present | HuRI attempt/evaluability log not public | PU/latent formulation; open ISSUE-0003 |
| Curated direct molecular evidence | Moderate–high | N-ary expansion and evidence duplication | PSI-MI XML 3.0, controlled-vocabulary filters, stable IDs |
| Experimental interface evidence | Moderate | Structural/construct selection bias | Experimental-only query, assembly and residue-mapping audit |
| Fully computational validation | Feasible | No new wet-lab confirmation | Strict splits, source holdouts, temporal tests, calibration, uncertainty, simulation |

Overall feasibility is **conditional but strong**. The project can credibly produce an assay-aware compatibility and prioritization model, uncertainty estimates, and reproducible hypotheses. It cannot honestly claim a universal probability of physical binding or experimentally validated novel interactions.

## Legal and redistribution findings

- Interactome Atlas published data: CC BY 4.0; cite the portal and source paper.
- UniProt data: CC BY 4.0; attribution and third-party/patent caveats apply.
- IntAct data: CC BY 4.0; software licensing is separate. A legacy downloads-page ambiguity is recorded.
- PDB/RCSB API and PDBe-derived structural data: CC0; attribution remains scientific best practice.
- Nature-hosted HuRI supplements: internal audit copy only under project policy; do not package raw files into a release without separate permission.
- Preliminary/unpublished HuRI registered-user data: outside project scope.

## Machine validation

The final manifest set was validated inside `containers/images/ipin-qual-arm64_0.1.0.sif` using Python 3.12.3 on Arrhenius ARM64.

- Result: pass
- Errors: 0
- Warnings: 3
- Passed structural/policy checks: 76 of 76
- Warnings: HuRI, IntAct, and PDB/SIFTS lack provider checksum catalogues for the selected assets; local SHA-256 therefore becomes authoritative
- Report: `artifacts/validation/source_manifests/preacquisition_validation_v2.json`

Six official policy pages were also frozen inside Apptainer with HTTP metadata and SHA-256 in `governance/licenses/snapshots/2026-08-03/SNAPSHOT_MANIFEST.json`.

## Gate decision

The source/license subgate passes with conditions because source identity, retrieval endpoints, release/snapshot logic, terms, redistribution treatment, checksum strategy, and label guards are all explicit and machine-validated.

The overall evidence gate remains in progress. Its quantitative thresholds—record provenance, systematic-state resolution, and construct confidence—can only be measured after raw acquisition and parsing. ISSUE-0003 blocks conventional negative-label construction.

## Authorized next execution unit

1. Implement a whitelist-only, atomic downloader driven by `PREACQUISITION_INDEX_v2.yaml`.
2. Acquire the listed assets inside Apptainer into their immutable `data/raw/<source>/<release-or-snapshot>/` paths.
3. Verify expected HTTP metadata and UniProt provider MD5, calculate SHA-256 for every payload, and create acquisition manifests without overwriting raw files.
4. Perform archive safety inspection and format detection before extraction or parsing.
5. Issue source-specific raw-inventory reports. No label construction occurs in that unit.

No expert-group choice is required to begin this acquisition unit; its scientific and legal boundaries are now frozen.
