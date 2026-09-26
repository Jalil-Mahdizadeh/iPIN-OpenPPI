"""Curator-only nested corpus builder. Never imported into model fitting jobs."""
import argparse
from collections import Counter
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.parquet as pq
from study import SEEDS, arrays, check, codes, c1_role, digest, now, pair_id, read, record, save, sha, write

def legacy_tests(repo, out, hashes):
    """Read historical truth only in the curator, preserve it in a private v1 view."""
    freeze=read(repo/'.private/model_optimization_followup_v1/bundle/SCORER_FREEZE.json')
    expected=freeze['sealed_packages']['protected_truth']
    cipher=repo/'data/canonical/pair_level_pu_r_benchmark_artifacts_v1/sealed/protected_truth.cms'
    cert=repo/'governance/keys/pair_level_pu_r_benchmark_artifacts_v1/protected_truth_certificate.pem'
    key=repo/'.private/pair_level_pu_r_benchmark_artifacts_v1/protected_truth_private.pem'
    check(sha(cipher)==expected['ciphertext_sha256'] and sha(cert)==expected['certificate_sha256'], 'Historical truth inputs changed')
    result={}
    with tempfile.TemporaryDirectory(prefix='curator-',dir=out/'work') as tmp:
        tmp=Path(tmp); archive=tmp/'truth.tar'
        subprocess.run(['openssl','cms','-decrypt','-binary','-inform','DER','-in',str(cipher),
                        '-recip',str(cert),'-inkey',str(key),'-out',str(archive)],check=True,capture_output=True)
        check(sha(archive)==expected['plaintext_archive_sha256'], 'Historical truth archive changed')
        with tarfile.open(archive,'r:') as t:
            for member in t.getmembers():
                p=Path(member.name)
                check(not p.is_absolute() and '..' not in p.parts and (member.isfile() or member.isdir()), 'Unsafe archive')
            t.extractall(tmp/'plain',filter='data')
        positives=ds.dataset(tmp/'plain/protected_positive_truth',format='parquet')
        unlabeled=ds.dataset(tmp/'plain/unlabeled_pairs',format='parquet')
        for cell, index, count in [('C3',0,2379),('C2',3,13446),('C1',6,3187)]:
            name=cell+'_test'
            candidate=repo/f'benchmark/tuna/private/session/cell-{index:02d}.parquet'
            rows=pq.read_table(candidate)
            p=positives.to_table(filter=ds.field('cell_id')==name,columns=['candidate_token'])
            u=unlabeled.to_table(filter=ds.field('cell_id')==name,columns=['pair_id','sampling_weight_numerator','sampling_weight_denominator'])
            check(len(p)==count and len(u)==1000000, 'Historical test census mismatch')
            tokens=pa.concat_arrays([p['candidate_token'].combine_chunks(),pa.array([
                'candidate:'+digest('pair_level_pu_r_benchmark_artifacts_v1:'+name+':'+s)
                for s in u['pair_id'].to_pylist()])])
            positions=pc.index_in(tokens,value_set=rows['candidate_token'])
            check(positions.null_count==0 and pc.count_distinct(tokens).as_py()==len(rows), 'Historical test identity mismatch')
            rows=rows.take(positions)
            av=pc.index_in(rows['endpoint_a_sha256'],value_set=pa.array(hashes))
            bv=pc.index_in(rows['endpoint_b_sha256'],value_set=pa.array(hashes))
            check(av.null_count==0 and bv.null_count==0, 'Unknown historical endpoint')
            values={'a':av.to_numpy().astype(np.int64),'b':bv.to_numpy().astype(np.int64),
                    'positive':np.arange(len(rows))<len(p),
                    'weight':np.r_[np.ones(len(p)),u['sampling_weight_numerator'].to_numpy().astype(float)/u['sampling_weight_denominator'].to_numpy()]}
            save(out/f'private/test/legacy/{cell}.npz',**values)
            result[('test',cell)]=values
    return result

