# iPIN-OpenPPI

Evidence-aware, sequence-based prioritization of direct human heteromeric protein-protein interactions.

## Current status

Arrhenius/Apptainer qualification, primary-source acquisition, evidence staging,
source reconciliation, systematic-screen analysis, and the negative-evidence
discovery audit are complete and accepted. The governance-bounded Lambourne
2026 and 2025 TF-isoform audits are complete and independently validated. The
TF-isoform audit and its [DEC-0016 disposition](governance/decisions/DEC-0016-propose-tf-isoform-y2h-disposition.md)
are technically accepted by [DEC-0017](governance/decisions/DEC-0017-accept-tf-isoform-y2h-disposition.md).

Both external panels remain quarantined from the primary design. In particular,
the TF-isoform panel is external-only and is unsuitable for training negatives,
universal-nonbinding claims, prevalence, calibration, or unseen-endpoint/family
benchmarking. Label, split, candidate-pair, and model construction remain
prohibited. The previously authorized eligibility and sequence-component audit
is resumed only within its bounded preconstruction scope. The current restart
record is [project status version 16](governance/PROJECT_STATUS_v16.md), and the
authoritative ledger is [gate status version 16](governance/gates/gate_status_v16.yaml).

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

## Next execution sequence

1. Preserve the completed external-panel audits and their immutable evidence;
   do not reopen, recompute, or extend them.
2. Execute only the authorized benchmark-eligibility and sequence-component
   audit from its unstarted checkpoint, preserving the primary PU-R design.
3. Validate the bounded audit independently and return to governance before
   constructing candidates, labels, splits, structures, or models.

Generated data and images are intentionally excluded from source control but remain in their designated project-local directories.
