"""Build publication source tables from immutable aggregate results; no model evaluation."""
from pathlib import Path
import json,hashlib,argparse,csv
import pandas as pd
M=Path(__file__).resolve().parents[1]; R=M.parent
SN=M/'source-data'/'snapshots';SN.mkdir(exist_ok=True)
PATHS={
'development':'artifacts/results/development_evaluation/development_embedding_identity_correction_v2/PRIMARY_METRICS.json',
'dev_source':'artifacts/results/development_evaluation/development_embedding_identity_correction_v2/SOURCE_EXCLUSIVE_METRICS.json',
'original':'artifacts/results/protected_final_test_v1/FINAL_TEST_RESULTS.json',
'followup':'artifacts/results/model_optimization_followup_v1/FOLLOWUP_TEST_RESULTS.json',
'optimization':'artifacts/results/model_optimization_v1/RESULTS.json',
'shift':'artifacts/results/c3_control_shift_investigation_v1/RESULTS.json',
'components':'artifacts/results/c3_control_shift_investigation_v1/COMPONENT_SUPPLEMENT.json',
'partner':'artifacts/results/within_anchor_partner_specificity_v1/RESULTS.json',
'partner_support':'artifacts/results/within_anchor_partner_specificity_v1/FEASIBILITY.json',
'homology':'artifacts/results/homology_source_challenge_v1/RESULTS.json',
'homology_support':'artifacts/results/homology_source_challenge_v1/FEASIBILITY.json',
'construction':'artifacts/validation/benchmark_design/pair_level_pu_r_benchmark_artifacts_v1/CONSTRUCTION_REPORT.json',
'split':'artifacts/validation/benchmark_design/final_benchmark_component_split_v1/AUDIT_REPORT.json',
'recipes':'configs/model_optimization_v1.json',
'negative':'artifacts/validation/negative_evidence/negative_evidence_audit_v1/AUDIT_REPORT.json',
}
# Retain only publication-relevant fields in portable snapshots.
FIELDS={'development':['cells'],'dev_source':['cells'],'original':['cells','model'],'followup':['cells','model','baseline','test_previously_examined'], 'optimization':['all_ensemble_groups','all_evaluations','development_gate','selected','stage1_runs','stage2_runs','total_epochs'], 'shift':['bootstrap','development','label_blind_endpoint_partition_summary','published_comparison'], 'components':['all_positive_participating_component_influences','groups','sensitivities','bootstrap_replicates'], 'partner':['macro_concordance','model_ci95','primary_delta','primary_delta_ci95','quartets','folds','propensity_sensitivity'], 'partner_support':['folds'], 'homology':['arms'], 'homology_support':['folds','alignments','undirected_remote_edges'], 'construction':['construction'],'split':['aggregate_metrics'],'negative':['metrics','pnu_feasibility','scientific_conclusion']}
refresh=argparse.ArgumentParser();refresh.add_argument('--refresh-snapshots',action='store_true');args=refresh.parse_args()
manifest=[]; D={}
for key,path in PATHS.items():
 p=SN/(key+'.json')
 if args.refresh_snapshots or not p.exists():
  raw=(R/path).read_bytes();obj=json.loads(raw)
  obj={k:obj[k] for k in FIELDS[key]} if key in FIELDS else obj
  p.write_text(json.dumps(obj,indent=2)+'\n')
  manifest.append({'snapshot':str(p.relative_to(M)),'source_file':path,'source_sha256':hashlib.sha256(raw).hexdigest(),'source_bytes':len(raw)})
 D[key]=json.loads(p.read_text(encoding='utf-8'))
if manifest:pd.DataFrame(manifest).to_csv(M/'source-data/source-manifest.csv',index=False)
A='lightweight_esm2_150m_linear__linear_lr3e-4'; O='esm2_150m__residual_wide__epoch04_ensemble3'
NAMES={A:'iPIN affine',O:'iPIN optimized','training_degree_sum':'Degree sum','preferential_attachment':'Preferential attachment','training_common_neighbors':'Common neighbors','component_degree_mass_product':'Component degree mass','sequence_length_ratio':'Length ratio','sequence_length_sum':'Length sum','within_pair_3mer_cosine':'3-mer cosine','exact_training_interolog_3mer':'3-mer interolog','pooled_150m_cosine':'ESM cosine','aac_cosine':'Composition cosine','deterministic_hash':'Hash sentinel'}
def row(panel,source,key,model='',condition='',dataset='',metric='concordance',estimate=None,ci=None,**extra):
 return dict(panel=panel,analysis=source,model=NAMES.get(model,model),model_id=model,condition=condition,dataset=dataset,metric=metric,estimate=estimate,CI_low=ci[0] if ci else None,CI_high=ci[1] if ci else None,source_file=PATHS[source],source_key=key,**extra)
