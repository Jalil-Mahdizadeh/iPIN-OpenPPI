from __future__ import annotations

import gzip
from pathlib import Path
import xml.etree.ElementTree as ET

import pyarrow.parquet as pq
import pytest

from ipin_openppi.ingestion.common import ParquetBatchWriter, stable_id
from ipin_openppi.ingestion.huri import (
    _feature_parts,
    _interaction_semantics as huri_interaction_semantics,
    _parse_identifier,
    _parse_term,
)
from ipin_openppi.ingestion.intact import (
    _interaction_semantics as intact_interaction_semantics,
    _parse_experiment,
    _parse_interaction,
    _parse_interactor,
)
from ipin_openppi.ingestion.schema import ContractError, load_contract
from ipin_openppi.ingestion.sifts import _optional_int
from ipin_openppi.ingestion.uniprot import (
    _parse_fasta_header,
    iter_fasta,
    parse_dat_metadata,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_schema_contract_rejects_bad_enum_and_missing_required() -> None:
    contract = load_contract(
        PROJECT_ROOT / "schemas/warehouse/evidence_warehouse_v1.yaml"
    )
    valid = {
        "pair_view_id": "pv:1",
        "source_key": "huri",
        "source_dataset": "HuRI",
        "source_release": "published_2020",
        "source_record_ordinal": 1,
        "member_a": "ENSG1",
        "member_b": "ENSG2",
        "unordered_pair_id": "pair:1",
        "view_membership": True,
        "provider_claim": "reported_interaction_pair",
        "label_authorized": False,
        "self_pair": False,
        "duplicate_ordinal": 0,
        "raw_file_path": "data/raw/example.tsv",
        "raw_file_sha256": "a" * 64,
        "raw_locator": "line:1",
        "source_fields_json": "{}",
    }
    assert contract.normalize_and_validate_rows("source_pair_views", [valid])[0]
    missing = dict(valid)
    missing["pair_view_id"] = None
    with pytest.raises(ContractError, match="null required"):
        contract.normalize_and_validate_rows("source_pair_views", [missing])

    evidence_schema = contract.arrow_schema("evidence_records")
    assert evidence_schema.metadata[b"ipin.schema_sha256"] == contract.sha256.encode()


def test_parquet_writer_embeds_contract_and_preserves_no_label_guard(
    tmp_path: Path,
) -> None:
    contract = load_contract(
        PROJECT_ROOT / "schemas/warehouse/evidence_warehouse_v1.yaml"
    )
    output = tmp_path / "pair_views"
    writer = ParquetBatchWriter(
        output,
        contract,
        "source_pair_views",
        batch_rows=1,
        compression="zstd",
        compression_level=3,
    )
    with writer:
        writer.append(
            {
                "pair_view_id": "pv:1",
                "source_key": "huri",
                "source_dataset": "HuRI",
                "source_release": "published_2020",
                "source_record_ordinal": 1,
                "member_a": "ENSG1",
                "member_b": "ENSG2",
                "unordered_pair_id": "pair:1",
                "view_membership": True,
                "provider_claim": "reported_interaction_pair",
                "label_authorized": False,
                "self_pair": False,
                "duplicate_ordinal": 0,
                "raw_file_path": "data/raw/example.tsv",
                "raw_file_sha256": "a" * 64,
                "raw_locator": "line:1",
                "source_fields_json": "{}",
            }
        )
    table = pq.read_table(output)
    assert table.num_rows == 1
    assert table.column("label_authorized").to_pylist() == [False]
    assert table.schema.metadata[b"ipin.table_name"] == b"source_pair_views"


def test_stable_id_is_framed_and_deterministic() -> None:
    assert stable_id("x", "ab", "c") == stable_id("x", "ab", "c")
    assert stable_id("x", "ab", "c") != stable_id("x", "a", "bc")


def test_uniprot_dat_and_fasta_parsing(tmp_path: Path) -> None:
    dat = tmp_path / "minimal.dat.gz"
    dat_text = """ID   TEST_HUMAN             Reviewed;           4 AA.
AC   P00001;
DT   01-JAN-2000, integrated into UniProtKB/Swiss-Prot.
DT   02-JAN-2000, sequence version 2.
DT   03-JAN-2000, entry version 7.
DE   RecName: Full=Test protein;
GN   Name=TEST1; Synonyms=TEST2,TEST3;
OX   NCBI_TaxID=9606;
SQ   SEQUENCE   4 AA;  400 MW;  ABC CRC64;
     MAAA
//
"""
    with gzip.open(dat, "wt", encoding="utf-8") as handle:
        handle.write(dat_text)
    metadata, stats = parse_dat_metadata(dat)
    assert stats == {"entries": 1}
    assert metadata["P00001"]["sequence"] == "MAAA"
    assert metadata["P00001"]["gene_names"] == ["TEST1", "TEST2", "TEST3"]
    assert metadata["P00001"]["sequence_version"] == 2
    assert metadata["P00001"]["entry_version"] == 7

    fasta = tmp_path / "minimal.fasta.gz"
    with gzip.open(fasta, "wt", encoding="utf-8") as handle:
        handle.write(
            ">sp|P00001|TEST_HUMAN Test protein OS=Homo sapiens OX=9606 GN=TEST1 PE=1 SV=2\nMA\nAA\n"
        )
    records = list(iter_fasta(fasta))
    assert records == [
        (
            1,
            "sp|P00001|TEST_HUMAN Test protein OS=Homo sapiens OX=9606 GN=TEST1 PE=1 SV=2",
            "MAAA",
        )
    ]
    parsed = _parse_fasta_header(records[0][1])
    assert parsed["accession"] == "P00001"
    assert parsed["taxid"] == 9606
    assert parsed["gene_names"] == ["TEST1"]


def test_huri_mitab_primitives_are_conservative() -> None:
    assert _parse_term("psi-mi:MI:0397(two hybrid array)") == (
        "MI:0397",
        "two hybrid array",
    )
    assert _parse_identifier("uniprotkb:P12345-2") == (
        "uniprotkb",
        "P12345-2",
    )
    features = _feature_parts("gal4 dna binding domain:n-n (N-terminal)|tag:4-8")
    assert features[0]["start"] is None
    assert features[1]["start"] == 4
    assert features[1]["end"] == 8
    semantics, flags = huri_interaction_semantics(2, "two hybrid array", "MI:0915", "-")
    assert semantics == "direct_binary"
    assert "source_term_physical_association_classified_binary_y2h" in flags


INTACT_XML = """<entrySet xmlns="http://psi.hupo.org/mi/mif300">
  <entry>
    <experimentList>
      <experimentDescription id="1">
        <bibref><xref><primaryRef db="pubmed" id="123"/></xref></bibref>
        <hostOrganismList><hostOrganism ncbiTaxId="4932"><names><shortLabel>yeast</shortLabel></names></hostOrganism></hostOrganismList>
        <interactionDetectionMethod><names><shortLabel>two hybrid</shortLabel></names><xref><primaryRef db="psi-mi" id="MI:0018"/></xref></interactionDetectionMethod>
        <participantIdentificationMethod><names><shortLabel>predetermined</shortLabel></names><xref><primaryRef db="psi-mi" id="MI:0396"/></xref></participantIdentificationMethod>
      </experimentDescription>
    </experimentList>
    <interactorList>
      <interactor id="2"><names><shortLabel>a_human</shortLabel></names><xref><primaryRef db="uniprotkb" id="P00001"/></xref><interactorType><names><shortLabel>protein</shortLabel></names><xref><primaryRef db="psi-mi" id="MI:0326"/></xref></interactorType><organism ncbiTaxId="9606"><names><shortLabel>human</shortLabel></names></organism><sequence>MAAA</sequence></interactor>
      <interactor id="3"><names><shortLabel>b_human</shortLabel></names><xref><primaryRef db="uniprotkb" id="P00002"/></xref><interactorType><names><shortLabel>protein</shortLabel></names><xref><primaryRef db="psi-mi" id="MI:0326"/></xref></interactorType><organism ncbiTaxId="9606"><names><shortLabel>human</shortLabel></names></organism><sequence>MBBB</sequence></interactor>
    </interactorList>
    <interactionList>
      <interaction id="4">
        <xref><primaryRef db="intact" id="EBI-1"/></xref>
        <experimentList><experimentRef>1</experimentRef></experimentList>
        <participantList>
          <participant id="5"><interactorRef>2</interactorRef><biologicalRole><names><shortLabel>unspecified role</shortLabel></names><xref><primaryRef db="psi-mi" id="MI:0499"/></xref></biologicalRole><experimentalRoleList><experimentalRole><names><shortLabel>bait</shortLabel></names><xref><primaryRef db="psi-mi" id="MI:0496"/></xref></experimentalRole></experimentalRoleList></participant>
          <participant id="6"><interactorRef>3</interactorRef><biologicalRole><names><shortLabel>unspecified role</shortLabel></names><xref><primaryRef db="psi-mi" id="MI:0499"/></xref></biologicalRole><experimentalRoleList><experimentalRole><names><shortLabel>prey</shortLabel></names><xref><primaryRef db="psi-mi" id="MI:0498"/></xref></experimentalRole></experimentalRoleList></participant>
        </participantList>
        <interactionType><names><shortLabel>direct interaction</shortLabel></names><xref><primaryRef db="psi-mi" id="MI:0407"/></xref></interactionType>
        <negative>true</negative>
      </interaction>
    </interactionList>
  </entry>
</entrySet>"""


def test_intact_xml_primitives_preserve_negative_and_binary_semantics() -> None:
    root = ET.fromstring(INTACT_XML)
    local = lambda element: element.tag.rsplit("}", 1)[-1]
    experiment_element = next(
        e for e in root.iter() if local(e) == "experimentDescription"
    )
    interactor_elements = [e for e in root.iter() if local(e) == "interactor"]
    interaction_element = next(e for e in root.iter() if local(e) == "interaction")
    experiment = _parse_experiment(experiment_element)
    assert experiment["publication_ids"] == ["pubmed:123"]
    assert experiment["detection_method_ac"] == "MI:0018"
    interactors = {
        parsed["source_interactor_id"]: parsed
        for parsed in map(_parse_interactor, interactor_elements)
    }
    parsed_interaction = _parse_interaction(interaction_element, interactors)
    assert parsed_interaction["negative"] is True
    assert len(parsed_interaction["participants"]) == 2
    assert intact_interaction_semantics("MI:0407", "direct interaction", 2) == (
        "direct_binary"
    )
    assert interactors["2"]["sequence_sha256"] is not None


def test_sifts_optional_integer_does_not_coerce_missing() -> None:
    assert _optional_int("42") == 42
    assert _optional_int("None") is None
    assert _optional_int("-") is None
    with pytest.raises(ValueError):
        _optional_int("4A")
