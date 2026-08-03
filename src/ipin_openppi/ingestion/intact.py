"""Streaming PSI-MI XML 3.0 and tabular IntAct ingestion."""

from __future__ import annotations

from collections import Counter
import csv
import hashlib
from pathlib import Path
import re
from typing import Any, Iterable
import xml.etree.ElementTree as ET
import zipfile

from .common import ParquetBatchWriter, canonical_json, stable_id, strip_version
from .context import ParsingContext


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _children(element: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in element if _local(child.tag) == name]


def _child(element: ET.Element, name: str) -> ET.Element | None:
    return next((child for child in element if _local(child.tag) == name), None)


def _descendant_text(element: ET.Element | None, *path: str) -> str | None:
    current = element
    for name in path:
        if current is None:
            return None
        current = _child(current, name)
    if current is None or current.text is None:
        return None
    value = current.text.strip()
    return value or None


def _names(element: ET.Element | None) -> dict[str, Any]:
    names = _child(element, "names") if element is not None else None
    if names is None:
        return {"short": None, "full": None, "aliases": []}
    aliases = []
    for alias in _children(names, "alias"):
        text = (alias.text or "").strip()
        if text:
            aliases.append(
                {
                    "value": text,
                    "type": alias.attrib.get("type"),
                    "type_ac": alias.attrib.get("typeAc"),
                }
            )
    return {
        "short": _descendant_text(names, "shortLabel"),
        "full": _descendant_text(names, "fullName"),
        "aliases": aliases,
    }


def _xref_records(element: ET.Element | None) -> list[dict[str, str | None]]:
    xref = _child(element, "xref") if element is not None else None
    if xref is None:
        return []
    records: list[dict[str, str | None]] = []
    for ref in xref:
        if _local(ref.tag) not in {"primaryRef", "secondaryRef"}:
            continue
        records.append(
            {
                "kind": _local(ref.tag),
                "db": ref.attrib.get("db"),
                "db_ac": ref.attrib.get("dbAc"),
                "id": ref.attrib.get("id"),
                "version": ref.attrib.get("version"),
                "ref_type": ref.attrib.get("refType"),
                "ref_type_ac": ref.attrib.get("refTypeAc"),
            }
        )
    return records


def _attributes(element: ET.Element | None) -> list[dict[str, str | None]]:
    attribute_list = _child(element, "attributeList") if element is not None else None
    if attribute_list is None:
        return []
    result = []
    for attribute in _children(attribute_list, "attribute"):
        result.append(
            {
                "name": attribute.attrib.get("name"),
                "name_ac": attribute.attrib.get("nameAc"),
                "value": (attribute.text or "").strip() or None,
            }
        )
    return result


def _cv_term(element: ET.Element | None) -> tuple[str | None, str | None]:
    if element is None:
        return None, None
    names = _names(element)
    accession = None
    for ref in _xref_records(element):
        if ref["db"] and ref["db"].casefold() == "psi-mi" and ref["id"]:
            accession = str(ref["id"])
            break
    return accession, names["short"] or names["full"]


def _organism(element: ET.Element | None) -> tuple[int | None, str | None]:
    if element is None:
        return None, None
    raw_taxid = element.attrib.get("ncbiTaxId")
    taxid = int(raw_taxid) if raw_taxid and re.fullmatch(r"-?\d+", raw_taxid) else None
    names = _names(element)
    return taxid, names["short"] or names["full"]


def _parse_interactor(element: ET.Element) -> dict[str, Any]:
    names = _names(element)
    xrefs = _xref_records(element)
    primary = next((ref for ref in xrefs if ref["kind"] == "primaryRef"), None)
    organism_element = _child(element, "organism")
    taxid, organism_name = _organism(organism_element)
    molecule_ac, molecule_name = _cv_term(_child(element, "interactorType"))
    sequence = _descendant_text(element, "sequence")
    relevant_databases = {
        "uniprotkb",
        "uniprot",
        "ensembl",
        "intact",
        "refseq",
        "ensemblgenomes",
    }
    relevant_xrefs = [
        ref
        for ref in xrefs
        if (ref["db"] or "").casefold() in relevant_databases
        or ref["ref_type"] in {"identity", "secondary-ac"}
    ]
    return {
        "source_interactor_id": element.attrib.get("id"),
        "names": names,
        "xrefs": xrefs,
        "relevant_xrefs": relevant_xrefs,
        "primary_db": primary["db"] if primary else None,
        "primary_id": primary["id"] if primary else None,
        "taxid": taxid,
        "organism_name": organism_name,
        "molecule_type_ac": molecule_ac,
        "molecule_type_name": molecule_name,
        "sequence": sequence,
        "sequence_sha256": (
            hashlib.sha256(sequence.encode()).hexdigest() if sequence else None
        ),
        "attributes": _attributes(element),
    }


def _publication_xrefs(experiment: ET.Element) -> list[str]:
    bibref = _child(experiment, "bibref")
    xrefs = _xref_records(bibref)
    xrefs.extend(_xref_records(experiment))
    values = []
    for ref in xrefs:
        if ref["db"] and ref["id"]:
            value = f"{str(ref['db']).casefold()}:{ref['id']}"
            if value not in values:
                values.append(value)
    return values


