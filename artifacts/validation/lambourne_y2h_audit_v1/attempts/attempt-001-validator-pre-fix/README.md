# Preserved validator attempt 001

This folder retains the immutable fail report produced while validating the
unchanged production Lambourne audit artifacts. The report passed 13 checks and
failed two overlap checks because the independent SQL did not gate DuckDB
`least`/`greatest` and endpoint comparisons on two-participant mapping usability.

Two earlier validator invocations stopped before writing reports because of an
ambiguous archive-basename lookup and Excel/TSV ORF-ID type mismatch. The three
validator-only defects were corrected in commits `0247bf6`, `5631411`, and
`eb33a29`, with regression tests. No production source, staging, or canonical
artifact was changed.

The authoritative final result is
`../../VALIDATION_REPORT.json`, which passes 15 of 15 checks with zero warnings.
