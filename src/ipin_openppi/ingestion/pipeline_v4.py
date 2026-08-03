"""Active parser routing for the primary-source v1 staging snapshot."""

from __future__ import annotations

import sys

from . import pipeline as base
from .huri_v2 import parse_huri
from .intact_v3 import parse_intact
from .uniprot_v2 import parse_uniprot


PARSER_VERSION = "1.2.0"

base.PARSER_VERSION = PARSER_VERSION
base.SOURCE_PARSERS["huri"] = parse_huri
base.SOURCE_PARSERS["intact_imex"] = parse_intact
base.SOURCE_PARSERS["uniprot"] = parse_uniprot


def _option_present(arguments: list[str], option: str) -> bool:
    return any(token == option or token.startswith(f"{option}=") for token in arguments)


def _require_scoped_nonproduction_output(arguments: list[str]) -> None:
    """Keep integrity bypasses confined to explicitly named smoke outputs."""

    bypasses = ("--allow-dirty", "--skip-raw-sha256")
    if not any(_option_present(arguments, option) for option in bypasses):
        return
    if not _option_present(arguments, "--output-root"):
        raise RuntimeError(
            "Nonproduction integrity overrides require an explicit --output-root"
        )
    parsed = base.build_argument_parser().parse_args(arguments)
    if parsed.output_root is None or not parsed.output_root.name.startswith("_smoke_"):
        raise RuntimeError(
            "Nonproduction integrity overrides are restricted to _smoke_* outputs"
        )


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not _option_present(arguments, "--config"):
        arguments = [
            "--config",
            "configs/parsing_primary_sources_v4.yaml",
            *arguments,
        ]
    _require_scoped_nonproduction_output(arguments)
    return base.main(arguments)
