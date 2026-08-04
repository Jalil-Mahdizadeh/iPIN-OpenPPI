from pathlib import Path
import tarfile
import zipfile

import pytest

from ipin_openppi.lambourne_audit.archives import (
    scan_tar_gzip_archive,
    scan_zip_archive,
)
from ipin_openppi.lambourne_audit.imex import parse_mitab27
from ipin_openppi.lambourne_audit.pipeline import (
    _aggregate_panel_metrics,
    _reconcile_imex,
)


def test_zip_inventory_selects_without_extracting(tmp_path: Path) -> None:
    path = tmp_path / "source.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("root/table.tsv", "a\tb\n")
        archive.writestr("root/other.txt", "ignored")
    inventory, selected = scan_zip_archive(
        path,
        asset_id="code",
        archive_sha256="a" * 64,
        select=lambda name: name.endswith("table.tsv"),
    )
    assert len(inventory) == 2
    assert selected == {"root/table.tsv": b"a\tb\n"}


def test_tar_inventory_rejects_links(tmp_path: Path) -> None:
    path = tmp_path / "source.tar.gz"
    with tarfile.open(path, "w:gz") as archive:
        info = tarfile.TarInfo("root/link")
        info.type = tarfile.SYMTYPE
        info.linkname = "/etc/passwd"
        archive.addfile(info)
    with pytest.raises(RuntimeError, match="links are prohibited"):
        scan_tar_gzip_archive(
            path,
            asset_id="input",
            archive_sha256="b" * 64,
            select=lambda _name: False,
        )


def test_mitab_parser_preserves_roles_features_and_negative_flag(
    tmp_path: Path,
) -> None:
    header = "#" + "\t".join(f"column_{i}" for i in range(42))
    values = ["-"] * 42
    values[0] = "uniprotkb:P12345"
    values[1] = "uniprotkb:Q99999"
    values[6] = "psi-mi:\"MI:0018\"(two hybrid)"
    values[8] = "pubmed:1"
    values[16] = "psi-mi:\"MI:0499\"(unspecified role)"
    values[18] = "psi-mi:\"MI:0496\"(bait)"
    values[19] = "psi-mi:\"MI:0498\"(prey)"
    values[35] = "true"
    values[36] = "binding-associated region:1-10"
    path = tmp_path / "study.mitab27.txt"
    path.write_text(header + "\n" + "\t".join(values) + "\n", encoding="utf-8")
    rows = parse_mitab27(path, raw_sha256="c" * 64)
    assert len(rows) == 1
    assert rows[0]["source_accession_a"] == "P12345"
    assert rows[0]["source_accession_b"] == "Q99999"
    assert "bait" in rows[0]["experimental_role_a"]
    assert "prey" in rows[0]["experimental_role_b"]
    assert rows[0]["feature_a"] == "binding-associated region:1-10"
    assert rows[0]["negative_flag"] is True


def test_imex_reconciliation_distinguishes_records_from_distinct_panel_pairs() -> None:
    panel = [
        {
            "panel_pair_id": "panel-1",
            "uniprot_accession_ad": "P12345",
            "uniprot_accession_db": "Q99999",
            "reported_outcome": "Positive",
            "in_final_analysis": True,
        }
    ]
    preview = [
        {
            "preview_record_id": f"preview-{ordinal}",
            "source_accession_a": "Q99999",
            "source_accession_b": "P12345",
            "negative_flag": None,
            "detection_method": "MI:0397",
            "taxid_a": "taxid:9606",
            "taxid_b": "taxid:9606",
            "host_taxid": "taxid:559292",
        }
        for ordinal in (1, 2)
    ]
    rows, metrics = _reconcile_imex(preview, panel)
    assert len(rows) == 2
    assert metrics["matched_panel_outcomes_by_preview_record"] == {"Positive": 2}
    assert metrics["matched_distinct_panel_pairs"] == 1
    assert metrics["matched_distinct_final_analysis_pairs"] == 1
    assert all(not row["supports_attempted_negative_or_na_semantics"] for row in rows)


def test_family_generalization_requires_both_class_size_thresholds() -> None:
    def panel_row(outcome: str, *, endpoint_overlap: bool) -> dict[str, object]:
        return {
            "in_final_analysis": True,
            "reported_outcome": outcome,
            "pair_mapping_state": "both_unique_human",
            "reference_pair_usable": True,
            "exact_future_training_pair_overlap": False,
            "uniref90_pair_overlap": False,
            "uniref50_pair_overlap": False,
            "exact_endpoint_overlap": endpoint_overlap,
            "uniref90_endpoint_overlap": endpoint_overlap,
            "uniref50_endpoint_overlap": endpoint_overlap,
            "huri_record_positive_count": 0,
            "huri_pair_view_count": 0,
            "intact_positive_count": 0,
            "current_permitted_positive_overlap": False,
            "intact_negative_overlap_count": 0,
            "negatome_overlap_count": 0,
        }

    panel = [
        panel_row("Positive", endpoint_overlap=False),
        panel_row("Negative", endpoint_overlap=True),
        panel_row("Negative", endpoint_overlap=True),
    ]
    _metrics, feasibility = _aggregate_panel_metrics(
        panel_rows=panel,
        mapping_rows=[],
        positive_metrics={},
        config={
            "benchmark_feasibility": {
                "minimum_positive_assay_observations": 1,
                "minimum_negative_assay_observations": 2,
            }
        },
    )
    assert feasibility["exact_pair_disjoint_assay_specific_diagnostic"][
        "size_threshold_met"
    ]
    assert not feasibility["uniref90_endpoint_disjoint_generalization"][
        "size_threshold_met"
    ]
    assert not feasibility["sequence_family_generalization_supported"]
