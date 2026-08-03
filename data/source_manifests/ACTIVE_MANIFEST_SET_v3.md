# Active pre-acquisition manifest set v3

The sole acquisition-authorizing index is:

`data/source_manifests/PREACQUISITION_INDEX_v3.yaml`

It incorporates two pre-acquisition corrections:

1. HuRI v2 separates CC BY 4.0 portal data from publisher-hosted Nature supplements, which are internal-only.
2. PDB/SIFTS v2 binds the rolling SIFTS files to live 2026-07-26 HTTP metadata observed on 2026-08-03.

All earlier indexes, superseded manifests, and failed/intermediate validation artifacts are retained only as an audit trail. They must not drive downloads.

The active set authorizes raw acquisition and quality-control parsing inside Apptainer. It does not authorize training-label construction or model training.
