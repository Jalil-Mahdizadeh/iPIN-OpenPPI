"""Strict candidate-identity adapter. No truth or reference mounts in either phase."""
import argparse
from pathlib import Path
import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from common import CELLS, P_COUNTS, now, read, sha, write
from comparison import cell_path, relative_record, session_check, verify
from policy import SCORERS


def prepare():
    session_check(); output = Path('/output')
    ids = pa.array(read('/bundle/endpoints.json')); census = []
    with (output/'pairs.txt').open('x') as f:
        for cell in CELLS:
            rows = pq.read_table(cell_path('/session', cell))
            a = pc.index_in(rows['endpoint_a_sha256'], value_set=ids)
            b = pc.index_in(rows['endpoint_b_sha256'], value_set=ids)
            assert not a.null_count and not b.null_count and len(rows) == P_COUNTS[cell] + 1000000
            for x, y in zip(a.to_pylist(), b.to_pylist()): f.write(f'p{x:05d} p{y:05d}\n')
            census.append({'cell': cell, 'rows': len(rows), 'candidate_file_sha256': sha(cell_path('/session', cell))})
    write(output/'NATIVE_INPUT.json', {'at_utc': now(), 'cells': census, 'rows': 3019012,
        'scorer_freeze_sha256': sha('/bundle/SCORER_FREEZE.json'), 'session_sha256': sha('/session/SESSION.json'),
        'files': [relative_record(output/'pairs.txt', output)], 'truth_accessed': False,
        'dummy_routing_marker': 1}, exclusive=True)


def collect():
    session_check(); output = Path('/output')
    request = read('/native_input/NATIVE_INPUT.json'); completion = read('/native_scores/NATIVE_COMPLETE.json')
    assert not request['truth_accessed'] and not completion['test_truth_read']
    assert request['scorer_freeze_sha256'] == completion['scorer_freeze_sha256'] == sha('/bundle/SCORER_FREEZE.json')
    assert request['session_sha256'] == sha('/session/SESSION.json')
    assert completion['native_input_sha256'] == sha('/native_input/NATIVE_INPUT.json')
    assert completion['scores_sha256'] == sha('/native_scores/scores.txt')
    verify('/native_input', request['files'])
    files = []; coverage = {}
    with Path('/native_scores/scores.txt').open() as native:
        for cell, item in zip(CELLS, request['cells'], strict=True):
            assert item['cell'] == cell and item['candidate_file_sha256'] == sha(cell_path('/session', cell))
            rows = pq.read_table(cell_path('/session', cell)); assert len(rows) == item['rows']
            values = np.empty(len(rows), dtype=np.float64)
            for i in range(len(rows)):
                fields = next(native).split()
                assert len(fields) == 2 and fields[1] == '1'
                values[i] = float(fields[0])
            assert np.isfinite(values).all() and (values >= 0).all()
            target = cell_path(output, cell); assert not target.exists()
            pq.write_table(pa.table({'candidate_token': rows['candidate_token'], SCORERS[0]: values}), target, compression='zstd')
            files.append({**relative_record(target, output), 'cell': cell})
            zeros = int((values == 0).sum())
            coverage[cell] = {'pairs_scored': len(rows), 'zero_scores': zeros, 'zero_fraction': zeros/len(rows),
                              'unique_scores': len(np.unique(values)), 'pairs_with_native_truncation': 0}
        assert native.read() == '', 'Unexpected extra native score rows'
    assert sum(x['pairs_scored'] for x in coverage.values()) == request['rows'] == 3019012
    write(output/'PREDICTIONS.json', {'at_utc': now(), 'files': files, 'coverage': coverage,
        'scorer_freeze_sha256': sha('/bundle/SCORER_FREEZE.json'), 'session_sha256': sha('/session/SESSION.json'),
        'native_completion_sha256': sha('/native_scores/NATIVE_COMPLETE.json'), 'truth_accessed': False,
        'native_output_precision_preserved': True, 'dummy_markers_discarded': True}, exclusive=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=['prepare', 'collect'])
    {'prepare': prepare, 'collect': collect}[parser.parse_args().phase]()
