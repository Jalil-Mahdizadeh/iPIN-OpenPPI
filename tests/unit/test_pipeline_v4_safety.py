from __future__ import annotations

import pytest

from ipin_openppi.ingestion import pipeline_v4


def test_integrity_overrides_require_explicit_smoke_output() -> None:
    with pytest.raises(RuntimeError, match="explicit --output-root"):
        pipeline_v4._require_scoped_nonproduction_output(["--allow-dirty"])
    with pytest.raises(RuntimeError, match=r"_smoke_\*"):
        pipeline_v4._require_scoped_nonproduction_output(
            [
                "--output-root",
                "data/staging/primary_sources_v1",
                "--skip-raw-sha256",
            ]
        )


def test_integrity_overrides_accept_only_named_smoke_output() -> None:
    pipeline_v4._require_scoped_nonproduction_output(
        [
            "--output-root=data/staging/_smoke_parser_test",
            "--allow-dirty",
            "--skip-raw-sha256",
        ]
    )


def test_main_injects_v4_config_once(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: list[list[str]] = []

    def fake_main(arguments: list[str]) -> int:
        observed.append(arguments)
        return 0

    monkeypatch.setattr(pipeline_v4.base, "main", fake_main)
    assert pipeline_v4.main([]) == 0
    assert observed == [["--config", "configs/parsing_primary_sources_v4.yaml"]]

    observed.clear()
    assert pipeline_v4.main(["--config=custom.yaml"]) == 0
    assert observed == [["--config=custom.yaml"]]
