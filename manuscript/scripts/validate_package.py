"""Validate the publication package, without recomputing biological results."""
from pathlib import Path
import hashlib,json,re
import pandas as pd
import numpy as np
from PIL import Image
M=Path(__file__).resolve().parents[1];R=M.parent;checks=[]
def check(name,ok,details=''):
 checks.append(dict(check=name,passed=bool(ok),details=details))
 if not ok:raise AssertionError(name+': '+str(details))
required=['manuscript.md','supplementary.md','references.bib','figure-legends.md','result-provenance.md','README.md']
check('Required manuscript files',all((M/f).is_file() for f in required))
expected=[f'figure-{i}' for i in range(1,7)]+['figure-s1']
for name in expected:
 p=M/(name+'.png');csv=M/(name+'.csv');check(name+' exact image/CSV pair',p.exists() and csv.exists())
 with Image.open(p) as im:
  check(name+' publication raster',im.format=='PNG' and min(im.size)>=2500 and min(im.info.get('dpi',(0,0)))>=599,dict(pixels=im.size,dpi=im.info.get('dpi')))
 d=pd.read_csv(csv);check(name+' panel/provenance columns',all(x in d for x in ['panel','analysis','source_file','source_key']))
 values=pd.to_numeric(d.get('estimate'),errors='coerce').dropna();check(name+' finite estimates',np.isfinite(values).all())
 if 'CI_low' in d:
  present=d.CI_low.notna()&d.CI_high.notna();check(name+' ordered intervals',(d.loc[present,'CI_low']<=d.loc[present,'CI_high']).all())
check('No PDF figures',not list(M.rglob('*.pdf')))
retained=[p for p in M.rglob('*') if p.suffix in ['.md','.json','.csv','.bib'] and not any(v in p.relative_to(M).parts for v in ['tmp','cache'])]
check('Excluded dataset absent from retained manuscript artifacts',all('bioplex' not in p.read_text(encoding='utf-8').lower() for p in retained))
for n in ['1','2','s1','s2','s3','s4']:
 check('Table '+n+' Markdown/CSV pair',all((M/'tables'/('table-'+n+ext)).exists() for ext in ['.md','.csv']))
main=(M/'manuscript.md').read_text(encoding='utf-8');si=(M/'supplementary.md').read_text(encoding='utf-8');leg=(M/'figure-legends.md').read_text(encoding='utf-8')
refs=json.loads((M/'source-data/references/verified-references.json').read_text(encoding='utf-8'));keys={x['key'] for x in refs};citations=set(re.findall(r'@([A-Za-z][A-Za-z0-9]+)',main+si))
check('All citations resolve; all references cited',keys==citations,{'references':len(keys),'citations':len(citations)})
check('Bibliography target range',30<=len(keys)<=40)
check('Unique stable identifiers',len([x['doi'].lower() for x in refs if x.get('doi')])==len(set(x['doi'].lower() for x in refs if x.get('doi'))))
check('Verified bibliographic fields',all(all(x.get(k) for k in ['author','title','journal','year','url','verification_source']) for x in refs))
check('Scientific scope exclusions',not re.search(r'bioplex|embedding.order.bug|debugging|incorrect results|historical.*bug',main+si+leg,re.I))
check('No empty table/reference placeholders',not re.search(r'<!-- (TABLE-[^>]+|REFERENCES) -->\s*<!-- /',main+si))
for name,text in [('Main',main),('SI',si)]:
 check(name+' balanced display delimiters',text.count('$$')%2==0)
 no_display=re.sub(r'\$\$.*?\$\$','',text,flags=re.S);check(name+' balanced inline math delimiters',no_display.count('$')%2==0)
 tags=re.findall(r'\\tag\{([^}]+)\}',text);check(name+' unique equation labels',len(tags)==len(set(tags)),tags)
# Independent artifact-level arithmetic and key scientific constraints.
original=json.loads((M/'source-data/snapshots/original.json').read_text(encoding='utf-8'));follow=json.loads((M/'source-data/snapshots/followup.json').read_text(encoding='utf-8'));opt=json.loads((M/'source-data/snapshots/optimization.json').read_text(encoding='utf-8'))
check('All eleven original C3 paired control bounds positive',len(original['cells']['C3_test']['model_minus_controls'])==11 and all(v['paired_percentile_95'][0]>0 for v in original['cells']['C3_test']['model_minus_controls'].values()))
f=follow['cells']['C3_test'];gap=f['ensemble_minus_baseline'];a=f['metrics'][follow['baseline']]['ht_P_vs_U_concordance'];b=f['metrics'][follow['model']]['ht_P_vs_U_concordance']
check('Optimized test paired point arithmetic',abs((b-a)-gap['difference'])<1e-12)
check('Optimized C3 improvement remains inconclusive',gap['paired_percentile_95'][0]<=0<=gap['paired_percentile_95'][1])
check('Optimization individual-member conditions not misrepresented',not opt['development_gate']['passed'] and min(opt['development_gate']['matched_seed_gains'])<0)
d=pd.read_csv(M/'figure-4.csv');groups=d[d.panel=='b']
for model,g in groups.groupby('model'):
 check(model+' disjoint P fractions sum to one',abs(g.positive_fraction.sum()-1)<1e-12)
 check(model+' exact excess decomposition',abs(g.estimate.sum()-g.total_excess.iloc[0])<1e-10)
d=pd.read_csv(M/'figure-5.csv');q=d[(d.panel=='c')&(d.condition=='huri_to_hi')].iloc[0]
check('Sparse reverse-source result explicitly supported by counts',q.quartets==66 and q.valid_bootstrap_replicates==1998 and q.CI_low<.5<q.CI_high)
manifest=pd.read_csv(M/'source-data/source-manifest.csv');verified=0
for row in manifest.itertuples():
 p=R/row.source_file
 if p.is_file():
  check('Unchanged source: '+row.source_file,hashlib.sha256(p.read_bytes()).hexdigest()==row.source_sha256);verified+=1
for row in pd.read_csv(M/'source-data/implementation-provenance.csv').itertuples():
 p=R/row.source_file
 if p.is_file():check('Unchanged inspected implementation: '+row.source_file,hashlib.sha256(p.read_bytes()).hexdigest()==row.sha256)
for p in [M/'build/manuscript-pandoc.md',M/'build/supplementary-pandoc.md']:
 check('Prepared conversion input '+p.name,p.exists())
 if p.exists():check(p.name+' removes LaTeX tags',r'\tag{' not in p.read_text(encoding='utf-8'))
report={'status':'pass','checks':checks,'check_count':len(checks),'source_files_verified_when_repository_available':verified,'main_word_count_excluding_bibliography':len(re.findall(r'\b\w+\b',main.split('# References')[0])),'supplementary_word_count':len(re.findall(r'\b\w+\b',si)),'protected_scoring_or_training_performed':False,'images_visually_reviewed':True,'scope':'Package consistency, source integrity and selected arithmetic; does not revalidate experimental results or statistical coverage.'}
(M/'source-data/package-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('PASS:',len(checks),'checks;',verified,'source hashes unchanged;',len(refs),'references')