def sample_pairs(left, right, count, forbidden, n, seed, hashes, role=None):
    """Uniform draws over unordered eligible pairs; keep draw order after deduplication."""
    rng=np.random.Generator(np.random.PCG64DXSM(seed)); selected=[]; used=set()
    left=np.asarray(left); right=np.asarray(right)
    check(len(left)>1 and len(right)>1, 'Insufficient endpoint population')
    attempts=0
    while len(selected)<count:
        size=max(10000, min(1000000, 2*(count-len(selected))))
        a=rng.choice(left,size=size); b=rng.choice(right,size=size)
        vals=codes(a,b,n)
        _,idx=np.unique(vals,return_index=True)
        for k in vals[np.sort(idx)]:
            k=int(k); a,b=divmod(k,n)
            if a==b or k in forbidden or k in used: continue
            if role and c1_role(hashes[a],hashes[b])!=role: continue
            selected.append(k); used.add(k)
            if len(selected)==count: break
        attempts+=size
        check(attempts<200000000, 'Requested U sample unavailable; do not weaken eligibility')
    vals=np.array(selected,np.int64)
    return vals//n, vals%n

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--study',type=Path,required=True)
    args=p.parse_args(); repo,out=args.repo,args.study
    check(not (out/'audit/CORPUS_FREEZE.json').exists(), 'Corpus already frozen')
    rows=read(out/'private/anchored_sequences.json'); hashes=[x['hash'] for x in rows]
    index={h:i for i,h in enumerate(hashes)}; n=len(rows)
    oldseq=read(repo/'benchmark/tuna/data/sequences.json')
    check(hashes[:17000]==oldseq['sha256'], 'Historical endpoint order changed')
    for i,r in enumerate(rows[:17000]):
        check(r['partition']==oldseq['partition'][i] and r['component']==oldseq['component'][i]
              and r['sequence']==oldseq['sequence'][i], 'Historical endpoint changed')
    meta={'sha256':hashes,'sequence':[r['sequence'] for r in rows], 'length':[r['length'] for r in rows],
          'partition':[r['partition'] for r in rows],'component':[r['component'] for r in rows],
          'extended_component':[r['extended_component'] for r in rows], 'accessions':[r['accessions'] for r in rows]}
    write(out/'data/sequences.json',meta); write(out/'data/endpoints.json',hashes)
    legacy=out/'data/legacy'; legacy.mkdir(parents=True,exist_ok=True)
    originals={}; parents=[]
    for name in ['training.npz','development_00.npz','development_01.npz','development_02.npz','sequences.json','endpoints.json','DATA_MANIFEST.json']:
        source=repo/'benchmark/tuna/data'/name
        check(not (legacy/name).exists(), 'Refusing to replace legacy snapshot')
        shutil.copyfile(source,legacy/name); parents.append(record(source,repo))
        check(sha(source)==sha(legacy/name), 'Legacy copy not identical')
    train1=arrays(legacy/'training.npz')
    train1_codes=set(map(int,codes(train1['p_a'],train1['p_b'],n)))
    check(len(train1_codes)==16799, 'Training positive census changed')
    for i in range(3): originals[('development',f'C{3-i}')]=arrays(legacy/f'development_{i:02d}.npz')
    originals.update(legacy_tests(repo,out,hashes))
    reserved=set(); reserved_original=set(); overlapping_legacy=0
    for name, panel in originals.items():
        vals=set(map(int,codes(panel['a'],panel['b'],n)))
        check(len(vals)==len(panel['a']), 'Duplicate original pair within panel')
        overlapping_legacy+=len(vals & reserved)
        reserved.update(vals)
    reserved_original=set(reserved)
    check(not (train1_codes & reserved), 'Original training P intersects holdout')
    pairs=pq.read_table(out/'private/qualified_pairs.parquet').to_pylist()
    qualified={int(codes([index[r['a']]],[index[r['b']]],n)[0]):r for r in pairs if r['a'] in index and r['b'] in index}
    # All released old positives remain P even if today's stricter import rule
    # cannot reconstruct every historical record; the parent version is immutable.
    positive_codes=set(qualified)|train1_codes
    for panel in originals.values():
        positive_codes.update(map(int,codes(panel['a'][panel['positive']],panel['b'][panel['positive']],n)))
    # Use the smallest training budget's exposure set for fixed C1/C2 definitions.
    exposed=set(map(int,np.r_[train1['p_a'],train1['p_b']]))
    partitions=np.array(meta['partition']); addition={key:[] for key in originals}; new_train=[]
    quarantine=Counter(); assigned=[]
    for k, evidence in sorted(qualified.items()):
        if k in train1_codes: continue
        if k in reserved:
            quarantine['existing_holdout_candidate_retained_in_its_panel']+=1
            continue
        a,b=divmod(k,n); pa_,pb_=partitions[a],partitions[b]
        role=None
        if pa_=='train' and pb_=='train':
            fold=c1_role(hashes[a],hashes[b])
            if fold=='train':
                new_train.append(k); role='train'
            elif a in exposed and b in exposed:
                addition[(fold,'C1')].append(k); role=fold+':C1'
            else: quarantine['C1_not_exposed_at_smallest_budget']+=1
        elif pa_==pb_ and pa_ in ('development','test'):
            addition[(pa_,'C3')].append(k); role=pa_+':C3'
        elif 'train' in (pa_,pb_):
            training_endpoint=a if pa_=='train' else b
            fold=pb_ if pa_=='train' else pa_
            if training_endpoint in exposed:
                addition[(fold,'C2')].append(k); role=fold+':C2'
            else: quarantine['C2_not_exposed_at_smallest_budget']+=1
        else: quarantine['development_test_cross_partition']+=1
        if role:
            assigned.append({'a':hashes[a],'b':hashes[b],'role':role,**evidence})
    pq.write_table(pa.Table.from_pylist(assigned),out/'private/addition_assignments.parquet',compression='zstd')
    forbidden=positive_codes|reserved
    # Same fixed U population for every P budget. Fresh control isolates P growth
    # under that population; the original 2M U rows are preserved in data/legacy.
    train_ids=np.flatnonzero(partitions=='train')
    ua,ub=sample_pairs(train_ids,train_ids,2000000,forbidden,n,2026092501,hashes,role='train')
    train_u_codes=set(map(int,codes(ua,ub,n))); forbidden.update(train_u_codes)
    save(out/'data/training_unlabeled.npz',u_a=ua,u_b=ub,u_weight=np.ones(len(ua),np.float64))
    ordered=sorted(new_train,key=lambda k:digest('human-ppi-data-scaling-v1:positive-budget:'+str(k)))
    maximum=16799+len(ordered)
    budgets=sorted(set([16799,maximum]+[x for x in (20000,25000,50000,70000) if x<maximum]))
    check(maximum>16799, 'No eligible expansion survived')
    previous=set()
    budget_summary=[]
    for budget in budgets:
        vals=np.array(ordered[:budget-16799],np.int64)
        a=np.r_[train1['p_a'],vals//n]; b=np.r_[train1['p_b'],vals%n]
        keys=set(map(int,codes(a,b,n)))
        check(len(keys)==budget and train1_codes<=keys and previous<=keys, 'Positive budgets are not nested')
        check(not (keys & reserved_original) and not (keys & train_u_codes), 'Positive training leakage or P/U collision')
        check(all(partitions[x]=='train' for x in np.r_[a,b]), 'Heldout endpoint in training')
        save(out/f'data/training_{budget}.npz',p_a=a,p_b=b)
        source_counts=Counter('|'.join(qualified[k]['sources']) for k in keys-train1_codes)
        budget_summary.append({'positive_pairs':budget,'positive_endpoints':len(set(map(int,np.r_[a,b]))),
                               'added_source_membership':dict(source_counts)})
        previous=keys
    panels={}; label_changes={}
    for i,((fold,cell),old) in enumerate(sorted(originals.items())):
        destination=out/('data/development' if fold=='development' else 'private/test')
        vals=codes(old['a'],old['b'],n)
        updated=old['positive'].copy()
        newly_positive=np.array([int(k) in positive_codes for k in vals]) & ~updated
        updated[newly_positive]=True
        weight=old['weight'].copy(); weight[newly_positive]=1.
        save(destination/'reconciled'/f'{cell}.npz',a=old['a'],b=old['b'],positive=updated,weight=weight)
        # Training and every holdout already have distinct identities. Added U
        # samples also exclude any legacy holdout and all admitted P identities.
        pop=np.flatnonzero(partitions==fold)
        left,right=(sorted(exposed), sorted(exposed)) if cell=='C1' else (sorted(exposed),pop) if cell=='C2' else (pop,pop)
        au,bu=sample_pairs(left,right,250000,forbidden,n,2026092510+i,hashes,role=fold if cell=='C1' else None)
        new_p=np.array(sorted(addition[(fold,cell)]),np.int64)
        check(len(new_p)>0, 'Expanded evaluation cell has no added positive pairs')
        a=np.r_[new_p//n,au]; b=np.r_[new_p%n,bu]
        current=set(map(int,codes(a,b,n)))
        check(len(current)==len(a) and not (current & reserved) and not(current & train_u_codes), 'Added panel overlaps earlier panel/training U')
        reserved.update(current); forbidden.update(current)
        save(destination/'added'/f'{cell}.npz',a=a,b=b,positive=np.arange(len(a))<len(new_p),weight=np.ones(len(a),np.float64))
        panels[fold+':'+cell]={'legacy_P':int(old['positive'].sum()),'legacy_U':int((~old['positive']).sum()),
          'legacy_U_now_supported_P':int(newly_positive.sum()),'added_P':len(new_p),'added_U':len(au),
          'v2_P':int(updated.sum())+len(new_p),'v2_U':int((~updated).sum())+len(au)}
        label_changes[fold+':'+cell]=int(newly_positive.sum())
    for parent in [repo/'benchmark/tuna/runs/TRAINING_FREEZE.json',repo/'benchmark/tuna/runs/scorer_bundle/SCORER_FREEZE.json',
                   repo/'benchmark/tuna/results/RESULTS.json',repo/'benchmark/partner_conditioned_residue_v1/results/RESULTS.json']:
        if parent.exists(): parents.append(record(parent,repo))
    write(out/'audit/PARENT_SNAPSHOT.json',{'at_utc':now(),'files':parents,'historical_artifacts_modified':False})
    protocol={'study':'human_ppi_data_scaling_v1','at_utc':now(),'positive_budgets':budgets,'seeds':SEEDS,
      'architecture':'unchanged qualified native PU-TUnA','epochs':8,'evaluation_epochs':[1,2,4,6,8],
      'comparison_batch':64,'comparisons_per_epoch':2000000,'lr':1e-4,'lr_decay':'.93 every two epochs',
      'selection':'three-seed mean scores; common epoch per budget; maximize 0.5*C3 reconciled-legacy concordance + 0.5*C3 added concordance',
      'tie_break':'smaller positive budget, then earlier epoch; strict numeric ordering without a tolerance',
      'training_U':'one frozen uniform 2M sample over eligible largest TRAIN universe, C1 train role, excluding all P and reserved candidate identities',
      'original_U_snapshot_retained':True,'U_is_confirmed_negative':False,
      'C1_C2_exposure':'original 16,799-P endpoint exposure, fixed across budgets',
      'test_2_fresh_independent_claim':False,'test_1_historically_examined':True,
      'test_truth_read_by_curator':True,'test_truth_available_to_training':False,
      'legacy_label_updates':'old candidate identity preserved; newly supported U becomes P only in version 2; legacy metrics retain old states',
      'subset_randomness':'one deterministic nested ordering; three seeds quantify fitting variability, not alternative corpus draws'}
    write(out/'data/PROTOCOL.json',protocol)
    public={'at_utc':now(),'budgets':budget_summary,'sequences':n,'new_sequences':n-17000,
      'partitions':dict(Counter(meta['partition'])),'panels':panels,'quarantine':dict(quarantine),
      'legacy_between_panel_identity_overlap_count':overlapping_legacy,
      'training_U_rows':len(ua),'training_P_holdout_overlap':0,'training_P_U_overlap':0,
      'test_curator_access_disclosed':True,'parent_snapshots_byte_identical':True,
      'qualified_source_pairs_not_admitted_after_anchor':len(pairs)-len(qualified),
      'v2_U_to_P_changes':label_changes,'selection':protocol['selection'],
      'data_files':[record(f,out) for f in sorted((out/'data').rglob('*')) if f.is_file()],
      'test_files':[record(f,out) for f in sorted((out/'private/test').rglob('*')) if f.is_file()],
      'private_assignment':record(out/'private/addition_assignments.parquet',out),
      'source_audit':record(out/'audit/SOURCE_AUDIT.json',out),'anchor_audit':record(out/'audit/ANCHOR_AUDIT.json',out)}
    write(out/'audit/CORPUS_FREEZE.json',public)
    print({k:v for k,v in public.items() if k not in ('data_files','test_files','private_assignment')},flush=True)

if __name__=='__main__': main()
