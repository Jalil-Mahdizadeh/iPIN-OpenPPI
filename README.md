# iPIN-OpenPPI

Evidence-aware, sequence-based prioritization of direct human heteromeric protein-protein interactions.

## Current status

Arrhenius/Apptainer qualification, primary-source acquisition, evidence staging,
source reconciliation, systematic-screen analysis, and the negative-evidence
discovery audit are complete and accepted. The eligibility/sequence-component
audit is paused and unstarted while the governance-bounded Lambourne et al. 2026
human Y2H-v1 pair-semantics audit is executed.

Lambourne outcomes may not become training labels, be merged with Negatome, or
be integrated into a benchmark before a new governance decision. Label, split,
candidate, and model construction remain prohibited. The exact restart point is
[project status version 12](governance/PROJECT_STATUS_v12.md), and the authoritative
ledger is [gate status version 12](governance/gates/gate_status_v12.yaml).

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

1. Acquire and freeze the manifested Nature, Zenodo, and IMEx IM-30553 sources.
2. Reconstruct the exact 4,100 selected pairs and 3,222 final-analysis pairs,
   preserving outcome, technical, construct, orientation, and confirmation states.
3. Map to frozen UniProt 2026_02 and audit permitted evidence, pair overlap, and
   sequence-family contamination without constructing splits.
4. Independently validate the audit and assess protected assay-specific external-
   benchmark feasibility and identifiable claims.
5. Return a scientific report and decision proposal to governance before any
   benchmark integration or resumption of the sequence-component audit.

Generated data and images are intentionally excluded from source control but remain in their designated project-local directories.