def save(name,rows,sub=''):
 df=pd.DataFrame(rows);df.to_csv(M/sub/(name+'.csv'),index=False,float_format='%.15g');return df
counts=D['construction']['construction']['cell_counts']
allrows=[]
for source in ['development','original','followup']:
 for cell,d in D[source]['cells'].items():
  for model,v in d['metrics'].items():
   if model not in NAMES:continue
   if source=='followup' and model==A:continue
   ci=d['bootstrap_percentile_95_for_controls_and_ensembles'].get(model) if source=='development' else v['percentile_95']
   value=v['ht_positive_vs_U_concordance'] if source=='development' else v['ht_P_vs_U_concordance']
   allrows.append(row('',source,'cells/'+cell+'/metrics/'+model,model,cell.split('_')[0], 'Development' if source=='development' else ('Protected follow-up' if source=='followup' else 'Original protected test'),estimate=value,ci=ci,cell=cell,positive_pairs=counts[cell]['positive_pairs'],sampled_unlabeled_pairs=counts[cell]['unlabeled_sample'],interval_source_key=('cells/'+cell+'/bootstrap_percentile_95_for_controls_and_ensembles/'+model if source=='development' else 'cells/'+cell+'/metrics/'+model+'/percentile_95')))
metrics=save('all-performance',allrows,'source-data')
# Figure 2: matched primary exposure regimes, original model and fixed controls.
models=[A,'training_degree_sum','preferential_attachment','training_common_neighbors','component_degree_mass_product','sequence_length_ratio','sequence_length_sum','within_pair_3mer_cosine','exact_training_interolog_3mer']
r=[dict(x,panel='a' if x['analysis']=='development' else 'b') for x in allrows if x['model_id'] in models and x['analysis']!='followup' and x['cell'] in ['C1_development','C2_development','C3_development','C1_test','C2_test','C3_test']]
save('figure-2',r)
models=[A,O,'within_pair_3mer_cosine','exact_training_interolog_3mer','sequence_length_ratio','sequence_length_sum','aac_cosine','pooled_150m_cosine']
r=[dict(x,panel='a') for x in allrows if x['model_id'] in models and x['cell'] in ['C3_development','C3_test']]
g=D['optimization']['development_gate'];r.append(row('a','optimization','development_gate/candidate_concordance',O,'C3','Development',estimate=g['candidate_concordance'],positive_pairs=counts['C3_development']['positive_pairs'],sampled_unlabeled_pairs=counts['C3_development']['unlabeled_sample'],interval_note='Marginal development interval not reported'))
save('figure-3',r)
# Figure 4: removal sensitivities and disjoint positive-group decompositions.
r=[]; chosen=[A,'within_pair_3mer_cosine','exact_training_interolog_3mer','sequence_length_ratio']
for model in chosen:
 for condition in ['Full C3','Exclude largest','Exclude rank 3','Exclude both','Between components']:
  if condition=='Full C3':
   obj=D['shift']['development'];point=obj['full_concordance'][model];ci=D['shift']['bootstrap']['scores'][model]['full_ci95'];p=counts['C3_development']['positive_pairs'];u=counts['C3_development']['unlabeled_sample'];src='shift';key='development/full_concordance/'+model
  elif condition=='Exclude largest':
   obj=D['shift']['development']['both_P_and_U_without_largest'];point=obj['concordance'][model];ci=D['shift']['bootstrap']['scores'][model]['without_largest_ci95'];p=obj['positive_rows'];u=obj['unlabeled_rows'];src='shift';key='development/both_P_and_U_without_largest'
  else:
   k={'Exclude rank 3':'neither_in_third','Exclude both':'neither_in_first_or_third','Between components':'between_component'}[condition];obj=D['components']['sensitivities'][k];point=obj['concordance'][model];ci=obj['ci95'][model];p=obj['positive_rows'];u=obj['unlabeled_rows'];src='components';key='sensitivities/'+k
  r.append(row('a',src,key,model,condition,'Development C3',estimate=point,ci=ci,positive_pairs=p,sampled_unlabeled_pairs=u))
