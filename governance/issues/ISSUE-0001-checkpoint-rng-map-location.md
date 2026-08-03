# ISSUE-0001: Checkpoint RNG state loaded onto CUDA

- **Detected:** 2026-08-03
- **Run:** `artifacts/runs/platform/platform-single-gpu-826757-20260803T124059Z`
- **Severity:** Low; qualification-fixture implementation only
- **Status:** Corrected in versioned entry point; rerun pending

## Observation

The first one-GPU qualification reached checkpoint restore but failed because `torch.load` mapped the saved CPU RNG-state ByteTensor onto CUDA. `torch.set_rng_state` requires a CPU ByteTensor.

## Correction

`scripts/platform/qualify_torch_gpu_v2.py` forces checkpoint deserialization onto CPU. Model and optimizer loaders then copy state to their CUDA-resident parameters. The original failed run and v1 fixture are preserved rather than overwritten.

## Scientific impact

None. No biological data or scientific model was involved, and the failed run is not accepted as platform-gate evidence.
