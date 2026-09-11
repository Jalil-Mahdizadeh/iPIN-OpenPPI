import numpy as np
import pytest

from ipin_openppi.external_bioplex.data import allowed_url, config, passed_tests, tsv
from ipin_openppi.external_bioplex.semantics import (
    accession_lookup, classify, directed_queries, make_panel, project_source, select_directed_quartets,
)
from ipin_openppi.partner_specificity.semantics import anchor_points, quartet_credit


def test_exact_accession_mapping_rejects_ambiguity_and_isoform_inference():
    rows = [dict(reference_sequence_sha256='a', uniprot_accessions=['P1', 'P2-2', 'AMB']),
            dict(reference_sequence_sha256='b', uniprot_accessions=['AMB', 'P3']),
            dict(reference_sequence_sha256='hidden', uniprot_accessions=['P3', 'P4'])]
    assert accession_lookup(rows, ['a', 'b']) == {'P1': 0, 'P2-2': 0}


def test_source_projection_emits_only_unambiguous_public_endpoints():
    net = [dict(GeneA='1', GeneB='2', UniprotA='P1', UniprotB='P2'),
           dict(GeneA='1', GeneB='3', UniprotA='P1', UniprotB='P3'),
           dict(GeneA='1', GeneB='4', UniprotA='P1', UniprotB='P4'),
           dict(GeneA='2', GeneB='4', UniprotA='P2', UniprotB='P4-2')]
    direct = [{'Bait GeneID': '1', 'Prey GeneID': b} for b in ('2', '3', '4')]
    edges, baits, preys, count = project_source(net, direct, [{'GeneID': '1'}], {'P1': 0, 'P2': 1, 'P4': 2, 'P4-2': 3})
    np.testing.assert_array_equal(edges, [[0, 1]])
    np.testing.assert_array_equal(baits, [0])
    np.testing.assert_array_equal(preys, [1])
    assert count['directed_rows_unmapped'] == 2


@pytest.mark.parametrize('baits,edge', [([], ('1', '2')), ([{'GeneID': '1'}], ('1', '3'))])
def test_source_direction_must_match_published_inventory(baits, edge):
    net = [dict(GeneA='1', GeneB='2', UniprotA='P1', UniprotB='P2')]
    with pytest.raises(ValueError, match='inconsistent'):
        project_source(net, [{'Bait GeneID': edge[0], 'Prey GeneID': edge[1]}], baits, {'P1': 0, 'P2': 1})


def test_duplicate_raw_evidence_does_not_duplicate_reference_edge():
    net = [dict(GeneA='1', GeneB='2', UniprotA='P1', UniprotB='P2')]
    direct = [{'Bait GeneID': '1', 'Prey GeneID': '2'}] * 2
    edges, _, _, count = project_source(net, direct, [{'GeneID': '1'}], {'P1': 0, 'P2': 1})
    assert len(edges) == 1 and count['directed_rows'] == 2


def example_data():
    return dict(fold=np.array([0, 0, 0, 0, 1, 1]), p_a=np.array([0]), p_b=np.array([1]),
                u_a=np.array([0, 0, 1, 1, 2, 4]), u_b=np.array([2, 3, 2, 3, 3, 5]),
                u_num=np.array([5, 7, 9, 11, 13, 15]), u_den=np.full(6, 2))


def test_panel_preserves_direction_c3_and_exact_old_U_weights():
    data = example_data()
    ev, counts = make_panel(data, {(0, 1), (2, 0), (1, 3), (4, 5)}, {0, 1, 2, 4}, {0, 1, 3, 5}, 0)
    p = set(zip(ev['a'][ev['positive']], ev['b'][ev['positive']]))
    u = set(zip(ev['a'][~ev['positive']], ev['b'][~ev['positive']]))
    assert p == {(2, 0), (1, 3)} and (0, 1) not in p
    assert (0, 2) not in u and (3, 1) not in u and (1, 3) not in u
    assert (0, 3) in u and (2, 1) in u and (3, 0) not in u
    assert set(data['fold'][ev['a']]) == {0} == set(data['fold'][ev['b']])
    idx = ev['parent_u_row'][~ev['positive']]
    np.testing.assert_array_equal(ev['num'][~ev['positive']], data['u_num'][idx])
    np.testing.assert_array_equal(ev['den'][~ev['positive']], data['u_den'][idx])
    assert counts['previously_released_P'] == 1 and counts['sampled_U_now_source_P'] == 2


def test_no_other_source_can_change_local_U():
    data = example_data()
    one, _ = make_panel(data, {(0, 3)}, {0, 1, 2}, {0, 1, 2, 3}, 0)
    two, _ = make_panel(data, {(0, 3), (4, 5)}, {0, 1, 2, 4}, {0, 1, 2, 3, 5}, 0)
    for name in one:
        np.testing.assert_array_equal(one[name], two[name])


def test_positive_inventory_inconsistency_fails_closed():
    with pytest.raises(ValueError, match='inventory'):
        make_panel(example_data(), {(0, 3)}, {1}, {3}, 0)


def test_self_pairs_are_dropped_not_negative():
    ev, count = make_panel(example_data(), {(0, 0)}, {0}, {0, 3}, 0)
    assert count['self'] == 1 and not ev['positive'].any()


