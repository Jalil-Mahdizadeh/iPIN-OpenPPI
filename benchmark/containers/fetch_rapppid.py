"""Fetch the pinned author's RAPPPID release; write only below benchmark/."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request

BENCH = Path(__file__).resolve().parents[1]
COMMIT = 'c3a28be56fb3bd96ccf8cc44ea9145cfcadeaf6c'
RELEASE = '1690837077.519848_red-dreamy'


def request(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'rapppid-benchmark-v1'}), timeout=90) as response:
        return response.read()


def main():
    destination = BENCH / 'rapppid/upstream'
    manifest = BENCH / 'containers/manifests/rapppid-downloads.json'
    if manifest.exists():
        previous = json.loads(manifest.read_text())
        assert previous['upstream_commit'] == COMMIT
        for item in previous['files']:
            p = destination / item['path']
            assert p.is_file() and not p.is_symlink()
            assert p.stat().st_size == item['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest() == item['sha256']
        print('Pinned RAPPPID downloads already verified', flush=True)
        return
    tree = json.loads(request(f'https://api.github.com/repos/jszym/rapppid/git/trees/{COMMIT}?recursive=1'))
    assert not tree.get('truncated') and tree['sha'] == COMMIT
    files = []
    for item in tree['tree']:
        name = item['path']
        if item['type'] != 'blob' or name == '.gitignore':
            continue
        relative = Path(name)
        assert not relative.is_absolute() and '..' not in relative.parts
        target = destination / relative
        url = f'https://raw.githubusercontent.com/jszym/rapppid/{COMMIT}/{name}'
        content = target.read_bytes() if target.exists() else request(url)
        assert len(content) == item['size']
        assert hashlib.sha1(f'blob {len(content)}\0'.encode() + content).hexdigest() == item['sha']
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as handle:
                handle.write(content)
        files.append({'path': name, 'bytes': len(content), 'git_blob_sha1': item['sha'],
                      'sha256': hashlib.sha256(content).hexdigest(), 'url': url})
        print('verified', name, len(content), flush=True)
    record = {'at_utc': datetime.now(timezone.utc).isoformat(), 'upstream_commit': COMMIT,
              'release': RELEASE, 'repository': 'https://github.com/jszym/rapppid',
              'authors_released_variant': 'RAPPPID-mult, human comparatives STRING C3',
              'not_exact_paper_concat_checkpoint': True, 'training_performed': False, 'files': files}
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with manifest.open('x') as handle:
        json.dump(record, handle, indent=2, sort_keys=True)
        handle.write('\n')


if __name__ == '__main__':
    main()
