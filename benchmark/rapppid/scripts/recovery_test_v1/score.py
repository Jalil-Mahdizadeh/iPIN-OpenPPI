"""Candidate-only scores for all selected seeds and their fixed logit ensemble."""
from pathlib import Path
import time
import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from common import CELLS, cuda, now, read, sha, write
from comparison import COLUMNS, cell_path, relative_record, session_check
from frozen_scorer import Scorer, SCORERS


def main():
    session_check(); output = Path('/output'); started = time.monotonic()
    write(output / 'STARTED.json', {'at_utc': now(), 'scorer_freeze_sha256': sha('/bundle/SCORER_FREEZE.json')}, exclusive=True)
    scorer = Scorer('/bundle', cuda()); ids = pa.array(read('/bundle/endpoints.json'))
    files, coverage = [], {}
    for cell in CELLS:
        rows = pq.read_table(cell_path('/session', cell))
        aa = pc.index_in(rows[COLUMNS[1]], value_set=ids)
        bb = pc.index_in(rows[COLUMNS[2]], value_set=ids)
        assert not aa.null_count and not bb.null_count
        a, b = aa.to_numpy(), bb.to_numpy()
        values = scorer.scores(a, b)
        assert np.array_equal(values[:, 0], values[:, 1:].mean(1, dtype=np.float64))
        error = float(np.max(np.abs(values[:32] - scorer.scores(b[:32], a[:32]))))
        assert error <= 1e-4
        truncated = int(np.sum((scorer.lengths[a] > 1500) | (scorer.lengths[b] > 1500)))
        path = cell_path(output, cell)
        assert not path.exists()
        pq.write_table(pa.table({'candidate_token': rows['candidate_token'],
                                 **{name: values[:, i] for i, name in enumerate(SCORERS)}}), path, compression='zstd')
        files.append({**relative_record(path, output), 'cell': cell, 'rows': len(rows), 'reversal_error': error})
        coverage[cell] = {'pairs_scored': len(rows), 'pairs_with_native_truncation': truncated,
                          'fraction_with_native_truncation': truncated / len(rows)}
        print({'cell': cell, 'rows': len(rows), 'all_four_scorers_finite': True,
               'seconds': time.monotonic() - started}, flush=True)
    scorer.verify_state()
    write(output / 'PREDICTIONS.json', {'at_utc': now(), 'files': files, 'coverage': coverage,
        'scorer_freeze_sha256': sha('/bundle/SCORER_FREEZE.json'), 'session_sha256': sha('/session/SESSION.json'),
        'truth_accessed': False, 'training_performed': False, 'training_resumed': False,
        'complete_unique_finite_coverage': True, 'exact_mean_logit_ensemble': True,
        'elapsed_seconds': time.monotonic()-started}, exclusive=True)


if __name__ == '__main__':
    main()
