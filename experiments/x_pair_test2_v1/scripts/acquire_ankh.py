"""Download the pinned public encoder; verify publisher-provided LFS hashes."""
from pathlib import Path
import hashlib
import json
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'ElnaggarLab/ankh-large'
REVISION = '74b371dbfa3ee0a05d32ae74df0c2e0b82d6b9a6'

def main():
    url = f'https://huggingface.co/api/models/{MODEL}/revision/{REVISION}?blobs=true'
    metadata = json.load(urllib.request.urlopen(url, timeout=30))
    assert metadata['sha'] == REVISION
    (ROOT/'sources/ankh_pinned_metadata.json').write_text(json.dumps(metadata, indent=2)+'\n')
    target = ROOT/'sources/ankh-large'
    target.mkdir(exist_ok=True)
    records = []
    for item in metadata['siblings']:
        name = item['rfilename']
        if name not in ('config.json', 'pytorch_model.bin', 'special_tokens_map.json', 'tokenizer.json', 'tokenizer_config.json'):
            continue
        path = target/name
        source = f'https://huggingface.co/{MODEL}/resolve/{REVISION}/{name}'
        if not path.exists():
            temporary = path.with_suffix(path.suffix+'.part')
            began = time.monotonic()
            with urllib.request.urlopen(source, timeout=120) as response, temporary.open('wb') as out:
                while True:
                    block = response.read(8<<20)
                    if not block:
                        break
                    out.write(block)
            temporary.rename(path)
            print({'downloaded':name,'bytes':path.stat().st_size,'seconds':time.monotonic()-began}, flush=True)
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda:stream.read(8<<20), b''):
                digest.update(block)
        assert path.stat().st_size == item['size']
        if item.get('lfs'):
            assert digest.hexdigest() == item['lfs']['sha256']
        records.append({'path':str(path.relative_to(ROOT)), 'bytes':path.stat().st_size,
                        'sha256':digest.hexdigest(), 'source':source})
    (ROOT/'sources/ANKH_FREEZE.json').write_text(json.dumps({'model':MODEL,'revision':REVISION,'files':records},indent=2)+'\n')

if __name__ == '__main__':
    main()
