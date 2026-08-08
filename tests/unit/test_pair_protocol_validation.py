from __future__ import annotations

from ipin_openppi.pair_protocol.semantics import (
    c1_role,
    hamilton_sample_allocation,
    pair_id,
)
from ipin_openppi.validation.pair_protocol import (
    _independent_apportion,
    _independent_pair_id,
    _independent_role,
)


def test_independent_hash_implementation_matches_frozen_fixtures() -> None:
    salt = "ipin-openppi-pair-level-pu-r-protocol-v1"
    seed = "20260803"
    fixtures = {
        ("a0", "b0"): "train",
        ("a3", "b3"): "development",
        ("a5", "b5"): "test",
    }
    for pair, expected in fixtures.items():
        assert _independent_pair_id(pair) == pair_id(pair)
        assert _independent_role(pair, salt=salt, seed=seed) == expected
        assert c1_role(pair, salt=salt, seed=seed) == expected


def test_independent_apportionment_matches_frozen_integer_rules() -> None:
    populations = {
        "0|0": 9,
        "0|1": 3,
        "1|1": 8,
        "2|2": 1,
    }
    assert _independent_apportion(populations, 13) == hamilton_sample_allocation(
        populations, 13
    )
