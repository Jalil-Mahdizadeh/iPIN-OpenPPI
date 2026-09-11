# Reproducing the bounded source inventory

This package is a source-triage result, not a trained model or a released P/N
benchmark. `SOURCE_STRUCTURE.json` contains aggregate counts and unresolved
gates. `PUBLIC_SOURCE_MANIFEST.json` records the exact allowlist, source hashes,
registration and acquisition-recovery provenance without publishing raw data.
The local detailed manifest also contains CSV column inventories and remains
under the ignored run directory.

Runtime: `containers/images/ipin-data-arm64_0.1.2.sif`, SHA256
`72e4a13299df1c7036dbf5c8845f3a1d9d02bf6143bd2e4ee675aabd03112629`.
All Python execution was inside this image, with the repository bound to
`/work` and working directory `/work`. Prefix commands below with the project's
`apptainer exec --cleanenv --containall --bind <repository>:/work --pwd /work
<image>` invocation. Add `env PYTHONPATH=src` for pytest.

```bash
# Read-only verification of existing source bytes and schema inventory:
python scripts/data/audit_direct_binary_feasibility_v1.py

# Eight targeted tests; do not overwrite the archived XML report:
python -m pytest tests/unit/test_direct_binary_feasibility.py -q
```

For a separately authorized fresh replay, acquire the eleven pinned files with
`audit_direct_binary_feasibility_v1.py --acquire`, then execute
`summarize_direct_binary_feasibility_v1.py` and
`validate_direct_binary_feasibility_v1.py`. These use exclusive creation and
refuse to overwrite existing outputs. Source bytes and structural counts are
reproducible; acquisition timestamps and receipt hashes naturally change on a
fresh replay. Preserve original files rather than deleting them to rerun.

The initial acquisition stopped during CSV inspection on Windows-1252 text.
The parser was corrected with an explicit strict fallback, and `--acquire
--resume` verified already acquired blobs before fetching remaining files.
Registration, raw bytes and the allowlist were preserved; the recovery record
identifies the revised script. No assay decision or model result existed at
that point. This is a documented operational correction, not a claim that the
final implementation was all frozen before source inspection.

The separate pandas check confirms the matrix, missingness, exact-alias
rectangle, main sequence and numeric-QC counts. Its terminal-stop clarification
must accompany interpretation of the 82 raw noncanonical-character flags.
It verifies all 11 raw SHA256 values and the 109 files in the four earlier
study registries. It does not validate assay P/N definitions, matched support,
current training exposure, or scientific generalization. No upstream R code
was executed and no source payload was redistributed.

`ARTIFACT_REGISTRY.json` freezes the completed new local audit package. Root
README/report-index navigation and the graphify index are intentionally outside
that closure so future navigation updates do not rewrite this scientific record.
