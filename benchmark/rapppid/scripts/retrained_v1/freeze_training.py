"""Freeze the qualified 20-epoch TRAIN/C3-DEV-only recipe before submission."""
from pathlib import Path
import shutil
from common import SEEDS, EVALUATION_EPOCHS, SIF_SHA, UPSTREAM_COMMIT, now, read, record, sha, verify, write
from model import CONFIG


def main():
    root = Path('/output')
    qualification = read(root / 'QUALIFICATION.json')
    assert qualification['passed'] and qualification['resume_model_optimizer_auxiliary_and_metrics_bit_identical']
    assert qualification['stochastic_tokens_step_repeatable'] and qualification['native_Ranger21_updates_passed']
    assert not qualification['test_pairs_read'] and not qualification['test_truth_read']
    assert not qualification['development_outcomes_used'] and not qualification['formal_training_performed']
    for name, digest in qualification['code_sha256'].items():
        assert sha(Path('/code') / name) == digest, name
    assert qualification['native_configuration'] == CONFIG
    assert sha(root / 'data/DATA_MANIFEST.json') == qualification['data_manifest_sha256']
    verify(root / 'data', read(root / 'data/DATA_MANIFEST.json')['files'])
    fixture = root / 'orchestration-qualification'
    io_check = read(fixture / 'PIPELINE_QUALIFICATION.json')
    assert io_check['passed'] and io_check['synthetic_TRAIN_fixture_only']
    assert not io_check['real_development_outcomes_used']
    aggregate = read(fixture / 'results/DEVELOPMENT_RESULTS.json')
    assert aggregate['through_epoch'] == 8 and len(aggregate['epochs']) == 2
    assert not aggregate['checkpoint_selected'] and not aggregate['test_evaluation_scheduled']
    for item in aggregate['epochs']:
        assert item['rows'] == 1002265 and len(item['member_concordance']) == 3
    for name, digest in qualification['code_sha256'].items():
        assert sha(fixture / 'code' / name) == digest
    code = root / 'code'
    code.mkdir(exist_ok=False)
    files = []
    for source in sorted(Path('/code').glob('*.py')):
        destination = code / source.name
        shutil.copyfile(source, destination)
        files.append(record(destination, code))
    recipe = {'at_utc': now(), 'execution_id': 'rapppid_retrained_v1', 'authorized_to_train': True,
              'authorization': 'User requested 20 epochs, retained checkpoints and full C3-development evaluation every 4 epochs; user will choose the epoch for later test evaluation.',
              'retrained_model': 'PU-RAPPPID-mult; fresh native encoder and interaction head, TRAIN-only SentencePiece',
              'native_configuration': CONFIG, 'upstream_commit': UPSTREAM_COMMIT, 'sif_sha256': SIF_SHA,
              'epochs': 20, 'evaluation_epochs': list(EVALUATION_EPOCHS), 'seeds': list(SEEDS),
              'comparison_batch': 40, 'pair_presentations_per_step': 80, 'comparisons_per_epoch': 2000000,
              'native_optimizer': 'Ranger21 0.1.0, lr 0.01, weight_decay 0.0001, default 2000-step warmup, warmdown from 72 percent of 1,000,000 updates, logging disabled only',
              'extra_swa': False, 'checkpoint_policy': 'Retain raw model and full recovery state at epochs 4, 8, 12, 16, 20 for every seed; no best-only pruning or early stopping',
              'swa_disclosure': 'No additional stochastic weight averaging; fixed raw-epoch candidates and three-seed mean-logit ensemble, rather than the original paper training recipe',
              'initialization': 'All 188,161 native parameters freshly initialized per seed; no original released PPI weights or original tokenizer used for fitting',
              'tokenizer': '250-piece unigram TRAIN-only full-sequence corpus; native stochastic training tokenization alpha 0.1, nbest_size -1; first 1500 residues; deterministic DEV tokenization',
              'tokenizer_sha256': qualification['tokenizer_sha256'],
              'tokenizer_recovery': 'SeedSequence([seed,epoch,comparison_start,2]) generates a 31-bit SentencePiece seed; fresh tokenization thread per step resets native thread-local RNG',
              'sampling': 'All 2,000,000 TRAIN U each epoch; balanced cycling of 16,799 P; independent PCG64DXSM SeedSequence([seed,epoch,stream]) streams 0 and 1, as iPIN/TUnA/D-SCRIPT',
              'objective': 'mean((U_design_weight/mean(TRAIN_U_design_weight))*softplus(native_logit_U-native_logit_P))',
              'objective_disclosure': 'Weighted PU ranking replaces supervised binary-negative BCE; U remains unlabeled; native optimizer regularization and AWD/embedding dropout retained',
              'training_batch_policy': 'Native separately padded endpoint batches and unmodified MultClassHead global moments; no cross-GPU batch synchronization or packed-sequence replacement',
              'development_policy': 'All 1,002,265 C3-DEV pairs: 2,265 P + 1,000,000 U; fixed singleton native endpoint encoding and per-pair native head moments; no pair exclusions; 1500-residue prefix cap',
              'train_eval_batch_disclosure': 'Training uses native batch-dependent padding/normalization; evaluation deliberately fixes singleton semantics, as in original RAPPPID evaluation. They are not numerically identical policies.',
              'development_score': 'Native pre-sigmoid logit; per-seed ranking and FP64 mean of all 3 seed logits at the same epoch',
              'development_metric': 'Historical full-panel design-weighted P-versus-U concordance; exact-score half ties',
              'checkpoint_selection': 'None automatic. Publish all five checkpoints for user review; later test evaluation requires a separate user instruction.',
              'test_evaluation_authorized': False, 'test_evaluation_scheduled': False,
              'test_pairs_read': False, 'test_truth_read': False,
              'precision': 'FP32 model/logits/softplus; FP64 weighted loss/ensemble; TF32 and AMP disabled',
              'recovery': 'Atomic model/Ranger21 moments + auxiliary counters/CPU + CUDA RNG/epoch/position/sums every 40,960 comparisons and boundaries; exact next 4 updates tested',
              'slurm': 'One 48-hour job, one 3-GPU node allocation, one independent seed per GPU; report full C3-DEV after each 4-epoch stage; no test job',
              'hyperparameter_recipes': 1, 'development_checkpoint_candidates': 5,
              'qualified_before_formal_training': True, 'qualification_sha256': sha(root / 'QUALIFICATION.json'),
              'synthetic_orchestration_qualification_sha256': sha(fixture / 'PIPELINE_QUALIFICATION.json'),
              'synthetic_orchestration_report_sha256': sha(fixture / 'results/DEVELOPMENT_RESULTS.json'),
              'data_manifest_sha256': sha(root / 'data/DATA_MANIFEST.json'), 'code_files': files,
              'output_scope': 'New files under benchmark/rapppid; existing original run and other model jobs untouched'}
    write(root / 'TRAINING_FREEZE.json', recipe, exclusive=True)
    print({'frozen': True, 'training_freeze_sha256': sha(root / 'TRAINING_FREEZE.json'),
           'test_evaluation_scheduled': False}, flush=True)


if __name__ == '__main__':
    main()
