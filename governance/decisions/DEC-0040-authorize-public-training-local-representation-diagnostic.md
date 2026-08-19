# DEC-0040: Authorize public-training local-representation diagnostic

**Date:** 2026-08-19

**Status:** Accepted and effective for the bounded prospective diagnostic

**Decision basis:** Explicit project-owner instruction to execute the proposed
public-only representation-bottleneck test and obtain results promptly

**Controlling records:** `RESUME-005`, `DEC-0039`, and
`PUBLIC_TRAINING_LOCAL_REPRESENTATION_DIAGNOSTIC_v1`

## Decision

Authorize the new prospective, public-training-only diagnostic frozen in
`configs/public_training_local_representation_diagnostic_v1.yaml`. This is a
separate scientific work package. It does not reopen, tune, or reinterpret the
stopped `DEC-0028` model claim.

The study may reuse the exact already-acquired ESM-2 150M checkpoint, tokenizer,
qualified container, frozen sequences, public training P/U rows, component
assignments, and design weights. It may retain contextual vectors only as
fixed contiguous segment means and compare partner-conditioned segment late
interaction against a matched global mean from the same forward pass.

Phase A is label-free and primary in a deterministic nested C3 component
holdout. The permissive, point-estimate trigger and the complete conditional
Phase B recipe are frozen before any local embedding is generated or score is
observed. Conditional Phase B is authorized only if the mechanical Phase A
trigger passes; it may fit only the two frozen low-capacity linear feature
scores on nested C1.

## Verified authorization preflight

The work package was opened on `main` at
`fde45833326797ce98f3d979fecaac78a4f0203c`, identical to freshly fetched
`origin/main` with zero divergence. `RESUME-005` resolves to that commit. The
recorded `DEC-0039`, gate v38, status v38, final development report, binding
model protocol, model config, qualified SIF, and both ESM weight files matched
their frozen SHA-256 values. The two protected ciphertexts matched gate v38
without being opened. One NVIDIA GH200 120 GB GPU was visible on node n180.

The label-independent nested split was feasibility-counted before this freeze:
2,380 endpoints in 1,366 whole components are held out, yielding 650 P and
86,450 U rows in nested C3 and leaving 11,051 P and 1,254,297 U rows in nested
C1. No salt, split, threshold, or scorer was selected from an observed model
score.

## Required evidence

Execution shall freeze the local embedding arrays and manifest, nested split
manifest, all pair scores and metrics, bootstrap draws/results, any conditional
Phase B configs/checkpoints/logs, a complete registry, and a final report.
Production checks and an independently implemented validator must confirm
input hashes, component disjointness, exact row census, global reconstruction,
score formulas, U weighting, trigger logic, output hashes, and forbidden-path
absence.

## Continuing prohibitions

This decision does not authorize development or protected access; a second
development release; use of any private key; alteration of frozen benchmark or
parent-model evidence; negative or pseudo-negative construction; encoder
tuning; interface/residue targets; structure or external panels; additional
PLMs, scorers, recipes, seeds, or adaptive search; probability/calibration
claims; or protected advancement.

Any positive result is exploratory evidence for a later, separately numbered
confirmatory protocol only. Any trigger failure is an ordinary scientific
result and stops the conditional work rather than inviting threshold changes.

