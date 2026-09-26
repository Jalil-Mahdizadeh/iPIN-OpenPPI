"""Extract model specification and compact internal support tables."""
from pathlib import Path
import json,hashlib
import pandas as pd
import yaml
M=Path(__file__).resolve().parents[1];R=M.parent;S=M/'source-data/snapshots'
paths={'model_spec':'artifacts/models/frozen_pair_models_v1/MODEL_REGISTRY.json','original_training':'configs/model_governance_and_baseline_training_protocol_v1.yaml'}
manifest=pd.read_csv(M/'source-data/source-manifest.csv').to_dict('records')
for key,path in paths.items():
 out=S/(key+'.json')
 if not out.exists():
  raw=(R/path).read_bytes();d=yaml.safe_load(raw) if path.endswith('yaml') else json.loads(raw)
  if key=='model_spec':d={k:d[k] for k in ['models','encoder','embedding_dimension','optimized_recipe']}
  else:d={k:d[k] for k in ['optimization_and_search','embedding_strategy','plm_provenance']}
  out.write_text(json.dumps(d,indent=2)+'\n')
  manifest.append(dict(snapshot=str(out.relative_to(M)),source_file=path,source_sha256=hashlib.sha256(raw).hexdigest(),source_bytes=len(raw)))
pd.DataFrame(manifest).drop_duplicates('snapshot',keep='last').to_csv(M/'source-data/source-manifest.csv',index=False)
reg=json.loads((S/'model_spec.json').read_text(encoding='utf-8'));old=json.loads((S/'original_training.json').read_text(encoding='utf-8'));new=json.loads((S/'recipes.json').read_text(encoding='utf-8'));rows=[]
for model,d in reg['models'].items():
 affine=d['head_family']=='affine';cfg=old['optimization_and_search'];recipe=cfg['linear_recipes'][0] if affine else reg['optimized_recipe']
 rows.append(dict(model='Original affine' if affine else 'Optimized residual',model_id=model,encoder=reg['encoder']['repository'],embedding_dimension=reg['embedding_dimension'],parameters_per_head=d['parameters_per_head'],ensemble_members=len(d['seeds']),selected_pass_or_epoch=d['selected_pass'] if affine else d['selected_epoch'],batch_comparisons=cfg['batch']['pairwise_comparisons'] if affine else new['batch_size'],learning_rate=recipe['learning_rate'] if affine else recipe['lr'],weight_decay=recipe['weight_decay'],dropout=recipe['dropout'],hidden_width=0 if affine else recipe['width'],training_passes=cfg['scheduler']['total_training_passes'] if affine else new['stage2_epochs'],source_file=paths['model_spec'],source_key='models/'+model))
pd.DataFrame(rows).to_csv(M/'tables/table-2.csv',index=False)
h=json.loads((S/'homology_support.json').read_text(encoding='utf-8'));cols=['arm','fold','fit_endpoints','removed_fit_endpoints','fit_P','fit_U','evaluation_P','evaluation_U','anchors','anchor_components','quartets','quartet_components','direct_remote_cross_edges','target_only_P_hidden_as_U']
pd.DataFrame(h['folds'])[cols].to_csv(M/'tables/table-s4.csv',index=False)
# Retain primary development + source-exclusive diagnostics and optimized C3 selection.
r=pd.read_csv(M/'source-data/all-performance.csv').to_dict('records');dev=json.loads((S/'dev_source.json').read_text(encoding='utf-8'));counts=json.loads((S/'construction.json').read_text(encoding='utf-8'))['construction']['cell_counts']
A='lightweight_esm2_150m_linear__linear_lr3e-4';O='esm2_150m__residual_wide__epoch04_ensemble3'
for cell,scorers in dev['cells'].items():
 for model in [A,'within_pair_3mer_cosine','exact_training_interolog_3mer']:
  v=scorers[model]
  val=v.get('ht_positive_vs_U_concordance',v.get('metrics',{}).get('ht_positive_vs_U_concordance'))
  # Source-exclusion readouts retain marginal intervals under their explicit key.
  ci=v.get('bootstrap_percentile_95',v.get('percentile_95',None))
  if val is None: raise ValueError(v)
  r.append(dict(panel='',analysis='dev_source',model={A:'iPIN affine','within_pair_3mer_cosine':'3-mer cosine','exact_training_interolog_3mer':'3-mer interolog'}[model],model_id=model,condition=cell.split(':')[-1].split('_')[0],dataset='Development',metric='concordance',estimate=val,CI_low=ci[0] if ci else None,CI_high=ci[1] if ci else None,cell=cell,positive_pairs=counts[cell]['positive_pairs'],sampled_unlabeled_pairs=counts[cell]['unlabeled_sample'],source_file='artifacts/results/development_evaluation/development_embedding_identity_correction_v2/SOURCE_EXCLUSIVE_METRICS.json',source_key='cells/'+cell+'/'+model))
g=json.loads((S/'optimization.json').read_text(encoding='utf-8'))['development_gate'];r.append(dict(analysis='optimization',model='iPIN optimized',model_id=O,condition='C3',cell='C3_development',dataset='Development',metric='concordance',estimate=g['candidate_concordance'],positive_pairs=counts['C3_development']['positive_pairs'],sampled_unlabeled_pairs=counts['C3_development']['unlabeled_sample'],source_file='artifacts/results/model_optimization_v1/RESULTS.json',source_key='development_gate/candidate_concordance'))
pd.DataFrame(r).to_csv(M/'tables/table-s2.csv',index=False,float_format='%.15g')
