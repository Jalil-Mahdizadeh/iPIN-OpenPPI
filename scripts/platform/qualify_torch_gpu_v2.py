#!/usr/bin/env python3
"""Compatibility entry point for the v1 fixture's checkpoint map-location bug.

The v1 fixture loaded every checkpoint tensor onto CUDA, including the CPU RNG
ByteTensor required by torch.set_rng_state. This version forces checkpoint loading
onto CPU; model and optimizer restoration then copy state to their CUDA parameters.
"""

from __future__ import annotations

import qualify_torch_gpu as fixture


_original_torch_load = fixture.torch.load


def _load_checkpoint_on_cpu(*args, **kwargs):
    kwargs["map_location"] = "cpu"
    return _original_torch_load(*args, **kwargs)


fixture.torch.load = _load_checkpoint_on_cpu


if __name__ == "__main__":
    raise SystemExit(fixture.main())

