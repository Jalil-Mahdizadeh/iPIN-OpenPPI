#!/usr/bin/env python3
"""New benchmark-local scoring/evaluation; historical ledgers are never written.

Each CLI phase has different allowlisted mounts. Candidate scoring cannot see
truth, keys, references or development data. Truth is opened only after every
prediction and both byte-identical iPIN references have been frozen.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import time
import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.parquet as pq
from benchmark_metrics import bootstrap, qualify
from common import CELLS, P_COUNTS, cuda, now, read, record, sha, write
from policy import ALL_SCORERS, SCORERS, REFERENCES

PACKAGE='pair_level_pu_r_benchmark_artifacts_v1'
CELL_INDEX={'C3_test':0,'C2_test':3,'C1_test':6}
BASELINE='lightweight_esm2_150m_linear__linear_lr3e-4'
OPTIMIZED='esm2_150m__residual_wide__epoch04_ensemble3'
COLUMNS=['candidate_token','endpoint_a_sha256','endpoint_b_sha256','cell_id']

def cell_path(root,cell):
    return Path(root)/f'cell-{CELL_INDEX[cell]:02d}.parquet'

def relative_record(path,root):
    item=record(path); item['path']=str(Path(path).relative_to(root)); return item

def verify(root,items):
    for item in items:
        relative=Path(item['path'])
        if relative.is_absolute() or '..' in relative.parts:
            raise RuntimeError('Unsafe artifact record')
        path=Path(root)/relative
        if path.is_symlink() or not path.is_file() or path.stat().st_size!=item['bytes'] or sha(path)!=item['sha256']:
            raise RuntimeError('Frozen artifact changed')

def bundle_check():
    manifest=read('/bundle/SCORER_FREEZE.json')
    if manifest['scorers']!=list(SCORERS) or manifest['test_pairs_read'] or manifest['test_truth_read']:
        raise RuntimeError('Invalid scorer freeze')
    verify('/bundle',manifest['files'])
    return manifest

def session_check():
    bundle_check()
    session=read('/session/SESSION.json')
    if session['scorer_freeze_sha256']!=sha('/bundle/SCORER_FREEZE.json') or session['truth_accessed']:
        raise RuntimeError('Scoring session drift')
    verify('/session',session['files'])
    if {x['cell'] for x in session['files']}!=set(CELLS):
        raise RuntimeError('Incomplete scoring session')
    return session

def prediction_values(tokens,table):
    if table.column_names!=['candidate_token','score'] or any(table[x].null_count for x in table.column_names):
        raise RuntimeError('Invalid reference prediction schema')
    if len(table)!=len(tokens) or pc.count_distinct(table['candidate_token']).as_py()!=len(tokens):
        raise RuntimeError('Reference prediction identity census mismatch')
    positions=pc.index_in(tokens,value_set=table['candidate_token'])
    if positions.null_count:
        raise RuntimeError('Missing reference predictions')
    values=table['score'].take(positions).to_numpy().astype(np.float64)
    if not np.isfinite(values).all():
        raise RuntimeError('Nonfinite reference score')
    return values

def open_session():
    bundle_check(); output=Path('/output')
    previous=read('/previous_session/SCORING_SESSION.json')
    if sha('/previous_session/SCORING_SESSION.json')!=read('/previous_session/SCORING_SESSION_HASH.json')['sha256'] or previous['truth_accessed']:
        raise RuntimeError('Historical candidate-only session integrity failure')
    records={x['path']:x for x in previous['files']}; files=[]
    ids=pa.array(read('/bundle/endpoints.json'))
    for cell in CELLS:
        relative=str(Path('candidates')/cell_path('',cell))
        verify('/previous_session',[records[relative]])
        source=Path('/previous_session')/relative; rows=pq.read_table(source)
        if rows.column_names!=COLUMNS or len(rows)!=P_COUNTS[cell]+1000000 or any(rows[c].null_count for c in COLUMNS):
            raise RuntimeError('Candidate identity/census/schema mismatch')
        if set(rows['cell_id'].to_pylist())!={cell} or pc.count_distinct(rows['candidate_token']).as_py()!=len(rows):
            raise RuntimeError('Candidate cell/uniqueness mismatch')
        for name in COLUMNS[1:3]:
            if pc.index_in(rows[name],value_set=ids).null_count:
                raise RuntimeError('Candidate endpoint missing from frozen inputs')
        if pc.any(pc.equal(rows[COLUMNS[1]],rows[COLUMNS[2]])).as_py():
            raise RuntimeError('Unexpected self pair')
        target=cell_path(output,cell)
        if target.exists():
            raise RuntimeError('Refusing to overwrite candidate session')
        shutil.copyfile(source,target)
        files.append({**relative_record(target,output),'cell':cell})
    write(output/'SESSION.json',{'at_utc':now(),'files':files,'truth_accessed':False,
        'historical_session_sha256':sha('/previous_session/SCORING_SESSION.json'),
        'scorer_freeze_sha256':sha('/bundle/SCORER_FREEZE.json')},exclusive=True)

def import_references():
    session_check(); output=Path('/output')
    predictions=read('/predictions/PREDICTIONS.json'); verify('/predictions',predictions['files'])
    files=[]
    definitions=[('ipin_baseline','/original_baseline','/baseline_freeze.json',BASELINE),
                 ('ipin_optimized','/original_optimized','/optimized_freeze.json','candidate/'+OPTIMIZED)]
    for name,source,freeze,prefix in definitions:
        old=read(freeze); records={x['path']:x for x in old['files']}
        (output/name).mkdir(exist_ok=False)
        for cell in CELLS:
            original=cell_path(source,cell)
            expected=records[str(Path(prefix)/original.name)]
            if sha(original)!=expected['sha256'] or original.stat().st_size!=expected['bytes']:
                raise RuntimeError('Historical reference prediction changed')
            tokens=pq.read_table(cell_path('/session',cell),columns=['candidate_token'])['candidate_token']
            prediction_values(tokens,pq.read_table(original))
            target=cell_path(output/name,cell); shutil.copyfile(original,target)
            files.append({**relative_record(target,output),'cell':cell,'model':name,'historical_sha256':expected['sha256']})
    write(output/'REFERENCES.json',{'at_utc':now(),'files':files,'byte_identical_to_historical_predictions':True,
        'candidate_predictions_manifest_sha256':sha('/predictions/PREDICTIONS.json'),
        'baseline_freeze_sha256':sha('/baseline_freeze.json'),'optimized_freeze_sha256':sha('/optimized_freeze.json')},exclusive=True)

def freeze_predictions():
    session_check()
    predictions=read('/predictions/PREDICTIONS.json'); refs=read('/references/REFERENCES.json')
    verify('/predictions',predictions['files']); verify('/references',refs['files'])
    if refs['candidate_predictions_manifest_sha256']!=sha('/predictions/PREDICTIONS.json') or not refs['byte_identical_to_historical_predictions']:
        raise RuntimeError('Invalid reference import ordering')
    if predictions['scorer_freeze_sha256']!=sha('/bundle/SCORER_FREEZE.json') or predictions['session_sha256']!=sha('/session/SESSION.json') or predictions['truth_accessed']:
        raise RuntimeError('Prediction provenance changed')
    for cell in CELLS:
        tokens=pq.read_table(cell_path('/session',cell),columns=['candidate_token'])['candidate_token'].combine_chunks()
        table=pq.read_table(cell_path('/predictions',cell))
        if table.column_names!=['candidate_token',*SCORERS] or not tokens.equals(table['candidate_token'].combine_chunks()):
            raise RuntimeError('Prediction token identity changed')
        values=np.column_stack([table[x].to_numpy() for x in SCORERS])
        if not np.isfinite(values).all():
            raise RuntimeError('Prediction finiteness/ensemble mismatch')
    write('/output/PREDICTION_FREEZE.json',{'at_utc':now(),'scorer_freeze_sha256':sha('/bundle/SCORER_FREEZE.json'),
        'session_sha256':sha('/session/SESSION.json'),'predictions_manifest_sha256':sha('/predictions/PREDICTIONS.json'),
        'references_manifest_sha256':sha('/references/REFERENCES.json'),'complete_unique_finite_coverage':True,
        'truth_accessed':False,'cells':list(CELLS),'rows':3019012},exclusive=True)

def token_for(cell,pair):
    return 'candidate:'+hashlib.sha256(f'{PACKAGE}:{cell}:{pair}'.encode()).hexdigest()

def decrypt_truth(target):
    package=read('/historical_scorer_freeze.json')['sealed_packages']['protected_truth']
    if sha('/cipher.cms')!=package['ciphertext_sha256'] or sha('/certificate.pem')!=package['certificate_sha256']:
        raise RuntimeError('Sealed truth input changed')
    archive=target/'archive.tar'
    subprocess.run(['openssl','cms','-decrypt','-binary','-inform','DER','-in','/cipher.cms',
        '-recip','/certificate.pem','-inkey','/key.pem','-out',str(archive)],check=True,capture_output=True)
    if sha(archive)!=package['plaintext_archive_sha256']:
        raise RuntimeError('Decrypted truth archive hash mismatch')
    with tarfile.open(archive,'r:') as handle:
        for member in handle.getmembers():
            path=Path(member.name)
            if path.is_absolute() or '..' in path.parts or not (member.isfile() or member.isdir()):
                raise RuntimeError('Unsafe truth archive entry')
        handle.extractall(target/'plain',filter='data')

def evaluate():
    session_check(); output=Path('/output'); device=cuda(); qualification=qualify(device)
    frozen=read('/freeze/PREDICTION_FREEZE.json')
    checks={'scorer_freeze_sha256':'/bundle/SCORER_FREEZE.json','session_sha256':'/session/SESSION.json',
        'predictions_manifest_sha256':'/predictions/PREDICTIONS.json','references_manifest_sha256':'/references/REFERENCES.json'}
    if frozen['truth_accessed'] or not frozen['complete_unique_finite_coverage'] or any(frozen[k]!=sha(v) for k,v in checks.items()):
        raise RuntimeError('Invalid complete prediction freeze before truth access')
    verify('/predictions',read('/predictions/PREDICTIONS.json')['files'])
    verify('/references',read('/references/REFERENCES.json')['files'])
    write(output/'EVALUATION_RESERVATION.json',{'at_utc':now(),'execution_id':'sprint_native_train_graph_v1',
        'prediction_freeze_sha256':sha('/freeze/PREDICTION_FREEZE.json'),'status':'reserved_before_truth_access',
        'historical_ledgers_not_modified':True},exclusive=True)
    component=dict(zip(read('/bundle/endpoints.json'),read('/bundle/components.json'),strict=True))
    old=read('/historical_results.json'); results={}; differences={}; started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='truth-',dir=output) as temporary:
        workspace=Path(temporary); decrypt_truth(workspace)
        positives=ds.dataset(workspace/'plain/protected_positive_truth',format='parquet')
        unlabeled=ds.dataset(workspace/'plain/unlabeled_pairs',format='parquet')
        for cell in CELLS:
            rows=pq.read_table(cell_path('/session',cell))
            p=positives.to_table(columns=['candidate_token','state'],filter=ds.field('cell_id')==cell)
            u=unlabeled.to_table(columns=['pair_id','sampling_weight_numerator','sampling_weight_denominator','state'],filter=ds.field('cell_id')==cell)
            if len(p)!=P_COUNTS[cell] or len(u)!=1000000 or set(p['state'].to_pylist())!={'released_positive'} or set(u['state'].to_pylist())!={'unlabeled'}:
                raise RuntimeError('Truth census/state mismatch')
            tokens=pa.concat_arrays([p['candidate_token'].combine_chunks(),pa.array([token_for(cell,x) for x in u['pair_id'].to_pylist()])])
            positions=pc.index_in(tokens,value_set=rows['candidate_token'])
            if positions.null_count or pc.count_distinct(tokens).as_py()!=len(rows):
                raise RuntimeError('Truth/candidate identity mismatch')
            ordered=rows.take(positions)
            table=pq.read_table(cell_path('/predictions',cell)).take(positions)
            scores=np.column_stack([table[x].to_numpy() for x in SCORERS]+[
                prediction_values(tokens,pq.read_table(cell_path(Path('/references')/name,cell))) for name in REFERENCES])
            num=u['sampling_weight_numerator'].to_numpy(); den=u['sampling_weight_denominator'].to_numpy()
            if (num<=0).any() or (den<=0).any():
                raise RuntimeError('Nonpositive design weights')
            weights=np.concatenate([np.ones(len(p)),num.astype(np.float64)/den])
            mask=np.arange(len(rows))<len(p)
            ca=[component[x] for x in ordered[COLUMNS[1]].to_pylist()]; cb=[component[x] for x in ordered[COLUMNS[2]].to_pylist()]
            points,draws,metadata=bootstrap(scores,mask,weights,ca,cb,cell,device=device)
            for reference,name in [(BASELINE,'ipin_baseline'),(OPTIMIZED,'ipin_optimized')]:
                expected=old['cells'][cell]['metrics'][reference]['ht_P_vs_U_concordance']
                if abs(points[ALL_SCORERS.index(name)]-expected)>1e-12:
                    raise RuntimeError('Historical reference metric failed exact-panel reproduction')
            if metadata!=old['cells'][cell]['bootstrap']:
                raise RuntimeError('Historical paired bootstrap draw definition changed')
            cell_result={}
            for j,name in enumerate(ALL_SCORERS):
                finite=np.isfinite(draws[j]); ci=np.percentile(draws[j,finite],[2.5,97.5]).tolist() if finite.any() else None
                cell_result[name]={'concordance':float(points[j]),'percentile_95':ci,'finite_bootstrap_draws':int(finite.sum())}
            contrasts=[(candidate,reference) for candidate in SCORERS for reference in REFERENCES]
            cell_differences=[]
            for candidate,reference in contrasts:
                a=ALL_SCORERS.index(candidate); b=ALL_SCORERS.index(reference)
                finite=np.isfinite(draws[a])&np.isfinite(draws[b]); delta=draws[a,finite]-draws[b,finite]
                cell_differences.append({'candidate':candidate,'reference':reference,'difference':float(points[a]-points[b]),
                    'paired_percentile_95':np.percentile(delta,[2.5,97.5]).tolist() if len(delta) else None,'finite_paired_draws':int(finite.sum())})
            results[cell]={'positive_pairs':len(p),'unlabeled_pairs':len(u),'metrics':cell_result,'bootstrap':metadata}
            differences[cell]=cell_differences
            with (output/f'bootstrap-{cell}.npz').open('xb') as f:
                np.savez(f,points=points,draws=draws)
            print({'cell':cell,'completed':True,'elapsed_seconds':time.monotonic()-started},flush=True)
    write(output/'RESULTS.json',{'at_utc':now(),'execution_id':'sprint_native_train_graph_v1','cells':results,'differences':differences,
        'metric_qualification':qualification,'prediction_freeze_sha256':sha('/freeze/PREDICTION_FREEZE.json'),
        'original_model':'SPRINT-native-TRAIN-positive-graph','elapsed_seconds':time.monotonic()-started,
        'original_model_revision':read('/bundle/SCORER_FREEZE.json')['model_revision'],
        'learned_neural_checkpoint':None,
        'sif_sha256':read('/bundle/SCORER_FREEZE.json')['sif_sha256'],
        'coverage':read('/predictions/PREDICTIONS.json')['coverage'],
        'historical_reference_points_reproduced':True,'historical_component_draws_reproduced':True,
        'U_is_not_negative':True,'test_previously_examined':True,'original_external_training_exposure':'none; all interaction edges are frozen TRAIN positives',
        'full_length_sequences':True,'sequence_only_transductive_preprocessing':True,
        'temporary_decrypted_truth_removed':True,'no_test_tuning':True},exclusive=True)

def publish():
    result=read('/aggregate/RESULTS.json'); output=Path('/output')
    with (output/'scores.csv').open('x',newline='') as f:
        writer=csv.writer(f); writer.writerow(['cell','model','weighted_P_vs_U_concordance','ci_95_low','ci_95_high','finite_bootstrap_draws','positive_pairs','unlabeled_pairs'])
        for cell in CELLS:
            for name in ALL_SCORERS:
                item=result['cells'][cell]['metrics'][name]; ci=item['percentile_95'] or [None,None]
                writer.writerow([cell,name,item['concordance'],*ci,item['finite_bootstrap_draws'],P_COUNTS[cell],1000000])
    with (output/'paired_differences.csv').open('x',newline='') as f:
        writer=csv.writer(f); writer.writerow(['cell','candidate','reference','difference','paired_ci_95_low','paired_ci_95_high','finite_paired_draws'])
        for cell in CELLS:
            for item in result['differences'][cell]:
                writer.writerow([cell,item['candidate'],item['reference'],item['difference'],*(item['paired_percentile_95'] or [None,None]),item['finite_paired_draws']])
    with (output/'coverage.csv').open('x',newline='') as f:
        writer=csv.writer(f); writer.writerow(['cell','pairs_scored','zero_scores','zero_fraction','unique_scores'])
        for cell in CELLS:
            item=result['coverage'][cell]
            writer.writerow([cell,item['pairs_scored'],item['zero_scores'],item['zero_fraction'],item['unique_scores']])
    lines=['# Native SPRINT benchmark results','',f"Completed: {result['at_utc']}. Original unmodified SPRINT algorithm; 16,799 frozen TRAIN-positive edges.",'',
        '| Model | C1 | C2 | C3 |','|---|---:|---:|---:|']
    for name in ALL_SCORERS:
        values=[result['cells'][cell]['metrics'][name]['concordance'] for cell in CELLS]
        lines.append('| '+name+' | '+' | '.join(f'{x:.6f}' for x in values)+' |')
    lines.extend(['','Primary contrast: SPRINT minus optimized iPIN on C3. See paired_differences.csv for paired intervals; C1/C2 are secondary.',
        '', 'Metric: design-weighted positive-versus-unlabeled concordance, not confirmed-positive-versus-confirmed-negative AUROC. Every one of the 3,019,012 candidate pairs is retained. Native zero scores and six-significant-digit output ties are retained; no probability calibration, score imputation, truncation, threshold search or test tuning.',
        '', 'SPRINT is not a neural pretrained checkpoint: the original algorithm propagates the permitted TRAIN-positive graph through native sequence similarities. No external or held-out PPI edges are provided. Sequence-only HSP/high-count preprocessing sees the fixed full 17,000-sequence corpus, including held-out endpoints; this is disclosed transductive feature construction, not strict inductive preprocessing.',
        '', 'Native HSP preprocessing uses defaults (Thit 15, Tsim 35, PAM120); the scorer uses Thc 40. Production prediction uses the unmodified serial executable because the parallel upstream scorer has unsynchronized matrix accumulation. Native HSP block ordering is canonicalized without changing records and qualified against the serial HSP/scorer path on the authors\' toy data.',
        '', 'Both iPIN reference files were reused byte-for-byte. Historical metric points and all 2,000 paired component bootstrap draw definitions were reproduced. This is a follow-up on previously examined test panels, not a new untouched confirmatory test.',
        '', 'Aggregate CSV files contain no protected pair identities. Token-aligned predictions and the original native text scores are retained under benchmark/sprint/private/original-v1/.'])
    with (output/'RESULTS.md').open('x') as f: f.write('\n'.join(lines)+'\n')
    shutil.copyfile('/aggregate/RESULTS.json',output/'RESULTS.json')

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('phase',choices=['open','references','freeze','evaluate','publish','qualify'])
    phase=parser.parse_args().phase
    if phase=='qualify':
        result=qualify(cuda()); write('/output/METRIC_QUALIFICATION.json',result); print(result,flush=True)
    else:
        {'open':open_session,'references':import_references,'freeze':freeze_predictions,'evaluate':evaluate,'publish':publish}[phase]()
