# iPIN-OpenPPI

Evidence-aware, sequence-based prioritization of direct human heteromeric protein-protein interactions.

## Current status

Project execution was authorized on 2026-08-03. Arrhenius/Apptainer qualification,
primary-source acquisition, evidence staging, and source reconciliation have been
completed and accepted. The evidence gate remains in progress because the systematic
tested-universe and structural-release blockers are unresolved.

The next authorized unit is **benchmark and estimand design only**. Label construction,
split construction, structural mapping under unresolved release alignment, and model
training remain prohibited. The exact restart point is recorded in
[the project status checkpoint](governance/PROJECT_STATUS.md), and the authoritative
gate ledger is [gate status version 8](governance/gates/gate_status_v8.yaml).

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

1. Audit systematic-screen selection, attempted-pair, evaluability, technical-state,
   orientation, and explicit negative/control metadata.
2. Resolve or formally disposition the missing HuRI attempted/evaluable pair universe;
   use a PU/latent-observation proposal if it cannot be reconstructed.
3. Define admissible benchmark tiers under the unresolved SIFTS/UniProt alignment and
   zero strict construct-A/B coverage.
4. Draft and validate the benchmark/estimand policy, including leakage controls,
   evaluation axes, prevalence, metrics, uncertainty, and minimum-size rules.
5. Prepare a decision record and gate update for approval before constructing labels
   or splits.

Generated data and images are intentionally excluded from source control but remain in their designated project-local directories.

