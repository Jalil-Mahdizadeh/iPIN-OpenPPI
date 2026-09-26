"""Embed reviewable tables and a bibliography into Markdown; preserve authored prose."""
from pathlib import Path
import json,re
import pandas as pd
M=Path(__file__).resolve().parents[1]
def table(headers,rows):
 return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(str(x) for x in row)+' |' for row in rows)
def write_table(name,title,headers,rows,foot=''):
 text='**'+title+'**\n\n'+table(headers,rows)+'\n\n'+foot+'\n';(M/'tables'/(name+'.md')).write_text(text);return text
def inject(file,marker,text):
 p=M/file;s=p.read_text(encoding='utf-8');pat=r'<!-- '+marker+r' -->.*?<!-- /'+marker+r' -->';s=re.sub(pat,lambda m:'<!-- '+marker+' -->\n'+text+'<!-- /'+marker+' -->',s,flags=re.S);p.write_text(s)
d=pd.read_csv(M/'tables/table-1.csv');names={'training':'Training','C1_development':'C1 development','C1_test':'C1 test','C2_development':'C2 development','C2_test':'C2 test','C3_development':'C3 development','C3_test':'C3 test'}
t=write_table('table-1','Table 1 | Primary benchmark cells',['Cell','Positive pairs','U population','Sampled U'],[[names[x.cell],f'{x.positive_pairs:,}',f'{x.unlabeled_population:,}',f'{x.unlabeled_sample:,}'] for x in d.itertuples()], 'P denotes released-positive evidence; U denotes unlabeled pairs. Evaluation-positive pairs are excluded from interaction-supervised training. Counts describe pair rows, not independent biological replicates.')
inject('manuscript.md','TABLE-1',t)
d=pd.read_csv(M/'tables/table-2.csv').set_index('model');a=d.loc['Original affine'];b=d.loc['Optimized residual']
rows=[['Frozen encoder','ESM-2 150M','ESM-2 150M'],['Head parameters per member',f'{a.parameters_per_head:,}',f'{b.parameters_per_head:,}'],['Ensemble members',int(a.ensemble_members),int(b.ensemble_members)],['Hidden width','—',int(b.hidden_width)],['Training dropout',a.dropout,b.dropout],['Initial learning rate',f'{a.learning_rate:.0e}',f'{b.learning_rate:.0e}'],['Weight decay',f'{a.weight_decay:g}',f'{b.weight_decay:g}'],['Comparisons per batch',f'{a.batch_comparisons:,}',f'{b.batch_comparisons:,}'],['Selected pass / epoch',int(a.selected_pass_or_epoch),int(b.selected_pass_or_epoch)],['Scheduled passes / epochs',int(a.training_passes),int(b.training_passes)]]
t=write_table('table-2','Table 2 | Final model specifications',['Property','Original affine','Optimized residual'],rows,'Both models use the same 640-dimensional standardized embeddings and 1,921-dimensional symmetric pair features. Optimization changes the training recipe as well as the head. The optimized epoch-four checkpoint comes from an eight-epoch schedule.');inject('manuscript.md','TABLE-2',t)
d=pd.read_csv(M/'tables/table-s1.csv');t=write_table('table-s1','Supplementary Table S1 | Endpoint and component partitions',['Partition','Endpoints','Components','Singletons','Largest component'],[[x.partition.title(),f'{x.endpoint_count:,}',f'{x.component_count:,}',f'{x.singleton_component_count:,}',f'{x.largest_component_size:,}'] for x in d.itertuples()]);inject('supplementary.md','TABLE-S1',t)
d=pd.read_csv(M/'tables/table-s2.csv');rows=[]
def fmt(x):return f'{x.estimate:.3f} [{x.CI_low:.3f}, {x.CI_high:.3f}]' if pd.notna(x.CI_low) else f'{x.estimate:.3f} [not reported]'
for model in ['iPIN affine','iPIN optimized','Degree sum','Preferential attachment','Common neighbors','Component degree mass','Length ratio','Length sum','3-mer cosine','3-mer interolog','ESM cosine','Composition cosine','Hash sentinel']:
 vs=[]
 for cell in ['C3_development','C3_test']:
  s=d[(d.model==model)&(d.cell==cell)];vs.append(fmt(s.iloc[0]) if len(s) else 'Not reported')
 rows.append([model,*vs])