def test_directed_queries_do_not_turn_preys_into_anchors():
    a, b = np.array([0, 0, 2]), np.array([1, 2, 1])
    q = directed_queries(a, b, np.array([1, 0, 1], bool))
    assert [x.anchor for x in q] == [0]
    assert anchor_points(np.array([.9, .1, 1.]), q, np.ones(3))[0] == 1


@pytest.mark.parametrize('a,b,p', [([0, 0], [1, 1], [1, 0]), ([0], [0], [1])])
def test_invalid_directed_pairs_rejected(a, b, p):
    with pytest.raises(ValueError):
        directed_queries(np.array(a), np.array(b), np.array(p, bool))


def quartet_fixture():
    return np.array([0, 2, 0, 2]), np.array([1, 3, 3, 1]), np.array([1, 1, 0, 0], bool)


def test_directed_quartet_keeps_baits_and_unary_cancels():
    a, b, p = quartet_fixture()
    rows, ends, count = select_directed_quartets(a, b, p, salt='fixed', maximum=5, edge_cap=2, endpoint_cap=2)
    assert count == 1
    np.testing.assert_array_equal(rows, [[0, 1, 2, 3]])
    np.testing.assert_array_equal(ends, [[0, 1, 2, 3]])
    values = np.array([.1, 2.5, -1., 3.])
    np.testing.assert_array_equal(quartet_credit(values[a] + values[b], rows)[0], [.5])


def test_reversed_U_does_not_supply_directed_alternative():
    a, b, p = quartet_fixture()
    a[2], b[2] = b[2], a[2]
    assert select_directed_quartets(a, b, p, salt='x', maximum=5, edge_cap=2, endpoint_cap=2)[2] == 0


def test_quartet_deterministic_and_caps_respected():
    edges = [(a, b) for a in range(0, 8, 2) for b in range(1, 8, 2)]
    a, b = np.array(edges).T
    p = b == a + 1
    first = select_directed_quartets(a, b, p, salt='s', maximum=2, edge_cap=1, endpoint_cap=1)
    second = select_directed_quartets(a, b, p, salt='s', maximum=2, edge_cap=1, endpoint_cap=1)
    assert len(first[0]) == 2 and len(np.unique(first[1])) == 8
    np.testing.assert_array_equal(first[0], second[0])


def test_empty_panels_and_quartets():
    ev, _ = make_panel(example_data(), set(), set(), set(), 0)
    assert directed_queries(ev['a'], ev['b'], ev['positive']) == []
    rows, ends, count = select_directed_quartets(ev['a'], ev['b'], ev['positive'], salt='x', maximum=1, edge_cap=1, endpoint_cap=1)
    assert rows.shape == ends.shape == (0, 4) and count == 0


@pytest.mark.parametrize('url', ['http://bioplex.hms.harvard.edu/x', 'https://example.com/x',
                               'https://bioplex.hms.harvard.edu/data/unpublished.tsv',
                               'https://user:pass@bioplex.hms.harvard.edu/interactions.php'])
def test_only_exact_https_published_urls_allowed(url):
    cfg = {'source': {'origin': 'https://bioplex.hms.harvard.edu',
                     'page': 'https://bioplex.hms.harvard.edu/interactions.php', 'files': {'n': 'published.tsv'}}}
    with pytest.raises(RuntimeError):
        allowed_url(url, cfg)
    allowed_url(cfg['source']['page'], cfg)
    allowed_url(cfg['source']['origin'] + '/data/published.tsv', cfg)


def test_tsv_ragged_and_duplicate_headers_fail(tmp_path):
    path = tmp_path / 'source.tsv'
    path.write_text('a\ta\n1\t2\n')
    with pytest.raises(RuntimeError):
        list(tsv(path))
    path.write_text('a\tb\n1\n')
    with pytest.raises(RuntimeError):
        list(tsv(path))


def test_failed_test_evidence_cannot_freeze(tmp_path):
    path = tmp_path / 'tests.xml'
    path.write_text('<testsuite><testcase name="x"><failure/></testcase></testsuite>')
    with pytest.raises(RuntimeError):
        passed_tests(path)


@pytest.mark.parametrize('supported,lower,status', [(False, .7, 'inconclusive_insufficient_support'),
                                                  (True, .49, 'does_not_pass'), (True, .7, 'pass')])
def test_decision_does_not_promote_underpowered_swap(supported, lower, status):
    macro = {'pair_linear': .8, 'endpoint_linear': .6, 'pooled_cosine': .65,
             'pair_linear__1': .8, 'endpoint_linear__1': .6}
    deltas = {c: {'ci95': [.1, .2]} for c in ('endpoint_linear', 'pooled_cosine')}
    quartet = {'interval': {'ci95': [lower, .9]}, 'deltas': deltas}
    out = classify(True, supported, macro, deltas, [{'macro': macro}], [1], quartet,
                   ['endpoint_linear', 'pooled_cosine'], .02)
    assert out['anchor_signal_survives'] and out['swap_status'] == status


def test_stronger_direct_control_cannot_be_ignored():
    macro = {'pair_linear': .7, 'endpoint_linear': .6, 'pooled_cosine': .8,
             'pair_linear__1': .7, 'endpoint_linear__1': .6}
    deltas = {c: {'ci95': [.01, .2]} for c in ('endpoint_linear', 'pooled_cosine')}
    out = classify(True, False, macro, deltas, [{'macro': macro}], [1],
                   {'interval': {'ci95': None}, 'deltas': deltas}, list(deltas), .02)
    assert not out['anchor_signal_survives']
