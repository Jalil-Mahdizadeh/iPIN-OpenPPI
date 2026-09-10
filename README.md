# iPIN-OpenPPI

Evidence-aware, sequence-based prioritization of direct human heteromeric protein-protein interactions.

## Current status

As of 2026-09-10, the development embedding-identity correction authorized by
[DEC-0045](governance/decisions/DEC-0045-authorize-development-embedding-identity-correction.md)
is complete. The original learned-model evaluation indexed almost every
protein's embedding incorrectly. Corrected reevaluation of all frozen models
passed 329 unit tests, nine production audit checks and 17 standalone
independent validation checks.

The selected simple ESM-2 150M model's C3 positive-versus-unlabeled concordance
is **0.784**, versus the invalid original **0.492**. The best C3 partner-gated
model reaches **0.760** and still fails the original complexity gates.
The project therefore has development ranking signal, but no demonstrated
benefit for its proposed gated architecture. Protected evaluation remains
unauthorized and sealed; this is not a calibrated probability-of-binding claim.

See the [findings and corrected results](docs/reports/m1/M1_Research_Reassessment_and_Embedding_Identity_Findings_2026-09-10.md),
[project status v45](governance/PROJECT_STATUS_v45.md), and
[gate ledger v45](governance/gates/gate_status_v45.yaml).
Original v1 evaluation artifacts remain preserved as incident evidence.

## Historical pre-model checkpoint (v27)

Arrhenius/Apptainer qualification, primary-source acquisition, evidence staging,
source reconciliation, systematic-screen analysis, and the negative-evidence
discovery audit are complete and accepted. The governance-bounded Lambourne
2026 and 2025 TF-isoform audits are complete and independently validated. The
TF-isoform audit and its [DEC-0016 disposition](governance/decisions/DEC-0016-propose-tf-isoform-y2h-disposition.md)
are technically accepted by [DEC-0017](governance/decisions/DEC-0017-accept-tf-isoform-y2h-disposition.md).

Both external panels remain quarantined from the primary design. In particular,
the TF-isoform panel is external-only and is unsuitable for training negatives,
universal-nonbinding claims, prevalence, calibration, or unseen-endpoint/family
benchmarking.

The bounded eligibility and sequence-component audit is complete, independently
validated, and technically accepted by [DEC-0018](governance/decisions/DEC-0018-accept-benchmark-eligibility-and-sequence-component-audit.md).
Its [final report](docs/reports/m0/M0_Benchmark_Eligibility_and_Sequence_Component_Audit_Final_v1.md)
freezes 17,000 eligible sequence endpoints and deterministic 40%/30%/20%
component inventories without materializing candidate pairs or constructing
labels or splits.

[DEC-0020](governance/decisions/DEC-0020-accept-pre-split-feasibility-and-leakage-stress-test.md)
accepts the independently validated aggregate pre-split feasibility and
leakage stress-test and its fail-closed homology and claim boundaries.

[DEC-0022](governance/decisions/DEC-0022-accept-final-benchmark-component-split.md)
accepts and freezes the 17,000-endpoint, 7,782-component
11,900/2,550/2,550 training/development/test skeleton under 30%
local_domain_union.

[DEC-0024](governance/decisions/DEC-0024-accept-pair-level-pu-r-benchmark-protocol.md)
accepts and freezes the independently validated pair-level PU-R protocol before
model work. Its [protocol report](docs/reports/m0/M0_Pair_Level_PU_R_Benchmark_Protocol_Final_v1.md)
defines evidence visibility, exact C1/C2/C3 withholding, deterministic
unlabeled sampling, PU-retrieval metrics, clustered uncertainty, supported
named-source diagnostics, and inactive unsupported holdouts.

[DEC-0026](governance/decisions/DEC-0026-accept-pair-level-pu-r-benchmark-artifacts.md)
accepts and freezes the independently validated pair-level benchmark artifacts
constructed exactly under that protocol. The
[artifact report](docs/reports/m0/M0_Pair_Level_PU_R_Benchmark_Artifacts_Final_v1.md)
records 16,799 training positives, 20,000,000 deterministic sampled-unlabeled
cell rows, separately sealed development/protected-candidate/protected-truth
packages, exact probabilities and weights, and zero positive-as-unlabeled or
public protected-identity leakage. Unlabeled pairs remain unlabeled, not
negatives. Development release, protected evaluation, and executable model
work remain unauthorized.

