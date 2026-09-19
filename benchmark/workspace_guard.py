#!/usr/bin/env python3
"""Record/verify non-benchmark tracked and visible untracked repository files."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

BENCH = Path(__file__).resolve().parent
ROOT = BENCH.parent

def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()

def snapshot():
    result = subprocess.run(['git','ls-files','-z','--cached','--others','--exclude-standard'], cwd=ROOT, check=True, capture_output=True)
    paths = sorted(set(result.stdout.decode().split('\0')) - {''})
    return {name:sha(ROOT/name) for name in paths if not name.startswith('benchmark/') and (ROOT/name).is_file()}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['record','verify'])
    args=parser.parse_args()
    path=BENCH/'.work/repository-before.json'
    current=snapshot()
    if args.mode=='record':
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('x') as handle:
            json.dump(current,handle,sort_keys=True,indent=2)
        print(json.dumps({'outside_benchmark_files_recorded':len(current)}))
    else:
        previous=json.loads(path.read_text())
        added=sorted(set(current)-set(previous))
        removed=sorted(set(previous)-set(current))
        changed=sorted(k for k in set(current)&set(previous) if current[k]!=previous[k])
        report={'passed':not(added or removed or changed),'files_checked':len(previous),'added':added,'removed':removed,'changed':changed}
        (BENCH/'REPOSITORY_SCOPE_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report))
        if not report['passed']:
            raise SystemExit(1)

if __name__=='__main__':
    main()