def _parse_experiment(element: ET.Element) -> dict[str, Any]:
    detection_ac, detection_name = _cv_term(
        _child(element, "interactionDetectionMethod")
    )
    identification_ac, identification_name = _cv_term(
        _child(element, "participantIdentificationMethod")
    )
    host_taxids: list[str] = []
    host_names: list[str] = []
    host_list = _child(element, "hostOrganismList")
    if host_list is not None:
        for host in _children(host_list, "hostOrganism"):
            taxid, name = _organism(host)
            if taxid is not None:
                host_taxids.append(str(taxid))
            if name:
                host_names.append(name)
    return {
        "source_experiment_id": element.attrib.get("id"),
        "names": _names(element),
        "publication_ids": _publication_xrefs(element),
        "detection_method_ac": detection_ac,
        "detection_method_name": detection_name,
        "identification_method_ac": identification_ac,
        "identification_method_name": identification_name,
        "host_taxids": host_taxids,
        "host_names": host_names,
        "attributes": _attributes(element),
        "xrefs": _xref_records(element),
    }


def _position(range_element: ET.Element, name: str) -> int | None:
    child = _child(range_element, name)
    if child is None:
        return None
    value = child.attrib.get("position")
    return int(value) if value and re.fullmatch(r"-?\d+", value) else None


def _range_boundary(range_element: ET.Element, boundary: str) -> int | None:
    direct = _position(range_element, boundary)
    if direct is not None:
        return direct
    interval = _child(range_element, f"{boundary}Interval")
    if interval is None:
        return None
    values = [
        int(child.attrib["position"])
        for child in interval
        if child.attrib.get("position")
        and re.fullmatch(r"-?\d+", child.attrib["position"])
    ]
    if not values:
        return None
    return min(values) if boundary == "begin" else max(values)


def _parse_feature(element: ET.Element) -> dict[str, Any]:
    type_ac, type_name = _cv_term(_child(element, "featureType"))
    role_ac, role_name = _cv_term(_child(element, "featureRole"))
    ranges: list[dict[str, Any]] = []
    range_list = _child(element, "featureRangeList")
    if range_list is not None:
        for range_ordinal, feature_range in enumerate(
            _children(range_list, "featureRange"), start=1
        ):
            start_status_ac, start_status_name = _cv_term(
                _child(feature_range, "startStatus")
            )
            end_status_ac, end_status_name = _cv_term(
                _child(feature_range, "endStatus")
            )
            ranges.append(
                {
                    "range_ordinal": range_ordinal,
                    "start_position": _range_boundary(feature_range, "begin"),
                    "end_position": _range_boundary(feature_range, "end"),
                    "start_status_ac": start_status_ac,
                    "start_status_name": start_status_name,
                    "end_status_ac": end_status_ac,
                    "end_status_name": end_status_name,
                    "original_sequence": _descendant_text(
                        feature_range, "originalSequence"
                    ),
                    "resulting_sequence": _descendant_text(
                        feature_range, "resultingSequence"
                    ),
                }
            )
    if not ranges:
        ranges.append(
            {
                "range_ordinal": 1,
                "start_position": None,
                "end_position": None,
                "start_status_ac": None,
                "start_status_name": None,
                "end_status_ac": None,
                "end_status_name": None,
                "original_sequence": None,
                "resulting_sequence": None,
            }
        )
    linked_feature = _child(element, "linkedFeature")
    return {
        "source_feature_id": element.attrib.get("id"),
        "names": _names(element),
        "type_ac": type_ac,
        "type_name": type_name,
        "role_ac": role_ac,
        "role_name": role_name,
        "ranges": ranges,
        "linked_feature_id": (
            linked_feature.attrib.get("id") if linked_feature is not None else None
        ),
        "xrefs": _xref_records(element),
        "attributes": _attributes(element),
    }


