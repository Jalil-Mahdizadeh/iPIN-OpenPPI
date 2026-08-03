"""IntAct parser revision with exact unary/binary/n-ary semantics.

Revision 2 repaired the provider's multiline mutation TSV. Full-source QC then
showed that 2,198 one-participant XML records were marked ``original_nary`` by
the older ``participant_count != 2`` condition. This revision preserves those
records as unary, reserves ``original_nary`` for counts greater than two, and
adds an explicit unary quality flag. No source record is dropped or projected.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import intact as base
from .context import ParsingContext
from .intact_v2 import _parse_mutations_v2


_ORIGINAL_EMIT_INTERACTION = base._emit_interaction


def _correct_participant_cardinality(row: dict[str, Any]) -> dict[str, Any]:
    corrected = dict(row)
    participant_count = int(corrected["participant_count"])
    corrected["original_nary"] = participant_count > 2
    quality_flags = [
        flag
        for flag in corrected.get("quality_flags", [])
        if flag != "original_nary_preserved" or participant_count > 2
    ]
    if participant_count == 1 and "original_unary_preserved" not in quality_flags:
        quality_flags.append("original_unary_preserved")
    corrected["quality_flags"] = quality_flags
    return corrected


class _CardinalityCorrectingWriter:
    def __init__(self, delegate: Any) -> None:
        self.delegate = delegate

    def append(self, row: dict[str, Any]) -> None:
        self.delegate.append(_correct_participant_cardinality(row))


def _emit_interaction_v3(**kwargs: Any) -> list[dict[str, Any]]:
    arguments = dict(kwargs)
    arguments["evidence_writer"] = _CardinalityCorrectingWriter(
        arguments["evidence_writer"]
    )
    emitted = _ORIGINAL_EMIT_INTERACTION(**arguments)
    for record in emitted:
        record["original_nary"] = int(record["participant_count"]) > 2
    return emitted


def parse_intact(context: ParsingContext, output_root: Path) -> dict[str, Any]:
    cfg = dict(context.config["sources"]["intact_imex"])
    previous_emitter = base._emit_interaction
    base._emit_interaction = _emit_interaction_v3
    try:
        xml = base._parse_psi_xml_archive(context, output_root, cfg)
    finally:
        base._emit_interaction = previous_emitter
    unary_records = int(xml["participant_count_distribution"].get("1", 0))
    xml["cardinality_semantics"] = {
        "original_unary_records": unary_records,
        "original_nary_definition": "participant_count_greater_than_2",
        "unary_quality_flag": "original_unary_preserved",
    }
    obo = base._parse_obo(context, output_root, cfg)
    mutations = _parse_mutations_v2(context, output_root, cfg)
    return {
        "source": "intact_imex",
        "release": str(cfg["source_release"]),
        "parser_revision": "v3_exact_unary_binary_nary_semantics",
        "psi_xml": xml,
        "controlled_vocabulary": obo,
        "mutations": mutations,
    }
