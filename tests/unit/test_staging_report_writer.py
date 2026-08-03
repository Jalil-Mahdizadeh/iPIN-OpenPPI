from __future__ import annotations

from pathlib import Path

import pytest

from ipin_openppi.ingestion.schema import sha256_file
from ipin_openppi.validation.staging import _write_report


def test_validation_report_and_sidecar_are_immutable(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    report_path = project_root / "artifacts/validation/gate/report.json"
    _write_report(report_path, {"status": "pass"}, project_root)

    sidecar = report_path.with_name("report.json.sha256")
    tokens = sidecar.read_text(encoding="utf-8").split()
    assert tokens == [sha256_file(report_path), "report.json"]
    assert report_path.stat().st_mode & 0o222 == 0
    assert sidecar.stat().st_mode & 0o222 == 0


def test_validation_report_refuses_preexisting_sidecar(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    report_path = project_root / "artifacts/validation/gate/report.json"
    report_path.parent.mkdir(parents=True)
    sidecar = report_path.with_name("report.json.sha256")
    sidecar.write_text("reserved\n", encoding="utf-8")

    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        _write_report(report_path, {"status": "pass"}, project_root)
    assert not report_path.exists()
    assert sidecar.read_text(encoding="utf-8") == "reserved\n"
