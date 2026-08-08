"""Sealed development release and one-first protected-test evaluator harness."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import tempfile
from typing import Any, Iterable, Mapping, Sequence

import duckdb
import numpy as np
import pyarrow.parquet as pq

from ipin_openppi.ingestion.common import AtomicDatasetDirectory, project_root_from
from ipin_openppi.ingestion.schema import sha256_file
from ipin_openppi.sequence_component_audit.support import write_manifest

from .support import (
    PACKAGE_ID,
    cms_decrypt,
    extract_verified_tar,
    load_json,
    load_yaml,
    private_key_paths,
    reject_symlink_components,
    resolve_inside,
    validate_config,
    verify_documents,
)


SCORER_INPUT_COLUMNS = (
    "candidate_token",
    "endpoint_a_sha256",
    "endpoint_b_sha256",
    "cell_id",
)


def _timestamp() -> str:
    from datetime import timezone

    return datetime.now(timezone.utc).isoformat()


def _require_regular(path: Path) -> Path:
    candidate = path if path.is_absolute() else Path.cwd() / path
    lexical = reject_symlink_components(candidate, stop=Path(candidate.anchor))
    info = lexical.stat(follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode):
        raise RuntimeError("Expected a regular non-link file")
    return lexical.resolve(strict=True)


def _require_private_workspace(project_root: Path, path: Path, *, exists: bool) -> Path:
    lexical_boundary = project_root / ".private"
    reject_symlink_components(lexical_boundary, stop=project_root)
    boundary = lexical_boundary.resolve(strict=True)
    candidate = path if path.is_absolute() else project_root / path
    lexical = reject_symlink_components(candidate, stop=lexical_boundary)
    if not exists and lexical.exists():
        raise RuntimeError("Evaluator workspace target already exists")
    resolved = lexical.resolve(strict=exists)
    resolved.relative_to(boundary)
    if exists:
        info = lexical.stat(follow_symlinks=False)
        if not stat.S_ISDIR(info.st_mode):
            raise RuntimeError("Evaluator workspace is not a regular directory")
        current = resolved
    else:
        current = resolved.parent.resolve(strict=True)
    while True:
        info = current.stat(follow_symlinks=False)
        if not stat.S_ISDIR(info.st_mode):
            raise RuntimeError("Evaluator workspace ancestor is not a directory")
        if stat.S_IMODE(info.st_mode) & 0o077:
            raise RuntimeError("Evaluator workspace has group/world permissions")
        if current == boundary:
            break
        current = current.parent
    return resolved


def _verify_json_sidecar(path: Path) -> None:
    expected = sha256_file(path)
    sidecar = path.with_name(path.name + ".sha256")
    if sidecar.read_text(encoding="utf-8").strip().split() != [expected, path.name]:
        raise RuntimeError("Manifest sidecar mismatch")


def _verify_package_manifest(
    project_root: Path, config: Mapping[str, Any]
) -> tuple[Path, dict[str, Any]]:
    root = resolve_inside(
        project_root,
        str(config["outputs"]["canonical_root"]),
        project_root / "data/canonical",
        strict=True,
    )
    path = root / "PACKAGE_MANIFEST.json"
    manifest = load_json(path)
    sidecar = path.with_name(path.name + ".sha256")
    expected = sha256_file(path)
    if sidecar.read_text(encoding="utf-8").strip().split() != [expected, path.name]:
        raise RuntimeError("Package manifest sidecar mismatch")
    if (
        manifest.get("package_id") != PACKAGE_ID
        or manifest.get("status") != "complete_frozen"
        or manifest.get("protected_test_candidate_or_truth_identity_public")
        is not False
    ):
        raise RuntimeError("Benchmark package is not a frozen protected package")
    return root, manifest


def _sealed_record(manifest: Mapping[str, Any], role: str) -> Mapping[str, Any]:
    try:
        return manifest["artifacts"]["sealed_packages"][role]
    except KeyError as exc:
        raise RuntimeError(f"Missing sealed package record: {role}") from exc


def _decrypt_checked(
    *,
    ciphertext: Path,
    certificate: Path,
    private_key: Path,
    expected_ciphertext_sha: str,
    expected_archive_sha: str,
    archive: Path,
) -> None:
    if sha256_file(ciphertext) != expected_ciphertext_sha:
        raise RuntimeError("Sealed ciphertext hash mismatch")
    observed = cms_decrypt(
        ciphertext=ciphertext,
        certificate=certificate,
        private_key=private_key,
        output=archive,
    )
    if observed != expected_archive_sha:
        raise RuntimeError("Decrypted deterministic archive hash mismatch")


def _project_scorer_inputs(*, source_root: Path, target_root: Path) -> dict[str, Any]:
    source = source_root / "protected_candidates"
    files = sorted(source.glob("part-*.parquet"))
    if not files:
        raise RuntimeError("Protected candidate package has no table parts")
    target_root.mkdir(parents=True, exist_ok=False)
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in files:
        table = pq.read_table(path, columns=list(SCORER_INPUT_COLUMNS))
        if tuple(table.schema.names) != SCORER_INPUT_COLUMNS:
            raise RuntimeError("Protected scorer projection columns changed")
        tokens = [str(value) for value in table.column("candidate_token").to_pylist()]
        token_set = set(tokens)
        if len(token_set) != len(tokens) or not seen.isdisjoint(token_set):
            raise RuntimeError("Protected scorer projection has duplicate tokens")
        seen.update(token_set)
        output = target_root / path.name
        pq.write_table(
            table,
            output,
            compression="zstd",
            use_dictionary=True,
            write_statistics=True,
        )
        records.append(
            {
                "path": output.relative_to(target_root.parent).as_posix(),
                "rows": table.num_rows,
                "bytes": output.stat().st_size,
                "sha256": sha256_file(output),
            }
        )
    return {
        "columns": list(SCORER_INPUT_COLUMNS),
        "rows": len(seen),
        "parts": len(records),
        "files": records,
    }


def _write_exclusive_text(path: Path, payload: str) -> None:
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise RuntimeError("Exclusive evaluator output already exists") from exc
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _write_exclusive_json(path: Path, value: Mapping[str, Any]) -> None:
    _write_exclusive_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def release_development(
    *,
    project_root: Path,
    config_path: Path,
    training_artifact_path: Path,
    output_root: Path,
) -> dict[str, Any]:
    config = load_yaml(config_path)
    validate_config(config)
    verify_documents(project_root=project_root, config=config, verify_hashes=True)
    canonical_root, manifest = _verify_package_manifest(project_root, config)
    training_artifact = _require_regular(training_artifact_path)
    training_sha = sha256_file(training_artifact)
    target = _require_private_workspace(project_root, output_root, exists=False)
    keys = private_key_paths(project_root, config)
    record = _sealed_record(manifest, "development")
    ciphertext = canonical_root / "sealed" / str(record["ciphertext_path"])
    certificate = resolve_inside(
        project_root,
        str(config["inputs"]["development_release_certificate"]),
        project_root,
        strict=True,
    )
    with tempfile.TemporaryDirectory(
        prefix="development_release_", dir=(project_root / "artifacts/tmp")
    ) as temp_name:
        archive = Path(temp_name) / "development.tar"
        _decrypt_checked(
            ciphertext=ciphertext,
            certificate=certificate,
            private_key=keys["development"],
            expected_ciphertext_sha=str(record["ciphertext_sha256"]),
            expected_archive_sha=str(record["plaintext_archive_sha256"]),
            archive=archive,
        )
        with AtomicDatasetDirectory(target) as temporary:
            extract_verified_tar(archive, temporary / "package")
            receipt = {
                "schema_version": 1,
                "package_id": PACKAGE_ID,
                "released_at_utc": _timestamp(),
                "training_artifact": training_artifact.as_posix(),
                "training_artifact_sha256": training_sha,
                "development_archive_sha256": str(record["plaintext_archive_sha256"]),
                "protected_test_accessed": False,
                "model_evaluation_performed": False,
            }
            write_manifest(temporary / "DEVELOPMENT_RELEASE_RECEIPT.json", receipt)
    return receipt


def open_protected_candidates(
    *,
    project_root: Path,
    config_path: Path,
    scoring_artifact_path: Path,
    session_root: Path,
) -> dict[str, Any]:
    if os.environ.get("IPIN_EVALUATOR_NETWORK_ISOLATED") != "1":
        raise RuntimeError(
            "Protected candidates require an explicitly network-isolated evaluator"
        )
    config = load_yaml(config_path)
    validate_config(config)
    verify_documents(project_root=project_root, config=config, verify_hashes=True)
    canonical_root, manifest = _verify_package_manifest(project_root, config)
    scoring_artifact = _require_regular(scoring_artifact_path)
    scoring_sha = sha256_file(scoring_artifact)
    target = _require_private_workspace(project_root, session_root, exists=False)
    keys = private_key_paths(project_root, config)
    record = _sealed_record(manifest, "protected_candidates")
    ciphertext = canonical_root / "sealed" / str(record["ciphertext_path"])
    certificate = resolve_inside(
        project_root,
        str(config["inputs"]["protected_candidates_certificate"]),
        project_root,
        strict=True,
    )
    with tempfile.TemporaryDirectory(
        prefix="protected_candidates_", dir=(project_root / "artifacts/tmp")
    ) as temp_name:
        archive = Path(temp_name) / "protected_candidates.tar"
        _decrypt_checked(
            ciphertext=ciphertext,
            certificate=certificate,
            private_key=keys["protected_candidates"],
            expected_ciphertext_sha=str(record["ciphertext_sha256"]),
            expected_archive_sha=str(record["plaintext_archive_sha256"]),
            archive=archive,
        )
        plaintext = Path(temp_name) / "candidate_plaintext"
        extract_verified_tar(archive, plaintext)
        with AtomicDatasetDirectory(target) as temporary:
            projection = _project_scorer_inputs(
                source_root=plaintext, target_root=temporary / "scorer_candidates"
            )
            session = {
                "schema_version": 1,
                "package_id": PACKAGE_ID,
                "opened_at_utc": _timestamp(),
                "scoring_artifact": scoring_artifact.as_posix(),
                "scoring_artifact_sha256": scoring_sha,
                "candidate_archive_sha256": str(record["plaintext_archive_sha256"]),
                "scorer_input_projection": projection,
                "unprojected_candidate_metadata_retained": False,
                "network_isolation_attested": True,
                "truth_accessed": False,
                "prediction_columns": ["candidate_token", "score"],
                "prediction_identity_may_leave_evaluator": False,
            }
            write_manifest(temporary / "SCORING_SESSION.json", session)
    return session


def validate_prediction_rows(
    expected_tokens: Iterable[str],
    prediction_rows: Iterable[tuple[str, float]],
) -> dict[str, float]:
    expected = set(map(str, expected_tokens))
    scores: dict[str, float] = {}
    duplicate = 0
    nonfinite = 0
    for raw_token, raw_score in prediction_rows:
        token = str(raw_token)
        score = float(raw_score)
        if token in scores:
            duplicate += 1
        if not math.isfinite(score):
            nonfinite += 1
        scores[token] = score
    unknown = set(scores) - expected
    missing = expected - set(scores)
    if duplicate or nonfinite or unknown or missing:
        raise RuntimeError(
            "Prediction validation failed: "
            f"duplicate={duplicate}, nonfinite={nonfinite}, "
            f"unknown={len(unknown)}, missing={len(missing)}"
        )
    return scores


def weighted_pairwise_concordance(
    positive_scores: Sequence[float],
    unlabeled_scores: Sequence[float],
    unlabeled_weights: Sequence[float],
) -> float:
    positives = np.asarray(positive_scores, dtype=np.float64)
    scores = np.asarray(unlabeled_scores, dtype=np.float64)
    weights = np.asarray(unlabeled_weights, dtype=np.float64)
    if (
        positives.size == 0
        or scores.size == 0
        or scores.size != weights.size
        or not np.isfinite(positives).all()
        or not np.isfinite(scores).all()
        or not np.isfinite(weights).all()
        or np.any(weights <= 0)
    ):
        raise ValueError(
            "Concordance requires finite nonempty scores and positive weights"
        )
    order = np.argsort(scores, kind="mergesort")
    sorted_scores = scores[order]
    sorted_weights = weights[order]
    cumulative = np.concatenate(([0.0], np.cumsum(sorted_weights)))
    left = np.searchsorted(sorted_scores, positives, side="left")
    right = np.searchsorted(sorted_scores, positives, side="right")
    below = cumulative[left]
    ties = cumulative[right] - cumulative[left]
    return float(np.mean((below + 0.5 * ties) / cumulative[-1]))


def _prediction_rows(path: Path) -> list[tuple[str, float]]:
    path = _require_regular(path)
    if path.suffix != ".parquet":
        raise RuntimeError(
            "Protected predictions must be a two-column Parquet artifact"
        )
    schema = pq.ParquetFile(path).schema_arrow
    if schema.names != ["candidate_token", "score"]:
        raise RuntimeError("Prediction artifact columns differ from frozen schema")
    connection = duckdb.connect(":memory:")
    try:
        rows = connection.execute(
            f"SELECT candidate_token, score FROM read_parquet('{path.as_posix()}')"
        ).fetchall()
    finally:
        connection.close()
    return [(str(token), float(score)) for token, score in rows]


def _sampled_metrics(
    *,
    scores: Mapping[str, float],
    truth_root: Path,
) -> dict[str, Any]:
    connection = duckdb.connect(":memory:")
    try:
        positive_rows = connection.execute(
            f"SELECT cell_id, candidate_token FROM read_parquet("
            f"'{(truth_root / 'protected_positive_truth/part-*.parquet').as_posix()}')"
        ).fetchall()
        unlabeled_rows = connection.execute(
            f"SELECT cell_id, "
            f"'candidate:' || sha256('{PACKAGE_ID}:' || cell_id || ':' || pair_id), "
            "sampling_weight_numerator::DOUBLE / sampling_weight_denominator::DOUBLE "
            f"FROM read_parquet('{(truth_root / 'unlabeled_pairs/part-*.parquet').as_posix()}')"
        ).fetchall()
    finally:
        connection.close()
    positive_by_cell: dict[str, list[float]] = defaultdict(list)
    unlabeled_by_cell: dict[str, list[float]] = defaultdict(list)
    weight_by_cell: dict[str, list[float]] = defaultdict(list)
    for cell, token in positive_rows:
        positive_by_cell[str(cell)].append(scores[str(token)])
    for cell, token, weight in unlabeled_rows:
        unlabeled_by_cell[str(cell)].append(scores[str(token)])
        weight_by_cell[str(cell)].append(float(weight))
    output = {}
    for cell in sorted(positive_by_cell):
        output[cell] = {
            "positive_unlabeled_pairwise_concordance_horvitz_thompson": (
                weighted_pairwise_concordance(
                    positive_by_cell[cell],
                    unlabeled_by_cell[cell],
                    weight_by_cell[cell],
                )
            ),
            "positive_pairs": len(positive_by_cell[cell]),
            "sampled_unlabeled_pairs": len(unlabeled_by_cell[cell]),
            "exact_recall_at_k_status": "demoted_no_full_candidate_stream",
            "exact_positive_rank_status": "demoted_no_full_candidate_stream",
        }
    return output


def evaluate_protected(
    *,
    project_root: Path,
    config_path: Path,
    session_root: Path,
    prediction_path: Path,
    receipt_path: Path,
) -> dict[str, Any]:
    if os.environ.get("IPIN_EVALUATOR_NETWORK_ISOLATED") != "1":
        raise RuntimeError("Protected evaluation requires network isolation")
    config = load_yaml(config_path)
    validate_config(config)
    canonical_root, manifest = _verify_package_manifest(project_root, config)
    session_root = _require_private_workspace(project_root, session_root, exists=True)
    session_path = _require_regular(session_root / "SCORING_SESSION.json")
    _verify_json_sidecar(session_path)
    session = load_json(session_path)
    if (
        session.get("package_id") != PACKAGE_ID
        or session.get("truth_accessed") is not False
        or session.get("unprojected_candidate_metadata_retained") is not False
        or session.get("scorer_input_projection", {}).get("columns")
        != list(SCORER_INPUT_COLUMNS)
    ):
        raise RuntimeError("Scoring session is invalid or already truth-accessed")
    scoring_artifact = _require_regular(Path(str(session["scoring_artifact"])))
    if sha256_file(scoring_artifact) != str(session["scoring_artifact_sha256"]):
        raise RuntimeError("Frozen scoring artifact changed after candidate access")

    prediction_path = _require_regular(prediction_path)
    prediction_sha = sha256_file(prediction_path)
    prediction_rows = _prediction_rows(prediction_path)
    candidate_glob = session_root / "scorer_candidates/part-*.parquet"
    connection = duckdb.connect(":memory:")
    try:
        expected_tokens = [
            str(row[0])
            for row in connection.execute(
                f"SELECT candidate_token FROM read_parquet('{candidate_glob.as_posix()}')"
            ).fetchall()
        ]
    finally:
        connection.close()
    scores = validate_prediction_rows(expected_tokens, prediction_rows)

    ledger_root = _require_private_workspace(
        project_root,
        Path(".private/pair_level_pu_r_benchmark_artifacts_v1"),
        exists=True,
    )
    ledger = ledger_root / "protected_evaluation_ledger.json"
    completion = ledger_root / "protected_evaluation_completion.json"

    receipt_boundary = project_root / str(config["protected_evaluator"]["receipt_root"])
    reject_symlink_components(receipt_boundary, stop=project_root)
    receipt_boundary.mkdir(parents=True, exist_ok=True)
    receipt_candidate = (
        receipt_path if receipt_path.is_absolute() else project_root / receipt_path
    )
    lexical_receipt = reject_symlink_components(
        receipt_candidate, stop=receipt_boundary
    )
    receipt_sidecar = lexical_receipt.with_name(lexical_receipt.name + ".sha256")
    if (
        lexical_receipt.suffix != ".json"
        or lexical_receipt.exists()
        or receipt_sidecar.exists()
    ):
        raise RuntimeError("Protected metric receipt target is unsafe or occupied")
    receipt_target = lexical_receipt.resolve(strict=False)
    receipt_target.parent.mkdir(parents=True, exist_ok=True)

    keys = private_key_paths(project_root, config)
    record = _sealed_record(manifest, "protected_truth")
    ciphertext = canonical_root / "sealed" / str(record["ciphertext_path"])
    certificate = resolve_inside(
        project_root,
        str(config["inputs"]["protected_truth_certificate"]),
        project_root,
        strict=True,
    )
    if sha256_file(ciphertext) != str(record["ciphertext_sha256"]):
        raise RuntimeError("Sealed truth ciphertext hash mismatch before reservation")
    _write_exclusive_json(
        ledger,
        {
            "schema_version": 1,
            "package_id": PACKAGE_ID,
            "reserved_at_utc": _timestamp(),
            "status": "one_first_attempt_reserved_before_truth_access",
            "scoring_artifact_sha256": str(session["scoring_artifact_sha256"]),
            "prediction_artifact_sha256": prediction_sha,
            "candidate_archive_sha256": str(session["candidate_archive_sha256"]),
            "prediction_hashed_before_truth_access": True,
            "truth_access_attempt_irrevocably_consumed": True,
        },
    )

    with tempfile.TemporaryDirectory(
        prefix="protected_truth_", dir=(project_root / "artifacts/tmp")
    ) as temp_name:
        temporary = Path(temp_name)
        archive = temporary / "protected_truth.tar"
        _decrypt_checked(
            ciphertext=ciphertext,
            certificate=certificate,
            private_key=keys["protected_truth"],
            expected_ciphertext_sha=str(record["ciphertext_sha256"]),
            expected_archive_sha=str(record["plaintext_archive_sha256"]),
            archive=archive,
        )
        truth_root = temporary / "truth"
        extract_verified_tar(archive, truth_root)
        metrics = _sampled_metrics(scores=scores, truth_root=truth_root)

    receipt = {
        "schema_version": 1,
        "package_id": PACKAGE_ID,
        "evaluated_at_utc": _timestamp(),
        "scoring_artifact_sha256": str(session["scoring_artifact_sha256"]),
        "prediction_artifact_sha256": prediction_sha,
        "prediction_hashed_before_truth_access": True,
        "network_isolation_attested": True,
        "one_first_evaluation_consumed": True,
        "metrics": metrics,
        "protected_pair_or_prediction_identities_emitted": False,
        "exact_full_universe_metrics_reported": False,
        "unlabeled_interpreted_as_negative": False,
        "prevalence_calibration_or_biological_precision_reported": False,
    }
    _write_exclusive_json(receipt_target, receipt)
    receipt_sha = sha256_file(receipt_target)
    _write_exclusive_text(receipt_sidecar, f"{receipt_sha}  {receipt_target.name}\n")
    _write_exclusive_json(
        completion,
        {
            "schema_version": 1,
            "package_id": PACKAGE_ID,
            "completed_at_utc": receipt["evaluated_at_utc"],
            "status": "one_first_evaluation_complete",
            "scoring_artifact_sha256": receipt["scoring_artifact_sha256"],
            "prediction_artifact_sha256": prediction_sha,
            "receipt_sha256": receipt_sha,
        },
    )
    return receipt


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/pair_level_pu_r_benchmark_artifacts_v1.yaml"),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    release = subparsers.add_parser("release-development")
    release.add_argument("--training-artifact", type=Path, required=True)
    release.add_argument("--output-root", type=Path, required=True)
    opening = subparsers.add_parser("open-protected-candidates")
    opening.add_argument("--scoring-artifact", type=Path, required=True)
    opening.add_argument("--session-root", type=Path, required=True)
    evaluate = subparsers.add_parser("evaluate-protected")
    evaluate.add_argument("--session-root", type=Path, required=True)
    evaluate.add_argument("--predictions", type=Path, required=True)
    evaluate.add_argument("--receipt", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    project_root = project_root_from(Path(__file__))
    config_path = (
        args.config if args.config.is_absolute() else project_root / args.config
    )
    if args.command == "release-development":
        result = release_development(
            project_root=project_root,
            config_path=config_path,
            training_artifact_path=args.training_artifact,
            output_root=args.output_root,
        )
    elif args.command == "open-protected-candidates":
        result = open_protected_candidates(
            project_root=project_root,
            config_path=config_path,
            scoring_artifact_path=args.scoring_artifact,
            session_root=args.session_root,
        )
    else:
        result = evaluate_protected(
            project_root=project_root,
            config_path=config_path,
            session_root=args.session_root,
            prediction_path=args.predictions,
            receipt_path=args.receipt,
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
