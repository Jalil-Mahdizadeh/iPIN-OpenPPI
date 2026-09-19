"""Freeze the qualified original predictor before opening test candidates."""
from pathlib import Path
import shutil
from common import now, read, write, sha, record, ORIGINAL_SHA
from frozen_scorer import SCORERS

CODE=('common.py','native_model.py','frozen_scorer.py','comparison.py','benchmark_metrics.py','gpu_guard.py','score_shard.py')

def main():
    root=Path('/output'); qualification=read(root/'QUALIFICATION.json')
    assert qualification['passed'] and qualification['learned_state_unchanged']
    assert not qualification['test_pairs_read'] and not qualification['test_truth_read'] and not qualification['training_performed']
    for name,digest in qualification['code_sha256'].items():assert sha(Path('/code')/name)==digest
    assert sha('/sequences.json')==qualification['sequence_sha256']
    meta=read('/sequences.json');bundle=root/'scorer_bundle';bundle.mkdir(exist_ok=False)
    for name in ('code','provenance'):(bundle/name).mkdir()
    for name,key in (('sequences.json','sequence'),('endpoints.json','sha256'),('components.json','component'),('lengths.json','length')):
        write(bundle/name,meta[key],exclusive=True)
    for name in CODE:shutil.copyfile(Path('/code')/name,bundle/'code'/name)
    shutil.copyfile(root/'QUALIFICATION.json',bundle/'provenance/QUALIFICATION.json')
    shutil.copyfile('/opt/plm_interact/downloads.json',bundle/'provenance/DOWNLOADS.json')
    files=[]
    for path in sorted(bundle.rglob('*')):
        if path.is_file():
            item=record(path);item['path']=str(path.relative_to(bundle));files.append(item)
    policy={'at_utc':now(),'execution_id':'plm_interact_original_benchmark_v1','scorers':list(SCORERS),
            'original_model':'danliu1226/PLM-interact-650M-humanV11','model_revision':'e86e392dec13dd0c23252c94947b04a7a9821b0e',
            'checkpoint_sha256':ORIGINAL_SHA,'sif_sha256':Path('/sif.sha256').read_text().split()[0],
            'learned_state_sha256':qualification['learned_state_sha256'],'sequence_metadata_sha256':sha('/sequences.json'),
            'maximum_tokens':1603,'batch_size':qualification['selected_timing']['batch_size'],
            'score_definition':'Native sigmoid probability; no calibration, inversion, fitting, seed ensemble or order averaging',
            'order':'Ascending frozen sequence SHA256; deterministic canonical input to the native ordered model',
            'residue_policy':'Native tokenizer longest_first, maximum1603 including3special tokens; all pairs retained; long sequences truncated',
            'precision':'FP32; TF32/AMP disabled; published Transformers4.40.1; bucketed batches within fixed512-row blocks',
            'batch_tolerance':1e-5,'workers':4,'test_pairs_read':False,'test_truth_read':False,'training_performed':False,
            'metric':'Design-weighted P-versus-U concordance, exact-score half ties; 2000 paired historical component-bootstrap draws',
            'primary_cell':'C3_test','rows':3019012,'length_policy_selected_without_test_results':True,
            'original_external_training':'Authors identify D-SCRIPT human training data; external pair/component exposure remains possible',
            'metadata_caveat':'650M-humanV11 model card has a conflicting STRINGV12 sentence; repository mapping,35Mcard,andV11training-section identify D-SCRIPT human data; checkpoint SHA pinned without test selection',
            'prior_test_exposure':'Disclosed follow-up on panels already examined for iPIN/TUnA/D-SCRIPT; not an untouched holdout',
            'files':files}
    write(bundle/'SCORER_FREEZE.json',policy,exclusive=True)
    print({'frozen':True,'sha256':sha(bundle/'SCORER_FREEZE.json'),'batch_size':policy['batch_size']},flush=True)

if __name__=='__main__':main()
