# Test2 competitor comparison status

Updated: 2026-09-26T11:33:44.907874+00:00

Comparison completed.

13 frozen predictors; 3,774,966 candidate rows; unchanged C1/C2/C3 test2 partitions.

- tuna: scoring complete.
- rapppid_original: scoring complete.
- rapppid_recovery: scoring complete.
- partner: scoring complete.
- plm: 755,954/755,954 added rows scored; 16/16 workers complete. Legacy scores are already verified.
- dscript_original: 755,954/755,954 added rows scored; 4/4 workers complete. Legacy scores are already verified.
- dscript_retrained: 755,954/755,954 added rows scored; 4/4 workers complete. Legacy scores are already verified.
- SPRINT: scoring complete.

| Stage | SLURM job |
|---|---|
| PLM-interact ranks 0–14 | 3031955 |
| PLM-interact rank 15 retry | 3032004 |
| D-SCRIPT | 3031479 |
| SPRINT | 3030402 |
| Final comparison | 3032005 |

```text
JOBID               NAME ST       TIME TIME_LIMIT  NODES NODELIST(REASON)
           3032005      test2-compare  R       2:32   12:00:00      1 n151
```

Final outputs: `results/RESULTS.md`, `results/scores.csv`, `results/paired_differences.csv`, and `results/C3_comparison.png`.
The comparison job depends on successful completion of every remaining scoring job. Original source preservation is verified afterward.
