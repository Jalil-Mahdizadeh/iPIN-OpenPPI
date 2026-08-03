# DEC-0004: Pass the M0 qualification-container gate

- **Date:** 2026-08-03
- **Status:** Accepted
- **Decision owner:** Codex, applying the frozen Version 3 gate

The immutable ARM64 SIF with SHA-256 `9259e1953dadc502af8949fe56db1fba56f4e3711ccb7542e7feda94c4718ce5` passed all M0 qualification-container criteria.

The extended four-GPU result achieved 89.5802% scaling efficiency against the prespecified 70% minimum. Both NCCL collective checks and all DDP ranks passed. One-GPU repeated outputs and checkpoint/restart were exact.

This decision applies only to qualification image version 0.1.0. Every scientific image or dependency revision requires a new image digest and regression qualification.

