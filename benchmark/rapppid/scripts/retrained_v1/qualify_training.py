"""TRAIN-only learning, speed, native scoring and exact Ranger21 resume gates."""
import copy
from pathlib import Path
import tempfile
import time
import numpy as np
import torch
from common import arrays, cuda, now, read, record, sha, verify, write
from benchmark_metrics import qualify as metric_qualify
from model import CONFIG, Tokens, endpoint_cache, fresh, learned_digest, optimizer, optimizer_auxiliary, orders, ranking_loss, scores, step
from pipeline import load_resume, nested_equal, save_resume

CORE = ('common.py', 'model.py', 'pipeline.py', 'train_worker.py', 'report_development.py',
        'qualify_training.py', 'gpu_guard.py', 'benchmark_metrics.py')


def main():
    root = Path('/output')
    verify(root / 'data', read(root / 'data/DATA_MANIFEST.json')['files'])
    device = cuda(731)
    tokens = Tokens(root / 'data')
    train = arrays(root / 'data/training.npz')
    train['normalized_u_weight'] = train['u_weight'] / train['u_weight'].mean()
    rng = np.random.Generator(np.random.PCG64DXSM(20260917))
    p = rng.integers(0, len(train['p_a']), 4096)
    u = rng.choice(len(train['u_a']), 4096, replace=False)
    # Independent analytic loss/gradient check, including unequal PU weights.
    logits = torch.tensor([-.7, .2, .9, .5, -.3, 1.2], device=device, requires_grad=True)
    weights = torch.tensor([.5, 2., 1.3], device=device, dtype=torch.float64)
    loss = ranking_loss(logits, weights)
    loss.backward()
    delta = logits.detach().cpu().numpy()[3:] - logits.detach().cpu().numpy()[:3]
    w = weights.cpu().numpy()
    expected_loss = float(np.mean(np.logaddexp(0., delta.astype(np.float64)) * w))
    expected_grad = w / (1. + np.exp(-delta.astype(np.float64))) / 3.
    gradient_error = float(np.max(np.abs(logits.grad.cpu().numpy() - np.r_[-expected_grad, expected_grad])))
    assert abs(float(loss.detach()) - expected_loss) <= 1e-7 and gradient_error <= 1e-7
    pa, ua = orders(91, 3, 16799, 2000000)
    counts = np.bincount(pa, minlength=16799)
    assert len(np.unique(ua)) == 2000000 and counts.max() - counts.min() == 1
    assert np.array_equal(pa, orders(91, 3, 16799, 2000000)[0])
    # SentencePiece stochastic draws repeat exactly for the same step key.
    a1, b1 = tokens.pack(train, p[:40], u[:40], 901, 1, 0, device)
    a2, b2 = tokens.pack(train, p[:40], u[:40], 901, 1, 0, device)
    assert torch.equal(a1, a2) and torch.equal(b1, b2)
    a3, b3 = tokens.pack(train, p[:40], u[:40], 901, 1, 40, device)
    assert not (torch.equal(a1, a3) and torch.equal(b1, b3))
    model = fresh(731, device).train()
    initial = learned_digest(model)
    opt = optimizer(model)
    for i in range(32):
        start = i * 40
        step(model, opt, tokens, train, p[start:start+40], u[start:start+40], 731, 1, start)
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
    tick = time.monotonic()
    for i in range(32, 96):
        start = i * 40
        last_metrics = step(model, opt, tokens, train, p[start:start+40], u[start:start+40], 731, 1, start)
    torch.cuda.synchronize()
    elapsed = time.monotonic() - tick
    assert learned_digest(model) != initial
    timing = {'timed_steps': 64, 'comparison_batch': 40, 'pair_batch': 80,
              'seconds': elapsed, 'comparisons_per_second': 2560 / elapsed,
              'projected_epoch_hours': elapsed / 2560 * 2000000 / 3600,
              'projected_20_epoch_hours': elapsed / 2560 * 2000000 * 20 / 3600,
              'includes': 'Fresh stochastic tokenization, forward/backward, actual native Ranger21 update and finiteness checks',
              'excludes': 'Checkpoint I/O, full DEV inference, other-node contention and queue wait',
              'peak_gpu_bytes': torch.cuda.max_memory_allocated(), 'last_metrics': last_metrics}
    print({'actual_training_pipeline_timing': timing}, flush=True)
    # Exercise recovery across lookahead merges and retain all Ranger21 counters.
    with tempfile.TemporaryDirectory(prefix='resume-check-', dir=root / 'tmp') as directory:
        path = Path(directory) / 'resume.pt'
        save_resume(path, model, opt, 1, 3840, {'loss': 3.}, 'qualification', 731)
        expected = []
        for start in (3840, 3880, 3920, 3960):
            expected.append(step(model, opt, tokens, train, p[:40], u[:40], 731, 1, start))
        expected_state = copy.deepcopy(model.state_dict())
        expected_opt = copy.deepcopy(opt.state_dict())
        expected_aux = optimizer_auxiliary(opt)
        resumed = fresh(991, device).train()
        resumed_opt = optimizer(resumed)
        assert load_resume(path, resumed, resumed_opt, 'qualification', 731, device)[:2] == (1, 3840)
        observed = []
        for start in (3840, 3880, 3920, 3960):
            observed.append(step(resumed, resumed_opt, tokens, train, p[:40], u[:40], 731, 1, start))
        assert expected == observed, (expected, observed)
        assert nested_equal(expected_state, resumed.state_dict())
        assert nested_equal(expected_opt, resumed_opt.state_dict())
        assert nested_equal(expected_aux, optimizer_auxiliary(resumed_opt))
        # Test auxiliary round trips in warmed-up/warmdown states without any
        # recipe change in formal runs (the tested class's own state controls it).
        resumed_opt.warmup_complete = True
        resumed_opt.warmdown_displayed = True
        resumed_opt.lookahead_step = 4
        save_resume(path, resumed, resumed_opt, 1, 4000, {'loss': 4.}, 'qualification', 731)
        expected = step(resumed, resumed_opt, tokens, train, p[:40], u[:40], 731, 1, 4000)
        state = copy.deepcopy(resumed.state_dict())
        again = fresh(119, device).train()
        again_opt = optimizer(again)
        load_resume(path, again, again_opt, 'qualification', 731, device)
        observed = step(again, again_opt, tokens, train, p[:40], u[:40], 731, 1, 4000)
        assert expected == observed and nested_equal(state, again.state_dict())
    del model, opt, resumed, resumed_opt, again, again_opt, expected_state, expected_opt, state
    torch.cuda.empty_cache()
    # Small TRAIN-only fixture must be learnable; none of these weights survive
    # into formal training. Keep the declared production optimizer schedule.
    model = fresh(4481, device).train()
    opt = optimizer(model)
    losses = []
    fixed_p, fixed_u = p[:40], u[:40]
    for i in range(160):
        losses.append(step(model, opt, tokens, train, fixed_p, fixed_u, 4481, 1, i * 40)['loss'])
    first, last = float(np.mean(losses[:16])), float(np.mean(losses[-16:]))
    assert last < first, (first, last)
    model.eval()
    fixture_ids = np.unique(np.concatenate((train['p_a'][fixed_p], train['p_b'][fixed_p], train['u_a'][fixed_u], train['u_b'][fixed_u])))
    before = learned_digest(model)
    embeddings = endpoint_cache(model, tokens, fixture_ids, allowed_partition='train')
    a = np.concatenate((train['p_a'][fixed_p], train['u_a'][fixed_u]))
    b = np.concatenate((train['p_b'][fixed_p], train['u_b'][fixed_u]))
    with torch.inference_mode():
        native = np.asarray([float(model.class_head(embeddings[int(x):int(x)+1], embeddings[int(y):int(y)+1]).item())
                             for x, y in zip(a, b, strict=True)])
    errors = []
    for batch in (1, 8, 8192):
        actual = scores(model, embeddings, a, b, batch=batch)
        errors.append(float(np.max(np.abs(actual - native))))
        errors.append(float(np.max(np.abs(actual - scores(model, embeddings, b, a, batch=batch)))))
    assert max(errors) <= 1e-4 and learned_digest(model) == before
    worst_a = torch.ones((80, 1500), device=device, dtype=torch.long)
    model.train()
    opt.zero_grad(set_to_none=True)
    torch.cuda.reset_peak_memory_stats()
    worst_logits = model.class_head(model(worst_a), model(worst_a)).reshape(-1)
    worst_loss = ranking_loss(worst_logits, torch.ones(40, device=device, dtype=torch.float64))
    worst_loss.backward()
    assert torch.isfinite(worst_loss) and all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters())
    worst_memory = torch.cuda.max_memory_allocated()
    assert worst_memory < torch.cuda.get_device_properties(device).total_memory * .8
    value = {'at_utc': now(), 'passed': True, 'gpu': torch.cuda.get_device_name(),
             'native_configuration': CONFIG, 'trainable_parameters': 188161,
             'tokenizer_sha256': sha(root / 'data/spm.model'),
             'data_manifest_sha256': sha(root / 'data/DATA_MANIFEST.json'),
             'code_sha256': {name: sha(Path('/code') / name) for name in CORE},
             'weighted_PU_loss_error': abs(float(loss.detach()) - expected_loss), 'weighted_PU_gradient_error': gradient_error,
             'balanced_positive_cycling_and_full_U_permutation_passed': True,
             'stochastic_tokens_step_repeatable': True, 'native_Ranger21_updates_passed': True,
             'resume_model_optimizer_auxiliary_and_metrics_bit_identical': True,
             'learning_fixture_first16_loss': first, 'learning_fixture_last16_loss': last,
             'development_scorer_maximum_native_logit_error': max(errors), 'logit_tolerance': 1e-4,
             'worst_case_pair_batch': 80, 'worst_case_tokens_per_endpoint': 1500,
             'worst_case_forward_backward_gpu_bytes': worst_memory,
             'timing': timing, 'metric_oracle': metric_qualify(device),
             'formal_training_performed': False, 'qualification_weights_discarded': True,
             'development_outcomes_used': False, 'test_pairs_read': False, 'test_truth_read': False}
    write(root / 'QUALIFICATION.json', value, exclusive=True)
    print(value, flush=True)


if __name__ == '__main__':
    main()
