"""Freeze and score the corrected PU benchmark using the qualified models."""
import argparse
from study_utils import *


def freeze():
    require(not (OUT/'INPUT_FREEZE.json').exists(), 'Already frozen')
    require(not any((OUT/n).exists() for n in ('ipin_scores.csv','tuna_scores.csv')), 'Freeze must precede new inference')
    selection=read(OUT/'PANEL_SELECTION.json')
    validation=read(OUT/'PANEL_VALIDATION.json')
    require(validation['status']=='passed', 'Panel validation required')
    verify(validation['selection'])
    check_records(selection['inputs']+selection['outputs'])
    require(read(OUT/'METRIC_SELFTEST.json')['status']=='passed', 'Metric self-test required')
    exposure=read(OUT/'EXPOSURE_AUDIT.json')
    require(exposure['protected_test_pairs_or_truth_read'] is False, 'Exposure audit required')
    check_records(exposure['files'])
    registry=ROOT/'artifacts/models/frozen_pair_models_v2/MODEL_REGISTRY.json'
    require(sha(registry)==CONFIG['model_registry_sha256'], 'Model registry changed')
    names=('config.json','PROTOCOL.md','study_utils.py','build_panels.py','validate_panels.py',
           'audit_exposure.py','score_models.py','analyze.py','validate_results.py','finalize.py',
           'PANEL_SELECTION.json','PANEL_VALIDATION.json','EXPOSURE_AUDIT.json',
           'HOMOLOGY_INPUT_FREEZE.json','METRIC_SELFTEST.json')
    dependencies=('benchmark/nonhuman_transfer_v1/score_models.py','benchmark/nonhuman_transfer_v1/audit_exposure.py',
        'example/twelve_target_comparison_v2/run_comparison.py','example/twelve_target_comparison_v1/metrics.py',
        'example/score_frozen_models.py','src/ipin_openppi/stage1/embeddings.py')
    files=[*selection['inputs'],*selection['outputs'],*exposure['files'],record(registry)]
    files += [record(OUT/n) for n in names]+[record(ROOT/n) for n in dependencies]
    unique={r['path']:r for r in files}
    write_json(OUT/'INPUT_FREEZE.json', {'at_utc':now(),'P':1555,'U':155500,'pairs':157055,
        'U_per_P':100,'globally_distinct_U':True,'primary_endpoint':'P_vs_unlabeled_concordance',
        'primary_aggregation':'equal_positive','secondary_aggregation':'equal_yeast_target',
        'models':list(MODELS),'model_registry_sha256':CONFIG['model_registry_sha256'],
        'no_new_panel_inference_yet':True,'prior_positive_scores_seen':True,
        'selection_uses_model_scores':False,'files':[unique[k] for k in sorted(unique)]})
    print('Frozen: all 1,555 P and 155,500 globally distinct U',flush=True)


def score(phase):
    frozen=read(OUT/'INPUT_FREEZE.json')
    require(frozen['primary_endpoint']=='P_vs_unlabeled_concordance','Unexpected evaluation endpoint')
    check_records(frozen['files'])
    require(not (OUT/(phase+'_scores.csv')).exists(), 'Refusing to replace scores')
    module=qualified_module('score_models')
    if phase=='ipin':
        module.parent().ipin(ROOT,OUT)
    else:
        module.tuna()
    write_json(OUT/(phase.upper()+'_DISPATCH.json'), {'at_utc':now(),
        'input_freeze':record(OUT/'INPUT_FREEZE.json'),'wrapper':record(Path(__file__)),
        'qualified_implementation':record(ROOT/'benchmark/nonhuman_transfer_v1/score_models.py'),
        'runtime_container':os.environ['APPTAINER_CONTAINER'],'P':1555,'U':155500})


if __name__=='__main__':
    require_container()
    parser=argparse.ArgumentParser()
    parser.add_argument('phase',choices=('freeze','ipin','tuna'))
    phase=parser.parse_args().phase
    freeze() if phase=='freeze' else score(phase)
