"""Freeze the unmodified official SPRINT checkout before building."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
source = ROOT.parent/'sprint/upstream'
commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
assert commit == 'b6272c76e1a943e6812b1b815607691819e6202e'
subprocess.run(['git', '-C', str(source), 'diff', '--exit-code', 'HEAD'], check=True)
names = subprocess.check_output(['git', '-C', str(source), 'ls-files'], text=True).splitlines()
items = [{'path': name, 'bytes': (source/name).stat().st_size,
          'sha256': hashlib.sha256((source/name).read_bytes()).hexdigest()}
         for name in names if name.startswith(('Src/', 'toy_example/', 'HSP/')) or name in ('LICENSE', 'makefile', 'README.md')]
target = ROOT/'manifests/sprint-source.json'
target.parent.mkdir(parents=True, exist_ok=True)
with target.open('x') as handle:
    json.dump({'upstream': 'https://github.com/lucian-ilie/SPRINT', 'commit': commit,
               'source_modified': False, 'files': items}, handle, indent=2, sort_keys=True)
    handle.write('\n')
