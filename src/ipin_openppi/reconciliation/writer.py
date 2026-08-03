"""Deterministic Arrow/Parquet output for DuckDB reconciliation queries."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from ipin_openppi.ingestion.schema import SchemaContract, sha256_file


class ArrowQueryDatasetWriter:
    """Stream a DuckDB query into fixed-schema, checksummed Parquet parts."""

    def __init__(
        self,
        *,
        connection: duckdb.DuckDBPyConnection,
        query: str,
        output_dir: Path,
        contract: SchemaContract,
        table_name: str,
        batch_rows: int,
        compression: str,
        compression_level: int | None,
    ) -> None:
        self.connection = connection
        self.query = query
        self.output_dir = output_dir
        self.contract = contract
        self.table_name = table_name
        self.batch_rows = batch_rows
        self.compression = compression
        self.compression_level = compression_level

    def _normalize(self, batch: pa.RecordBatch) -> pa.Table:
        expected = self.contract.arrow_schema(self.table_name)
        table = pa.Table.from_batches([batch])
        if table.column_names != expected.names:
            raise RuntimeError(
                f"{self.table_name} query columns differ from contract: "
                f"{table.column_names} != {expected.names}"
            )
        target_without_metadata = pa.schema(list(expected))
        table = table.cast(target_without_metadata, safe=True)
        for field, column in zip(expected, table.columns, strict=True):
            if not field.nullable and column.null_count:
                raise RuntimeError(
                    f"{self.table_name}.{field.name} has {column.null_count} nulls"
                )
        return table.replace_schema_metadata(expected.metadata)

    def write(self) -> dict[str, Any]:
        self.output_dir.mkdir(parents=True, exist_ok=False)
        reader = self.connection.execute(self.query).fetch_record_batch(
            rows_per_batch=self.batch_rows
        )
        files: list[dict[str, Any]] = []
        row_count = 0
        for part_number, batch in enumerate(reader):
            table = self._normalize(batch)
            path = self.output_dir / f"part-{part_number:05d}.parquet"
            pq.write_table(
                table,
                path,
                compression=self.compression,
                compression_level=self.compression_level,
                use_dictionary=True,
                write_statistics=True,
                row_group_size=self.batch_rows,
            )
            files.append(
                {
                    "path": path.as_posix(),
                    "rows": table.num_rows,
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
            row_count += table.num_rows

        if not files:
            expected = self.contract.arrow_schema(self.table_name)
            table = pa.Table.from_arrays(
                [pa.array([], type=field.type) for field in expected],
                schema=expected,
            )
            path = self.output_dir / "part-00000.parquet"
            pq.write_table(
                table,
                path,
                compression=self.compression,
                compression_level=self.compression_level,
            )
            files.append(
                {
                    "path": path.as_posix(),
                    "rows": 0,
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )

        return {
            "table": self.table_name,
            "rows": row_count,
            "parts": len(files),
            "files": files,
            "schema_name": self.contract.name,
            "schema_version": self.contract.version,
            "schema_sha256": self.contract.sha256,
        }
