"""Load and enforce versioned Arrow table contracts."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any, Iterable, Mapping

import pyarrow as pa
import yaml


_PRIMITIVE_TYPES: dict[str, pa.DataType] = {
    "string": pa.string(),
    "int32": pa.int32(),
    "int64": pa.int64(),
    "float64": pa.float64(),
    "bool": pa.bool_(),
}


class ContractError(ValueError):
    """Raised when a schema contract or row violates the frozen contract."""


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _arrow_type(type_name: str) -> pa.DataType:
    if type_name in _PRIMITIVE_TYPES:
        return _PRIMITIVE_TYPES[type_name]
    if type_name == "list<string>":
        return pa.list_(pa.string())
    raise ContractError(f"Unsupported contract type: {type_name}")


@dataclass(frozen=True)
class SchemaContract:
    path: Path
    sha256: str
    document: Mapping[str, Any]

    @property
    def name(self) -> str:
        return str(self.document["schema_name"])

    @property
    def version(self) -> int:
        return int(self.document["schema_version"])

    def table_spec(self, table_name: str) -> Mapping[str, Any]:
        try:
            return self.document["tables"][table_name]
        except KeyError as exc:
            raise ContractError(
                f"Table {table_name!r} is not defined in {self.path}"
            ) from exc

    def arrow_schema(self, table_name: str) -> pa.Schema:
        spec = self.table_spec(table_name)
        fields = [
            pa.field(
                str(column["name"]),
                _arrow_type(str(column["type"])),
                nullable=bool(column.get("nullable", True)),
            )
            for column in spec["columns"]
        ]
        metadata = {
            b"ipin.schema_name": self.name.encode(),
            b"ipin.schema_version": str(self.version).encode(),
            b"ipin.schema_sha256": self.sha256.encode(),
            b"ipin.schema_path": self.path.as_posix().encode(),
            b"ipin.table_name": table_name.encode(),
        }
        return pa.schema(fields, metadata=metadata)

    def normalize_and_validate_rows(
        self, table_name: str, rows: Iterable[Mapping[str, Any]]
    ) -> list[dict[str, Any]]:
        spec = self.table_spec(table_name)
        columns = [str(column["name"]) for column in spec["columns"]]
        column_set = set(columns)
        required = set(spec.get("required_non_null", []))
        enum_columns = spec.get("enum_columns", {})
        enums = self.document.get("enums", {})
        normalized: list[dict[str, Any]] = []

        for row_number, source_row in enumerate(rows, start=1):
            unexpected = set(source_row) - column_set
            if unexpected:
                raise ContractError(
                    f"{table_name} row {row_number} has unexpected fields: "
                    f"{sorted(unexpected)}"
                )
            row = {column: source_row.get(column) for column in columns}
            missing_required = [name for name in required if row.get(name) is None]
            if missing_required:
                raise ContractError(
                    f"{table_name} row {row_number} has null required fields: "
                    f"{sorted(missing_required)}"
                )
            for column, enum_name in enum_columns.items():
                value = row.get(column)
                allowed = enums.get(enum_name)
                if allowed is None:
                    raise ContractError(
                        f"{table_name}.{column} references undefined enum {enum_name}"
                    )
                if value is not None and value not in allowed:
                    raise ContractError(
                        f"{table_name}.{column}={value!r} is outside enum {enum_name}"
                    )
            normalized.append(row)
        return normalized


def load_contract(path: Path) -> SchemaContract:
    resolved = path.resolve(strict=True)
    with resolved.open("rt", encoding="utf-8") as handle:
        document = yaml.safe_load(handle)
    if not isinstance(document, dict):
        raise ContractError(f"Schema contract is not a mapping: {resolved}")
    for key in ("schema_name", "schema_version", "tables"):
        if key not in document:
            raise ContractError(f"Schema contract lacks {key}: {resolved}")
    return SchemaContract(path=path, sha256=sha256_file(resolved), document=document)
