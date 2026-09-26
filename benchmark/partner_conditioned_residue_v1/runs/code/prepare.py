"""Verify and copy only TRAIN/development and sequence-derived inputs."""
from collections import Counter
from pathlib import Path
import shutil
import h5py
import numpy as np
from common import arrays, now, read, record, sha, write
from data import train_standardization, validate_training


def main():
    output = Path('/output/data')
    output.mkdir(exist_ok=False)
    source = Path('/source_data')
    manifest = read(source / 'DATA_MANIFEST.json')
    names = ('endpoints.json', 'sequences.json', 'training.npz',
             'development_00.npz', 'development_01.npz', 'development_02.npz')
    expected = {Path(x['path']).name: x for x in manifest['outputs']}
    for name in names:
        if sha(source / name) != expected[name]['sha256']:
            raise RuntimeError(f'Source input identity changed: {name}')
        shutil.copyfile(source / name, output / name)
    meta = read(output / 'sequences.json')
    if Counter(meta['partition']) != Counter(train=11900, development=2550, test=2550):
        raise RuntimeError('Endpoint partition census mismatch')
    if meta['sha256'] != read(output / 'endpoints.json') or len(set(meta['sha256'])) != 17000:
        raise RuntimeError('Endpoint identity/order mismatch')
    validate_training(arrays(output / 'training.npz'), meta)
    for i in range(3):
        dev = arrays(output / f'development_{i:02d}.npz')
        partitions = np.asarray(meta['partition'])
        if np.any(partitions[dev['a']] == 'test') or np.any(partitions[dev['b']] == 'test'):
            raise RuntimeError('Test endpoint in development')
    cache_manifest = read('/cache/RESIDUE_CACHE_MANIFEST.json')
    print({'stage': 'verify_residue_cache_bytes', 'bytes': cache_manifest['cache']['bytes']}, flush=True)
    if Path('/cache/residues.h5').stat().st_size != cache_manifest['cache']['bytes'] or sha('/cache/residues.h5') != cache_manifest['cache']['sha256']:
        raise RuntimeError('Frozen residue cache checksum mismatch')
    means = np.empty((17000, 640), np.float32)
    with h5py.File('/cache/residues.h5', 'r') as handle:
        if not handle.attrs.get('complete') or len(handle) != 17000 or handle.attrs['sequence_manifest_sha256'] != sha(output / 'sequences.json'):
            raise RuntimeError('Invalid residue cache manifest linkage')
        for i, length in enumerate(meta['length']):
            values = handle[str(i)][:]
            if values.shape != (length, 640) or values.dtype != np.float32 or not np.isfinite(values).all():
                raise RuntimeError('Invalid residue cache matrix')
            means[i] = values.mean(0, dtype=np.float32)
    center, scale = train_standardization(means, meta['partition'])
    standardized = ((means.astype(np.float64) - center) / scale).astype(np.float32)
    if not np.isfinite(standardized).all():
        raise RuntimeError('Nonfinite standardized mean')
    np.save(output / 'global_means.npy', means, allow_pickle=False)
    np.save(output / 'global_standardized.npy', standardized, allow_pickle=False)
    np.savez(output / 'normalizer.npz', mean=center, std=scale)
    files = []
    for path in sorted(output.iterdir()):
        item = record(path); item['path'] = path.name; files.append(item)
    write(output / 'DATA_MANIFEST.json', {'at_utc': now(), 'files': files,
          'source_manifest_sha256': sha(source / 'DATA_MANIFEST.json'),
          'residue_manifest_sha256': sha('/cache/RESIDUE_CACHE_MANIFEST.json'),
          'residue_cache_sha256_verified': cache_manifest['cache']['sha256'],
          'proteins': 17000, 'residues': sum(meta['length']),
          'standardizer_fitted_to': '11900 TRAIN sequence endpoints only',
          'test_pairs_read': False, 'test_truth_read': False}, exclusive=True)
    print({'passed': True, 'proteins': 17000, 'output': str(output)}, flush=True)


if __name__ == '__main__':
    main()