def _parse_participant(
    element: ET.Element, interactors: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    interactor_ref = _descendant_text(element, "interactorRef")
    embedded = _child(element, "interactor")
    if interactor_ref:
        interactor = interactors.get(interactor_ref)
    elif embedded is not None:
        embedded_id = embedded.attrib.get("id")
        interactor = interactors.get(embedded_id or "") or _parse_interactor(embedded)
        interactor_ref = embedded_id
    else:
        interactor = None
    biological_ac, biological_name = _cv_term(_child(element, "biologicalRole"))
    experimental_roles = []
    role_list = _child(element, "experimentalRoleList")
    if role_list is not None:
        for role in _children(role_list, "experimentalRole"):
            ac, name = _cv_term(role)
            experimental_roles.append({"ac": ac, "name": name})
    identification_methods = []
    method_list = _child(element, "participantIdentificationMethodList")
    if method_list is not None:
        for method in _children(method_list, "participantIdentificationMethod"):
            ac, name = _cv_term(method)
            identification_methods.append({"ac": ac, "name": name})
    expressed_taxid, expressed_name = _organism(_child(element, "expressedInOrganism"))
    features = []
    feature_list = _child(element, "featureList")
    if feature_list is not None:
        features = [
            _parse_feature(feature) for feature in _children(feature_list, "feature")
        ]
    return {
        "source_participant_id": element.attrib.get("id"),
        "source_interactor_id": interactor_ref,
        "interactor": interactor,
        "biological_role_ac": biological_ac,
        "biological_role_name": biological_name,
        "experimental_roles": experimental_roles,
        "identification_methods": identification_methods,
        "expressed_in_taxid": expressed_taxid,
        "expressed_in_name": expressed_name,
        "features": features,
        "attributes": _attributes(element),
    }


def _interaction_semantics(
    interaction_ac: str | None, interaction_name: str | None, participant_count: int
) -> str:
    name = (interaction_name or "").casefold()
    if interaction_ac == "MI:0407" or name == "direct interaction":
        return "direct_binary" if participant_count == 2 else "direct_within_complex"
    if interaction_ac == "MI:0915" or name == "physical association":
        return "physical_association"
    if interaction_ac == "MI:0914" or name in {
        "association",
        "colocalization",
        "proximity",
    }:
        return "association"
    if any(
        token in name for token in ("phosphorylation", "methylation", "ubiquitination")
    ):
        return "functional_association"
    return "unknown"


def _assay_family(name: str | None) -> str | None:
    normalized = (name or "").casefold()
    mappings = (
        ("two hybrid", "Y2H"),
        ("coimmunoprecipitation", "coIP"),
        ("pull down", "pull_down"),
        ("x-ray", "structural"),
        ("fluorescence", "fluorescence"),
        ("affinity chromatography", "affinity_capture"),
    )
    return next((family for token, family in mappings if token in normalized), None)


def _interaction_xrefs(element: ET.Element) -> list[dict[str, str | None]]:
    return _xref_records(element)


def _confidence_values(element: ET.Element) -> list[str]:
    confidence_list = _child(element, "confidenceList")
    if confidence_list is None:
        return []
    values = []
    for confidence in _children(confidence_list, "confidence"):
        unit_ac, unit_name = _cv_term(_child(confidence, "unit"))
        value = _descendant_text(confidence, "value")
        values.append(f"{unit_ac or unit_name or 'unspecified'}:{value or ''}")
    return values


def _parse_interaction(
    element: ET.Element, interactors: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    experiment_refs: list[str] = []
    experiment_list = _child(element, "experimentList")
    if experiment_list is not None:
        for child in experiment_list:
            if _local(child.tag) == "experimentRef" and child.text:
                experiment_refs.append(child.text.strip())
            elif _local(child.tag) == "experimentDescription":
                experiment_refs.append(str(child.attrib.get("id", "")))
    participant_list = _child(element, "participantList")
    participants = (
        [
            _parse_participant(p, interactors)
            for p in _children(participant_list, "participant")
        ]
        if participant_list is not None
        else []
    )
    interaction_ac, interaction_name = _cv_term(_child(element, "interactionType"))
    expansion_ac, expansion_name = _cv_term(_child(element, "expansionMethod"))
    negative_text = _descendant_text(element, "negative")
    negative = negative_text.casefold() == "true" if negative_text is not None else None
    modelled_text = _descendant_text(element, "modelled")
    intramolecular_text = _descendant_text(element, "intraMolecular")
    return {
        "local_id": element.attrib.get("id"),
        "names": _names(element),
        "xrefs": _interaction_xrefs(element),
        "experiment_refs": experiment_refs,
        "participants": participants,
        "interaction_type_ac": interaction_ac,
        "interaction_type_name": interaction_name,
        "expansion_method_ac": expansion_ac,
        "expansion_method_name": expansion_name,
        "negative": negative,
        "modelled": modelled_text,
        "intramolecular": intramolecular_text,
        "attributes": _attributes(element),
        "confidence_values": _confidence_values(element),
    }


def _emit_participant(
    *,
    parsed: dict[str, Any],
    participant_ordinal: int,
    evidence_id: str,
    raw_file_path: str,
    raw_locator: str,
    participant_writer: ParquetBatchWriter,
    feature_writer: ParquetBatchWriter,
) -> dict[str, Any]:
    interactor = parsed["interactor"] or {}
    xrefs = interactor.get("relevant_xrefs", [])
    primary_db = interactor.get("primary_db")
    primary_id = interactor.get("primary_id")
    alternates = [
        f"{ref['db']}:{ref['id']}" for ref in xrefs if ref.get("db") and ref.get("id")
    ]
    uniprot = [
        str(ref["id"])
        for ref in xrefs
        if (ref.get("db") or "").casefold() in {"uniprotkb", "uniprot"}
        and ref.get("id")
    ]
    ensembl = [
        str(ref["id"])
        for ref in xrefs
        if (ref.get("db") or "").casefold() == "ensembl" and ref.get("id")
    ]
    genes = [value for value in ensembl if value.startswith("ENSG")]
    transcripts = [value for value in ensembl if value.startswith("ENST")]
    proteins = [value for value in ensembl if value.startswith("ENSP")]
    roles = parsed["experimental_roles"]
    role_ac = roles[0]["ac"] if len(roles) == 1 else None
    role_name = roles[0]["name"] if len(roles) == 1 else None
    methods = parsed["identification_methods"]
    method_ac = methods[0]["ac"] if len(methods) == 1 else None
    method_name = methods[0]["name"] if len(methods) == 1 else None
    features = parsed["features"]
    mutations = [
        feature["names"]["short"] or feature["type_name"]
        for feature in features
        if "mutation" in (feature["type_name"] or "").casefold()
    ]
    tags = [
        feature["type_name"] or feature["names"]["short"]
        for feature in features
        if "tag" in (feature["type_name"] or "").casefold()
    ]
    fusions = [
        feature["type_name"] or feature["names"]["short"]
        for feature in features
        if "fusion" in (feature["type_name"] or "").casefold()
    ]
    participant_id = f"{evidence_id}:p{participant_ordinal}"
    confidence = "C" if primary_id or uniprot else "D"
    participant_writer.append(
        {
            "participant_id": participant_id,
            "evidence_id": evidence_id,
            "participant_ordinal": participant_ordinal,
            "source_participant_id": parsed["source_participant_id"],
            "source_interactor_id": parsed["source_interactor_id"],
            "primary_identifier_db": primary_db,
            "primary_identifier": primary_id,
            "alternate_identifiers": alternates,
            "aliases": [
                alias["value"]
                for alias in interactor.get("names", {}).get("aliases", [])
            ],
            "taxid": interactor.get("taxid"),
            "organism_name": interactor.get("organism_name"),
            "molecule_type_ac": interactor.get("molecule_type_ac"),
            "molecule_type_name": interactor.get("molecule_type_name"),
            "biological_role_ac": parsed["biological_role_ac"],
            "biological_role_name": parsed["biological_role_name"],
            "experimental_role_ac": role_ac,
            "experimental_role_name": role_name,
            "orientation_role": role_name,
            "expressed_in_taxid": parsed["expressed_in_taxid"],
            "expressed_in_name": parsed["expressed_in_name"],
            "raw_uniprot_accessions": uniprot,
            "raw_ensembl_gene_ids": genes,
            "raw_ensembl_transcript_ids": transcripts,
            "raw_ensembl_protein_ids": proteins,
            "raw_orf_ids": [],
            "mapped_uniprot_accession": None,
            "mapped_isoform_id": None,
            "mapped_sequence_sha256": None,
            "mapping_state": "not_attempted",
            "mapping_basis": "source_native_parse_only",
            "construct_sequence_sha256": None,
            "construct_start": None,
            "construct_end": None,
            "construct_mutations": [value for value in mutations if value],
            "construct_tags": [value for value in tags if value],
            "construct_fusion_partners": [value for value in fusions if value],
            "signal_propeptide_handling": None,
            "construct_confidence": confidence,
            "construct_confidence_basis": (
                "source_identifier_and_features_without_reconstructed_construct_sequence"
                if confidence == "C"
                else "source_interactor_identifier_ambiguous_or_absent"
            ),
            "participant_identification_method_ac": method_ac,
            "participant_identification_method_name": method_name,
            "stoichiometry": None,
            "raw_file_path": raw_file_path,
            "raw_locator": raw_locator,
            "source_fields_json": canonical_json(
                {
                    "experimental_roles": roles,
                    "participant_identification_methods": methods,
                    "attributes": parsed["attributes"],
                    "interactor_sequence_sha256": interactor.get("sequence_sha256"),
                }
            ),
            "missingness_json": canonical_json(
                {
                    "mapped_uniprot_accession": "not_parsed",
                    "mapped_sequence_sha256": "not_parsed",
                    "construct_sequence_sha256": "unresolved",
                    "construct_start": "unresolved",
                    "construct_end": "unresolved",
                }
            ),
        }
    )
    for feature in features:
        for feature_range in feature["ranges"]:
            feature_id = stable_id(
                "intact-feature",
                participant_id,
                feature["source_feature_id"],
                feature_range["range_ordinal"],
            )
            feature_writer.append(
                {
                    "feature_id": feature_id,
                    "participant_id": participant_id,
                    "evidence_id": evidence_id,
                    "source_feature_id": feature["source_feature_id"],
                    "feature_short_label": feature["names"]["short"],
                    "feature_type_ac": feature["type_ac"],
                    "feature_type_name": feature["type_name"],
                    "feature_role_ac": feature["role_ac"],
                    "feature_role_name": feature["role_name"],
                    "range_ordinal": feature_range["range_ordinal"],
                    "start_position": feature_range["start_position"],
                    "end_position": feature_range["end_position"],
                    "start_status_ac": feature_range["start_status_ac"],
                    "start_status_name": feature_range["start_status_name"],
                    "end_status_ac": feature_range["end_status_ac"],
                    "end_status_name": feature_range["end_status_name"],
                    "original_sequence": feature_range["original_sequence"],
                    "resulting_sequence": feature_range["resulting_sequence"],
                    "linked_feature_id": feature["linked_feature_id"],
                    "raw_file_path": raw_file_path,
                    "raw_locator": raw_locator,
                    "source_fields_json": canonical_json(
                        {"xrefs": feature["xrefs"], "attributes": feature["attributes"]}
                    ),
                    "missingness_json": canonical_json(
                        {
                            key: "not_reported"
                            for key in ("original_sequence", "resulting_sequence")
                            if feature_range[key] is None
                        }
                    ),
                }
            )
    return {
        "participant_id": participant_id,
        "primary_token": (
            f"{str(primary_db).casefold()}:{primary_id}"
            if primary_db and primary_id
            else f"source_interactor:{parsed['source_interactor_id']}"
        ),
        "is_protein": interactor.get("molecule_type_ac") == "MI:0326"
        or (interactor.get("molecule_type_name") or "").casefold() == "protein",
    }


def _emit_interaction(
    *,
    parsed: dict[str, Any],
    experiments: dict[str, dict[str, Any]],
    context: ParsingContext,
    cfg: dict[str, Any],
    asset,
    member: str,
    entry_ordinal: int,
    interaction_ordinal: int,
    xml_release_date: str | None,
    evidence_writer: ParquetBatchWriter,
    participant_writer: ParquetBatchWriter,
    feature_writer: ParquetBatchWriter,
) -> list[dict[str, Any]]:
    experiment_refs = parsed["experiment_refs"] or [""]
    emitted: list[dict[str, Any]] = []
    xrefs = parsed["xrefs"]
    intact_ids = [
        str(ref["id"])
        for ref in xrefs
        if (ref.get("db") or "").casefold() == "intact" and ref.get("id")
    ]
    imex_ids = [
        str(ref["id"])
        for ref in xrefs
        if (ref.get("db") or "").casefold() == "imex" and ref.get("id")
    ]
    source_record_id = (
        intact_ids[0]
        if intact_ids
        else (f"{member}:entry:{entry_ordinal}:interaction:{parsed['local_id']}")
    )
    participant_count = len(parsed["participants"])
    interaction_semantics = _interaction_semantics(
        parsed["interaction_type_ac"],
        parsed["interaction_type_name"],
        participant_count,
    )
    original_nary = participant_count != 2
    expanded = (
        parsed["expansion_method_ac"] is not None
        or parsed["expansion_method_name"] is not None
    )

    for experiment_ref in experiment_refs:
        experiment = experiments.get(experiment_ref, {})
        evidence_id = stable_id(
            "intact-evidence",
            asset.sha256,
            member,
            entry_ordinal,
            parsed["local_id"],
            experiment_ref,
        )
        raw_locator = (
            f"zip:{member}#entry:{entry_ordinal}/interaction:{parsed['local_id']}"
            f"/experiment:{experiment_ref or 'missing'}"
        )
        participant_emissions = [
            _emit_participant(
                parsed=participant,
                participant_ordinal=ordinal,
                evidence_id=evidence_id,
                raw_file_path=asset.relative_path,
                raw_locator=raw_locator,
                participant_writer=participant_writer,
                feature_writer=feature_writer,
            )
            for ordinal, participant in enumerate(parsed["participants"], start=1)
        ]
        if participant_count == 2:
            tokens = [item["primary_token"] for item in participant_emissions]
            ordered_pair_id = stable_id("ordered-pair", *tokens)
            unordered_pair_id = stable_id("unordered-pair", *sorted(tokens))
        else:
            ordered_pair_id = None
            unordered_pair_id = None
        negative = parsed["negative"] is True
        if negative:
            observation = "negative"
            evaluability = "unknown"
            technical = "unknown"
            state_basis = "source_asserted"
        else:
            observation = "positive"
            evaluability = "evaluable"
            technical = "passed"
            state_basis = "logically_implied_by_source_positive"
        quality_flags = []
        if original_nary:
            quality_flags.append("original_nary_preserved")
        if expanded:
            quality_flags.append("expanded_projection_not_direct_binary")
        if participant_count == 2 and all(
            item["is_protein"] for item in participant_emissions
        ):
            quality_flags.append("binary_two_protein_record")
        else:
            quality_flags.append("not_binary_two_protein_record")
        if member.endswith("_negative.xml") and not negative:
            quality_flags.append("negative_member_without_true_negative_flag")
        if not member.endswith("_negative.xml") and negative:
            quality_flags.append("true_negative_flag_in_nonnegative_member")
        host_taxids = experiment.get("host_taxids", [])
        host_names = experiment.get("host_names", [])
        missingness = {
            "search_space_state": "not_applicable",
            "selection_state": "unresolved",
            "assay_version": "not_reported",
            "assay_batch": "not_reported",
        }
        if parsed["negative"] is None:
            missingness["negative_flag"] = "not_reported"
        if not experiment_ref:
            missingness["experiment_ids"] = "not_reported"
        evidence_writer.append(
            {
                "evidence_id": evidence_id,
                "source_key": "intact_imex",
                "source_dataset": "human_psi_mi_xml_3",
                "source_release": str(cfg["source_release"]),
                "source_record_id": source_record_id,
                "source_record_ordinal": interaction_ordinal,
                "source_member": member,
                "record_kind": "psi_mi_xml_interaction_experiment",
                "unordered_pair_id": unordered_pair_id,
                "ordered_pair_id": ordered_pair_id,
                "experiment_ids": [experiment_ref] if experiment_ref else [],
                "publication_ids": experiment.get("publication_ids", []),
                "imex_ids": imex_ids,
                "source_database_ids": [
                    f"{ref['db']}:{ref['id']}"
                    for ref in xrefs
                    if ref.get("db") and ref.get("id")
                ],
                "participant_count": participant_count,
                "original_nary": original_nary,
                "is_expanded_projection": expanded,
                "expansion_method_ac": parsed["expansion_method_ac"],
                "expansion_method_name": parsed["expansion_method_name"],
                "negative_flag": parsed["negative"],
                "interaction_type_ac": parsed["interaction_type_ac"],
                "interaction_type_name": parsed["interaction_type_name"],
                "interaction_semantics": interaction_semantics,
                "detection_method_ac": experiment.get("detection_method_ac"),
                "detection_method_name": experiment.get("detection_method_name"),
                "participant_identification_method_ac": experiment.get(
                    "identification_method_ac"
                ),
                "participant_identification_method_name": experiment.get(
                    "identification_method_name"
                ),
                "assay_family": _assay_family(experiment.get("detection_method_name")),
                "assay_version": None,
                "assay_batch": None,
                "host_taxid": int(host_taxids[0]) if len(host_taxids) == 1 else None,
                "host_name": host_names[0] if len(host_names) == 1 else None,
                "orientation_semantics": (
                    "source_experimental_roles_preserved"
                    if any(p["experimental_roles"] for p in parsed["participants"])
                    else "unspecified"
                ),
                "search_space_state": "not_applicable",
                "selection_state": "unknown",
                "attempted_state": "attempted",
                "evaluability_state": evaluability,
                "technical_state": technical,
                "observation_state": observation,
                "state_basis": state_basis,
                "failure_reasons": [],
                "context_json": canonical_json(
                    {
                        "xml_source_release_date": xml_release_date,
                        "experiment_host_taxids": host_taxids,
                        "experiment_host_names": host_names,
                        "experiment_attributes": experiment.get("attributes", []),
                        "interaction_attributes": parsed["attributes"],
                    }
                ),
                "assay_parameters_json": canonical_json({}),
                "confidence_values": parsed["confidence_values"],
                "repeat_group_id": source_record_id,
                "quality_flags": quality_flags,
                "source_created_date": None,
                "source_updated_date": None,
                "raw_file_path": asset.relative_path,
                "raw_file_sha256": asset.sha256,
                "raw_locator": raw_locator,
                "source_acquired_at_utc": asset.acquired_at_utc,
                "parser_name": "ipin_openppi.ingestion.intact",
                "parser_version": context.parser_version,
                "parser_git_commit": context.parser_git_commit,
                "container_sif_sha256": context.container_sif_sha256,
                "schema_version": context.evidence_contract.version,
                "schema_sha256": context.evidence_contract.sha256,
                "license_id": str(cfg["license_id"]),
                "attribution": str(cfg["attribution"]),
                "redistribution_tier": str(cfg["redistribution_tier"]),
                "source_fields_json": canonical_json(
                    {
                        "local_interaction_id": parsed["local_id"],
                        "names": parsed["names"],
                        "xrefs": xrefs,
                        "modelled": parsed["modelled"],
                        "intramolecular": parsed["intramolecular"],
                    }
                ),
                "missingness_json": canonical_json(missingness),
            }
        )
        emitted.append(
            {
                "negative": negative,
                "participant_count": participant_count,
                "original_nary": original_nary,
                "expanded": expanded,
                "interaction_semantics": interaction_semantics,
                "all_protein_binary": participant_count == 2
                and all(item["is_protein"] for item in participant_emissions),
            }
        )
    return emitted


def _write_interactor_record(
    *,
    parsed: dict[str, Any],
    context: ParsingContext,
    cfg: dict[str, Any],
    asset,
    member: str,
    entry_ordinal: int,
    interactor_ordinal: int,
    writer: ParquetBatchWriter,
) -> None:
    writer.append(
        {
            "staging_record_id": stable_id(
                "intact-interactor",
                asset.sha256,
                member,
                entry_ordinal,
                parsed["source_interactor_id"],
            ),
            "source_key": "intact_imex",
            "source_dataset": "psi_mi_xml_interactor",
            "source_release": str(cfg["source_release"]),
            "source_member": member,
            "source_record_ordinal": interactor_ordinal,
            "raw_file_path": asset.relative_path,
            "raw_file_sha256": asset.sha256,
            "raw_locator": (
                f"zip:{member}#entry:{entry_ordinal}/interactor:"
                f"{parsed['source_interactor_id']}"
            ),
            "fields_json": canonical_json(parsed),
            "redistribution_tier": str(cfg["redistribution_tier"]),
        }
    )


def _write_experiment_record(
    *,
    parsed: dict[str, Any],
    context: ParsingContext,
    cfg: dict[str, Any],
    asset,
    member: str,
    entry_ordinal: int,
    writer: ParquetBatchWriter,
) -> None:
    experiment_id = parsed["source_experiment_id"]
    missingness = {
        key: "not_reported"
        for key in (
            "interaction_detection_method_ac",
            "participant_identification_method_ac",
        )
        if parsed[
            {
                "interaction_detection_method_ac": "detection_method_ac",
                "participant_identification_method_ac": "identification_method_ac",
            }[key]
        ]
        is None
    }
    writer.append(
        {
            "experiment_record_id": stable_id(
                "intact-experiment",
                asset.sha256,
                member,
                entry_ordinal,
                experiment_id,
            ),
            "source_release": str(cfg["source_release"]),
            "source_member": member,
            "source_entry_ordinal": entry_ordinal,
            "source_experiment_id": experiment_id,
            "publication_ids": parsed["publication_ids"],
            "interaction_detection_method_ac": parsed["detection_method_ac"],
            "interaction_detection_method_name": parsed["detection_method_name"],
            "participant_identification_method_ac": parsed["identification_method_ac"],
            "participant_identification_method_name": parsed[
                "identification_method_name"
            ],
            "host_taxids": parsed["host_taxids"],
            "host_names": parsed["host_names"],
            "raw_file_path": asset.relative_path,
            "raw_file_sha256": asset.sha256,
            "raw_locator": (
                f"zip:{member}#entry:{entry_ordinal}/experiment:{experiment_id}"
            ),
            "fields_json": canonical_json(
                {
                    "names": parsed["names"],
                    "xrefs": parsed["xrefs"],
                    "attributes": parsed["attributes"],
                }
            ),
            "missingness_json": canonical_json(missingness),
        }
    )


def _parse_psi_xml_archive(
    context: ParsingContext, output_root: Path, cfg: dict[str, Any]
) -> dict[str, Any]:
    asset = context.asset(str(cfg["psi_xml_asset_id"]))
    evidence_writer = ParquetBatchWriter(
        output_root / "evidence_records",
        context.evidence_contract,
        "evidence_records",
        **context.writer_kwargs(),
    )
    participant_writer = ParquetBatchWriter(
        output_root / "participants",
        context.evidence_contract,
        "participants",
        **context.writer_kwargs(),
    )
    feature_writer = ParquetBatchWriter(
        output_root / "participant_features",
        context.evidence_contract,
        "participant_features",
        **context.writer_kwargs(),
    )
    interactor_writer = ParquetBatchWriter(
        output_root / "interactors",
        context.staging_contract,
        "raw_tabular_records",
        **context.writer_kwargs(),
    )
    experiment_writer = ParquetBatchWriter(
        output_root / "experiments",
        context.staging_contract,
        "intact_experiments",
        **context.writer_kwargs(),
    )
    global_counts = Counter()
    semantic_counts = Counter()
    participant_count_distribution = Counter()
    member_stats: dict[str, Any] = {}
    interaction_ordinal = 0
    interactor_ordinal = 0

    with (
        zipfile.ZipFile(asset.path) as archive,
        evidence_writer,
        participant_writer,
        feature_writer,
        interactor_writer,
        experiment_writer,
    ):
        members = [
            info
            for info in archive.infolist()
            if not info.is_dir() and info.filename.endswith(".xml")
        ]
        for member_index, info in enumerate(members, start=1):
            if info.flag_bits & 0x1:
                raise ValueError(f"Encrypted IntAct ZIP member: {info.filename}")
            print(
                f"INTACT_MEMBER {member_index}/{len(members)} {info.filename} "
                f"uncompressed_bytes={info.file_size}",
                flush=True,
            )
            entry_ordinal = 0
            interactors: dict[str, dict[str, Any]] = {}
            experiments: dict[str, dict[str, Any]] = {}
            xml_release_date: str | None = None
            stack: list[str] = []
            current_member_counts = Counter()
            with archive.open(info) as handle:
                for event, element in ET.iterparse(handle, events=("start", "end")):
                    local = _local(element.tag)
                    if event == "start":
                        stack.append(local)
                        if local == "entry":
                            entry_ordinal += 1
                            interactors = {}
                            experiments = {}
                            xml_release_date = None
                        continue

                    parent = stack[-2] if len(stack) >= 2 else None
                    if local == "source" and parent == "entry":
                        xml_release_date = element.attrib.get("releaseDate")
                        element.clear()
                    elif local == "experimentDescription":
                        parsed_experiment = _parse_experiment(element)
                        experiment_id = parsed_experiment["source_experiment_id"]
                        if experiment_id:
                            experiments[str(experiment_id)] = parsed_experiment
                            _write_experiment_record(
                                parsed=parsed_experiment,
                                context=context,
                                cfg=cfg,
                                asset=asset,
                                member=info.filename,
                                entry_ordinal=entry_ordinal,
                                writer=experiment_writer,
                            )
                            global_counts["experiments"] += 1
                            current_member_counts["experiments"] += 1
                        if parent == "experimentList":
                            element.clear()
                    elif local == "interactor":
                        parsed_interactor = _parse_interactor(element)
                        interactor_id = parsed_interactor["source_interactor_id"]
                        if interactor_id:
                            interactors[str(interactor_id)] = parsed_interactor
                            interactor_ordinal += 1
                            _write_interactor_record(
                                parsed=parsed_interactor,
                                context=context,
                                cfg=cfg,
                                asset=asset,
                                member=info.filename,
                                entry_ordinal=entry_ordinal,
                                interactor_ordinal=interactor_ordinal,
                                writer=interactor_writer,
                            )
                            global_counts["interactors"] += 1
                            current_member_counts["interactors"] += 1
                        if parent == "interactorList":
                            element.clear()
                    elif local == "interaction":
                        interaction_ordinal += 1
                        parsed_interaction = _parse_interaction(element, interactors)
                        emitted = _emit_interaction(
                            parsed=parsed_interaction,
                            experiments=experiments,
                            context=context,
                            cfg=cfg,
                            asset=asset,
                            member=info.filename,
                            entry_ordinal=entry_ordinal,
                            interaction_ordinal=interaction_ordinal,
                            xml_release_date=xml_release_date,
                            evidence_writer=evidence_writer,
                            participant_writer=participant_writer,
                            feature_writer=feature_writer,
                        )
                        global_counts["source_interactions"] += 1
                        global_counts["evidence_records"] += len(emitted)
                        current_member_counts["source_interactions"] += 1
                        current_member_counts["evidence_records"] += len(emitted)
                        for record in emitted:
                            global_counts["negative_records"] += int(record["negative"])
                            global_counts["original_nary_records"] += int(
                                record["original_nary"]
                            )
                            global_counts["expanded_records"] += int(record["expanded"])
                            global_counts["binary_two_protein_records"] += int(
                                record["all_protein_binary"]
                            )
                            semantic_counts[record["interaction_semantics"]] += 1
                            participant_count_distribution[
                                str(record["participant_count"])
                            ] += 1
                        element.clear()
                    elif local == "entry":
                        element.clear()
                    stack.pop()
            member_stats[info.filename] = {
                "uncompressed_bytes": info.file_size,
                "compressed_bytes": info.compress_size,
                **dict(current_member_counts),
            }

    return {
        "archive_member_count": len(member_stats),
        "counts": dict(global_counts),
        "interaction_semantics": dict(sorted(semantic_counts.items())),
        "participant_count_distribution": dict(
            sorted(
                participant_count_distribution.items(), key=lambda item: int(item[0])
            )
        ),
        "members": member_stats,
        "tables": {
            "evidence_records": evidence_writer.summary(),
            "participants": participant_writer.summary(),
            "participant_features": feature_writer.summary(),
            "interactors": interactor_writer.summary(),
            "experiments": experiment_writer.summary(),
        },
    }


def _parse_obo(
    context: ParsingContext, output_root: Path, cfg: dict[str, Any]
) -> dict[str, Any]:
    asset = context.asset(str(cfg["cv_asset_id"]))
    writer = ParquetBatchWriter(
        output_root / "controlled_vocabulary_terms",
        context.staging_contract,
        "controlled_vocabulary_terms",
        **context.writer_kwargs(),
    )
    stanza: str | None = None
    fields: dict[str, list[str]] = {}
    start_line = 0
    term_count = 0
    skipped_stanzas = Counter()

    def emit(end_line: int) -> None:
        nonlocal term_count
        if stanza != "Term":
            if stanza:
                skipped_stanzas[stanza] += 1
            return
        term_ids = fields.get("id", [])
        if len(term_ids) != 1:
            raise ValueError(f"OBO term at line {start_line} has {len(term_ids)} IDs")
        term_id = term_ids[0]
        writer.append(
            {
                "term_record_id": stable_id("intact-cv", asset.sha256, start_line),
                "source_key": "intact_imex",
                "source_release": str(cfg["source_release"]),
                "term_id": term_id,
                "term_name": (fields.get("name") or [None])[0],
                "namespace": (fields.get("namespace") or [None])[0],
                "definition": (fields.get("def") or [None])[0],
                "synonyms": fields.get("synonym", []),
                "parent_terms": fields.get("is_a", []),
                "relationships": fields.get("relationship", []),
                "obsolete": (fields.get("is_obsolete") or ["false"])[0].casefold()
                == "true",
                "raw_file_path": asset.relative_path,
                "raw_file_sha256": asset.sha256,
                "raw_locator": f"lines:{start_line}-{end_line}",
                "fields_json": canonical_json(fields),
            }
        )
        term_count += 1

    with writer, asset.path.open("rt", encoding="utf-8", newline="") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.rstrip("\r\n")
            if stripped.startswith("[") and stripped.endswith("]"):
                emit(line_number - 1)
                stanza = stripped[1:-1]
                fields = {}
                start_line = line_number
            elif (
                stanza and stripped and not stripped.startswith("!") and ":" in stripped
            ):
                key, value = stripped.split(":", 1)
                fields.setdefault(key, []).append(value.strip())
        emit(line_number)
    return {
        "term_count": term_count,
        "skipped_stanzas": dict(skipped_stanzas),
        "table": writer.summary(),
    }


def _parse_mutations(
    context: ParsingContext, output_root: Path, cfg: dict[str, Any]
) -> dict[str, Any]:
    asset = context.asset(str(cfg["mutations_asset_id"]))
    writer = ParquetBatchWriter(
        output_root / "mutations",
        context.staging_contract,
        "intact_mutations",
        **context.writer_kwargs(),
    )
    with writer, asset.path.open("rt", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("IntAct mutation table lacks a header")
        reader.fieldnames = [name.lstrip("#") for name in reader.fieldnames]
        for data_ordinal, row in enumerate(reader, start=1):
            line_number = data_ordinal + 1
            feature_ac = row["Feature AC"]
            interaction_ac = row["Interaction AC"]
            if not feature_ac or not interaction_ac:
                raise ValueError(
                    f"IntAct mutation line {line_number} lacks feature/interaction AC"
                )
            participants = [
                token for token in row["Interaction participants"].split("|") if token
            ]
            writer.append(
                {
                    "mutation_record_id": stable_id(
                        "intact-mutation", asset.sha256, line_number
                    ),
                    "source_release": str(cfg["source_release"]),
                    "feature_ac": feature_ac,
                    "feature_short_label": row["Feature short label"] or None,
                    "feature_ranges": row["Feature range(s)"] or None,
                    "original_sequence": row["Original sequence"] or None,
                    "resulting_sequence": row["Resulting sequence"] or None,
                    "feature_type": row["Feature type"] or None,
                    "feature_annotation": row["Feature annotation"] or None,
                    "affected_protein_ac": row["Affected protein AC"] or None,
                    "affected_protein_symbol": row["Affected protein symbol"] or None,
                    "affected_protein_name": row["Affected protein full name"] or None,
                    "affected_protein_organism": row["Affected protein organism"]
                    or None,
                    "interaction_participants": participants,
                    "publication_id": row["PubMedID"] or None,
                    "figure_legend": row["Figure legend"] or None,
                    "interaction_ac": interaction_ac,
                    "raw_file_path": asset.relative_path,
                    "raw_file_sha256": asset.sha256,
                    "raw_locator": f"line:{line_number}",
                    "fields_json": canonical_json(row),
                }
            )
    return {"table": writer.summary()}


def parse_intact(context: ParsingContext, output_root: Path) -> dict[str, Any]:
    cfg = dict(context.config["sources"]["intact_imex"])
    xml = _parse_psi_xml_archive(context, output_root, cfg)
    obo = _parse_obo(context, output_root, cfg)
    mutations = _parse_mutations(context, output_root, cfg)
    return {
        "source": "intact_imex",
        "release": str(cfg["source_release"]),
        "psi_xml": xml,
        "controlled_vocabulary": obo,
        "mutations": mutations,
    }
