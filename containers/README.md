# Apptainer environments

All production software is packaged as immutable ARM64 SIF images.

- `definitions/`: human-readable Apptainer recipes.
- `locks/`: base references, dependency locks, and SIF SHA-256 records.
- `manifests/`: `apptainer inspect` output and build provenance.
- `images/`: generated SIF files; never committed and never overwritten.
- `cache/`: project-local OCI/Apptainer cache.
- `tmp/`: project-local build temporary space.

The first image is a minimal NVIDIA PyTorch qualification environment. It is not yet the final scientific environment. A later version will add only audited, pinned dependencies after the ARM64/GPU base passes qualification.

