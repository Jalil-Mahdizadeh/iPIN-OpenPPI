"""Copy fixed TRAIN/C3-DEV inputs and fit a TRAIN-only SentencePiece model."""
import hashlib
import io
from pathlib import Path
import shutil
import numpy as np
import sentencepiece as sp
from data import RapppidDataset2
from common import DATA_SHA, DEV_SHA, SEQUENCES_SHA, arrays, now, read, record, sha, write


def main():
    source = Path('/source_data')
    root = Path('/output/data')
    root.mkdir(exist_ok=False)
    expected = {'training.npz': DATA_SHA, 'development_00.npz': DEV_SHA,
                'sequences.json': SEQUENCES_SHA,
                'endpoints.json': '7268cafef3623854e95348bd9bab5a8eefb9e04f2a75d1df02e620c23cd6d4f1'}
    for name, digest in expected.items():
        assert sha(source / name) == digest
        shutil.copyfile(source / name, root / name)
    meta = read(root / 'sequences.json')
    train = arrays(root / 'training.npz')
    dev = arrays(root / 'development_00.npz')
    part = np.asarray(meta['partition'])
    assert len(meta['sequence']) == 17000 and read(root / 'endpoints.json') == meta['sha256']
    assert len(set(meta['sha256'])) == 17000
    assert all(hashlib.sha256(s.encode()).hexdigest() == h for s, h in zip(meta['sequence'], meta['sha256'], strict=True))
    assert len(train['p_a']) == 16799 and len(train['u_a']) == 2000000
    for key in ('p_a', 'p_b', 'u_a', 'u_b'):
        assert (part[train[key]] == 'train').all()
    assert len(dev['a']) == 1002265 and int(dev['positive'].sum()) == 2265
    assert (part[dev['a']] == 'development').all() and (part[dev['b']] == 'development').all()
    assert np.isfinite(train['u_weight']).all() and (train['u_weight'] > 0).all()
    assert np.isfinite(dev['weight']).all() and (dev['weight'] > 0).all()
    train_ids = np.unique(np.concatenate([train[k] for k in ('p_a', 'p_b', 'u_a', 'u_b')]))
    dev_ids = np.unique(np.concatenate([dev['a'], dev['b']]))
    assert not np.intersect1d(train_ids, dev_ids).size
    # Stable input order, single-threaded tokenizer fitting, and every TRAIN
    # endpoint retained. No released tokenizer or released PPI weights loaded.
    corpus = [meta['sequence'][int(i)] for i in train_ids]
    kwargs = {'vocab_size': 250, 'model_type': 'unigram', 'character_coverage': 1.,
              'bos_id': -1, 'eos_id': -1, 'pad_id': 0, 'unk_id': 1,
              'num_threads': 1, 'input_sentence_size': 0, 'shuffle_input_sentence': False,
              'max_sentence_length': max(map(len, corpus)) + 1, 'hard_vocab_limit': True}
    stream = io.BytesIO()
    sp.set_random_generator_seed(20260803)
    sp.SentencePieceTrainer.train(sentence_iterator=iter(corpus), model_writer=stream, **kwargs)
    with (root / 'spm.model').open('xb') as handle:
        handle.write(stream.getvalue())
    spp = sp.SentencePieceProcessor(model_file=str(root / 'spm.model'))
    assert spp.get_piece_size() == 250 and spp.pad_id() == 0 and spp.unk_id() == 1
    # This is a tokenizer/cache census, not development outcome evaluation.
    maximum = 0
    for i in np.concatenate((train_ids, dev_ids)):
        tokens = np.asarray(RapppidDataset2.static_encode(1500, spp, meta['sequence'][int(i)],
                                                       sp=True, pad=True, sampling=False), np.int64)
        assert tokens.shape == (1500,) and ((tokens >= 0) & (tokens < 250)).all()
        assert np.count_nonzero(tokens) > 0
        maximum = max(maximum, int(np.count_nonzero(tokens)))
    write(root / 'TOKENIZER.json', {'at_utc': now(), 'train_endpoint_count': len(train_ids),
          'train_endpoint_indices': train_ids.tolist(), 'train_sequence_corpus_sha256': hashlib.sha256('\n'.join(corpus).encode()).hexdigest(),
          'parameters': kwargs, 'seed': 20260803, 'spm_sha256': sha(root / 'spm.model'),
          'TRAIN_only_fitting': True, 'external_tokenizer_used': False,
          'development_endpoints_checked_not_fitted': len(dev_ids), 'max_effective_tokens': maximum,
          'test_pairs_read': False, 'test_truth_read': False}, exclusive=True)
    files = [record(root / name, root) for name in (*expected, 'spm.model', 'TOKENIZER.json')]
    write(root / 'DATA_MANIFEST.json', {'at_utc': now(), 'files': files,
          'source_manifest_sha256': sha(source / 'DATA_MANIFEST.json'),
          'train_positive_rows': 16799, 'train_unlabeled_rows': 2000000,
          'development_cell': 'C3_development', 'development_rows': 1002265,
          'development_positive_rows': 2265, 'TRAIN_only_fitting_enforced': True,
          'test_pairs_read': False, 'test_truth_read': False}, exclusive=True)
    print({'prepared': True, 'training_endpoints': len(train_ids), 'development_endpoints': len(dev_ids),
           'tokenizer_sha256': sha(root / 'spm.model')}, flush=True)


if __name__ == '__main__':
    main()
