#!/usr/bin/env python3
"""Fetch UniProt sequences and score ire1_ipin_panel2.csv with both frozen models.

The network-isolated model container requires two invocations. From the repository
root, first fetch a release-labelled UniProt snapshot to temporary storage::

    python3 example/score_ire1_ipin_panel2.py \
      --fetch-sequences /tmp/ire1_ipin_panel2_uniprot.json

Then embed and score those sequences in the checksum-pinned model SIF::

    apptainer exec --cleanenv --containall --no-home --nv \
      --bind "$PWD:/project:ro" --bind "$PWD/example:/project/example:rw" \
      --bind /tmp/ire1_ipin_panel2_uniprot.json:/uniprot.json:ro \
      --pwd /project containers/images/ipin-model-arm64_0.1.0.sif \
      python example/score_ire1_ipin_panel2.py \
      --sequence-snapshot /uniprot.json

Scores are raw ranking scores, not probabilities or calibrated predictions.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


UNIPROT_API = "https://rest.uniprot.org/uniprotkb"
USER_AGENT = "iPIN-OpenPPI-example/1.0"
ACCESSION_PATTERN = re.compile(
    r"(?:[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})"
)
ALLOWED_RESIDUES = frozenset("ACDEFGHIKLMNPQRSTVWYBXZUO")
REQUIRED_COLUMNS = ("query_uniprot", "partner_uniprot")
PROVENANCE_COLUMNS = (
    "query_primary_uniprot",
    "query_sequence_length",
    "query_sequence_sha256",
    "partner_primary_uniprot",
    "partner_sequence_length",
    "partner_sequence_sha256",
    "uniprot_release",
    "uniprot_release_date",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def read_pairs(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        missing = [column for column in REQUIRED_COLUMNS if column not in columns]
        if missing:
            raise RuntimeError(f"input CSV is missing columns: {', '.join(missing)}")
        rows = list(reader)
    if not rows:
        raise RuntimeError("input CSV contains no protein pairs")
    for row_number, row in enumerate(rows, start=2):
        for column in REQUIRED_COLUMNS:
            row[column] = row[column].strip().upper()
            if not ACCESSION_PATTERN.fullmatch(row[column]):
                raise RuntimeError(f"invalid {column} at CSV row {row_number}: {row[column]!r}")
    return rows, columns


def request_json(url: str) -> tuple[dict[str, Any], dict[str, str]]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    last_error: Exception | None = None
    for attempt in range(5):
        try:
            with urlopen(request, timeout=60) as response:
                payload = json.load(response)
                metadata = {
                    "release": response.headers.get("X-UniProt-Release", ""),
                    "release_date": response.headers.get("X-UniProt-Release-Date", ""),
                    "api_deployment_date": response.headers.get("X-API-Deployment-Date", ""),
                }
            if not metadata["release"] or not metadata["release_date"]:
                raise RuntimeError("UniProt response omitted release headers")
            return payload, metadata
        except HTTPError as error:
            last_error = error
            if error.code not in (429, 500, 502, 503, 504):
                raise RuntimeError(f"UniProt request failed with HTTP {error.code}: {url}") from error
            retry_after = error.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else 2.0**attempt
        except URLError as error:
            last_error = error
            delay = 2.0**attempt
        if attempt < 4:
            time.sleep(delay)
    raise RuntimeError(f"UniProt request failed after retries: {url}") from last_error


def sequence_record(requested: str, entry: dict[str, Any]) -> dict[str, Any]:
    primary = str(entry["primaryAccession"])
    organism = entry.get("organism", {})
    if int(organism.get("taxonId", -1)) != 9606:
        raise RuntimeError(f"UniProt accession {requested} is not a human protein")
    sequence_data = entry["sequence"]
    sequence = str(sequence_data["value"]).upper()
    length = int(sequence_data["length"])
    if not sequence or len(sequence) != length:
        raise RuntimeError(f"UniProt sequence length mismatch for {requested}")
    unexpected = sorted(set(sequence) - ALLOWED_RESIDUES)
    if unexpected:
        raise RuntimeError(f"unsupported UniProt residues for {requested}: {''.join(unexpected)}")
    return {
        "requested_accession": requested,
        "primary_accession": primary,
        "taxon_id": 9606,
        "sequence": sequence,
        "sequence_length": length,
        "sequence_sha256": sha256_bytes(sequence.encode("ascii")),
    }


def fetch_uniprot(accessions: list[str]) -> dict[str, Any]:
    records: dict[str, dict[str, Any]] = {}
    response_metadata: dict[str, str] | None = None

    def accept_metadata(observed: dict[str, str]) -> None:
        nonlocal response_metadata
        if response_metadata is None:
            response_metadata = observed
        elif observed != response_metadata:
            raise RuntimeError("UniProt release metadata changed during sequence retrieval")

    for start in range(0, len(accessions), 40):
        chunk = accessions[start : start + 40]
        query_text = "(" + " OR ".join(f"accession:{accession}" for accession in chunk) + ")"
        parameters = urlencode(
            {
                "query": query_text,
                "format": "json",
                "fields": "accession,sequence,organism_id",
                "size": "500",
            }
        )
        payload, metadata = request_json(f"{UNIPROT_API}/search?{parameters}")
        accept_metadata(metadata)
        for entry in payload.get("results", []):
            primary = str(entry["primaryAccession"])
            if primary in chunk:
                records[primary] = sequence_record(primary, entry)

    # Direct entry retrieval also resolves valid secondary accessions and records
    # the current primary accession returned by UniProt.
    for accession in sorted(set(accessions) - set(records)):
        fields = urlencode({"fields": "accession,sequence,organism_id"})
        payload, metadata = request_json(f"{UNIPROT_API}/{quote(accession, safe='')}.json?{fields}")
        accept_metadata(metadata)
        records[accession] = sequence_record(accession, payload)

    if set(records) != set(accessions):
        missing = sorted(set(accessions) - set(records))
        raise RuntimeError(f"UniProt did not return all requested accessions: {missing}")
    assert response_metadata is not None
    body = {
        "schema_version": 1,
        "source": "UniProtKB REST API",
        "source_base_url": UNIPROT_API,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "uniprot_release": response_metadata["release"],
        "uniprot_release_date": response_metadata["release_date"],
        "uniprot_api_deployment_date": response_metadata["api_deployment_date"],
        "records": {accession: records[accession] for accession in sorted(records)},
    }
    return {**body, "snapshot_sha256": sha256_bytes(canonical_json(body))}


def write_snapshot(path: Path, snapshot: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(snapshot, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def read_snapshot(path: Path, accessions: set[str]) -> dict[str, Any]:
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    digest = snapshot.pop("snapshot_sha256", None)
    if digest != sha256_bytes(canonical_json(snapshot)):
        raise RuntimeError("UniProt sequence snapshot checksum mismatch")
    if snapshot.get("source_base_url") != UNIPROT_API or snapshot.get("schema_version") != 1:
        raise RuntimeError("unexpected UniProt sequence snapshot format")
    records = snapshot.get("records", {})
    if set(records) != accessions:
        raise RuntimeError("UniProt snapshot accessions differ from the input CSV")
    for accession, record in records.items():
        if record.get("requested_accession") != accession or record.get("taxon_id") != 9606:
            raise RuntimeError(f"invalid UniProt identity record for {accession}")
        sequence = record.get("sequence", "")
        if (
            not sequence
            or len(sequence) != record.get("sequence_length")
            or sha256_bytes(sequence.encode("ascii")) != record.get("sequence_sha256")
        ):
            raise RuntimeError(f"UniProt sequence snapshot drift for {accession}")
    snapshot["snapshot_sha256"] = digest
    return snapshot


def score(
    project_root: Path,
    rows: list[dict[str, str]],
    columns: list[str],
    snapshot: dict[str, Any],
    output_path: Path,
) -> None:
    import numpy as np
    import torch

    sys.path.insert(0, str(project_root / "src"))
    from ipin_openppi.stage1 import embeddings as embedding_source

    import score_frozen_models as frozen

    bundle = project_root / ".private/frozen_pair_models_v1/bundle"
    registry = frozen.load_registry(project_root, bundle)
    bundle_records = {item["path"]: item for item in registry["bundle_files"]}

    # Verify all encoder files and the preserved embedding implementation before
    # using the live import of that byte-identical source file.
    for relative, record in bundle_records.items():
        if relative.startswith("encoder/"):
            frozen.checked_file(bundle, record)
    preserved_embedding_source = frozen.checked_file(bundle, bundle_records["code/embeddings.py"])
    live_embedding_source = project_root / "src/ipin_openppi/stage1/embeddings.py"
    if frozen.sha256_file(live_embedding_source) != frozen.sha256_file(preserved_embedding_source):
        raise RuntimeError("live embedding source differs from the frozen preserved copy")

    unique_sequences: dict[str, str] = {}
    for record in snapshot["records"].values():
        digest = record["sequence_sha256"]
        sequence = record["sequence"]
        if digest in unique_sequences and unique_sequences[digest] != sequence:
            raise RuntimeError("sequence SHA-256 collision in UniProt snapshot")
        unique_sequences[digest] = sequence
    sequence_records = sorted(
        (
            embedding_source.SequenceRecord(digest, sequence, len(sequence))
            for digest, sequence in unique_sequences.items()
        ),
        key=lambda record: (record.sequence_length, record.sequence_sha256),
    )
    raw_matrix, metadata = embedding_source.extract_matrix(
        candidate_id="esm2_150m",
        records=sequence_records,
        model_root=bundle / "encoder",
    )

    normalizer_path = frozen.checked_file(
        bundle, registry["shared_inputs"]["training_normalization.npz"]
    )
    with np.load(normalizer_path, allow_pickle=False) as normalizer:
        mean = normalizer["mean"].copy()
        standard_deviation = normalizer["standard_deviation"].copy()
    if (
        mean.shape != (640,)
        or standard_deviation.shape != (640,)
        or mean.dtype != np.float64
        or standard_deviation.dtype != np.float64
        or not np.isfinite(mean).all()
        or not np.isfinite(standard_deviation).all()
        or np.any(standard_deviation < 1e-6)
    ):
        raise RuntimeError("frozen training normalizer drift")
    standardized = (
        (raw_matrix.astype(np.float64) - mean) / standard_deviation
    ).astype(np.float32)
    if not np.isfinite(standardized).all():
        raise RuntimeError("nonfinite standardized UniProt embeddings")
    vector_by_digest = {
        record.sequence_sha256: standardized[index]
        for index, record in enumerate(sequence_records)
    }
    records = snapshot["records"]
    left = torch.from_numpy(
        np.stack(
            [vector_by_digest[records[row["query_uniprot"]]["sequence_sha256"]] for row in rows]
        ).copy()
    )
    right = torch.from_numpy(
        np.stack(
            [vector_by_digest[records[row["partner_uniprot"]]["sequence_sha256"]] for row in rows]
        ).copy()
    )
    features = frozen.pair_features(left, right)
    optimized = frozen.ensemble_scores(features, bundle, registry, frozen.BEST_MODEL)
    baseline = frozen.ensemble_scores(features, bundle, registry, frozen.BASELINE_MODEL)

    added_columns = [*PROVENANCE_COLUMNS, "optimized_score", "baseline_score"]
    collisions = sorted(set(columns) & set(added_columns))
    if collisions:
        raise RuntimeError(f"output columns already exist in input CSV: {collisions}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(output_path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[*columns, *added_columns],
            lineterminator="\n",
        )
        writer.writeheader()
        for row, optimized_score, baseline_score in zip(rows, optimized, baseline, strict=True):
            query = records[row["query_uniprot"]]
            partner = records[row["partner_uniprot"]]
            writer.writerow(
                {
                    **row,
                    "query_primary_uniprot": query["primary_accession"],
                    "query_sequence_length": query["sequence_length"],
                    "query_sequence_sha256": query["sequence_sha256"],
                    "partner_primary_uniprot": partner["primary_accession"],
                    "partner_sequence_length": partner["sequence_length"],
                    "partner_sequence_sha256": partner["sequence_sha256"],
                    "uniprot_release": snapshot["uniprot_release"],
                    "uniprot_release_date": snapshot["uniprot_release_date"],
                    "optimized_score": format(float(optimized_score), ".17g"),
                    "baseline_score": format(float(baseline_score), ".17g"),
                }
            )
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, output_path)
    print(
        f"Embedded {len(sequence_records)} unique UniProt sequences in "
        f"{metadata['batches']} batches and scored {len(rows)} pairs."
    )
    print(
        f"UniProt release {snapshot['uniprot_release']} "
        f"({snapshot['uniprot_release_date']}); wrote {output_path}"
    )


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=script_dir / "ire1_ipin_panel2.csv")
    parser.add_argument("--output", type=Path, default=script_dir / "ire1_ipin_panel2_scores.csv")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--fetch-sequences",
        type=Path,
        metavar="SNAPSHOT_JSON",
        help="fetch current canonical sequences from UniProt and stop",
    )
    mode.add_argument(
        "--sequence-snapshot",
        type=Path,
        metavar="SNAPSHOT_JSON",
        help="embed and score a temporary snapshot produced by --fetch-sequences",
    )
    args = parser.parse_args()
    input_path = args.input.resolve()
    output_path = args.output.resolve()
    rows, columns = read_pairs(input_path)
    accessions = sorted(
        {row[column] for row in rows for column in REQUIRED_COLUMNS}
    )

    if args.fetch_sequences is not None:
        snapshot = fetch_uniprot(accessions)
        target = args.fetch_sequences.resolve()
        write_snapshot(target, snapshot)
        print(
            f"Fetched {len(accessions)} human sequences from UniProt release "
            f"{snapshot['uniprot_release']} ({snapshot['uniprot_release_date']})."
        )
        print(f"Wrote temporary sequence snapshot {target}")
        return

    if input_path == output_path:
        raise RuntimeError("input and output CSV paths must differ")
    snapshot = read_snapshot(args.sequence_snapshot.resolve(), set(accessions))
    score(project_root, rows, columns, snapshot, output_path)


if __name__ == "__main__":
    main()
