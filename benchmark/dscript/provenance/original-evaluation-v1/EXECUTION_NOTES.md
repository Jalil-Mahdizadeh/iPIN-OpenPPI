# Original-model execution notes

Scientific freeze: `4ceaf28210f74b4f8519d2e8b9453376ce08edf27dcf79ef5ef12fbb8fc0ee86`.

- Job 2338513: failed before scoring because the interactive job's CPU mask was not valid on the new node. Explicit `--cpu-bind=none` resolved this.
- Job 2338537: allocated four GPUs on n494, but its scoring step received one GPU. `SLURM_GPUS=1` and `SLURM_GPUS_PER_NODE=1` were inherited from the submitting interactive allocation. Process inspection showed four Python workers (PIDs 1335329–1335332) on GPU UUID `GPU-3ed6329f-8f91-9564-017d-8aa63e5c55ce`, while the other three GPUs were idle. Stopped after 10m52s; each shard had 45,056 checkpointed C1 predictions, 180,224 total. No predictions were deleted, and no test metrics were accessed.
- A read-only four-task diagnostic with explicit `--gpus=4 --gpus-per-node=4 --gpus-per-task=1 --gpu-bind=single:1` mapped ranks 0–3 to four distinct GPU UUIDs: `GPU-3ed6329f-8f91-9564-017d-8aa63e5c55ce`, `GPU-40e8a6d5-1f4c-5991-5265-2812ef74cae6`, `GPU-0343341a-a542-e9a3-cc55-3264acbcfd81`, `GPU-7b85ea7b-f545-0ea6-c6e1-5affda1df554`. Each task correctly reported logical CUDA device 0 within its own device namespace.
- Job 2338739: resumed the existing identity-checked score shards, with explicit total/per-node GPU counts. Added one-device assertion and per-rank GPU UUID logging to the execution wrapper. No frozen model/code/cache/metric or candidate-panel change. The finalization step explicitly requests one GPU.

Checkpointing writes each score block and flushes its memmap before atomically replacing the progress manifest. On resume, any trailing uncheckpointed block is overwritten by the unchanged deterministic scorer; all checkpointed rows are retained.

Only the D-SCRIPT job was stopped. Interactive allocation 2322263 and all unrelated jobs were untouched. No training or follow-on benchmark was submitted.

## Completion

Job 2338739 completed successfully with exit code 0 in 44m01s on n494. Scoring step 2338739.0 took 42m46s on four GPUs; finalization step 2338739.1 took 1m12s on one GPU. All 3,019,012 predictions were merged and frozen at 20:55:37 UTC before evaluation reservation at 20:55:46 UTC. Metrics completed at 20:56:15 UTC on 2026-09-12. The 44m01s elapsed time excludes the earlier interrupted scoring and the initial 341.7-second embedding/projection-cache build.

The completion audit verified four distinct scoring GPU UUIDs, all frozen artifacts and the SIF, finite coverage, historical reference reproduction, all 2,000 finite paired bootstrap draws, and absence of temporary decrypted truth. A separate post-result read-only native inference check reproduced 24 saved predictions exactly; no scores or frozen artifacts were changed. The repository-scope audit passed for all 1,842 covered files outside `benchmark/`. Only the pre-existing interactive allocation remained in the user's queue when reporting; no D-SCRIPT or retraining job remained.
