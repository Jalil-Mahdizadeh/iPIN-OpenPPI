"""Fail-closed Y2H semantics and analytical-filter reconstruction."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Iterable, Mapping

import pandas as pd


GOVERNANCE_FALSE = {
    "training_label_authorized": False,
    "benchmark_integration_authorized": False,
    "universal_nonbinding_asserted": False,
}


@dataclass(frozen=True)
class OutcomeSemantics:
    outcome_class: str
    evaluability_state: str
    observation_state: str
    technical_state: str
    state_basis: str


def text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def optional_bool(value: Any) -> bool | None:
    token = text(value).casefold()
    if token in {"true", "1"}:
        return True
    if token in {"false", "0"}:
        return False
    if token in {"", "na", "nan", "none"}:
        return None
    raise ValueError(f"Unexpected boolean token: {value!r}")


def growth_score(value: Any) -> int | None:
    token = text(value)
    if token.casefold() in {"", "na", "nan", "none"}:
        return None
    score = int(float(token))
    if score not in {0, 1, 2, 3, 4}:
        raise ValueError(f"Unexpected Y2H growth score: {value!r}")
    return score


def classify_y2h_outcome(row: Mapping[str, Any]) -> OutcomeSemantics:
    """Classify a public call without ever inferring an assay negative.

    The published True/False values are authoritative observations. A blank is
    classified only from explicit technical fields and the paper's stated
    rules. The precedence follows assay execution: mating/control growth,
    autoactivation, readable growth measurements, then sequence confirmation.
    """

    reported = text(row.get("Y2H_result"))
    if reported == "True":
        return OutcomeSemantics(
            "positive_y2h_observation",
            "evaluable",
            "positive",
            "passed",
            "source_reported_true_after_growth_and_sequence_acceptance",
        )
    if reported == "False":
        return OutcomeSemantics(
            "explicit_negative_y2h_observation",
            "evaluable",
            "negative",
            "passed",
            "source_reported_false_after_growth_and_sequence_acceptance",
        )
    if reported:
        raise ValueError(f"Unexpected public Y2H result: {reported!r}")

    pair_lw = growth_score(row.get("LW"))
    control_lw = growth_score(row.get("empty_AD_LW"))
    if (
        pair_lw is None
        or control_lw is None
        or pair_lw <= 1
        or control_lw <= 1
    ):
        return OutcomeSemantics(
            "mating_or_spotting_failure",
            "technically_unevaluable",
            "not_applicable",
            "mating_or_spotting_failure",
            "pair_or_autoactivation_control_failed_to_grow_on_SC_Leu_Trp",
        )

    control_3at = growth_score(row.get("empty_AD_3AT"))
    if control_3at == 4:
        return OutcomeSemantics(
            "autoactivation",
            "technically_unevaluable",
            "not_applicable",
            "db_autoactivation",
            "autoactivation_control_growth_score_equals_4",
        )

    pair_3at = growth_score(row.get("3AT"))
    if pair_3at is None or control_3at is None:
        return OutcomeSemantics(
            "assay_measurement_failure",
            "technically_unevaluable",
            "not_applicable",
            "missing_or_failed_3AT_measurement",
            "pair_or_autoactivation_control_3AT_score_is_NA_or_absent",
        )

    seq_3at = optional_bool(row.get("seq_confirmation_3AT"))
    seq_lw = optional_bool(row.get("seq_confirmation_LW"))
    if seq_3at is False or seq_lw is False:
        return OutcomeSemantics(
            "sequence_confirmation_failure",
            "technically_unevaluable",
            "not_applicable",
            "orf_sequence_confirmation_failed",
            "source_contains_an_explicit_false_sequence_confirmation",
        )

    return OutcomeSemantics(
        "unknown_unresolved",
        "technically_unevaluable",
        "not_applicable",
        "unresolved_blank",
        "blank_public_result_not_resolved_by_explicit_archived_technical_fields",
    )


def reconstruct_analytical_filter(
    frame: pd.DataFrame,
) -> tuple[pd.Series, list[dict[str, Any]]]:
    """Reproduce the archived default isoform-PPI analytical filter.

    The returned membership includes technically unevaluable attempts. The
    reported 3,509-pair universe is its evaluable subset.
    """

    required = {
        "ad_clone_id",
        "ad_gene_symbol",
        "db_gene_symbol",
        "source_category",
        "observation_state",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing analytical-filter columns: {sorted(missing)}")

    working = frame.index.to_series().map(lambda _value: True)
    stages: list[dict[str, Any]] = []

    def retain(name: str, description: str, condition: pd.Series) -> None:
        nonlocal working
        input_rows = int(working.sum())
        working = working & condition.fillna(False)
        output_rows = int(working.sum())
        stages.append(
            {
                "filter_step": len(stages) + 1,
                "filter_name": name,
                "filter_description": description,
                "input_rows": input_rows,
                "output_rows": output_rows,
                "excluded_rows": input_rows - output_rows,
            }
        )

    noncontrol = frame["source_category"].isin(
        {
            "tf_isoform_ppis",
            "tf_paralog_ppis",
            "paralog_with_PDI",
            "non_paralog_control",
        }
    )
    retain(
        "eligible_source_categories",
        "Archived loader includes the four non-reference-control categories.",
        noncontrol,
    )
    positive = frame["observation_state"].eq("positive")
    evaluable = frame["observation_state"].isin({"positive", "negative"})
    active = frame.loc[working]
    group_has_positive = (
        active.groupby(["ad_gene_symbol", "db_gene_symbol"])["observation_state"]
        .transform(lambda values: values.eq("positive").any())
        .reindex(frame.index, fill_value=False)
    )
    retain(
        "gene_partner_has_positive",
        "Retain only TF-gene/partner groups positive for at least one isoform.",
        group_has_positive,
    )
    active = frame.loc[working]
    clone_has_evaluable = (
        active.groupby("ad_clone_id")["observation_state"]
        .transform(lambda values: values.isin({"positive", "negative"}).any())
        .reindex(frame.index, fill_value=False)
    )
    retain(
        "clone_has_evaluable_test",
        "Remove isoform clones with no technically successful Y2H test.",
        clone_has_evaluable,
    )
    active = frame.loc[working]
    clone_has_positive = (
        active.groupby("ad_clone_id")["observation_state"]
        .transform(lambda values: values.eq("positive").any())
        .reindex(frame.index, fill_value=False)
    )
    retain(
        "clone_has_positive",
        "Archived default requires every retained isoform clone to have a positive.",
        clone_has_positive,
    )
    active = frame.loc[working]
    gene_has_two_isoforms = (
        active.groupby("ad_gene_symbol")["ad_clone_id"]
        .transform("nunique")
        .ge(2)
        .reindex(frame.index, fill_value=False)
    )
    retain(
        "gene_has_two_isoforms",
        "Retain TF genes represented by at least two distinct isoform clones.",
        gene_has_two_isoforms,
    )
    active = frame.loc[working]
    group_has_two_evaluable = (
        active.groupby(["ad_gene_symbol", "db_gene_symbol"])["observation_state"]
        .transform(lambda values: values.isin({"positive", "negative"}).sum() >= 2)
        .reindex(frame.index, fill_value=False)
    )
    retain(
        "gene_partner_has_two_evaluable_isoforms",
        "Retain TF-gene/partner groups with at least two evaluable isoform tests.",
        group_has_two_evaluable,
    )
    return working.astype(bool), stages


def sequence_sha256(sequence: str) -> str:
    return sha256(sequence.strip().upper().encode("ascii")).hexdigest()


_CODON_TABLE = {
    codon: amino
    for codons, amino in (
        ("TTT TTC", "F"), ("TTA TTG CTT CTC CTA CTG", "L"),
        ("ATT ATC ATA", "I"), ("ATG", "M"), ("GTT GTC GTA GTG", "V"),
        ("TCT TCC TCA TCG AGT AGC", "S"), ("CCT CCC CCA CCG", "P"),
        ("ACT ACC ACA ACG", "T"), ("GCT GCC GCA GCG", "A"),
        ("TAT TAC", "Y"), ("TAA TAG TGA", "*"), ("CAT CAC", "H"),
        ("CAA CAG", "Q"), ("AAT AAC", "N"), ("AAA AAG", "K"),
        ("GAT GAC", "D"), ("GAA GAG", "E"),
        ("TGT TGC", "C"), ("TGG", "W"),
        ("CGT CGC CGA CGG AGA AGG", "R"),
        ("GGT GGC GGA GGG", "G"),
    )
    for codon in codons.split()
}


def translate_cds(cds: str) -> str:
    sequence = cds.strip().upper()
    if len(sequence) % 3:
        raise ValueError("CDS length is not divisible by three")
    try:
        protein = "".join(
            _CODON_TABLE[sequence[index : index + 3]]
            for index in range(0, len(sequence), 3)
        )
    except KeyError as exc:
        raise ValueError(f"Unsupported CDS codon: {exc.args[0]}") from exc
    return protein[:-1] if protein.endswith("*") else protein


def split_multi_identifier(value: Any) -> list[str]:
    token = text(value)
    if not token or token.casefold() == "na":
        return []
    return sorted({item.strip() for item in token.split("|") if item.strip()})


def percentile(values: Iterable[float], quantile: float) -> float | None:
    series = pd.Series(list(values), dtype=float)
    if series.empty:
        return None
    return float(series.quantile(quantile))
