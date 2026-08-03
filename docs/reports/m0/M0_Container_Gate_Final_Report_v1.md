# M0 qualification-container gate: final report

**Project:** iPIN-OpenPPI  
**Date:** 2026-08-03  
**Gate result:** PASS for qualification SIF `ipin-qual-arm64_0.1.0.sif`  
**Continuing condition:** Every later data or scientific image version requires its own regression qualification.

## Decision

The M0 Arrhenius/Apptainer qualification gate is passed for the initial immutable ARM64 GPU environment. The accepted SIF completed CPU/architecture import tests, two matching one-GPU BF16/training/checkpoint fixtures, one- and four-GPU DDP/NCCL runs, and an extended scaling confirmation above the frozen 70% threshold.

This decision qualifies the execution platform and bootstrap environment only. It does not validate any biological data, model, or scientific claim.

## Frozen environment

| Field | Accepted value |
|---|---|
| SIF | `containers/images/ipin-qual-arm64_0.1.0.sif` |
| SIF SHA-256 | `9259e1953dadc502af8949fe56db1fba56f4e3711ccb7542e7feda94c4718ce5` |
| Base OCI digest | `sha256:ace9a848c0ae543317e3c4763b6b4248961c47902625abfe3c77a0fb931c50fb` |
| Architecture | ARM64 / `aarch64` |
| Python | 3.12.3 |
| PyTorch | 2.8.0a0+34c6371d24.nv25.08 |
| CUDA reported by PyTorch | 13.0 |
| cuDNN | 9.12.0 |
| NCCL | 2.27.7 |
| GPU | NVIDIA GH200 120GB, compute capability 9.0 |
| Apptainer | 1.5.2-1.el9 |

## One-GPU repeat and restart evidence

Accepted run: `artifacts/runs/platform/platform-single-gpu-v2-826757-20260803T124251Z`.

Two independent runs produced identical BF16 matmul digests, identical final-model digests, identical losses, and exact uninterrupted-versus-resumed model, optimizer, scheduler, RNG, and data-position state. Peak allocated GPU memory was 187,814,912 bytes in each repeat. All comparison checks passed at tolerance 1e-6.

## Four-GPU smoke result

Slurm job `834109` ran on `n112` and completed `0:0` in 38 seconds using four GH200 GPUs.

- One GPU: 176,641.53 samples/s.
- Four GPUs: 631,274.57 samples/s.
- Scaling efficiency: 0.893440, or 89.3440%.
- NCCL all-reduce: pass.
- Four DDP ranks: pass.

Because the timed window was below one second, this result was accepted as four-GPU execution evidence but not used alone for the final scaling decision.

## Extended scaling confirmation

Accepted run: `artifacts/runs/platform/platform-four-gpu-long-834510-20260803T125331Z`.

Slurm job `834510` ran on `n411` and completed `0:0` in 51 seconds using four GH200 GPUs, 400 GB requested host memory, and an exclusive node allocation.

The unchanged fixture contained 134,217,728 trainable parameters, eight 4096-dimensional linear layers, fused AdamW, BF16 autocast, a local batch of 1,024 per GPU, 50 warm-up steps, and 1,000 measured steps.

| Measurement | One GPU | Four GPUs |
|---|---:|---:|
| World size | 1 | 4 |
| Global batch | 1,024 | 4,096 |
| Timed duration | 6.1421 s | 6.8565 s |
| Aggregate throughput | 166,718.12 samples/s | 597,385.71 samples/s |
| Peak allocated memory per GPU | 2,692,749,824 B | 2,692,749,824 B |
| NCCL all-reduce | pass | pass |

Scaling efficiency was:

`597385.7112 / (4 × 166718.1237) = 0.8958019947`

The measured **89.5802%** exceeds the frozen 70% threshold by 19.5802 percentage points.

## Gate checklist

| Requirement | Evidence | Result |
|---|---|---|
| Required computation inside ARM64 SIF on Arrhenius | All accepted fixtures | Pass |
| Definition, source/resolved locks, inspection metadata, SHA-256 | `containers/` records | Pass |
| CPU and architecture test | Embedded SIF `%test` | Pass |
| CUDA and BF16 test | Two one-GPU repeats | Pass |
| Repeated fixture outputs within tolerance | `comparison.json` | Pass |
| One-GPU job without NaN, deadlock, or fallback | Slurm 826757 run | Pass |
| Four-GPU job without NaN, deadlock, or fallback | Slurm 834109 and 834510 | Pass |
| Four-GPU scaling efficiency at least 70% | Extended result 89.5802% | Pass |
| Checkpoint/restart restores required state | Exact v2 comparison | Pass |

## Advisory retained

PyTorch warned that the NCCL process group inferred the CUDA device already selected with `torch.cuda.set_device`. Device counts, DDP world sizes, all-reduce values, and GPU execution all passed. Future distributed entry points should pass the device identifier explicitly to remove ambiguity; this advisory does not invalidate the accepted measurements.

## Next action

Proceed to the evidence-source and licensing gate: freeze release identifiers and terms for HuRI/HI-III, UniProt, IntAct/IMEx, and the structural-interface source before downloading any scientific files. The first full scientific SIF will then add only the dependencies required by the approved ingestion and validation design and will undergo regression qualification.

