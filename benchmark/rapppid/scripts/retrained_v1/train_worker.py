"""Three independent TRAIN-only runs, retained every four epochs; never test."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import time
import numpy as np
import torch
from common import SEEDS, EVALUATION_EPOCHS, arrays, atomic_json, cuda, now, read, sha, verify, write
from model import CONFIG, Tokens, fresh, learned_digest, optimizer, orders, step
from pipeline import evaluate_development, load_resume, save_resume


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, choices=SEEDS, required=True)
    parser.add_argument('--through-epoch', type=int, choices=EVALUATION_EPOCHS, required=True)
    args = parser.parse_args()
    root = Path('/output')
    lock = (root / '.worker.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    protocol = read('/protocol.json')
    protocol_sha = sha('/protocol.json')
    verify('/code', protocol['code_files'])
    assert protocol['epochs'] == 20 and protocol['native_configuration'] == CONFIG
    assert sha('/data/DATA_MANIFEST.json') == protocol['data_manifest_sha256']
    verify('/data', read('/data/DATA_MANIFEST.json')['files'])
    stage = root / f'STAGE_{args.through_epoch:02d}_COMPLETE.json'
    if stage.exists():
        assert read(stage)['protocol_sha256'] == protocol_sha
        assert sha(root / f'epoch_{args.through_epoch:02d}.json') == read(stage)['development_report_sha256']
        print('Completed training/development stage verified', flush=True)
        return
    device = cuda(args.seed)
    tokens = Tokens()
    train = arrays('/data/training.npz')
    train['normalized_u_weight'] = train['u_weight'] / train['u_weight'].mean()
    dev = arrays('/data/development_00.npz')
    part = np.asarray(tokens.meta['partition'])
    for key in ('p_a', 'p_b', 'u_a', 'u_b'):
        assert (part[train[key]] == 'train').all()
    assert (part[dev['a']] == 'development').all() and (part[dev['b']] == 'development').all()
    assert len(train['u_a']) == 2000000 and len(train['p_a']) == 16799
    model = fresh(args.seed, device)
    initial_digest = learned_digest(model)
    opt = optimizer(model)
    resume = root / 'resume.pt'
    epoch, done, sums = 1, 0, {'loss': 0.}
    if resume.exists():
        epoch, done, sums = load_resume(resume, model, opt, protocol_sha, args.seed, device)
    if args.through_epoch > 4:
        previous = read(root / f'STAGE_{args.through_epoch-4:02d}_COMPLETE.json')
        assert previous['protocol_sha256'] == protocol_sha
        assert epoch >= args.through_epoch - 3
    assert 1 <= epoch <= args.through_epoch + 1 and 0 <= done <= len(train['u_a'])
    stop_requested = [False]
    for sig in (signal.SIGTERM, signal.SIGUSR1):
        signal.signal(sig, lambda *_: stop_requested.__setitem__(0, True))

    def event(fields):
        value = {'at_utc': now(), 'seed': args.seed, **fields}
        print(value, flush=True)
        with (root / 'events.jsonl').open('a') as handle:
            handle.write(json.dumps(value, allow_nan=False) + '\n')
        atomic_json(root / 'PROGRESS.json', value)

    event({'event': 'start', 'epoch': epoch, 'next_comparison': done, 'through_epoch': args.through_epoch,
           'protocol_sha256': protocol_sha, 'gpu': torch.cuda.get_device_name(),
           'slurm_job_id': os.environ.get('SLURM_JOB_ID'), 'trainable_parameters': 188161,
           'fresh_initial_state_sha256': initial_digest, 'resumed': resume.exists()})
    started = time.monotonic()
    for current in range(epoch, args.through_epoch + 1):
        model.train()
        tick, start_done = time.monotonic(), done
        p_order, u_order = orders(args.seed, current, len(train['p_a']), len(train['u_a']))
        if done == 0:
            save_resume(resume, model, opt, current, 0, sums, protocol_sha, args.seed)
        for start in range(done, len(u_order), protocol['comparison_batch']):
            end = min(start + protocol['comparison_batch'], len(u_order))
            metrics = step(model, opt, tokens, train, p_order[start:end], u_order[start:end], args.seed, current, start)
            sums['loss'] += metrics['loss'] * (end - start)
            done = end
            if end % 5120 == 0 or end == len(u_order):
                seconds = time.monotonic() - tick
                event({'event': 'training_progress', 'epoch': current, 'comparisons_done': end,
                       'comparisons_total': len(u_order), 'metrics': metrics,
                       'running_mean_loss': sums['loss'] / end,
                       'comparisons_per_second_this_epoch_process': (end - start_done) / max(seconds, 1e-9),
                       'epoch_seconds_this_process': seconds, 'peak_gpu_bytes': torch.cuda.max_memory_allocated()})
            if end % 40960 == 0 or end == len(u_order) or stop_requested[0]:
                save_resume(resume, model, opt, current, done, sums, protocol_sha, args.seed)
            if stop_requested[0]:
                event({'event': 'checkpointed_stop', 'epoch': current, 'comparisons_done': done})
                raise SystemExit(75)
        event({'event': 'epoch_complete', 'epoch': current, 'running_mean_loss': sums['loss'] / len(u_order)})
        if current in protocol['evaluation_epochs']:
            evaluate_development(root, current, model, opt, tokens, dev, protocol_sha, args.seed, sums, event)
        done, sums = 0, {'loss': 0.}
        save_resume(resume, model, opt, current + 1, 0, sums, protocol_sha, args.seed)
    result = {'at_utc': now(), 'seed': args.seed, 'through_epoch': args.through_epoch,
              'protocol_sha256': protocol_sha, 'elapsed_this_process_seconds': time.monotonic() - started,
              'test_pairs_read': False, 'test_truth_read': False, 'test_evaluation_authorized': False,
              'resume_checkpoint_sha256': sha(resume),
              'development_report_sha256': sha(root / f'epoch_{args.through_epoch:02d}.json')}
    write(stage, result, exclusive=True)
    if args.through_epoch == 20:
        write(root / 'COMPLETE.json', result, exclusive=True)
    event({'event': 'stage_complete', 'through_epoch': args.through_epoch})


if __name__ == '__main__':
    main()
