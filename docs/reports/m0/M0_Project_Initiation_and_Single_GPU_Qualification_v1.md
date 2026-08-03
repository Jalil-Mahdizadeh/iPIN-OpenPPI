# M0 project initiation and single-GPU qualification

**Project:** iPIN-OpenPPI  
**Report version:** 1.0  
**Date:** 2026-08-03  
**Overall state:** M0 active; single-GPU qualification passed; full container gate remains open pending four-GPU qualification.

## Executive result

Project execution has started under the Version 3 blueprint. A structured repository, governance records, frozen initial scope, claim ceiling, novelty matrix, risk register, license register, gate configuration, and project-local runtime layout now exist.

The first ARM64 Apptainer image built successfully on Arrhenius and passed two independent deterministic tests on the allocated NVIDIA GH200. BF16 execution, forward/backward training, optimizer and scheduler state, checkpoint writing/loading, and exact continuation after restart all passed. Both repeats produced identical tensor and model SHA-256 digests.

No biological dataset has been downloaded, no scientific model has been trained, and no biological result has been generated.

## Start authorization and scope

Execution was authorized by the project sponsor on 2026-08-03 with the instruction “Start it.” The durable authorization is `governance/START_MANIFEST_v1.yaml`.

The locked primary task remains direct human heteromeric binary PPI prioritization from two amino-acid sequences. Wet-lab work is unavailable. Outputs are restricted to named-assay probabilities, sequence compatibility scores, uncertainty, optional partner-aware interface scores, retrieval scores, and computational hypotheses under the claim ceiling.

## Observed Arrhenius allocation

| Field | Observation |
|---|---|
| Node | `n34` |
| Architecture | `aarch64`, ARM Neoverse-V2 |
| Allocation | Slurm job `826757`, account `naiss2025-3-10-gpu`, partition `gpu` |
| Visible GPU | 1 × NVIDIA GH200 120GB |
| GPU compute capability | 9.0 |
| Host driver | 580.159.04 |
| Host-reported CUDA compatibility | 13.0 |
| Apptainer | 1.5.2-1.el9 |
| Project Disk free space at initiation | approximately 8.9 TB |

## Qualification container

| Field | Value |
|---|---|
| Definition | `containers/definitions/ipin-qual-arm64_0.1.0.def` |
| Base | `nvcr.io/nvidia/pytorch:25.08-py3` |
| Upstream OCI digest | `sha256:ace9a848c0ae543317e3c4763b6b4248961c47902625abfe3c77a0fb931c50fb` |
| SIF | `containers/images/ipin-qual-arm64_0.1.0.sif` |
| SIF size | 9.9 GB |
| SIF SHA-256 | `9259e1953dadc502af8949fe56db1fba56f4e3711ccb7542e7feda94c4718ce5` |
| Python | 3.12.3 |
| PyTorch | 2.8.0a0+34c6371d24.nv25.08 |
| PyTorch CUDA | 13.0 |
| cuDNN | 9.12.0 |

The build used only project-local `containers/cache/` and `containers/tmp/`. The initial full build took roughly thirty minutes and staged approximately 11 GB of OCI cache plus 7.2 GB of extracted temporary content before producing the 9.9 GB SIF.

Arrhenius reported expected rootless/fakeroot extended-attribute warnings on the project Disk `nodev` mount. They did not prevent the embedded test, SIF creation, checksum verification, inspection, or GPU execution. These warnings remain preserved in the build log.

## Deterministic one-GPU result

Accepted run directory:

`artifacts/runs/platform/platform-single-gpu-v2-826757-20260803T124251Z`

| Measurement | Repeat 1 | Repeat 2 | Result |
|---|---:|---:|---|
| Status | pass | pass | pass |
| BF16 supported | true | true | pass |
| Fixture elapsed time | 1.451 s | 1.434 s | recorded |
| Peak allocated GPU memory | 187,814,912 B | 187,814,912 B | identical |
| BF16 matmul mean | 0.9980394840 | 0.9980394840 | identical |
| Resumed loss | 1.0026799440 | 1.0026799440 | identical |
| Uninterrupted versus resumed state | exact | exact | pass |
| Matmul digest | `9684526a…a055c` | `9684526a…a055c` | identical |
| Final model digest | `00590a02…887e` | `00590a02…887e` | identical |

Every comparison check in `comparison.json` passed at the prespecified tolerance of 1e-6.

## Failed attempt retained for audit

The original v1 fixture reached checkpoint restoration but loaded a CPU RNG-state ByteTensor onto CUDA and was rejected by `torch.set_rng_state`. The failure is preserved under `artifacts/runs/platform/platform-single-gpu-826757-20260803T124059Z` and documented as `governance/issues/ISSUE-0001-checkpoint-rng-map-location.md`.

The corrected v2 entry point forces checkpoint deserialization onto CPU before state restoration. No scientific data or model was involved.

## Container-gate status

| Requirement | State |
|---|---|
| ARM64 SIF built on Arrhenius | Pass |
| Definition, source lock, inspection metadata, and SIF SHA-256 | Pass |
| Embedded CPU/PyTorch architecture test | Pass |
| One-GPU CUDA and BF16 test | Pass |
| Two repeated fixture outputs within tolerance | Pass |
| Exact checkpoint/restart continuation | Pass |
| One-GPU run without NaN, deadlock, or silent CPU fallback | Pass |
| Four-GPU run | Pending |
| Four-GPU scaling efficiency at least 70% | Pending |

The full container gate therefore remains **in progress**, not passed.

## Next controlled action

Create and submit a bounded one-node/four-GPU DDP/NCCL qualification. It will run a comparable one-GPU baseline and four-GPU fixture inside the same SIF and allocation, verify collective communication, record aggregate throughput and peak memory, and evaluate the frozen 70% scaling-efficiency threshold.

Scientific source acquisition begins only after source terms and manifests are verified; it does not depend on claiming the full four-GPU gate complete.

