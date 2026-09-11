#!/usr/bin/env python3
"""Run DEC-0049 only inside the qualified ARM64 data Apptainer image."""

from ipin_openppi.composition_order.pipeline import main

if __name__ == '__main__':
    main()
