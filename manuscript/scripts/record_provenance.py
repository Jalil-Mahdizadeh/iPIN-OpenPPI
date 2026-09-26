"""Record aggregate-only provenance, ancillary claims and implementation checks."""
from pathlib import Path
import json,hashlib
import pandas as pd
M=Path(__file__).resolve().parents[1];R=M.parent;S=M/'source-data/snapshots'
extra={
'source_membership':('artifacts/results/homology_source_challenge_v1/SOURCE_PROJECTION.json',['counts']),
'homology_edges':('artifacts/validation/homology_source_challenge_v1/HOMOLOGY_EDGE_AUDIT.json',['counts','all_use_minimum_span_80_and_both_coverage_20pct_and_evalue_1e_3']),
'screen_metadata':('artifacts/validation/benchmark_design/systematic_screen_metadata_v1/AUDIT_REPORT.json',['scientific_conclusion','systematic_universe_assessment']),
}
manifest=pd.read_csv(M/'source-data/source-manifest.csv').to_dict('records')
for key,(path,fields) in extra.items():
 p=S/(key+'.json')
 if not p.exists():
  raw=(R/path).read_bytes();d=json.loads(raw)
  if fields:d={k:d[k] for k in fields}
  else:
   # Broad metadata records are consulted read-only; only semantic keys are retained.
   d={k:v for k,v in d.items() if k in ['scientific_conclusion','calibration_feasibility','metadata_completeness','estimand_assessment','metrics','claim_limits']}
  p.write_text(json.dumps(d,indent=2)+'\n');manifest.append(dict(snapshot=str(p.relative_to(M)),source_file=path,source_sha256=hashlib.sha256(raw).hexdigest(),source_bytes=len(raw)))
pd.DataFrame(manifest).drop_duplicates('snapshot',keep='last').to_csv(M/'source-data/source-manifest.csv',index=False)
# Ancillary textual values are flattened to retain exact paths and values.
items=[]
def flatten(obj,path,src):
 if isinstance(obj,dict):
  for k,v in obj.items():flatten(v,path+'/'+str(k),src)
 elif isinstance(obj,list):
  for i,v in enumerate(obj):flatten(v,path+'/'+str(i),src)
 elif isinstance(obj,(int,float)) and not isinstance(obj,bool):items.append(dict(snapshot=src,source_key=path.lstrip('/'),value=obj))
for key in ['source_membership','homology_edges','negative','split','partner_support','homology_support','shift','components','construction','model_spec','original_training']:
 d=json.loads((S/(key+'.json')).read_text(encoding='utf-8'));flatten(d,'',key+'.json')
pd.DataFrame(items).to_csv(M/'source-data/ancillary-claim-values.csv',index=False)
code={
'src/ipin_openppi/stage1/embeddings.py':['window_starts','extract_candidate','standardize'],
'src/ipin_openppi/stage1/models.py':['exact_cosine','commutative_features','LinearPairHead'],
'src/ipin_openppi/model_optimization/models.py':['features','PairHead'],
'src/ipin_openppi/model_optimization/run.py':['train_run','run'],
'src/ipin_openppi/stage1/training.py':['weighted_pairwise_logistic_loss'],
'src/ipin_openppi/stage1/baselines.py':['degree_sum_score','length_ratio_score','kmer3_counts','exact_interolog_score'],
'src/ipin_openppi/development_evaluation/semantics.py':['weighted_pairwise_concordance','pair_component_multipliers'],
'src/ipin_openppi/partner_specificity/semantics.py':['anchor_points','bootstrap_anchor_totals','quartet_credit'],
'src/ipin_openppi/partner_specificity/models.py':['EndpointHead'],
'src/ipin_openppi/homology_source/semantics.py':['alignment_scores','fit_rows','exhaustive_transfer_numpy'],
'scripts/benchmark/protected_final_core_v1.py':['score_all','evaluate'],
'scripts/benchmark/model_optimization_followup_core_v1.py':['score_all','evaluate'],
}
out=[]
for path,functions in code.items():
 data=(R/path).read_bytes();out.append(dict(source_file=path,sha256=hashlib.sha256(data).hexdigest(),relevant_symbols='; '.join(functions),inspection='read-only implementation inspection; no execution'))
pd.DataFrame(out).to_csv(M/'source-data/implementation-provenance.csv',index=False)
print('Recorded source fingerprints and ancillary numerical claims')
