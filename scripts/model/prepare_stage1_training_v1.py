#!/usr/bin/env python3
"""Prepare immutable public-only arrays, orders, and 30 run configs."""

from pathlib import Path

from ipin_openppi.stage1.preparation import prepare_stage1


if __name__ == "__main__":
    prepare_stage1(Path.cwd().resolve(strict=True))
