from __future__ import annotations

from pathlib import Path

import pytest

from ipin_openppi.validation.reconciliation import _require_validation_scope
from ipin_openppi.validation.reconciliation_semantics import (
    normalize_manifest_metrics,
)


def test_smoke_validation_requires_explicit_scoped_flag(tmp_path: Path) -> None:
    smoke = tmp_path / "_smoke_reconciliation"
    production = tmp_path / "primary_reconciliation_v1"
    assert _require_validation_scope(smoke, True) == "qualification_smoke"
    assert _require_validation_scope(production, False) == "production_full"
    with pytest.raises(RuntimeError, match="requires --allow-smoke"):
        _require_validation_scope(smoke, False)
    with pytest.raises(RuntimeError, match="restricted to a _smoke_"):
        _require_validation_scope(production, True)


def test_manifest_metrics_are_normalized_to_frozen_keyed_form() -> None:
    manifest_metrics = {
        "participant_mapping_states": [
            {
                "source_key": "huri",
                "mapping_state": "unmapped",
                "construct_confidence": "unmapped",
                "participants": 2,
            }
        ],
        "participant_totals": {"participants": 2},
        "evidence_totals": {"evidence_records": 1},
        "huri_representation_reconciliation": [
            {"source_dataset": "HuRI", "union_gene_pairs": 1}
        ],
        "sifts_release_alignment_audit": {"chain_mapping_rows": 3},
    }
    assert normalize_manifest_metrics(manifest_metrics) == {
        "participant_mapping_states": {"huri|unmapped|unmapped": 2},
        "participant_totals": {"participants": 2},
        "evidence_totals": {"evidence_records": 1},
        "huri_representation_reconciliation": {"HuRI": {"union_gene_pairs": 1}},
        "sifts_release_alignment_audit": {"chain_mapping_rows": 3},
    }