for model,group_names in [('within_pair_3mer_cosine',['within_component','between_component']),('exact_training_interolog_3mer',['touching_third','neither_in_third'])]:
 for group in group_names:
  if group=='touching_third':
   obj=next(x for x in D['components']['all_positive_participating_component_influences'] if x['endpoint_size_rank']==3);key='all_positive_participating_component_influences/[endpoint_size_rank=3]'
  else:obj=D['components']['groups'][group];key='groups/'+group
  point=obj['positive_group_vs_full_U'][model];fraction=obj['positive_fraction'];contribution=fraction*(point-.5)
  r.append(row('b','components',key,model,group,'Development C3',metric='contribution_to_excess_concordance',estimate=contribution,group_concordance=point,positive_fraction=fraction,unlabeled_mass_fraction=obj['HT_U_fraction'],positive_pairs=obj['positive_rows'],sampled_unlabeled_pairs=obj['unlabeled_rows'],total_excess=D['shift']['development']['full_concordance'][model]-.5,derivation='positive_fraction * (group_concordance - 0.5)'))
for x in r:
 x['largest_component_endpoints']=D['shift']['label_blind_endpoint_partition_summary']['development']['largest_component']
 x['rank3_component_endpoints']=next(v['endpoints'] for v in D['components']['all_positive_participating_component_influences'] if v['endpoint_size_rank']==3)
save('figure-4',r)
# Figure 5: conditioning, robustness and endpoint-balanced swaps; no external data.
r=[];p=D['partner'];anchors=sum(x['anchors'] for x in p['folds'])
for model in ['pair_linear','endpoint_linear','endpoint_mlp64','kmer3_cosine','pooled_cosine','length_ratio']:
 ci=p['model_ci95'].get(model)
 if model=='endpoint_linear':ci=D['homology']['arms']['union']['model_intervals'][model]['ci95']
 x=row('a','partner','macro_concordance/'+model,model,'Original internal panel','Public-training cross-validation',metric='equal_anchor_concordance',estimate=p['macro_concordance'][model],ci=ci,anchors=anchors)
 if model=='endpoint_linear':x['interval_source_file']=PATHS['homology'];x['interval_source_key']='arms/union/model_intervals/endpoint_linear/ci95'
 r.append(x)
r.append(row('a_difference','partner','primary_delta', 'pair_linear − endpoint_mlp64','Original internal panel','Public-training cross-validation',metric='paired_difference',estimate=p['primary_delta'],ci=p['primary_delta_ci95'],anchors=anchors))
for arm,obj in D['homology']['arms'].items():
 an=sum(x['anchors'] for x in obj['folds']);qn=sum(x['quartets'] for x in obj['folds']);delta=obj['deltas']['endpoint_linear']
 r.append(row('b','homology','arms/'+arm+'/deltas/endpoint_linear','pair_linear − endpoint_linear',arm,'Public-training cross-validation',metric='paired_difference',estimate=delta['point'],ci=delta['ci95'],anchors=an,pair_concordance=obj['macro']['pair_linear'],unary_concordance=obj['macro']['endpoint_linear']))
 q=obj['quartet'];r.append(row('c','homology','arms/'+arm+'/quartet','pair_linear',arm,'Public-training cross-validation',metric='quartet_preference',estimate=q['points']['pair_linear'],ci=q['pair_interval']['ci95'],quartets=qn,valid_bootstrap_replicates=q['pair_interval']['valid_replicates']))
save('figure-5',r)
# Figure 6: every screened recipe, all promoted ensembles, seed differences.
r=[];opt=D['optimization'];spec={x['name']:x for x in D['recipes']['recipes_per_encoder']}
for i,x in enumerate(opt['all_evaluations']):
 if x['stage']!=1:continue
 encoder,recipe=x['recipe_id'].split('__');s=spec[recipe]
 r.append(row('a','optimization',f'all_evaluations/{i}',x['recipe_id'],s['family'],'Development C3',estimate=x['concordance'],parameters=x['parameters'],encoder=encoder,recipe=recipe,seed=x['seed'],epoch=x['epoch'],stage=x['stage']))
for i,x in enumerate(opt['all_ensemble_groups']):
 encoder,recipe=x['recipe_id'].split('__');r.append(row('b','optimization',f'all_ensemble_groups/{i}',x['recipe_id'],spec[recipe]['family'],'Development C3',estimate=x['concordance'],parameters=x['parameters'],encoder=encoder,recipe=recipe,epoch=x['epoch'],stage=2,selected=x['recipe_id']==opt['selected']['recipe_id'] and x['epoch']==opt['selected']['epoch']))
