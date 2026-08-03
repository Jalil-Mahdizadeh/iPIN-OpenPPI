# DEC-0003: Accept single-GPU platform qualification

- **Date:** 2026-08-03
- **Status:** Accepted as partial container-gate evidence
- **Decision owner:** Codex, within the frozen gate criteria

Two independent GH200 fixture runs inside SIF SHA-256 `9259e1953dadc502af8949fe56db1fba56f4e3711ccb7542e7feda94c4718ce5` passed BF16 execution, deterministic tensor/model comparison, training, and exact checkpoint/restart.

This decision does not pass the full container gate. Four-GPU execution and at least 70% scaling efficiency remain mandatory.

