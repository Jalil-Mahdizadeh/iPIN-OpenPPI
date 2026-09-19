"""Candidate-local repository-boundary audit, preserving prior audits."""
import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('record', 'verify'))
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('workspace_guard', ROOT.parent / 'workspace_guard.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    current = module.snapshot()
    target = ROOT / 'provenance/original-v1/repository-before.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    if args.mode == 'record':
        with target.open('x') as handle: json.dump(current, handle, indent=2, sort_keys=True)
        print(json.dumps({'outside_benchmark_files_recorded': len(current)})); return
    old = json.loads(target.read_text())
    report = {'files_checked': len(old), 'coverage': 'Git-tracked and non-ignored untracked files outside benchmark/',
              'added': sorted(current.keys()-old.keys()), 'removed': sorted(old.keys()-current.keys()),
              'changed': sorted(k for k in old.keys() & current.keys() if old[k] != current[k])}
    report['passed'] = not any(report[k] for k in ('added', 'removed', 'changed'))
    with (target.parent / 'scope-audit.json').open('w') as handle: json.dump(report, handle, indent=2)
    print(json.dumps(report))
    assert report['passed']


if __name__ == '__main__': main()