for i,seed in enumerate(D['recipes']['seeds']):
 r.append(row('c','optimization',f'development_gate/matched_seed_gains/{i}',str(seed),'Individual seed','Development C3',metric='paired_point_difference',estimate=g['matched_seed_gains'][i],seed=seed,baseline_concordance=g['baseline_seed_concordances'][i],candidate_concordance=g['candidate_seed_concordances'][i]))
r.append(row('c','optimization','development_gate','Ensemble','Selected ensemble','Development C3',metric='paired_difference',estimate=g['gain'],ci=g['paired_gain_ci95']))
f=D['followup']['cells']['C3_test']['ensemble_minus_baseline'];r.append(row('c','followup','cells/C3_test/ensemble_minus_baseline','Ensemble','Selected ensemble','Protected C3 follow-up',metric='paired_difference',estimate=f['difference'],ci=f['paired_percentile_95']))
save('figure-6',r)
# Supplementary figure: all fixed-control paired comparisons.
r=[]
for cell in ['C1_test','C2_test','C3_test']:
 for model,v in D['original']['cells'][cell]['model_minus_controls'].items():
  r.append(row(cell[:2],'original','cells/'+cell+'/model_minus_controls/'+model,model,cell[:2],'Original protected test',metric='affine_minus_control',estimate=v['model_minus_control'],ci=v['paired_percentile_95'],positive_pairs=counts[cell]['positive_pairs'],sampled_unlabeled_pairs=counts[cell]['unlabeled_sample']))
save('figure-s1',r)
# Tables, no redundant primary performance table in main text.
save('table-1',[dict(cell=cell,**counts[cell]) for cell in ['training','C1_development','C1_test','C2_development','C2_test','C3_development','C3_test']],'tables')
part=D['split']['aggregate_metrics']['partition_summaries']
save('table-s1',[{k:x[k] for k in ['partition','endpoint_count','component_count','singleton_component_count','largest_component_size']} for x in part],'tables')
save('table-s2',allrows,'tables')
save('table-s3',[dict(x, **spec[x['recipe_id'].split('__')[1]]) for x in opt['all_evaluations']],'tables')
# Figure 1 structured schematic with numerics obtained from source objects.
r=[]
for x in part:
 r.append(row('a','split','aggregate_metrics/partition_summaries',condition=x['partition'],metric='endpoint_partition',estimate=x['endpoint_count'],components=x['component_count'],label={'train':'Training','development':'Development','test':'Protected test'}[x['partition']]))
for condition,exposure,definition in [('C1',2,'Held-out pair; both endpoints exposed'),('C2',1,'One endpoint exposed; one held out'),('C3',0,'Both endpoints held out')]:
 r.append(dict(panel='b',analysis='design',condition=condition,metric='exposed_endpoints',estimate=exposure,label=definition,source_file='configs/pair_level_pu_r_benchmark_protocol_v1.yaml',source_key='pair_assignment/'+condition))
for order,label,detail in [(1,'Sequence A / Sequence B','Shared frozen encoder'),(2,'ESM-2 150M','Residue means → training standardization'),(3,'Symmetric pair features','sum | absolute difference | product | cosine'),(4,'Residual head','Affine branch + LayerNorm → 256 → GELU → scalar'),(5,'Interaction-associated ranking','Mean raw score across three seeds')]:
 r.append(dict(panel='c',analysis='schematic',order=order,label=label,detail=detail,source_file='src/ipin_openppi/model_optimization/models.py',source_key='PairHead/features',relationship='directed_processing_step',next_order=order+1 if order<5 else None))
for state,label in [('P','Released positive interactions'),('U','Unlabeled eligible pairs')]:r.append(dict(panel='a',analysis='schematic',condition=state,label=label,source_file='configs/pair_level_pu_r_benchmark_protocol_v1.yaml',source_key='candidate_universes/state_semantics'))
save('figure-1',r)
# Additional statistics for textual claims, with exact machine paths.
claims=[]
for cell in ['C1_test','C2_test','C3_test']:
 v=D['followup']['cells'][cell]['ensemble_minus_baseline'];claims.append(row('','followup','cells/'+cell+'/ensemble_minus_baseline',O,cell,'Protected follow-up',metric='optimized_minus_affine',estimate=v['difference'],ci=v['paired_percentile_95']))
save('claim-values',claims,'source-data')
print('Extracted figure CSVs and base tables.')
