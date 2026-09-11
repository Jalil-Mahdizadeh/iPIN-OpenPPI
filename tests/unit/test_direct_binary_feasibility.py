"""Source triage must preserve missingness and never manufacture labels."""
import importlib.util
import sys
from pathlib import Path

import pytest


DATA_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts/data"


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, DATA_SCRIPTS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


acquisition = load_module("audit_direct_binary_feasibility_v1")
# Isolate the sibling import without changing any frozen production module.
sys.modules.setdefault("audit_direct_binary_feasibility_v1", acquisition)
structural = load_module("summarize_direct_binary_feasibility_v1")


def test_missing_is_not_zero():
    result = acquisition.csv_inventory(b"id,signal\na,0\nb,\nc,NA\nd,nan\ne,inf\n")
    assert result["columns"]["signal"] == {
        "unique_text_values": 5, "blank": 1, "finite_numeric": 1,
        "nonfinite_numeric_tokens": 2, "NA_tokens": 1,
    }


def test_explicit_encoding_fallback():
    result = acquisition.csv_inventory("id,note\na,\u00b1\n".encode("cp1252"))
    assert result["encoding"] == "cp1252"
    assert result["rows"] == 1


@pytest.mark.parametrize("data", [b"", b"a,a\n1,2\n", b"a,b\n1\n"])
def test_reject_malformed_tables(data):
    with pytest.raises(ValueError):
        acquisition.csv_inventory(data)


def test_no_overwrite(tmp_path):
    path = tmp_path / "raw.csv"
    acquisition.write_new(path, b"original")
    with pytest.raises(FileExistsError):
        acquisition.write_new(path, b"replacement")
    assert path.read_bytes() == b"original"


def test_blob_hash():
    assert acquisition.git_blob(b"") == "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"


def test_matrix_alias_rectangle_does_not_assert_QC_or_labels():
    matrix = [["", "A", "B", "control"], ["A", "0", "", "2"], ["control", "nan", "5", "6"]]
    result = structural.matrix_summary(matrix, {"A", "B"})
    assert result["cells_including_controls"] == 6
    assert result["finite_cells_including_controls"] == 4
    assert result["blank_cells_including_controls"] == 1
    assert result["other_nonfinite_cells"] == 1
    assert result["exact_alias_rectangle_cells_not_QC_filtered"] == 2
    assert result["exact_alias_rectangle_finite_cells_not_QC_filtered"] == 1
    assert result["not_a_negative_label_count"]
