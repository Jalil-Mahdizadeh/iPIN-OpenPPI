# Apptainer environments

All production software is packaged as immutable ARM64 SIF images.

- `definitions/`: human-readable Apptainer recipes.
- `locks/`: base references, dependency locks, and SIF SHA-256 records.
- `manifests/`: `apptainer inspect` output and build provenance.
- `images/`: generated SIF files; never committed and never overwritten.
- `cache/`: project-local OCI/Apptainer cache.
- Build commands create project-local temporary space as needed.

The core environments are:

| Image | Role |
|---|---|
| `ipin-qual-arm64_0.1.0.sif` | Initial NVIDIA PyTorch ARM64/GPU qualification |
| `ipin-data-arm64_0.1.2.sif` | Data ingestion, evidence processing, MMseqs, and core synthetic tests |
| `ipin-model-arm64_0.1.0.sif` | Qualified ESM representation, model training, and scoring runtime |

Recipes are in `definitions/`; exact image checksums are in `locks/*.sif.sha256`.
The images themselves are local execution assets. Use the checksum required by
the relevant frozen protocol rather than substituting a similarly named image.

Published-method environments and their build records are separate under
[benchmark/containers/](../benchmark/containers/). Each method documents its
native dependencies and numerical qualification in the
[benchmark index](../benchmark/README.md). See [tests/](../tests/README.md) for
the core test runtime and writable scratch-mount requirements.
