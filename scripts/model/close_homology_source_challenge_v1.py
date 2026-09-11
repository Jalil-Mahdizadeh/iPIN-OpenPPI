#!/usr/bin/env python3
"""Verify the completed DEC-0047 evidence and write its closure registry.

No scientific computation or authorization is introduced by this bookkeeping
step. A completed registry cannot be overwritten.
"""

from pathlib import Path
import xml.etree.ElementTree as ET

import yaml

from ipin_openppi.homology_source import data as io
from ipin_openppi.stage1.support import sha256_file


def passed_tests(path):
    result = set()
    for case in ET.parse(path).getroot().iter('testcase'):
        if case.find('failure') is not None or case.find('error') is not None:
            raise RuntimeError('failed final unit test')
        if case.find('skipped') is None:
            result.add((case.get('classname'), case.get('name')))
    return result


def close(root):
    if (root / io.RESULT / 'ARTIFACT_REGISTRY.json').exists():
        raise RuntimeError('study closure already recorded')
    io.verify_freeze(root)
    parent_registry = io.read_json(root / 'artifacts/results/within_anchor_partner_specificity_v1/ARTIFACT_REGISTRY.json')
    io.verify_records(root, parent_registry['artifacts'])
    for name in ('SOURCE_PROJECTION.json', 'SEARCH_COMPLETE.json', 'FEASIBILITY.json',
                 'PRE_EXECUTION_PRECISION_CORRECTION.json', 'TRAINING_COMPLETE.json',
                 'SCORING_COMPLETE.json', 'RESULTS.json'):
        io.verify_records(root, io.read_json(root / io.RESULT / name)['artifacts'])
    ref = io.read_json(root / io.VALID / 'REFERENCE_VALIDATION.json')
    support = io.read_json(root / io.VALID / 'SUPPORTING_READOUT_AUDIT.json')
    assert ref['passed'] is True and support['passed'] is True
    before = passed_tests(root / io.VALID / 'unit_tests_final_pre_execution.xml') | passed_tests(root / io.VALID / 'gpu_control_pre_execution.xml')
    after = passed_tests(root / io.VALID / 'unit_tests_post_execution.xml') | passed_tests(root / io.VALID / 'gpu_control_post_execution.xml')
    if before != after or len(after) != 390:
        raise RuntimeError('final qualified test coverage mismatch')
    result = io.read_json(root / io.RESULT / 'RESULTS.json')
    gates = yaml.safe_load((root / 'governance/gates/gate_status_v47.yaml').read_text())
    assert gates['scientific_result']['readout_sha256'] == sha256_file(root / io.RESULT / 'RESULTS.json')
    assert not result['all_challenges_survived']
    assert all(r['anchor_signal_survives'] for r in result['arms'].values())
    assert sum(r['quartet']['signal_survives'] for r in result['arms'].values()) == 3
    for arm, value in gates['gates']['anchor_ranking_challenges']['pair_concordance'].items():
        assert value == result['arms'][arm]['macro']['pair_linear']
    paths = [root / p for p in (
        'configs/homology_source_challenge_v1.yaml',
        'docs/protocols/HOMOLOGY_SOURCE_CHALLENGE_v1.md',
        'docs/reports/m1/M1_Homology_and_Source_Challenge_v1.md',
        'governance/decisions/DEC-0047-authorize-homology-and-source-challenge.md',
        'governance/issues/ISSUE-0015-residual-homology-in-frozen-component-folds.md',
        'governance/PROJECT_STATUS_v47.md', 'governance/gates/gate_status_v47.yaml',
        'scripts/model/run_homology_source_challenge_v1.py',
        'scripts/model/audit_homology_source_support_v1.py',
        'scripts/model/close_homology_source_challenge_v1.py',
        'tests/unit/test_homology_source.py')]
    paths += sorted((root / 'src/ipin_openppi/homology_source').glob('*.py'))
    paths += sorted((root / io.RESULT).glob('*.json'))
    paths += sorted(p for p in (root / io.VALID).iterdir() if p.is_file())
    output = {'protocol_id': io.ID, 'created_utc': io.now(), 'execution_complete': True,
              'numerical_validation_passed': True, 'distinct_tests_covered': len(after),
              'all_anchor_challenges_pass': True, 'swap_challenges_passed': 3,
              'reverse_source_swap': 'inconclusive_insufficient_frozen_support',
              'prior_study_closure_artifacts_unchanged': True,
              'protected_candidate_truth_or_key_access_performed': False,
              'remote_push_performed': False, 'external_review_implied': False,
              'generated_artifacts': 'Ignored local arrays/checkpoints/scores are transitively hash-bound by the phase records; no raw source or large matrix redistribution.',
              'artifacts': [io.artifact(root, p) for p in paths]}
    io.write_json(root / io.RESULT / 'ARTIFACT_REGISTRY.json', output)
    print({'closure_artifacts': len(output['artifacts']), 'tests': len(after),
           'parent_unchanged': True, 'status': 'complete_and_numerically_verified'})


if __name__ == '__main__':
    close(Path.cwd())
