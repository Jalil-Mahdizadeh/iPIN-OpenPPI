from __future__ import annotations

from ipin_openppi.pair_protocol.semantics import (
    c1_role,
    degree_bin,
    hamilton_sample_allocation,
    pair_id,
    pair_stratum_populations,
    sampling_design,
)


SALT = "ipin-openppi-pair-level-pu-r-protocol-v1"
SEED = "20260803"


def test_pair_identity_and_c1_role_are_orientation_stable_and_frozen() -> None:
    assert pair_id(("b", "a")) == (
        "pair:0eab8a0a3380abf4c7d1fb0b43b66aafbb64a4b953e4eb2dccca579461912d0c"
    )
    fixtures = {
        ("a0", "b0"): "train",
        ("a3", "b3"): "development",
        ("a5", "b5"): "test",
    }
    for pair, expected in fixtures.items():
        assert c1_role(pair, salt=SALT, seed=SEED) == expected
        assert c1_role(pair[::-1], salt=SALT, seed=SEED) == expected


def test_degree_bins_and_pair_populations_are_algebraic() -> None:
    assert [degree_bin(value) for value in (0, 1, 2, 3, 9, 19, 49, 99, 100)] == [
        "0",
        "1",
        "2",
        "3-4",
        "5-9",
        "10-19",
        "20-49",
        "50-99",
        "100+",
    ]
    populations = pair_stratum_populations({"1": 3, "2": 2})
    assert populations == {"1|1": 3, "1|2": 6, "2|2": 1}
    assert sum(populations.values()) == 10


def test_hamilton_sampling_has_positive_exact_probabilities() -> None:
    populations = {"0|0": 9, "0|1": 3, "1|1": 8}
    assert hamilton_sample_allocation(populations, 10) == {
        "0|0": 4,
        "0|1": 2,
        "1|1": 4,
    }
    design = sampling_design(populations, 10)
    assert design["sample_size"] == 10
    assert design["unlabeled_candidate_count"] == 20
    assert all(row["sample_size"] > 0 for row in design["strata"])
    for row in design["strata"]:
        assert (
            row["inclusion_probability_numerator"]
            * row["sampling_weight_numerator"]
            == row["inclusion_probability_denominator"]
            * row["sampling_weight_denominator"]
        )
