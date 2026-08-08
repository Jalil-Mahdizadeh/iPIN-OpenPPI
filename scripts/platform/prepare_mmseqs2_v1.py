#!/usr/bin/env python3
"""Prepare and verify the checksum-pinned MMseqs2 ARM64 audit tool."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ipin_openppi.ingestion.common import project_root_from
from ipin_openppi.sequence_component_audit.tooling import prepare_mmseqs_install


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/benchmark_eligibility_and_sequence_component_audit_v1.yaml"),
    )
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args(argv)
    project_root = project_root_from(Path.cwd())
    config = args.config if args.config.is_absolute() else project_root / args.config
    archive = args.archive
    if archive is not None and not archive.is_absolute():
        archive = project_root / archive
    result = prepare_mmseqs_install(
        project_root=project_root,
        config_path=config,
        archive_source=archive,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
