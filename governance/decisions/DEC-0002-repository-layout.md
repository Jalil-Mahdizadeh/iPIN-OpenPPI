# DEC-0002: Repository and artifact layout

- **Date:** 2026-08-03
- **Status:** Accepted
- **Decision owner:** Codex, within routine technical authority

## Decision

Use the directory layout prescribed by Appendix A of the Version 3 blueprint, with the existing expert documents retained under `docs/blueprints/` and human-readable reports placed under `docs/reports/`.

Every generated cache, temporary file, container image, run log, model artifact, figure, table, dataset, and release package will remain beneath the project root. Large and generated artifacts will not be source-controlled, but their manifests and checksums will be.

## Rationale

The project will generate many heterogeneous artifacts. Separating immutable inputs, canonical data, derived data, source code, scheduler definitions, run outputs, governance records, and releases prevents accidental overwrites and makes provenance auditable.