t=write_table('table-s2','Supplementary Table S2 | C3 performance and available marginal 95% intervals',['Model/control','Development C3','Protected C3'],rows,'The CSV additionally includes C1/C2 and source-specific results with sample counts and exact provenance. Optimized test values are from the disclosed follow-up. Missing intervals/estimates are not imputed. The paired optimized-minus-affine interval, rather than overlap of marginal intervals, determines the incremental conclusion.');inject('supplementary.md','TABLE-S2',t)
d=pd.read_csv(M/'tables/table-s3.csv');groups=json.loads((M/'source-data/snapshots/optimization.json').read_text(encoding='utf-8'))['all_ensemble_groups'];rows=[]
for x in d[d.stage==1].itertuples():
 es={g['epoch']:g['concordance'] for g in groups if g['recipe_id']==x.recipe_id}
 rows.append([x.recipe_id.replace('esm2_','').replace('__',' / '),f'{x.parameters:,}',f'{x.concordance:.4f}',f"{es[4]:.4f}" if 4 in es else '—',f"{es[8]:.4f}" if 8 in es else '—'])
t=write_table('table-s3','Supplementary Table S3 | Complete bounded search',['Encoder / recipe','Head parameters','Screen, epoch 3','Ensemble, epoch 4','Ensemble, epoch 8'],rows,'Screen scores use one seed; promoted ensemble scores use three. Dashes indicate recipes not promoted. The CSV retains every individual-seed evaluation, exact hyperparameters and checkpoint identifiers. These development-selected comparisons are not protected head-to-head tests.');inject('supplementary.md','TABLE-S3',t)
d=pd.read_csv(M/'tables/table-s4.csv');names={'union':'Union','purged20':'Homology purge','hi_to_huri':'HI-II-14 → HuRI','huri_to_hi':'HuRI → HI-II-14'}
t=write_table('table-s4','Supplementary Table S4 | Internal challenge support',['Arm','Fold','Fit endpoints','Fit P','Evaluation P','Anchors','Quartets'],[[names[x.arm],x.fold,f'{x.fit_endpoints:,}',f'{x.fit_P:,}',f'{x.evaluation_P:,}',f'{x.anchors:,}',f'{x.quartets:,}'] for x in d.itertuples()], 'The CSV also reports fitting/evaluation U counts, participating components, removed endpoints and target-only positives restored to fitting U. Folds and seeds are robustness views of the same public training evidence.');inject('supplementary.md','TABLE-S4',t)
refs={x['key']:x for x in json.loads((M/'source-data/references/verified-references.json').read_text(encoding='utf-8'))};body=(M/'manuscript.md').read_text(encoding='utf-8');keys=list(dict.fromkeys(re.findall(r'@([A-Za-z][A-Za-z0-9]+)',body)))
assert set(keys)==set(refs),(set(refs)-set(keys),set(keys)-set(refs))
lines=[]
for i,key in enumerate(keys,1):
 x=refs[key];aa=x['author'].split(' and ');authors='; '.join(aa[:6])+('; et al.' if len(aa)>6 else '')
 tail=' '.join(str(x.get(k,'')) for k in ['volume','pages'] if x.get(k))
 lines.append(f'{i}. <a id="ref-{key}"></a>{authors}. [{x["title"]}]({x["url"]}). *{x["journal"]}* {tail} ({x["year"]}).')
inject('manuscript.md','REFERENCES','\n\n'.join(lines)+'\n')
# A rendered reference list makes the Markdown draft complete; conversion strips
# this display block and lets citeproc generate native ordered references.
print('Rendered six tables and',len(keys),'bibliographic entries')
