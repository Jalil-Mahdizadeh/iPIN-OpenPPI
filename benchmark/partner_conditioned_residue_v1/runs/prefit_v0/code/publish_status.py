"""Publish a concise status using aggregate records only."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('status', choices=['submitted', 'complete', 'no_promotion'])
    args = parser.parse_args()
    value = {'updated_at_utc': datetime.now(timezone.utc).isoformat(), 'status': args.status}
    lines = ['# Partner-conditioned residue study status', '', f"Updated: {value['updated_at_utc']}", '']
    if args.status == 'submitted':
        jobs = json.loads((ROOT / 'runs/JOBS.json').read_text())
        value['jobs'] = jobs['jobs']
        lines += ['Training and the dependent development-selection/test stage have been submitted.', '',
                  '| Stage | SLURM job |', '|---|---:|']
        lines += [f"| {x['stage']} | {x['job_id']} |" for x in jobs['jobs']]
        lines += ['', 'No new test results exist yet. The comparison stage runs only after successful training.']
    elif args.status == 'no_promotion':
        lines += ['Training and development selection completed. No advanced ensemble exceeded the frozen PU-TUnA development reference, so no test evaluation was performed.', '',
                  'See [development results](results/DEVELOPMENT.md) and [selection](results/SELECTION.json).']
    else:
        lines += ['Training, development selection, and the C1/C2/C3 comparison completed.', '',
                  'See [comparison results](results/RESULTS.md), [all scores](results/scores.csv), and [paired differences](results/paired_differences.csv).']
    (ROOT / 'STATUS.md').write_text('\n'.join(lines) + '\n')
    (ROOT / 'STATUS.json').write_text(json.dumps(value, indent=2) + '\n')


if __name__ == '__main__':
    main()
