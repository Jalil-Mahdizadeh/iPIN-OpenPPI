"""Reliability tiers and conflict overlays for conditional negative evidence."""

from __future__ import annotations


def conflict_overlays(*, direct_positive: bool, broader_positive: bool) -> list[str]:
    overlays: list[str] = []
    if direct_positive or broader_positive:
        overlays.append("CF")
    if direct_positive:
        overlays.append("CF-D")
    if broader_positive:
        overlays.append("CF-B")
    return overlays


def reliability_tier(
    *,
    evidence_family: str,
    stringent_member: bool,
    reference_pair_usable: bool,
    direct_positive_conflict: bool,
) -> str:
    if not reference_pair_usable:
        return "MX"
    if evidence_family == "manual_experimental_negative":
        if stringent_member and not direct_positive_conflict:
            return "ME-1"
        return "ME-2"
    if evidence_family == "structure_derived_noncontact":
        return "SN-1" if stringent_member else "SN-2"
    raise ValueError(f"Unknown negative-evidence family: {evidence_family}")


def permitted_role(tier: str, overlays: list[str]) -> str:
    if "CF" in overlays:
        return "explicit_conflict_stratum_no_negative_label_or_training_use"
    roles = {
        "ME-1": "conditional_source_scoped_diagnostic_candidate_only",
        "ME-2": "conditional_descriptive_or_sensitivity_evidence_only",
        "SN-1": "structure_context_noncontact_diagnostic_only",
        "SN-2": "descriptive_structure_context_noncontact_only",
        "MX": "outside_primary_human_sequence_scope_retain_for_audit",
    }
    return roles[tier]


def effective_tier(tier: str, overlays: list[str]) -> str:
    return "+".join([tier, *overlays]) if overlays else tier
