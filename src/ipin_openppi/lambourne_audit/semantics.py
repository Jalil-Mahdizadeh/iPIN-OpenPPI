"""Pure semantic rules for the Lambourne Y2H-v1 audit.

These functions deliberately describe assay observations and technical states.  They
never emit reusable PPI labels or a universal nonbinding assertion.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable, Mapping


PAPER_OUTCOME_SEMANTICS: dict[str, tuple[str, str, str, str]] = {
    "Positive": (
        "positive_assay_observation",
        "attempted",
        "evaluable",
        "assay_signal_observed",
    ),
    "Negative": (
        "negative_assay_observation",
        "attempted",
        "evaluable",
        "assay_signal_not_observed",
    ),
    "Failed sequence confirmation": (
        "technically_unevaluable_sequence_confirmation",
        "attempted",
        "not_evaluable",
        "sequence_confirmation_failed",
    ),
    "Autoactivator": (
        "technically_unevaluable_autoactivator",
        "attempted",
        "not_evaluable",
        "bait_autoactivation",
    ),
    "Test failed": (
        "technically_unevaluable_assay_failure",
        "attempted",
        "not_evaluable",
        "assay_test_failed",
    ),
}


@dataclass(frozen=True)
class OutcomeSemantics:
    reported_outcome: str
    outcome_semantics: str
    attempted_state: str
    evaluability_state: str
    technical_state: str

    @property
    def observation_state(self) -> str:
        if self.outcome_semantics == "positive_assay_observation":
            return "positive"
        if self.outcome_semantics == "negative_assay_observation":
            return "negative"
        return "not_applicable_technically_unevaluable"

    def governance_fields(self) -> dict[str, bool]:
        return {
            "outcome_training_label_authorized": False,
            "universal_nonbinding_asserted": False,
            "benchmark_integration_authorized": False,
        }


def classify_paper_outcome(value: Any) -> OutcomeSemantics:
    """Map the five reported states to assay-bounded semantics, fail closed."""
    token = str(value).strip()
    if token not in PAPER_OUTCOME_SEMANTICS:
        raise ValueError(f"Unsupported Lambourne outcome: {value!r}")
    semantics, attempted, evaluability, technical = PAPER_OUTCOME_SEMANTICS[token]
    return OutcomeSemantics(token, semantics, attempted, evaluability, technical)


def raw_readout_to_reported_outcome(
    final_score: Any,
    sequence_confirmation_3at: Any,
    sequence_confirmation_lw: Any,
) -> str:
    """Reproduce the archived raw-readout crosswalk without collapsing NA states."""

    def tri(value: Any) -> int | None:
        if value is None:
            return None
        try:
            if value != value:  # NaN
                return None
        except TypeError:
            pass
        token = str(value).strip()
        if token in {"", "nan", "NaN", "NULL", "None"}:
            return None
        if token in {"0", "0.0", "False", "false"}:
            return 0
        if token in {"1", "1.0", "True", "true"}:
            return 1
        raise ValueError(f"Unexpected sequence-confirmation value: {value!r}")

    if final_score is None:
        score = None
    else:
        try:
            score = None if final_score != final_score else str(final_score).strip()
        except TypeError:
            score = str(final_score).strip()
    if score in {"", "nan", "NaN", "NULL", "None"}:
        score = None
    if score in {"0.0", "1.0"}:
        score = score[0]
    seq_3at = tri(sequence_confirmation_3at)
    seq_lw = tri(sequence_confirmation_lw)
    if score == "AA":
        return "Autoactivator"
    if score is None:
        return "Test failed"
    if score == "0":
        return "Negative" if seq_lw == 1 else "Failed sequence confirmation"
    if score == "1":
        return "Positive" if seq_3at == 1 else "Failed sequence confirmation"
    raise ValueError(f"Unexpected final score: {final_score!r}")


def unordered_text_pair(left: Any, right: Any) -> tuple[str, str]:
    a, b = str(left).strip(), str(right).strip()
    if not a or not b:
        raise ValueError("Pair members must be non-empty")
    return (a, b) if a <= b else (b, a)


def summarize_final_analysis(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Independently count the final Zhang subset and preserve all five outcomes."""
    selected = [
        row
        for row in rows
        if str(row["source_dataset"]) == "Zhang_et_al"
        and bool(row["in_published_version"])
    ]
    outcomes = Counter(str(row["reported_outcome"]) for row in selected)
    positive = outcomes["Positive"]
    negative = outcomes["Negative"]
    technically_unevaluable = sum(
        outcomes[name]
        for name in (
            "Failed sequence confirmation",
            "Autoactivator",
            "Test failed",
        )
    )
    return {
        "selected_pairs": len(selected),
        "positive_assay_observations": positive,
        "negative_assay_observations": negative,
        "technically_unevaluable_or_na": technically_unevaluable,
        "evaluable": positive + negative,
        "reported_outcomes": dict(sorted(outcomes.items())),
    }


def benchmark_claim_identifiability() -> dict[str, dict[str, str]]:
    """Frozen claim boundary used by both the pipeline and independent validator."""
    return {
        "identifiable": {
            "assay_observation_rate": (
                "conditional on the attempted, technically evaluable Y2H-v1 pairs"
            ),
            "workflow_recovery_rate": (
                "conditional on all final-analysis attempts with technical states retained"
            ),
            "assay_specific_discrimination": (
                "potentially identifiable only for a protected, provenance-matched panel"
            ),
            "pair_and_family_contamination": (
                "identifiable relative to the frozen local evidence/reference releases"
            ),
        },
        "not_identifiable": {
            "universal_nonbinding": (
                "a single Y2H orientation and condition cannot establish universal nonbinding"
            ),
            "biological_interaction_probability": (
                "assay sensitivity, selection and technical missingness are not separated"
            ),
            "proteome_wide_prevalence": (
                "the panel is model-selected and not a probability sample of all human pairs"
            ),
            "calibrated_unconditional_probability": (
                "selection probabilities and a universal gold standard are unavailable"
            ),
            "orientation_invariant_binding": (
                "the panel reports one bait/prey orientation per selected pair"
            ),
        },
    }
