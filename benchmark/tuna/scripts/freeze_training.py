#!/usr/bin/env python3
"""Record the prospective recipe BEFORE any formal retraining or test access."""
from pathlib import Path
from common import SEEDS, now, read, record, sha, write

def main():
    root=Path('/output')
    for name in ('QUALIFICATION.json','REAL_QUALIFICATION.json'):
        if not read(root/name)['passed']:
            raise RuntimeError('Numerical qualification missing or failed')
    pilot=read(root/'PILOT.json')
    if len(pilot['trials'])!=3 or pilot['pu_hessian_max_absolute_error']>1e-10:
        raise RuntimeError('Pilot qualification failed')
    recipe={'execution_id':'tuna_pu_benchmark_v1','frozen_at_utc':now(),'authorized_to_train':True,
        'user_authorization':'Start TUnA first; compare released and retrained models with both frozen iPIN references on C1/C2/C3; GPU allowed; all outputs under benchmark.',
        'upstream_commit':'b5bda8fee261a4f27821738db995cf5883dcd133',
        'gp_commit':'18565eb86026800817857e37243ae81f15f089d7',
        'original_checkpoint':record('/weights/bernett_original.pt'),
        'original_choice':'Authors Bernett human-interaction checkpoint chosen before any TUnA test score; relevance to human held-out-protein evaluation, not empirical test performance.',
        'original_checkpoint_hf_revision':'eaec69cafc574d984119079220e75b11ffcb7c09',
        'original_score':'Released batch-one mean-field sigmoid probability, FP32, no ensemble',
        'retrained_id':'PU-TUnA; native architecture retrained from random PPI-head initialization on iPIN TRAIN',
        'epochs':8,'evaluation_epochs':[4,8],'seeds':list(SEEDS),'comparison_batch':64,
        'selection':'Maximum C3-development concordance of the FP64 mean of three adjusted-logit members; exact ties choose earlier epoch; no seed acceptance gate',
        'hyperparameter_recipes':1,'checkpoint_choices':2,
        'objective':'mean(normalized_U_design_weight * softplus(score_U-score_P)); softplus FP32, weighted accumulation FP64; U is unlabeled, not a verified negative',
        'epoch_sampling':'All 2,000,000 U once; balanced cycling of 16,799 P; same PCG64DXSM SeedSequence([seed,epoch,stream]) orders as frozen iPIN',
        'optimizer':'Native Adam with Lookahead(alpha=.8,k=5); lr=1e-4*.93**floor((epoch-1)/2); weight decay1e-5 except biases0',
        'architecture':{'esm_layers':30,'esm_dim':640,'head_dim':64,'intra_layers':1,'inter_layers':1,
            'attention_heads':8,'feedforward_dim':256,'dropout':.2,'activation':'swish','rff_features':4096,'ridge':1.},
        'training_length_policy':'Independent uniform contiguous crop up to512 residues per endpoint per occurrence; short endpoints padded; no pair exclusions',
        'inference_length_policy':'Full context ESM and full-length native TUnA endpoint representations; no truncation/windowing/exclusions; longest frozen sequence7570',
        'GP_covariance_adaptation':'For each evaluated frozen checkpoint, compute TRAIN-only weighted pairwise-logistic RFF Hessian + ridge I in FP64, Cholesky inverse, store FP32 covariance. Fixed positive-comparison stream seed+900000. This is a PU adaptation, not native BCE uncertainty or calibrated interaction probability.',
        'retrained_score':'Per-seed logit/sqrt(1+pi*variance/8); arithmetic mean of three adjusted logits in FP64; report individual seeds too',
        'precision':'FP32 model/attention/residue cache; no AMP or TF32; weighted loss and curvature accumulation FP64',
        'determinism':'Fixed seeds and data orders; cudnn deterministic and benchmark off; CUBLAS_WORKSPACE_CONFIG=:4096:8; SDPA stochastic dropout RNG differs from native attention; bitwise cross-hardware determinism not claimed',
        'native_forward_retained_during_training':True,'training_factorized':False,
        'inference_acceleration':'Qualified SDPA and algebraically equivalent per-endpoint caching for this exact upstream implementation',
        'test_cells':['C1_test','C2_test','C3_test'],'test_rows':3019012,
        'primary_contrast':'PU-TUnA ensemble minus frozen optimized iPIN on C3; baseline and original-TUnA contrasts also mandatory',
        'secondary_contrasts':'Both candidate versions vs both references on C1/C2; retrained-vs-original on every cell; all member scores',
        'metric':'Design-weighted positive-versus-unlabeled concordance with half credit for exact ties',
        'bootstrap':'2000 paired frozen component-multiplicity draws, same seed derivation/design weights/same-component convention as historical evaluation; two-sided percentile95%; finite draw counts disclosed',
        'test_exposure':'Disclosed follow-up on already-used iPIN test panels, not an independent fresh confirmation. No TUnA test predictions/truth inspected before this freeze.',
        'original_overlap':'External downstream-supervision exposure possible; must be disclosed/audited, not treated as clean TRAIN-only evidence',
        'stopping_rules':'8 epochs each seed; no test-guided retraining; fail on nonfinite scores/gradients or changed identities; resumable interrupted training only with same frozen code/config/RNG; report any incomplete seed',
        'pilot':record(root/'PILOT.json'),
        'qualifications':[record(root/name) for name in ['QUALIFICATION.json','REAL_QUALIFICATION.json']],
        'data_manifest_sha256':sha('/data/DATA_MANIFEST.json'),
        'residue_manifest_sha256':sha(root/'residue_cache/RESIDUE_CACHE_MANIFEST.json'),
        'training_code':[{'name':name,'sha256':sha(Path('/code')/name)} for name in
            ['adapter.py','common.py','residues.py','training.py','train.py','freeze_training.py']],
        'all_new_outputs_location':'benchmark/','test_pairs_read':False,'test_truth_read':False}
    write(root/'TRAINING_FREEZE.json',recipe,exclusive=True)
    print({'training_freeze_sha256':sha(root/'TRAINING_FREEZE.json'),'epochs':8,'seeds':list(SEEDS),'comparison_batch':64},flush=True)

if __name__=='__main__':
    main()
