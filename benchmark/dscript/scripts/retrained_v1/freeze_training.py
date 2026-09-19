"""Freeze one qualified PU-D-SCRIPT recipe before formal training."""
from pathlib import Path
import shutil
from common import SEEDS,SIF_SHA,read,write,record,sha,now


def main():
    root=Path('/output')
    qualifications=('PILOT.json','REPRESENTATIVE_PILOT.json','PIPELINE_QUALIFICATION.json','CACHE_QUALIFICATION.json')
    for name in qualifications:assert read(root/name)['passed']
    cache=read(root/'residue_cache/CACHE.json');assert cache['full_length'] and cache['no_PPI_projection_applied']
    assert cache['shape']==[9237157,6165] and cache['dtype']=='float32'
    code=root/'code';code.mkdir(exist_ok=False);code_files=[]
    for source in sorted(Path('/code').glob('*.py')):
        target=code/source.name;shutil.copyfile(source,target)
        item=record(target);item['path']=source.name;code_files.append(item)
    recipe={'at_utc':now(),'execution_id':'dscript_retrained_benchmark_v1','authorized_to_train':True,
        'authorization':'User requested D-SCRIPT retraining on their data, subsequent C1/C2/C3 testing, generous Slurm margins, and pause after healthy startup.',
        'retrained_id':'PU-D-SCRIPT; native original architecture, fresh PPI-head initialization, fixed native Bepler-Berger lm_v1',
        'initialization':'Fresh published DSCRIPTModel construction using human_v1 architecture/configuration; no released human_v1 PPI weights loaded.',
        'encoder':'Native Bepler-Berger lm_v1; full-context FP32 6165-D residues; frozen, no encoder fitting',
        'sif_sha256':SIF_SHA,'upstream_commit':'0b3f7363b7d62fb99f5c8bfc6780833f088b8d84',
        'epochs':8,'evaluation_epochs':[4,8],'training_stages':[2,4,6,8],'seeds':list(SEEDS),
        'comparison_batch':16,'learning_rate':0.001,'optimizer':'Native Adam, constant lr=0.001, weight_decay=0; native model.clip after every optimizer step',
        'objective':'0.35*mean(wU*softplus(sU-sP)) + 0.65*mean(wU*(mean(CP)+mean(CU))/2), with wU=U_design_weight/mean(TRAIN_U_design_weight)',
        'objective_adaptation':'Replace native binary-label BCE with matched-data weighted P-versus-U ranking; retain native contact-map sparsity regularization and its 0.35/0.65 mixture. U is never represented as a verified negative.',
        'ranking_score':'Native pre-sigmoid logit k*(raw_pool-0.5), fixed native k=20; no saturation/clamp inversion; ensemble mean of three logits in FP64, not calibrated probability',
        'sampling':'Every one of 2,000,000 TRAIN U comparisons each epoch; balanced cycling of 16,799 positives; same PCG64DXSM SeedSequence([seed,epoch,stream]) order convention as iPIN/TUnA',
        'training_length_policy':'Independent uniform contiguous <=512-residue crop per endpoint occurrence from full-context native LM embeddings; short proteins unpadded; no pair exclusions',
        'inference_length_policy':'All residues, maximum7570; learned projection cached only after eval-mode weights are fixed; full native pooling and qualified three-residue halo tiling at contact area1000000',
        'native_batchnorm':'Native pair-at-a-time BatchNorm updates; no padded pair batching, tiled training, or cross-GPU synchronization that changes native normalization',
        'precision':'FP32 model/cache/softplus, FP64 weighted loss and ensemble accumulation; AMP and TF32 disabled',
        'selection':'Maximum full C3-DEV weighted P-vs-U concordance of the three-seed mean logit at epoch4 or8; exact ties choose earlier epoch; retain every seed; no acceptance threshold',
        'hyperparameter_recipes':1,'checkpoint_choices':2,'primary_contrast':'Retrained three-seed ensemble minus frozen optimized iPIN on C3',
        'secondary_contrasts':'Retrained vs original D-SCRIPT and baseline iPIN; both D-SCRIPT versions vs both iPIN references on all C1/C2/C3; individual-seed metrics',
        'test_rows':3019012,'test_cells':['C1_test','C2_test','C3_test'],
        'metric':'Historical design-weighted P-vs-U concordance, exact-score half ties; 2000 paired component-bootstrap draws, same historical design/seed/multiplicity definition',
        'test_exposure':'Original D-SCRIPT/iPIN/TUnA test results were already examined. This is a disclosed follow-up, not a newly untouched confirmatory test. No retrained test outcomes used for fitting or selection.',
        'original_reference_policy':'Reuse completed original D-SCRIPT and iPIN prediction files byte-for-byte; independently reproduce their metric points at final evaluation',
        'original_predictions_manifest_sha256':'0ca09cb7c4d0d72740146f040e01215ba260b7953a8e630770c9b8e6a693f042',
        'original_results_sha256':'d1cc407b7bcaeb2451880633585838a4f91005115587f925f3ebbdc9184d90da',
        'stopping':'Fixed8epochs; fail on nonfinite losses/gradients/parameters/scores or identity drift; no test-guided continuation or score selection',
        'resume':'Atomic model/Adam/CPU-RNG/CUDA-RNG/position/loss checkpoints every2048comparisons and epoch boundary; next-step bitwise recovery qualified on same GH200',
        'slurm_training_stage_walltime':'72hours each two-epoch stage, three parallel single-GPU seeds on one node; four afterok-dependent stages',
        'slurm_selection_walltime':'24hours on one GPU','slurm_test_walltime':'24hours on four GPUs for scoring, then one GPU for metrics',
        'logit_tolerance':0.0001,'data_manifest_sha256':sha('/data/DATA_MANIFEST.json'),
        'cache_manifest_sha256':sha(root/'residue_cache/CACHE.json'),'code_files':code_files,
        'qualifications':[record(root/name) for name in qualifications],
        'formal_training_started':False,'retrained_test_pairs_read':False,'retrained_test_truth_read':False,
        'output_scope':'All new artifacts under benchmark/dscript; original run, repository data/models and SIF images unchanged'}
    write(root/'TRAINING_FREEZE.json',recipe,exclusive=True)
    print({'training_freeze_sha256':sha(root/'TRAINING_FREEZE.json'),'stages':recipe['training_stages'],'seeds':recipe['seeds']},flush=True)


if __name__=='__main__':main()