[DEC-0028](governance/decisions/DEC-0028-accept-model-governance-and-baseline-training-protocol.md)
accepts and freezes the independently validated, deliberately simple first-
stage [model protocol](docs/protocols/MODEL_GOVERNANCE_AND_BASELINE_TRAINING_PROTOCOL_v1.md).
It fixes exact frozen ESM-2 candidates and exposure limits, mandatory shortcut
and sequence baselines, a design-weighted P-versus-U objective, one symmetric
partner-gated pooled head with minimal ablations, a finite 30-run budget,
development/model-selection rules, C3/C2/C1 reporting, degree/hub and novel-U
diagnostics, and complexity/kill gates. No model files, embeddings, training,
development release, or protected evaluation are authorized or have begun.

The fresh-thread phase-boundary checkpoint at that stage was
[RESUME-003](governance/checkpoints/RESUME-003-post-model-governance-protocol-freeze.md).
Its historical scientific status was
[project status version 27](governance/PROJECT_STATUS_v27.md), with
[gate status version 27](governance/gates/gate_status_v27.yaml).

The binding scientific specification is [the Version 3 final blueprint](docs/blueprints/iPIN_OpenPPI_Final_Computational_Blueprint_and_Workflow_v3.md). All production computation must run on NAISS Arrhenius through immutable ARM64 Apptainer SIF images.

## Repository layout

| Path | Purpose |
|---|---|
| `docs/blueprints/` | Reviewed specifications and expert-group documents |
| `docs/reports/` | Human-readable milestone, platform, and scientific reports |
| `governance/` | Start manifest, decisions, gates, risks, licenses, and novelty claims |
| `configs/` | Versioned scientific, path, source, and gate configuration |
| `containers/` | Apptainer definitions, locks, metadata, cache, and SIF images |
| `data/` | Source manifests, immutable raw snapshots, staging, canonical data, derived data, and frozen splits |
| `src/` | Project implementation by functional work package |
| `scripts/` | Thin, auditable entry points for platform, data, benchmark, model, and release tasks |
| `slurm/` | Arrhenius job specifications and scheduler logs |
| `tests/` | Unit, integration, fixture, and reproducibility tests |
| `artifacts/` | Run manifests, logs, checkpoints, embeddings, metrics, figures, tables, reports, and project-local caches |
| `releases/` | Immutable release candidates and final release packages |

## Non-negotiable operating rules

1. Keep every project artifact beneath this repository root; keep private keys and
   credentials in account-protected locations outside source control.
2. Do not install or run a native project Python environment on the host.
3. Run scientific code inside a checksum-identified ARM64 Apptainer SIF.
4. Treat `data/raw/` as immutable after source checksum registration.
5. Give every material run a unique directory and machine-readable manifest.
6. Never overwrite a frozen split, source snapshot, container image, or release; create a new version.
7. Preserve assay, construct, orientation, selection, evaluability, and outcome semantics.
8. Describe untested predictions as computational hypotheses, never validated interactions.

## Current governance hold

1. Preserve the completed external-panel audits and their immutable evidence;
   do not reopen, recompute, or extend them.
2. Preserve the accepted eligibility/component and pre-split leakage audits,
   their immutable manifests, and the primary PU-R design.
3. Preserve the immutable `DEC-0022` endpoint/component split.
4. Preserve the `DEC-0024` information, pair-assignment, sampling, metric,
   uncertainty, holdout, and claim rules.
5. Preserve the immutable `DEC-0026` pair artifacts; do not modify, extend,
   resample, relabel or open protected candidates/truth. The bounded
   development correction under `DEC-0045` is complete.
6. Preserve the `DEC-0028` frozen model-governance and baseline/training
   protocol. Do not construct additional pair rows, negatives or pseudo-
   negatives, materialize the full candidate universe, integrate panels or
   structures, acquire model files, implement models, extract embeddings, or
   train unless a new numbered decision authorizes that bounded package.
7. Preserve both the invalid original evaluation evidence and the corrected
   `development_embedding_identity_correction_v2` evidence. The corrected
   result does not authorize another phase or protected evaluation.

Generated data and images are intentionally excluded from source control but remain in their designated project-local directories.
