"""Extend the old split without moving old endpoints or crossing old partitions."""
import argparse
from collections import Counter, defaultdict
from pathlib import Path
import subprocess
from study import check, digest, now, read, record, sha, write

class Union:
    def __init__(self, values):
        self.parent = {x: x for x in values}
    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x
    def join(self, a, b):
        a,b = self.find(a), self.find(b)
        if a != b:
            self.parent[max(a,b)] = min(a,b)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--study', type=Path, required=True)
    p.add_argument('--mmseqs', type=Path, required=True)
    args=p.parse_args(); out=args.study; work=out/'work'
    check(not (out/'audit/ANCHOR_AUDIT.json').exists(), 'Anchors already frozen')
    check(sha(args.mmseqs)=='d5f6d96578e3dbcd1d8772bb575b112e9dd1dbf077d150914962a2356ae0d75d', 'MMseqs binary changed')
    rows=read(out/'private/sequence_candidates.json')
    u=Union([r['hash'] for r in rows]); original=defaultdict(list)
    for r in rows:
        if r['original']:
            original[r['component']].append(r['hash'])
    for members in original.values():
        for h in members[1:]: u.join(members[0], h)
    commands=[]; edges=0
    if any(not r['original'] for r in rows):
        for mode in ('full', 'local'):
            for direction in ('new_all', 'all_new'):
                query,target=direction.split('_')
                result=work/f'{mode}_{direction}.tsv'
                cmd=[str(args.mmseqs),'easy-search',str(work/f'{query}.fasta'),str(work/f'{target}.fasta'),
                     str(result),str(work/f'tmp_{mode}_{direction}'),
                     '--threads','16','-s','7.5','--min-seq-id','0.30',
                     '-c','0.8' if mode=='full' else '0.2','--cov-mode','0',
                     '-e','1e100' if mode=='full' else '1e-3',
                     '--alignment-mode','3','--max-seqs','50000','--max-accept','50000',
                     '--max-rejected','50000','--min-ungapped-score','0','--comp-bias-corr','1',
                     '--mask','1','--mask-lower-case','0','--prefilter-mode','1',
                     '--format-output','query,target,fident,qcov,tcov,qstart,qend,tstart,tend,evalue',
                     '--remove-tmp-files','1']
                commands.append(cmd)
                marker=result.with_suffix('.complete.json')
                if marker.exists():
                    check(read(marker)['sha256']==sha(result), 'Completed alignment output changed')
                else:
                    with (work/f'{mode}_{direction}.log').open('w') as log:
                        subprocess.run(cmd,check=True,stdout=log,stderr=subprocess.STDOUT)
                    write(marker,{'sha256':sha(result),'at_utc':now()})
                with result.open() as f:
                    for line in f:
                        q,t,ident,qcov,tcov,qs,qe,ts,te,ev=line.rstrip().split('\t')
                        if q==t or float(ident)<.30: continue
                        coverage=min(float(qcov),float(tcov))
                        span=min(abs(int(qe)-int(qs))+1,abs(int(te)-int(ts))+1)
                        passes=(coverage>=.8) if mode=='full' else (coverage>=.2 and span>=80 and float(ev)<=.001)
                        if passes:
                            u.join(q,t); edges+=1
                print({'stage':mode+'_'+direction,'qualified_directed_edges_so_far':edges},flush=True)
    groups=defaultdict(list)
    for r in rows: groups[u.find(r['hash'])].append(r)
    quarantined=[]; inherited=Counter(); new_components=Counter(); bridge_components=0
    for root, members in sorted(groups.items()):
        old_parts={r['partition'] for r in members if r['original']}
        if len(old_parts)>1:
            bridge_components+=1
            for r in members:
                if not r['original']:
                    quarantined.append({'hash':r['hash'],'reason':'bridge_between_old_partitions',
                                        'old_partitions':sorted(old_parts)})
            continue
        if old_parts:
            part=next(iter(old_parts))
        else:
            bucket=int(digest('human-ppi-data-scaling-v1:component:'+root)[:16],16)%10000
            part='train' if bucket<7000 else 'development' if bucket<8500 else 'test'
            new_components[part]+=1
        comp='extended:'+root
        for r in members:
            # Component linkage is audited separately; old component IDs stay intact
            # for exact reproduction of the historical bootstrap and diagnostics.
            r['extended_component']=comp
            if not r['original']:
                r['partition']=part; r['component']=comp; inherited[part]+=1
    excluded={r['hash'] for r in quarantined}
    accepted=[r for r in rows if r['hash'] not in excluded]
    # A collision component may contain old endpoints. Their original partition and
    # component identifiers are retained, and no new bridge endpoint is admitted.
    for r in accepted:
        r.setdefault('extended_component',r['component'])
    write(out/'private/anchored_sequences.json',accepted)
    write(out/'private/quarantined_sequences.json',quarantined)
    write(out/'audit/ANCHOR_AUDIT.json',{'at_utc':now(),'old_assignments_retained':True,
        'old_endpoint_count':sum(r['original'] for r in accepted),
        'admitted_new_endpoints_by_partition':dict(inherited),
        'new_unanchored_components_by_partition':dict(new_components),
        'quarantined_bridge_endpoints':len(quarantined),'bridge_components':bridge_components,
        'directed_qualifying_hits':edges,'exhaustive_homology_claim':False,
        'legacy_residual_homology_limitation_retained':True,'commands':commands,
        'inputs':[record(out/'private/sequence_candidates.json',out),record(args.mmseqs)],
        'outputs':[record(out/'private/anchored_sequences.json',out),record(out/'private/quarantined_sequences.json',out)]})
    print({'admitted_new':dict(inherited),'quarantined_new':len(quarantined)},flush=True)

if __name__=='__main__': main()
