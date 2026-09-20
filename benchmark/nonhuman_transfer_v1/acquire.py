"""Download immutable public source archives; checksum and validate every member."""
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen, Request
import os
import time
import zipfile
from study_utils import *

def download(species):
    name = species['archive']
    dest = LOCAL / name
    url = CONFIG['source_base'] + name
    sidecar = LOCAL / (name + '.json')
    if sidecar.exists():
        result = read(sidecar)
        check_records([result['artifact']])
        return result
    if dest.exists():
        raise RuntimeError(f'Unmanifested source {dest}')
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={'User-Agent': 'iPIN-nonhuman-audit/1.0'}), timeout=90) as r:
                headers = dict(r.headers.items())
                with dest.with_suffix('.partial').open('wb') as f:
                    for chunk in iter(lambda: r.read(8 << 20), b''):
                        f.write(chunk)
            os.replace(dest.with_suffix('.partial'), dest)
            break
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2)
    with zipfile.ZipFile(dest) as z:
        if z.testzip() is not None:
            raise RuntimeError('ZIP CRC failure')
        members = [dict(name=i.filename, bytes=i.file_size, crc32=i.CRC) for i in z.infolist()]
    result = dict(at_utc=now(), species=species['id'], url=url,
                  headers=headers, artifact=record(dest), members=members)
    write_json(sidecar, result)
    print(f"Downloaded {name}: {dest.stat().st_size:,} bytes, {len(members)} members", flush=True)
    return result

def main():
    require_container()
    LOCAL.mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        sources = list(pool.map(download, CONFIG['species']))
    write_json(OUT / 'SOURCES.json', dict(at_utc=now(), sources=sources,
               protocol=record(OUT / 'PROTOCOL.md'), config=record(OUT / 'config.json'),
               source_license='CC-BY-4.0', attribution='EMBL-EBI IntAct / IMEx; original studies retained per evidence record',
               license_url='https://www.ebi.ac.uk/intact/about'))

if __name__ == '__main__':
    main()
