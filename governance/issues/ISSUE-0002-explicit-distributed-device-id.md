# ISSUE-0002: Distributed device identifier advisory

- **Detected:** 2026-08-03
- **Runs:** Slurm jobs `834109` and `834510`
- **Severity:** Advisory
- **Status:** Open for the next distributed entry-point version

PyTorch warned that `init_process_group` and `barrier` inferred the current device. The fixture explicitly called `torch.cuda.set_device(local_rank)`, observed the required one- and four-device counts, passed NCCL all-reduce, completed all DDP ranks, and exceeded the scaling threshold.

Future distributed entry points will provide the device identifier directly to the process-group/barrier API where supported. The accepted qualification artifacts remain unchanged.

