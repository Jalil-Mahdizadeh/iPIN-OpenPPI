"""Read-only live-run checkpoint inspection; writes only a diagnostic record."""
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import torch

sys.path.insert(0, '/frozen_code')
from common import SEEDS, now, read, sha, write
from model import fresh, learned_digest, optimizer, restore_optimizer_auxiliary


def main():
    protocol_sha = sha('/protocol.json')
    records = []
    uuids = []
    for rank, seed in enumerate(SEEDS):
        directory = Path('/training') / f'seed_{seed}'
        events = [json.loads(line) for line in (directory / 'events.jsonl').read_text().splitlines()]
        start = next(event for event in events if event['event'] == 'start')
        progress = [event for event in events if event['event'] == 'training_progress'][-1]
        # Read a single complete atomic checkpoint version, even if the worker
        # replaces the path while this diagnostic is inspecting it.
        raw = (directory / 'resume.pt').read_bytes()
        state = torch.load(io.BytesIO(raw), map_location='cpu', weights_only=True)
        assert state['protocol_sha256'] == protocol_sha and state['seed'] == seed
        assert state['epoch'] == 1 and state['next_comparison'] >= 40960
        model = fresh(seed, device='cpu')
        assert learned_digest(model) == start['fresh_initial_state_sha256']
        opt = optimizer(model)
        model.load_state_dict(state['model'], strict=True)
        opt.load_state_dict(state['optimizer'])
        restore_optimizer_auxiliary(opt, state['ranger21_auxiliary'])
        digest = learned_digest(model)
        assert digest != start['fresh_initial_state_sha256']
        assert all(torch.isfinite(value).all() for value in model.state_dict().values())
        assert len(opt.state) == len(list(model.parameters())) == 23
        step_counts = []
        for parameter_state in opt.state.values():
            for value in parameter_state.values():
                if torch.is_tensor(value):
                    assert torch.isfinite(value).all()
            step_counts.append(int(parameter_state['step']))
        assert set(step_counts) == {state['next_comparison'] // 40}
        assert progress['metrics']['gradient_norm'] > 0
        log = Path('/logs') / f'retrained-train-2578434-epoch4-rank-{rank}.log'
        binding = re.search(r'GPU_BINDING rank=(\d+) seed=(\d+) uuid=(\S+) visible=(\S+)', log.read_text())
        assert binding and int(binding[1]) == rank and int(binding[2]) == seed
        uuids.append(binding[3])
        records.append({'seed': seed, 'gpu_uuid': binding[3], 'latest_progress': progress,
                        'checkpoint_sha256_at_inspection': hashlib.sha256(raw).hexdigest(),
                        'checkpoint_epoch': state['epoch'], 'checkpoint_next_comparison': state['next_comparison'],
                        'checkpoint_update_count': step_counts[0], 'checkpoint_learned_state_sha256': digest,
                        'different_from_fresh_initial_state': True, 'all_model_and_optimizer_tensors_finite': True,
                        'strict_model_and_optimizer_state_loading_passed': True})
    assert len(set(uuids)) == 3
    write('/output/STARTUP_HEALTH.json', {'at_utc': now(), 'passed': True, 'job_id': '2578434', 'node': 'n178',
          'distinct_GPUs': 3, 'seeds': records, 'training_freeze_sha256': protocol_sha,
          'live_training_modified_by_this_inspection': False, 'test_pairs_read': False, 'test_truth_read': False}, exclusive=True)
    print(json.dumps({'passed': True, 'job_id': '2578434', 'checkpoint_positions': [r['checkpoint_next_comparison'] for r in records],
                      'comparisons_per_second': [r['latest_progress']['comparisons_per_second_this_epoch_process'] for r in records]}, indent=2))


if __name__ == '__main__':
    main()
