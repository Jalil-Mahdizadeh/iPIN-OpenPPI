from ipin_openppi.lambourne_audit.source import (
    parse_raw_assay_records,
    parse_selection_records,
)


def test_selection_parser_preserves_orientation_and_forbidden_flags() -> None:
    rows = parse_selection_records(
        b"ad_orf_id\tdb_orf_id\tsource\n2\t1\tZhang_et_al\n",
        member_path="archive/table.tsv",
        member_sha256="a" * 64,
    )
    assert rows[0]["ad_orf_id"] == "2"
    assert rows[0]["db_orf_id"] == "1"
    assert rows[0]["original_selection_candidate"]
    assert not rows[0]["outcome_training_label_authorized"]
    assert not rows[0]["universal_nonbinding_asserted"]


def test_raw_parser_does_not_collapse_failed_sequence_confirmation() -> None:
    payload = (
        b"db_orf_id\tad_orf_id\tcategory\tfinal_score\t"
        b"seq_confirmation_final_3at\tseq_confirmation_final_lw\n"
        b"1\t2\tZhang_et_al\t0\t\t0\n"
    )
    rows = parse_raw_assay_records(
        payload, member_path="archive/raw.tsv", member_sha256="b" * 64
    )
    assert rows[0]["derived_reported_outcome"] == "Failed sequence confirmation"
