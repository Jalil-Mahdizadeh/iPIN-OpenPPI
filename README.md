# iPIN-OpenPPI

Evidence-aware, sequence-based prioritization of direct human heteromeric protein-protein interactions.

## Current status

Arrhenius/Apptainer qualification, primary-source acquisition, evidence staging,
source reconciliation, systematic-screen analysis, and the negative-evidence
discovery audit are complete and accepted. The governance-bounded Lambourne et
al. 2026 human Y2H-v1 pair-semantics audit is complete and independently
validated; its expert-group disposition is pending. The eligibility/sequence-
component audit remains paused and unstarted.

Lambourne outcomes may not become training labels, be merged with Negatome, or
be integrated into a benchmark before a new governance decision. Label, split,
candidate, and model construction remain prohibited. The expert-facing result
is the [final pair-semantics audit](docs/reports/m0/M0_Lambourne_2026_Human_Y2H_Pair_Semantics_Audit_Final_v1.md),
and the pending disposition is [DEC-0014](governance/decisions/DEC-0014-propose-lambourne-panel-disposition.md).
The exact restart point is [project status version 13](governance/PROJECT_STATUS_v13.md),
and the authoritative ledger is [gate status version 13](governance/gates/gate_status_v13.yaml).

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

1. Obtain an explicit expert-group disposition of the proposed Lambourne
   technical-acceptance-and-quarantine decision.
2. Do not integrate the panel or resume the paused sequence-component audit
   while that proposal is pending.
3. If explicitly authorized, resume the sequence-component audit at its prior
   unstarted checkpoint under the original prohibitions.

Generated data and images are intentionally excluded from source control but remain in their designated project-local directories.
