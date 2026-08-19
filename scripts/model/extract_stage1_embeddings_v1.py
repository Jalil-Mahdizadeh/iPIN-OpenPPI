#!/usr/bin/env python3
"""Extract one frozen PLM candidate's complete Stage 1 endpoint embeddings."""

from __future__ import annotations

import argparse
from pathlib import Path

from ipin_openppi.stage1.embeddings import extract_candidate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-id", required=True, choices=("esm2_150m", "esm2_650m"))
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    extract_candidate(project_root=args.project_root.resolve(strict=True), candidate_id=args.candidate_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
