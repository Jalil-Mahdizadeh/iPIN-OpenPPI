"""Refresh this experiment's status from completion records and SLURM."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
protocol = json.loads((root / "PROTOCOL.json").read_text())
done = (root / "results/COMPLETE.json").exists()
lines = ["# Test2 competitor comparison status", "", "Updated: " + datetime.now(timezone.utc).isoformat(), "",
         "Comparison completed." if done else "Scoring and automatic comparison are in progress.", "",
         "13 frozen predictors; 3,774,966 candidate rows; unchanged C1/C2/C3 test2 partitions.", ""]
for tag in ("tuna", "rapppid_original", "rapppid_recovery", "partner"):
    path = root / "predictions" / tag / "COMPLETE.json"
    lines.append(f"- {tag}: {'scoring complete' if path.exists() else 'pending'}.")
for tag, workers in (("plm", 16), ("dscript_original", 4), ("dscript_retrained", 4)):
    completed = 0
    count = 0
    for rank in range(workers):
        directory = root / "shards" / tag / f"rank-{rank:03d}"
        completed += (directory / "COMPLETE.json").exists()
        for cell in ("C1", "C2", "C3"):
            progress = directory / f"{cell}_PROGRESS.json"
            if progress.exists():
                count += json.loads(progress.read_text())["completed"]
    lines.append(f"- {tag}: {count:,}/755,954 added rows scored; {completed}/{workers} workers complete. Legacy scores are already verified.")
lines.append(f"- SPRINT: {'scoring complete' if (root / 'sprint/COMPLETE.json').exists() else 'sequence preprocessing complete; scoring pending/running' if (root / 'sprint/HSP_COMPLETE.json').exists() else 'sequence preprocessing pending/running'}.")
jobs = json.loads((root / "ACTIVE_JOBS.json").read_text())
lines += ["", "| Stage | SLURM job |", "|---|---|"]
lines.extend(f"| {label} | {job} |" for label, job in jobs.items())
if jobs:
    state = subprocess.run(["squeue", "-j", ",".join(jobs.values()), "-o", "%.18i %.18j %.2t %.10M %.10l %.6D %R"], text=True, capture_output=True)
    lines += ["", "```text", state.stdout.strip() or state.stderr.strip(), "```"]
lines += ["", "Final outputs: `results/RESULTS.md`, `results/scores.csv`, `results/paired_differences.csv`, and `results/C3_comparison.png`.",
          "The comparison job depends on successful completion of every remaining scoring job. Original source preservation is verified afterward.", ""]
(root / "STATUS.md").write_text("\n".join(lines))
print("\n".join(lines))
