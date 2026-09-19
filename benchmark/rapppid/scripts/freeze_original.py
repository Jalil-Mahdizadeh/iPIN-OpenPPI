"""Freeze qualified original RAPPPID code, cache and policies before test access."""
from pathlib import Path
import shutil
from common import now, read, write, sha, record, ORIGINAL_SHA
from frozen_scorer import SCORERS
from native_model import TOKENIZER_SHA

CODE=('common.py','native_model.py','frozen_scorer.py','comparison.py','benchmark_metrics.py','gpu_guard.py','score_shard.py')


def main():
    root=Path('/output'); qualification=read(root/'QUALIFICATION.json')
    assert qualification['passed'] and qualification['learned_state_unchanged']
    assert not qualification['test_pairs_read'] and not qualification['test_truth_read'] and not qualification['training_performed']
    for name,digest in qualification['code_sha256'].items():assert sha(Path('/code')/name)==digest
    assert sha('/sequences.json')==qualification['sequence_sha256']
    assert sha(root/'endpoint_cache/embeddings.npy')==qualification['cache']['embedding_sha256']
    meta=read('/sequences.json');bundle=root/'scorer_bundle';bundle.mkdir(exist_ok=False)
    for name in ('code','provenance'):(bundle/name).mkdir()
    for name,key in (('sequences.json','sequence'),('endpoints.json','sha256'),('components.json','component'),('lengths.json','length')):
        write(bundle/name,meta[key],exclusive=True)
    for name in CODE:shutil.copyfile(Path('/code')/name,bundle/'code'/name)
    shutil.copyfile(root/'endpoint_cache/embeddings.npy',bundle/'embeddings.npy')
    shutil.copyfile(root/'endpoint_cache/CACHE.json',bundle/'provenance/CACHE.json')
    shutil.copyfile(root/'QUALIFICATION.json',bundle/'provenance/QUALIFICATION.json')
    shutil.copyfile('/opt/rapppid/downloads.json',bundle/'provenance/DOWNLOADS.json')
    shutil.copyfile('/opt/rapppid/runtime-downloads.json',bundle/'provenance/RUNTIME_DOWNLOADS.json')
    files=[]
    for path in sorted(bundle.rglob('*')):
        if path.is_file():
            item=record(path);item['path']=str(path.relative_to(bundle));files.append(item)
    policy={'at_utc':now(),'execution_id':'rapppid_original_benchmark_v1','scorers':list(SCORERS),
            'original_model':'RAPPPID-released-mult-red-dreamy','release':'1690837077.519848_red-dreamy',
            'model_revision':'c3a28be56fb3bd96ccf8cc44ea9145cfcadeaf6c',
            'checkpoint_sha256':ORIGINAL_SHA,'tokenizer_sha256':TOKENIZER_SHA,
            'sif_sha256':Path('/sif.sha256').read_text().split()[0],
            'learned_state_sha256':qualification['learned_state_sha256'],'sequence_metadata_sha256':sha('/sequences.json'),
            'maximum_residues':1500,'pair_batch_size':8192,'workers':1,'batch_tolerance':1e-5,
            'score_definition':'Native sigmoid probability; separate native singleton endpoint encoding and singleton MultClassHead moments; no fitting, inversion, calibration, ensemble or order averaging',
            'batching':'Exact effective-token-length endpoint batches, maximum32, qualified against singleton encoder; algebraically equivalent rowwise head moments qualified against native singleton head',
            'order':'Native multiplicative head is symmetric for singleton pair inputs; no order averaging',
            'residue_policy':'First1500 residues per endpoint, native deterministic validation/test SentencePiece; original0-padding and nonzero-count encoder slicing preserved; no excluded pairs',
            'precision':'FP32 model/cache/score, FP64 probability storage; TF32/AMP disabled',
            'test_pairs_read':False,'test_truth_read':False,'training_performed':False,
            'metric':'Design-weighted P-versus-U concordance, exact-score half ties; 2000 paired historical component-bootstrap draws',
            'primary_cell':'C3_test','rows':3019012,'policies_selected_without_test_results':True,
            'original_external_training':'Authors identify human comparatives STRING C3 dataset; external pair/component exposure remains possible',
            'release_caveat':'Authors released mult head, not the original paper concat head; singleton inference policy avoids native batch dependence',
            'prior_test_exposure':'Disclosed follow-up on panels already examined for iPIN/TUnA/D-SCRIPT/PLM-interact; not an untouched holdout',
            'files':files}
    write(bundle/'SCORER_FREEZE.json',policy,exclusive=True)
    print({'frozen':True,'sha256':sha(bundle/'SCORER_FREEZE.json')},flush=True)


if __name__=='__main__':main()
