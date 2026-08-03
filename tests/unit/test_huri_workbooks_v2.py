from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from ipin_openppi.ingestion.huri_v2 import (
    _append_contact_row,
    _append_fusion_row,
    _headers,
    _optional_nonnegative_float,
    _strict_bool,
)
from ipin_openppi.ingestion.pipeline_v4 import PARSER_VERSION
from ipin_openppi.ingestion.schema import load_contract


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class CaptureWriter:
    def __init__(self) -> None:
        self.rows: list[dict[str, object]] = []

    def append(self, row: dict[str, object]) -> None:
        self.rows.append(row)


def _asset() -> SimpleNamespace:
    return SimpleNamespace(
        sha256="a" * 64,
        relative_path="data/raw/huri/publication_2020/supplement.zip",
    )


def _config() -> dict[str, str]:
    return {
        "source_release": "published_2020",
        "supplement_redistribution_tier": "internal_only",
    }


def test_workbook_headers_are_strict() -> None:
    assert _headers(
        ["protein1", "protein2", "in_contact"],
        member="table.xls",
        sheet="HuRI",
        row=1,
    ) == ["protein1", "protein2", "in_contact"]
    with pytest.raises(ValueError, match="Blank workbook header"):
        _headers(["a", None], member="table.xlsx", sheet="s", row=3)
    with pytest.raises(ValueError, match="Duplicate workbook header"):
        _headers(["a", "a"], member="table.xlsx", sheet="s", row=3)


def test_source_boolean_and_distance_parsing_is_conservative() -> None:
    assert _strict_bool("TRUE", locator="row:1", field="flag") is True
    assert _strict_bool("false", locator="row:1", field="flag") is False
    with pytest.raises(ValueError, match="source boolean"):
        _strict_bool("maybe", locator="row:1", field="flag")

    assert _optional_nonnegative_float("NA", locator="row:1", field="distance") == (
        None,
        "source_reported_na",
    )
    assert _optional_nonnegative_float(18.9, locator="row:1", field="distance") == (
        18.9,
        None,
    )
    with pytest.raises(ValueError, match="Invalid non-negative distance"):
        _optional_nonnegative_float(-1, locator="row:1", field="distance")


def test_contact_annotation_is_typed_but_never_label_authorized() -> None:
    writer = CaptureWriter()
    _append_contact_row(
        writer=writer,  # type: ignore[arg-type]
        cfg=_config(),
        asset=_asset(),
        member="Supplementary Table 10.xls",
        sheet="HuRI",
        physical_row=2,
        raw_locator="zip:table#sheet:HuRI#row:2",
        fields={"protein1": "P12345", "protein2": "Q99999", "in_contact": "TRUE"},
    )
    row = writer.rows[0]
    assert row["in_contact"] is True
    assert row["label_authorized"] is False
    assert row["protein_a_uniprot"] == "P12345"
    assert json.loads(str(row["fields_json"]))["in_contact"] == "TRUE"


def test_fusion_interference_preserves_orientation_and_missingness() -> None:
    writer = CaptureWriter()
    _append_fusion_row(
        writer=writer,  # type: ignore[arg-type]
        cfg=_config(),
        asset=_asset(),
        member="Supplementary Table 15.xls",
        sheet="20190418_fusion_interference",
        physical_row=2,
        raw_locator="zip:table#sheet:fusion#row:2",
        fields={
            "DBD_fused": "P12345",
            "AD_fused": "Q99999",
            "d_N1_iface": "NA",
            "d_C1_iface": 18.9,
            "d_N2_iface": 24.2,
            "d_C2_iface": "NA",
            "found_v1": "TRUE",
            "found_v2": "TRUE",
            "found_v3": "FALSE",
        },
    )
    row = writer.rows[0]
    assert row["dbd_fused_uniprot"] == "P12345"
    assert row["ad_fused_uniprot"] == "Q99999"
    assert row["distance_n1_interface"] is None
    assert row["distance_c1_interface"] == 18.9
    assert row["found_v3"] is False
    assert row["label_authorized"] is False
    assert json.loads(str(row["missingness_json"])) == {
        "distance_c2_interface": "source_reported_na",
        "distance_n1_interface": "source_reported_na",
    }


def test_staging_v2_contract_and_active_parser_version() -> None:
    contract = load_contract(PROJECT_ROOT / "schemas/staging/source_native_v2.yaml")
    assert contract.version == 2
    assert contract.table_spec("huri_structural_contact_annotations")
    assert contract.table_spec("huri_fusion_interference")
    assert PARSER_VERSION == "1.2.0"
