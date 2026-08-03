# Active primary-source parser

Use `ipin_openppi.ingestion.pipeline_v4` through
`scripts/data/parse_primary_sources.py`, with
`configs/parsing_primary_sources_v4.yaml`.

Revision 1.2.0 runs only in the qualified
`containers/images/ipin-data-arm64_0.1.2.sif` image. It provides:

- explicit UniProt canonical, additional-isoform, and additional-non-isoform
  sequence semantics;
- deterministic IntAct multiline-mutation reconstruction;
- exact IntAct unary/binary/n-ary cardinality semantics, with unary records
  retained but never marked n-ary;
- complete HuRI coverage across all 25 text tables and four XLS/XLSX
  workbooks;
- explicit source cell-type and Excel-error preservation;
- typed, label-prohibited HuRI structural-contact annotations; and
- typed, label-prohibited HuRI fusion-interference records.

The pipeline does not authorize label construction or model training.
