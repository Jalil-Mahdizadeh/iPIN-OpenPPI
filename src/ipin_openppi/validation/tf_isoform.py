"""Independent fail-closed validation of the 2025 TF-isoform Y2H audit."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
from io import BytesIO, StringIO
import json
import math
from pathlib import Path
import stat
import tarfile
from typing import Any, Mapping
import zipfile

import duckdb
import pandas as pd
import pyarrow.dataset as ds
import pyarrow.parquet as pq
import yaml

from ipin_openppi.ingestion.common import (
    load_asset_index,
    project_root_from,
    require_apptainer,
)
from ipin_openppi.ingestion.schema import load_contract, sha256_file
from ipin_openppi.validation.staging import Checks, _write_report


STAGING_TABLES = {
    "archive_members",
    "clone_records",
    "screen_selection_records",
    "raw_y2h_records",
    "raw_n2h_records",
}
CANONICAL_TABLES = {
    "clone_sequence_mappings",
    "partner_construct_mappings",
    "y2h_pair_audit",
    "n2h_observation_audit",
    "matched_contrast_groups",
    "analytical_filter_steps",
}
RECORD_KEYS = {
    "clone_record_id",
    "pair_record_id",
    "n2h_record_id",
    "matched_group_id",
    "raw_y2h_record_id",
    "raw_n2h_record_id",
}

PUBLIC_CLONES = "supp/SuppTable_CloneList.txt"
PUBLIC_Y2H = "supp/SuppTable_PairwiseY2HResults.txt"
PUBLIC_N2H = "supp/SuppTable_N2HResults.txt"
RAW_Y2H = "data/internal/Y2H-data_2022-03-08.tsv"
SCREEN = "data/internal/tf_isoform_y2h_screen.tsv"
INTERNAL_CLONES = "data/internal/isoform_clones.tsv"
RAW_N2H = "data/internal/N2H_results.tsv"
CLONE_FASTA = "data/internal/j2_6k_unique_isoacc_and_nt_seqs.fa"
OUTCOMES = (
    "positive_y2h_observation",
    "explicit_negative_y2h_observation",
    "sequence_confirmation_failure",
    "mating_or_spotting_failure",
    "assay_measurement_failure",
    "autoactivation",
    "unknown_unresolved",
)


def _text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected YAML mapping: {path}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected JSON object: {path}")
    return value


def _resolve_inside(
    project_root: Path,
    value: str | Path,
    boundary: Path,
    *,
    strict: bool = True,
) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = project_root / candidate
    resolved = candidate.resolve(strict=strict)
    try:
        resolved.relative_to(boundary.resolve(strict=True))
    except ValueError as exc:
        raise RuntimeError(f"Path escapes boundary {boundary}: {resolved}") from exc
    return resolved


def contains_record_keys(value: Any) -> bool:
    if isinstance(value, Mapping):
        if any(str(key) in RECORD_KEYS for key in value):
            return True
        return any(contains_record_keys(child) for child in value.values())
    if isinstance(value, list):
        return any(contains_record_keys(child) for child in value)
    return False


def independent_y2h_outcome(row: Mapping[str, Any]) -> tuple[str, str, str]:
    """Reimplement assay semantics without importing production semantics."""

    result = _text(row.get("Y2H_result"))
    if result == "True":
        return "positive_y2h_observation", "evaluable", "positive"
    if result == "False":
        return "explicit_negative_y2h_observation", "evaluable", "negative"
    if result:
        raise RuntimeError(f"Unexpected Y2H result: {result!r}")

    def score(name: str) -> int | None:
        token = _text(row.get(name)).casefold()
        if token in {"", "na", "nan", "none"}:
            return None
        value = int(float(token))
        if value not in {0, 1, 2, 3, 4}:
            raise RuntimeError(f"Unexpected {name} score: {token!r}")
        return value

    pair_lw, control_lw = score("LW"), score("empty_AD_LW")
    if (
        pair_lw is None
        or control_lw is None
        or pair_lw <= 1
        or control_lw <= 1
    ):
        return (
            "mating_or_spotting_failure",
            "technically_unevaluable",
            "not_applicable",
        )
    control_3at = score("empty_AD_3AT")
    if control_3at == 4:
        return "autoactivation", "technically_unevaluable", "not_applicable"
    if score("3AT") is None or control_3at is None:
        return (
            "assay_measurement_failure",
            "technically_unevaluable",
            "not_applicable",
        )
    confirmations = {
        _text(row.get(name)).casefold()
        for name in ("seq_confirmation_3AT", "seq_confirmation_LW")
    }
    if confirmations & {"false", "0"}:
        return (
            "sequence_confirmation_failure",
            "technically_unevaluable",
            "not_applicable",
        )
    return "unknown_unresolved", "technically_unevaluable", "not_applicable"


def _read_zip_suffix(archive: zipfile.ZipFile, suffix: str) -> bytes:
    names = [name for name in archive.namelist() if name.endswith(suffix)]
    if len(names) != 1:
        raise RuntimeError(
            f"Expected one ZIP member ending {suffix!r}; found {len(names)}"
        )
    return archive.read(names[0])


def _read_tar_members(path: Path, required: set[str]) -> dict[str, bytes]:
    found: dict[str, bytes] = {}
    with tarfile.open(path, mode="r|gz") as archive:
        for member in archive:
            if member.name not in required:
                continue
            if not member.isfile() or member.name in found:
                raise RuntimeError(
                    f"Unsafe or duplicate governed TAR member: {member.name}"
                )
            handle = archive.extractfile(member)
            if handle is None:
                raise RuntimeError(f"Could not read governed TAR member: {member.name}")
            found[member.name] = handle.read()
    missing = required - set(found)
    if missing:
        raise RuntimeError(f"Missing governed TAR members: {sorted(missing)}")
    return found


def _tsv(payload: bytes) -> pd.DataFrame:
    return pd.read_csv(
        BytesIO(payload), sep="\t", dtype=str, keep_default_na=False
    )


def _parse_fasta(payload: bytes) -> dict[str, str]:
    output: dict[str, str] = {}
    current: str | None = None
    parts: list[str] = []
    for raw in StringIO(payload.decode("utf-8")):
        line = raw.strip()
        if not line:
            continue
        if line.startswith(">"):
            if current is not None:
                output[current] = "".join(parts).upper()
            current, parts = line[1:].split()[0], []
            if current in output:
                raise RuntimeError(f"Duplicate FASTA identifier: {current}")
        elif current is None:
            raise RuntimeError("FASTA sequence before identifier")
        else:
            parts.append(line)
    if current is not None:
        output[current] = "".join(parts).upper()
    return output


_CODONS = {
    codon: amino
    for codons, amino in (
        ("TTT TTC", "F"),
        ("TTA TTG CTT CTC CTA CTG", "L"),
        ("ATT ATC ATA", "I"),
        ("ATG", "M"),
        ("GTT GTC GTA GTG", "V"),
        ("TCT TCC TCA TCG AGT AGC", "S"),
        ("CCT CCC CCA CCG", "P"),
        ("ACT ACC ACA ACG", "T"),
        ("GCT GCC GCA GCG", "A"),
        ("TAT TAC", "Y"),
        ("TAA TAG TGA", "*"),
        ("CAT CAC", "H"),
        ("CAA CAG", "Q"),
        ("AAT AAC", "N"),
        ("AAA AAG", "K"),
        ("GAT GAC", "D"),
        ("GAA GAG", "E"),
        ("TGT TGC", "C"),
        ("TGG", "W"),
        ("CGT CGC CGA CGG AGA AGG", "R"),
        ("GGT GGC GGA GGG", "G"),
    )
    for codon in codons.split()
}


def _translation_matches(cds: str, protein: str) -> bool:
    try:
        if len(cds) % 3:
            return False
        translated = "".join(
            _CODONS[cds[index : index + 3]]
            for index in range(0, len(cds), 3)
        )
    except KeyError:
        return False
    if translated.endswith("*"):
        translated = translated[:-1]
    return translated == protein


def _independent_filter(frame: pd.DataFrame) -> tuple[pd.Series, list[int]]:
    active = pd.Series(True, index=frame.index)
    outputs: list[int] = []

    def retain(condition: pd.Series) -> None:
        nonlocal active
        active = active & condition.reindex(frame.index, fill_value=False).fillna(False)
        outputs.append(int(active.sum()))

    retain(
        frame["source_category"].isin(
            {
                "tf_isoform_ppis",
                "tf_paralog_ppis",
                "paralog_with_PDI",
                "non_paralog_control",
            }
        )
    )
    subset = frame.loc[active]
    groups = {
        key
        for key, group in subset.groupby(["ad_gene_symbol", "db_gene_symbol"])
        if group["observation_state"].eq("positive").any()
    }
    retain(
        pd.Series(
            [
                (left, right) in groups
                for left, right in zip(
                    frame.ad_gene_symbol, frame.db_gene_symbol, strict=True
                )
            ],
            index=frame.index,
        )
    )
    subset = frame.loc[active]
    clones = {
        key
        for key, group in subset.groupby("ad_clone_id")
        if group.observation_state.isin({"positive", "negative"}).any()
    }
    retain(frame.ad_clone_id.isin(clones))
    subset = frame.loc[active]
    clones = {
        key
        for key, group in subset.groupby("ad_clone_id")
        if group.observation_state.eq("positive").any()
    }
    retain(frame.ad_clone_id.isin(clones))
    subset = frame.loc[active]
    genes = {
        key
        for key, group in subset.groupby("ad_gene_symbol")
        if group.ad_clone_id.nunique() >= 2
    }
    retain(frame.ad_gene_symbol.isin(genes))
    subset = frame.loc[active]
    groups = {
        key
        for key, group in subset.groupby(["ad_gene_symbol", "db_gene_symbol"])
        if group.observation_state.isin({"positive", "negative"}).sum() >= 2
    }
    retain(
        pd.Series(
            [
                (left, right) in groups
                for left, right in zip(
                    frame.ad_gene_symbol, frame.db_gene_symbol, strict=True
                )
            ],
            index=frame.index,
        )
    )
    return active, outputs


def _source_reconstruction(
    project_root: Path,
    config: Mapping[str, Any],
    acquisition_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    _, assets = load_asset_index(
        project_root, acquisition_path.relative_to(project_root)
    )
    code = assets[str(config["raw_assets"]["archived_code"])]
    raw_input = assets[str(config["raw_assets"]["archived_input"])]
    license_ids = {}
    for name in ("code_metadata", "input_metadata"):
        metadata = _load_json(assets[str(config["raw_assets"][name])].path)
        license_ids[name] = _text(
            metadata.get("metadata", {}).get("license", {}).get("id")
        )
    with zipfile.ZipFile(code.path) as archive:
        clones = _tsv(_read_zip_suffix(archive, PUBLIC_CLONES))
        public_y2h = _tsv(_read_zip_suffix(archive, PUBLIC_Y2H))
        public_n2h = _tsv(_read_zip_suffix(archive, PUBLIC_N2H))
    tar_values = _read_tar_members(
        raw_input.path,
        {RAW_Y2H, SCREEN, INTERNAL_CLONES, RAW_N2H, CLONE_FASTA},
    )
    raw_y2h, screen = _tsv(tar_values[RAW_Y2H]), _tsv(tar_values[SCREEN])
    internal_clones = _tsv(tar_values[INTERNAL_CLONES])
    raw_n2h = _tsv(tar_values[RAW_N2H])
    fasta = _parse_fasta(tar_values[CLONE_FASTA])

    def y2h_key(row: Mapping[str, Any], public: bool) -> tuple[str, ...]:
        return (
            _text(row["ad_clone_id" if public else "ad_clone_name"]),
            _text(row["ad_gene_symbol"]),
            _text(row["ad_orf_id"]),
            _text(row["db_gene_symbol"]),
            _text(row["db_orf_id"]),
        )

    raw_index = {
        y2h_key(row, False): row for row in raw_y2h.to_dict("records")
    }
    if len(raw_index) != len(raw_y2h):
        raise RuntimeError("Independent validator found duplicate raw Y2H keys")
    semantic_rows: list[dict[str, Any]] = []
    disagreements = 0
    for public in public_y2h.to_dict("records"):
        key = y2h_key(public, True)
        raw = raw_index.get(key)
        if raw is None:
            raise RuntimeError(f"Public Y2H row absent from raw archive: {key}")
        disagreements += _text(public["Y2H_result"]) != _text(raw["Y2H_result"])
        outcome, evaluability, observation = independent_y2h_outcome(
            {**raw, "Y2H_result": public["Y2H_result"]}
        )
        semantic_rows.append(
            {
                **public,
                "source_category": _text(raw["category"]),
                "outcome_class": outcome,
                "evaluability_state": evaluability,
                "observation_state": observation,
            }
        )
    semantic = pd.DataFrame(semantic_rows)
    membership, filter_outputs = _independent_filter(semantic)
    semantic["in_post_selection_attempt_universe"] = membership
    semantic["in_reported_3509_evaluable_analysis"] = (
        membership & semantic.evaluability_state.eq("evaluable")
    )

    accessions: dict[str, str] = {}
    for row in internal_clones.to_dict("records"):
        accession = _text(row["clone_acc"])
        fields = accession.split("|")
        clone_id = fields[0] + "-" + fields[1].split("/", 1)[0]
        accessions[clone_id] = accession
    clone_hashes: dict[str, str] = {}
    fasta_disagreements = 0
    translation_counts: Counter[str] = Counter()
    for row in clones.to_dict("records"):
        clone_id = _text(row["clone_id"])
        cds, aa = _text(row["cds_seq"]).upper(), _text(row["aa_seq"]).upper()
        accession = accessions.get(clone_id)
        fasta_disagreements += accession is None or fasta.get(str(accession)) != cds
        state = "concordant" if _translation_matches(cds, aa) else "discordant"
        translation_counts[state] += 1
        clone_hashes[clone_id] = sha256(aa.encode("ascii")).hexdigest()

    n2h_fields = (
        "test_orf_ida",
        "test_orf_idb",
        "source",
        "score_pair",
        "score_empty-N1",
        "score_empty-N2",
        "gene_symbol_tf",
        "gene_symbol_partner",
    )
    complete_raw_n2h: dict[tuple[str, ...], dict[str, Any]] = {}
    for row in raw_n2h.to_dict("records"):
        complete = all(
            _text(row[name])
            for name in ("score_pair", "score_empty-N1", "score_empty-N2")
        )
        if not complete or _text(row["source"]) == "vignettes":
            continue
        key = tuple(_text(row[name]) for name in n2h_fields)
        if key in complete_raw_n2h:
            raise RuntimeError(f"Duplicate public-eligible raw N2H key: {key}")
        complete_raw_n2h[key] = row
    public_n2h_keys = {
        tuple(_text(row[name]) for name in n2h_fields)
        for row in public_n2h.to_dict("records")
    }
    y2h_orfs = {
        (str(row.ad_orf_id), str(row.db_orf_id)): str(row.observation_state)
        for row in semantic.itertuples(index=False)
    }
    isoform_states: Counter[tuple[str, str]] = Counter()
    n2h_crosswalk, nlr_errors = 0, 0
    isoform_values: list[tuple[int, float]] = []
    for row in public_n2h.to_dict("records"):
        pair = (_text(row["test_orf_idb"]), _text(row["test_orf_ida"]))
        state = y2h_orfs.get(pair, "not_available")
        n2h_crosswalk += state != "not_available"
        source = _text(row["source"])
        if source in {"isoform positives", "isoform negatives"}:
            isoform_states[(source, state)] += 1
            isoform_values.append(
                (1 if state == "positive" else 0, float(row["log2 NLR"]))
            )
        calculated = math.log2(
            float(row["score_pair"])
            / max(float(row["score_empty-N1"]), float(row["score_empty-N2"]))
        )
        nlr_errors += not math.isclose(
            calculated,
            float(row["log2 NLR"]),
            rel_tol=1e-12,
            abs_tol=1e-12,
        )

    counts = Counter(str(value) for value in semantic.outcome_class)
    outcome_counts = {name: int(counts[name]) for name in OUTCOMES}
    analysis = semantic.loc[semantic.in_reported_3509_evaluable_analysis]
    attempted = semantic.loc[semantic.in_post_selection_attempt_universe]
    screen_flags = Counter(
        (
            _text(row["in_orfeome_screen"]).casefold() in {"true", "1"},
            _text(row["in_focussed_screen"]).casefold() in {"true", "1"},
        )
        for row in screen.to_dict("records")
    )
    ranks = pd.DataFrame(isoform_values, columns=["y2h", "nlr"])
    metrics = {
        "source_rows": {
            "clone_rows": len(clones),
            "screen_selection_rows": len(screen),
            "raw_y2h_rows": len(raw_y2h),
            "public_y2h_rows": len(public_y2h),
            "raw_n2h_rows": len(raw_n2h),
            "public_n2h_rows": len(public_n2h),
        },
        "public_raw_y2h_crosswalk_disagreements": int(disagreements),
        "raw_y2h_rows_excluded_from_public": len(raw_y2h) - len(public_y2h),
        "outcome_counts": dict(sorted(outcome_counts.items())),
        "blank_rows": int(public_y2h.Y2H_result.eq("").sum()),
        "filter_output_rows": filter_outputs,
        "analytical_attempt_rows": int(membership.sum()),
        "analytical_evaluable_rows": len(analysis),
        "analytical_positive_rows": int(
            analysis.observation_state.eq("positive").sum()
        ),
        "analytical_negative_rows": int(
            analysis.observation_state.eq("negative").sum()
        ),
        "analytical_technical_rows": int(
            attempted.evaluability_state.ne("evaluable").sum()
        ),
        "analytical_positive_gene_partner_groups": int(
            analysis.loc[
                analysis.observation_state.eq("positive"),
                ["ad_gene_symbol", "db_gene_symbol"],
            ].drop_duplicates().shape[0]
        ),
        "screen_flag_counts": {
            f"orfeome_{str(key[0]).lower()}__focussed_{str(key[1]).lower()}": int(
                value
            )
            for key, value in sorted(screen_flags.items())
        },
        "clone_fasta_disagreements": int(fasta_disagreements),
        "clone_translation_concordant": int(translation_counts["concordant"]),
        "clone_translation_discordant": int(translation_counts["discordant"]),
        "raw_complete_non_vignette_n2h_rows": len(complete_raw_n2h),
        "raw_public_n2h_set_concordant": (
            len(public_n2h_keys) == len(public_n2h)
            and set(complete_raw_n2h) == public_n2h_keys
        ),
        "n2h_y2h_crosswalk_rows": int(n2h_crosswalk),
        "n2h_log2_recalculation_errors": int(nlr_errors),
        "n2h_isoform_source_state_counts": {
            f"{key[0]}__{key[1]}": int(value)
            for key, value in sorted(isoform_states.items())
        },
        "n2h_spearman": float(ranks.y2h.rank().corr(ranks.nlr.rank())),
        "machine_verified_license_ids": dict(sorted(license_ids.items())),
    }
    context = {
        "clones": clones,
        "public_y2h": public_y2h,
        "semantic": semantic,
        "clone_hashes": clone_hashes,
    }
    return metrics, context


def _validate_dataset(
    *,
    checks: Checks,
    project_root: Path,
    root: Path,
    manifest_name: str,
    expected_tables: set[str],
    contract: Any,
    label: str,
) -> tuple[dict[str, Path], dict[str, Any]]:
    manifest_path = root / manifest_name
    sidecar = root / f"{manifest_name}.sha256"
    manifest = _load_json(manifest_path)
    digest = sha256_file(manifest_path)
    checks.require(
        f"inventory.{label}.manifest_sidecar",
        sidecar.read_text(encoding="utf-8").split() == [digest, manifest_name],
        observed={"sha256": digest},
        expected={"sidecar_matches": True},
    )
    observed_tables = set(manifest.get("tables", {}))
    checks.require(
        f"inventory.{label}.table_set",
        observed_tables == expected_tables,
        observed=sorted(observed_tables),
        expected=sorted(expected_tables),
    )
    roots: dict[str, Path] = {}
    declared: set[Path] = set()
    errors, rows = 0, 0
    for table_name in sorted(expected_tables & observed_tables):
        table_root = root / table_name
        roots[table_name] = table_root
        summary = manifest["tables"][table_name]
        table_rows = 0
        for index, record in enumerate(summary.get("files", [])):
            path = Path(str(record["path"]))
            if not path.is_absolute():
                path = project_root / path
            try:
                path = path.resolve(strict=True)
                path.relative_to(table_root)
                info = path.stat(follow_symlinks=False)
                parquet_rows = int(pq.ParquetFile(path).metadata.num_rows)
                schema = pq.read_schema(path)
                valid = (
                    path.parent == table_root
                    and path.name == f"part-{index:05d}.parquet"
                    and not path.is_symlink()
                    and stat.S_ISREG(info.st_mode)
                    and not info.st_mode & 0o222
                    and info.st_size == int(record["bytes"])
                    and parquet_rows == int(record["rows"])
                    and sha256_file(path) == str(record["sha256"])
                    and schema.remove_metadata().equals(
                        contract.arrow_schema(table_name).remove_metadata()
                    )
                    and (schema.metadata or {}).get(b"ipin.audit_version")
                    == b"1.0.0"
                    and (schema.metadata or {}).get(b"ipin.redistribution")
                    == b"internal_governance_bounded_audit_only"
                )
                errors += int(not valid or path in declared)
                declared.add(path)
                table_rows += parquet_rows
                rows += parquet_rows
            except (FileNotFoundError, ValueError, KeyError):
                errors += 1
        errors += int(table_rows != int(summary.get("rows", -1)))
        errors += int(summary.get("schema_sha256") != contract.sha256)
    actual = {path.resolve() for path in root.rglob("*.parquet")}
    errors += int(actual != declared)
    allowed = {manifest_path.resolve(), sidecar.resolve(), *actual}
    for path in (root, *root.rglob("*")):
        mode = path.lstat().st_mode
        errors += int(bool(stat.S_ISLNK(mode) or mode & 0o222))
        errors += int(bool(stat.S_ISREG(mode) and path.resolve() not in allowed))
    checks.require(
        f"inventory.{label}.hash_schema_immutability",
        errors == 0,
        observed={"errors": errors, "rows": rows},
        expected={"errors": 0},
    )
    return roots, {"tables": len(roots), "rows": rows}


def _glob(path: Path) -> str:
    return (path / "*.parquet").as_posix()


def _sql(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _mapping_checks(
    checks: Checks,
    canonical: Mapping[str, Path],
    dataset_paths: Mapping[str, Path],
    context: Mapping[str, Any],
    release: str,
) -> dict[str, int]:
    clone_rows = ds.dataset(
        canonical["clone_sequence_mappings"], format="parquet"
    ).to_table().to_pylist()
    partner_rows = ds.dataset(
        canonical["partner_construct_mappings"], format="parquet"
    ).to_table().to_pylist()
    proteins = ds.dataset(
        dataset_paths["protein_sequences"], format="parquet"
    ).to_table(
        columns=[
            "uniprot_accession",
            "canonical",
            "gene_names",
            "sequence_sha256",
            "source_release",
        ]
    ).to_pylist()
    hashes: dict[str, list[dict[str, Any]]] = defaultdict(list)
    canonical_by_gene: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in proteins:
        if str(row["source_release"]) != release:
            raise RuntimeError("Frozen sequence table contains an unexpected release")
        hashes[str(row["sequence_sha256"])].append(row)
        if row["canonical"]:
            for gene in row["gene_names"]:
                canonical_by_gene[str(gene)].append(row)

    clone_errors = 0
    for row in clone_rows:
        source_hash = context["clone_hashes"].get(str(row["clone_id"]))
        candidates = hashes.get(str(source_hash), [])
        clone_errors += int(source_hash != row["construct_aa_sha256"])
        clone_errors += int(
            bool(candidates) != bool(row["construct_exact_frozen_match"])
        )
        clone_errors += int(
            sorted({str(item["sequence_sha256"]) for item in candidates})
            != list(row["frozen_candidate_sequence_hashes"])
        )
        expected_canonical = sorted(
            {
                str(item["sequence_sha256"])
                for item in canonical_by_gene.get(str(row["gene_symbol"]), [])
            }
        )
        clone_errors += int(
            expected_canonical != list(row["canonical_candidate_sequence_hashes"])
        )

    clone_hash_by_orf: dict[str, dict[str, str]] = defaultdict(dict)
    for source in context["public_y2h"].to_dict("records"):
        clone_id, orf = _text(source["ad_clone_id"]), _text(source["ad_orf_id"])
        clone_hash_by_orf[orf][clone_id] = context["clone_hashes"][clone_id]
    participant = ds.dataset(
        dataset_paths["participant_sequence_mappings"], format="parquet"
    ).to_table(
        columns=[
            "source_key",
            "raw_orf_ids",
            "mapped_sequence_sha256",
            "reference_sequence_usable",
        ]
    ).to_pylist()
    huri_by_orf: dict[str, set[str]] = defaultdict(set)
    for row in participant:
        if (
            row["source_key"] == "huri"
            and row["reference_sequence_usable"]
            and row["mapped_sequence_sha256"]
        ):
            for orf in row["raw_orf_ids"]:
                huri_by_orf[str(orf)].add(str(row["mapped_sequence_sha256"]))
    partner_errors = 0
    for row in partner_rows:
        orf = str(row["db_orf_id"])
        source_hashes = set(clone_hash_by_orf.get(orf, {}).values())
        if len(source_hashes) == 1:
            candidates = {
                str(item["sequence_sha256"])
                for item in hashes.get(next(iter(source_hashes)), [])
            }
            source_available = True
        elif len(source_hashes) > 1:
            candidates, source_available = set(), False
        else:
            candidates, source_available = set(huri_by_orf.get(orf, set())), False
        usable = len(candidates) == 1
        partner_errors += int(
            bool(row["source_construct_sequence_available"]) != source_available
        )
        partner_errors += int(set(row["candidate_sequence_hashes"]) != candidates)
        partner_errors += int(bool(row["reference_sequence_usable"]) != usable)
        partner_errors += int(
            row["mapped_sequence_sha256"]
            != (next(iter(candidates)) if usable else None)
        )
        expected_canonical = sorted(
            {
                str(item["sequence_sha256"])
                for item in canonical_by_gene.get(str(row["db_gene_symbol"]), [])
            }
        )
        partner_errors += int(
            expected_canonical != list(row["canonical_candidate_sequence_hashes"])
        )
    checks.require(
        "mapping.independent_construct_and_canonical_recomputation",
        clone_errors == 0 and partner_errors == 0,
        observed={
            "clone_errors": clone_errors,
            "partner_errors": partner_errors,
        },
        expected={"clone_errors": 0, "partner_errors": 0},
    )
    return {
        "clone_rows": len(clone_rows),
        "clone_exact_frozen": sum(
            bool(row["construct_exact_frozen_match"]) for row in clone_rows
        ),
        "partner_rows": len(partner_rows),
        "partner_reference_usable": sum(
            bool(row["reference_sequence_usable"]) for row in partner_rows
        ),
        "clone_errors": clone_errors,
        "partner_errors": partner_errors,
    }


def _evidence_checks(
    checks: Checks,
    connection: duckdb.DuckDBPyConnection,
    allowed_views: list[str],
) -> dict[str, int]:
    allowed = ",".join(_sql(value) for value in sorted(set(allowed_views)))
    connection.execute(
        """
        CREATE TEMP TABLE independent_positive_records AS
        WITH mapped AS (
            SELECT evidence_id, source_key,
                   min(mapped_sequence_sha256) sequence_a,
                   max(mapped_sequence_sha256) sequence_b,
                   count(*) participant_rows
            FROM upstream_participant_sequence_mappings
            WHERE reference_sequence_usable
            GROUP BY evidence_id, source_key
        ), evidence AS (
            SELECT * FROM upstream_huri_evidence
            UNION ALL BY NAME
            SELECT * FROM upstream_intact_evidence
        )
        SELECT mapped.sequence_a, mapped.sequence_b, evidence.source_key,
               evidence.interaction_semantics
        FROM mapped
        JOIN evidence USING (evidence_id, source_key)
        JOIN upstream_evidence_mapping_summaries summary
          USING (evidence_id, source_key)
        WHERE mapped.participant_rows = 2
          AND summary.reference_pair_usable
          AND evidence.observation_state = 'positive'
          AND evidence.participant_count = 2
          AND NOT evidence.original_nary
          AND NOT evidence.is_expanded_projection
        """
    )
    connection.execute(
        f"""
        CREATE TEMP TABLE independent_pair_views AS
        WITH candidates AS (
            SELECT mapping.identifier_versionless gene_id,
                   sequence.sequence_sha256
            FROM upstream_identifier_mappings mapping
            JOIN upstream_protein_sequences sequence
              ON sequence.uniprot_accession = mapping.uniprot_accession
             AND sequence.canonical
            WHERE mapping.database = 'Ensembl'
        ), unique_map AS (
            SELECT gene_id, min(sequence_sha256) sequence_sha256
            FROM candidates GROUP BY gene_id
            HAVING count(DISTINCT sequence_sha256) = 1
        )
        SELECT least(a.sequence_sha256, b.sequence_sha256) sequence_a,
               greatest(a.sequence_sha256, b.sequence_sha256) sequence_b,
               count(*)::BIGINT pair_view_count
        FROM upstream_huri_pair_views pair
        JOIN unique_map a ON a.gene_id = pair.member_a
        JOIN unique_map b ON b.gene_id = pair.member_b
        WHERE pair.source_dataset IN ({allowed}) AND pair.view_membership
        GROUP BY sequence_a, sequence_b
        """
    )
    connection.execute(
        """
        CREATE TEMP TABLE independent_training_pairs AS
        SELECT DISTINCT sequence_a, sequence_b
        FROM independent_positive_records
        WHERE interaction_semantics = 'direct_binary'
        UNION
        SELECT sequence_a, sequence_b FROM independent_pair_views
        """
    )
    connection.execute(
        """
        CREATE TEMP TABLE independent_families AS
        SELECT DISTINCT sequence.sequence_sha256, mapping.identifier family_id
        FROM upstream_protein_sequences sequence
        JOIN upstream_identifier_mappings mapping USING (uniprot_accession)
        WHERE mapping.database = 'UniRef90'
        """
    )
    connection.execute(
        """
        CREATE TEMP TABLE independent_training_family_pairs AS
        SELECT DISTINCT least(a.family_id, b.family_id) family_a,
                        greatest(a.family_id, b.family_id) family_b
        FROM independent_training_pairs pair
        JOIN independent_families a ON a.sequence_sha256 = pair.sequence_a
        JOIN independent_families b ON b.sequence_sha256 = pair.sequence_b
        """
    )
    connection.execute(
        """
        CREATE TEMP TABLE independent_training_family_endpoints AS
        SELECT DISTINCT family_id
        FROM independent_training_pairs pair
        JOIN independent_families family
          ON family.sequence_sha256 = pair.sequence_a
        UNION
        SELECT DISTINCT family_id
        FROM independent_training_pairs pair
        JOIN independent_families family
          ON family.sequence_sha256 = pair.sequence_b
        """
    )
    mismatch = int(
        connection.execute(
            """
            WITH record_counts AS (
                SELECT sequence_a, sequence_b,
                       count_if(source_key = 'huri')::BIGINT huri_count,
                       count_if(interaction_semantics = 'direct_binary')::BIGINT
                           direct_count
                FROM independent_positive_records
                GROUP BY sequence_a, sequence_b
            ), family_expected AS (
                SELECT panel.pair_record_id,
                       coalesce(bool_or(training.family_a IS NOT NULL), false)
                           pair_overlap
                FROM y2h_pair_audit panel
                LEFT JOIN independent_families a
                  ON a.sequence_sha256 = panel.ad_mapped_sequence_sha256
                LEFT JOIN independent_families b
                  ON b.sequence_sha256 = panel.db_mapped_sequence_sha256
                LEFT JOIN independent_training_family_pairs training
                  ON training.family_a = least(a.family_id, b.family_id)
                 AND training.family_b = greatest(a.family_id, b.family_id)
                GROUP BY panel.pair_record_id
            ), endpoint_expected AS (
                SELECT panel.pair_record_id,
                       coalesce(bool_or(training.family_id IS NOT NULL), false)
                           endpoint_overlap
                FROM y2h_pair_audit panel
                LEFT JOIN independent_families family
                  ON family.sequence_sha256 IN (
                      panel.ad_mapped_sequence_sha256,
                      panel.db_mapped_sequence_sha256
                  )
                LEFT JOIN independent_training_family_endpoints training
                  USING (family_id)
                GROUP BY panel.pair_record_id
            ), training_endpoints AS (
                SELECT sequence_a sequence_sha256 FROM independent_training_pairs
                UNION
                SELECT sequence_b FROM independent_training_pairs
            )
            SELECT count(*)
            FROM y2h_pair_audit panel
            LEFT JOIN record_counts records
              ON records.sequence_a = least(
                   panel.ad_mapped_sequence_sha256,
                   panel.db_mapped_sequence_sha256
              )
             AND records.sequence_b = greatest(
                   panel.ad_mapped_sequence_sha256,
                   panel.db_mapped_sequence_sha256
              )
            LEFT JOIN independent_pair_views views
              ON views.sequence_a = least(
                   panel.ad_mapped_sequence_sha256,
                   panel.db_mapped_sequence_sha256
              )
             AND views.sequence_b = greatest(
                   panel.ad_mapped_sequence_sha256,
                   panel.db_mapped_sequence_sha256
              )
            JOIN family_expected family USING (pair_record_id)
            JOIN endpoint_expected endpoints USING (pair_record_id)
            WHERE panel.reference_pair_usable
              AND (
                   panel.huri_positive_record_count <>
                    coalesce(records.huri_count, 0)
               OR panel.permitted_positive_record_count <>
                    coalesce(records.direct_count, 0)
               OR panel.permitted_pair_view_count <>
                    coalesce(views.pair_view_count, 0)
               OR panel.current_permitted_positive_overlap <>
                    (coalesce(records.direct_count, 0) > 0
                     OR coalesce(views.pair_view_count, 0) > 0)
               OR panel.exact_future_training_pair_overlap <>
                    (coalesce(records.direct_count, 0) > 0
                     OR coalesce(views.pair_view_count, 0) > 0)
               OR panel.uniref90_pair_overlap <> family.pair_overlap
               OR panel.exact_endpoint_overlap <>
                    (panel.ad_mapped_sequence_sha256 IN (
                         SELECT sequence_sha256 FROM training_endpoints
                     ) OR panel.db_mapped_sequence_sha256 IN (
                         SELECT sequence_sha256 FROM training_endpoints
                     ))
               OR panel.uniref90_endpoint_overlap <> endpoints.endpoint_overlap
              )
            """
        ).fetchone()[0]
    )
    unusable_flag_errors = int(
        connection.execute(
            """
            SELECT count(*) FROM y2h_pair_audit
            WHERE NOT reference_pair_usable
              AND (current_permitted_positive_overlap
                   OR exact_future_training_pair_overlap
                   OR uniref90_pair_overlap
                   OR exact_endpoint_overlap
                   OR uniref90_endpoint_overlap)
            """
        ).fetchone()[0]
    )
    checks.require(
        "contamination.independent_positive_and_family_recomputation",
        mismatch == 0 and unusable_flag_errors == 0,
        observed={
            "mismatched_pair_rows": mismatch,
            "unusable_rows_with_overlap_flags": unusable_flag_errors,
        },
        expected={
            "mismatched_pair_rows": 0,
            "unusable_rows_with_overlap_flags": 0,
        },
    )
    return {
        "mapped_positive_records": int(
            connection.execute(
                "SELECT count(*) FROM independent_positive_records"
            ).fetchone()[0]
        ),
        "permitted_pair_view_pairs": int(
            connection.execute(
                "SELECT count(*) FROM independent_pair_views"
            ).fetchone()[0]
        ),
        "mismatched_pair_rows": mismatch,
        "unusable_rows_with_overlap_flags": unusable_flag_errors,
    }


def run_validation(
    *,
    project_root: Path,
    config_path: Path,
    report_path: Path | None = None,
    staging_root_override: Path | None = None,
    canonical_root_override: Path | None = None,
    audit_report_override: Path | None = None,
) -> dict[str, Any]:
    require_apptainer()
    config_path = _resolve_inside(
        project_root, config_path, project_root / "configs"
    )
    config = _load_yaml(config_path)
    checks = Checks()
    for name, spec in config["inputs"]["documents"].items():
        path = _resolve_inside(
            project_root,
            str(spec["path"]),
            project_root / str(spec["boundary"]),
        )
        digest = sha256_file(path)
        checks.require(
            f"inputs.{name}.hash",
            digest == str(spec["sha256"]),
            observed={"sha256": digest},
            expected={"sha256": str(spec["sha256"])},
        )
    schema_spec = config["inputs"]["documents"]["audit_schema"]
    schema_path = project_root / str(schema_spec["path"])
    contract = load_contract(schema_path)
    staging_root = _resolve_inside(
        project_root,
        staging_root_override or str(config["outputs"]["staging_root"]),
        project_root / "data/staging",
    )
    canonical_root = _resolve_inside(
        project_root,
        canonical_root_override or str(config["outputs"]["canonical_root"]),
        project_root / "data/canonical",
    )
    staging, staging_inventory = _validate_dataset(
        checks=checks,
        project_root=project_root,
        root=staging_root,
        manifest_name="STAGING_MANIFEST.json",
        expected_tables=STAGING_TABLES,
        contract=contract,
        label="staging",
    )
    canonical, canonical_inventory = _validate_dataset(
        checks=checks,
        project_root=project_root,
        root=canonical_root,
        manifest_name="AUDIT_MANIFEST.json",
        expected_tables=CANONICAL_TABLES,
        contract=contract,
        label="canonical",
    )
    audit_path = _resolve_inside(
        project_root,
        audit_report_override or str(config["outputs"]["audit_report"]),
        project_root / "artifacts/validation",
    )
    audit = _load_json(audit_path)
    audit_digest = sha256_file(audit_path)
    audit_sidecar = audit_path.with_name(audit_path.name + ".sha256")
    checks.require(
        "audit_report.aggregate_only_and_checksummed",
        audit_sidecar.read_text(encoding="utf-8").split()
        == [audit_digest, audit_path.name]
        and not contains_record_keys(audit),
        observed={
            "sha256": audit_digest,
            "contains_record_keys": contains_record_keys(audit),
        },
        expected={"sidecar_matches": True, "contains_record_keys": False},
    )
    acquisition_spec = config["inputs"]["documents"]["acquisition_manifest"]
    acquisition_path = _resolve_inside(
        project_root,
        str(acquisition_spec["path"]),
        project_root / str(acquisition_spec["boundary"]),
    )
    source_metrics, context = _source_reconstruction(
        project_root, config, acquisition_path
    )
    expected = config["expected"]
    expected_source = {
        "source_rows": {
            name: int(expected[name])
            for name in (
                "clone_rows",
                "screen_selection_rows",
                "raw_y2h_rows",
                "public_y2h_rows",
                "raw_n2h_rows",
                "public_n2h_rows",
            )
        },
        "outcome_counts": {
            str(key): int(value)
            for key, value in expected["public_y2h_outcomes"].items()
        },
        "blank_rows": int(expected["public_blank_rows"]),
        "analytical_attempt_rows": int(expected["analytical_attempt_rows"]),
        "analytical_evaluable_rows": int(expected["analytical_evaluable_rows"]),
        "analytical_positive_rows": int(expected["analytical_positive_rows"]),
        "analytical_negative_rows": int(expected["analytical_negative_rows"]),
        "analytical_technical_rows": int(expected["analytical_technical_rows"]),
        "analytical_positive_gene_partner_groups": int(
            expected["analytical_positive_gene_partner_groups"]
        ),
    }
    source_observed = {key: source_metrics[key] for key in expected_source}
    source_valid = (
        source_observed == expected_source
        and source_metrics["public_raw_y2h_crosswalk_disagreements"] == 0
        and source_metrics["clone_fasta_disagreements"] == 0
        and source_metrics["raw_public_n2h_set_concordant"]
        and source_metrics["n2h_log2_recalculation_errors"] == 0
        and all(
            value.casefold() == "cc-by-4.0"
            for value in source_metrics["machine_verified_license_ids"].values()
        )
    )
    checks.require(
        "source.independent_counts_semantics_and_filter",
        source_valid,
        observed={
            **source_observed,
            "crosswalk_errors": source_metrics[
                "public_raw_y2h_crosswalk_disagreements"
            ],
            "clone_fasta_errors": source_metrics["clone_fasta_disagreements"],
            "n2h_set_concordant": source_metrics[
                "raw_public_n2h_set_concordant"
            ],
            "n2h_recalculation_errors": source_metrics[
                "n2h_log2_recalculation_errors"
            ],
            "machine_verified_license_ids": source_metrics[
                "machine_verified_license_ids"
            ],
        },
        expected={
            **expected_source,
            "crosswalk_errors": 0,
            "clone_fasta_errors": 0,
            "n2h_set_concordant": True,
            "n2h_recalculation_errors": 0,
            "machine_verified_license_ids": {
                "code_metadata": "cc-by-4.0",
                "input_metadata": "cc-by-4.0",
            },
        },
    )

    dataset_paths: dict[str, Path] = {}
    for name, relative in config["inputs"]["dataset_paths"].items():
        boundary = project_root / (
            "data/staging"
            if str(relative).startswith("data/staging/")
            else "data/canonical"
        )
        dataset_paths[str(name)] = _resolve_inside(
            project_root, str(relative), boundary
        )
    mapping_metrics = _mapping_checks(
        checks,
        canonical,
        dataset_paths,
        context,
        str(config["inputs"]["frozen_uniprot_release"]),
    )
    connection = duckdb.connect()
    connection.execute(
        f"SET memory_limit='{config['runtime']['duckdb_memory_limit']}'"
    )
    connection.execute(f"SET threads={int(config['runtime']['duckdb_threads'])}")
    try:
        for name, path in {**staging, **canonical, **dataset_paths}.items():
            prefix = "" if name in staging or name in canonical else "upstream_"
            connection.execute(
                f"CREATE TEMP VIEW {prefix}{name} AS "
                f"SELECT * FROM read_parquet({_sql(_glob(path))})"
            )
        row_counts = {
            name: int(
                connection.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
            )
            for name in canonical
        }
        expected_rows = {
            "clone_sequence_mappings": 693,
            "partner_construct_mappings": 753,
            "y2h_pair_audit": 9562,
            "n2h_observation_audit": 765,
            "matched_contrast_groups": 2750,
            "analytical_filter_steps": 6,
        }
        checks.require(
            "canonical.row_counts",
            row_counts == expected_rows,
            observed=row_counts,
            expected=expected_rows,
        )
        governance_true = sum(
            int(
                connection.execute(
                    f"SELECT count(*) FROM {table} "
                    "WHERE training_label_authorized "
                    "OR benchmark_integration_authorized "
                    "OR universal_nonbinding_asserted"
                ).fetchone()[0]
            )
            for table in (
                *(name for name in staging if name != "archive_members"),
                *canonical,
            )
        )
        technical_negative = int(
            connection.execute(
                "SELECT count(*) FROM y2h_pair_audit "
                "WHERE evaluability_state <> 'evaluable' "
                "AND observation_state = 'negative'"
            ).fetchone()[0]
        )
        n2h_binary = int(
            connection.execute(
                "SELECT count(*) FROM n2h_observation_audit "
                "WHERE n2h_binary_label_assigned"
            ).fetchone()[0]
        )
        checks.require(
            "governance.row_level_guards",
            governance_true == technical_negative == n2h_binary == 0,
            observed={
                "true_authorization_guards": governance_true,
                "technical_rows_marked_negative": technical_negative,
                "n2h_binary_labels": n2h_binary,
            },
            expected={
                "true_authorization_guards": 0,
                "technical_rows_marked_negative": 0,
                "n2h_binary_labels": 0,
            },
        )
        pair_table = ds.dataset(
            canonical["y2h_pair_audit"], format="parquet"
        ).to_table(
            columns=[
                "source_row_ordinal",
                "outcome_class",
                "evaluability_state",
                "observation_state",
                "in_post_selection_attempt_universe",
                "in_reported_3509_evaluable_analysis",
            ]
        ).to_pandas().sort_values("source_row_ordinal")
        independent = context["semantic"].sort_index()
        semantic_errors = 0
        for column in (
            "outcome_class",
            "evaluability_state",
            "observation_state",
            "in_post_selection_attempt_universe",
            "in_reported_3509_evaluable_analysis",
        ):
            semantic_errors += int(
                (pair_table[column].to_numpy() != independent[column].to_numpy()).sum()
            )
        semantic_errors += int(
            pair_table.source_row_ordinal.tolist()
            != list(range(1, len(pair_table) + 1))
        )
        checks.require(
            "canonical.rowwise_semantics_and_filter",
            semantic_errors == 0,
            observed={"field_mismatches": semantic_errors},
            expected={"field_mismatches": 0},
        )
        evidence_metrics = _evidence_checks(
            checks,
            connection,
            list(config["evidence_policy"]["permitted_pair_views"]),
        )
        group_mismatches = int(
            connection.execute(
                """
                WITH expected AS (
                  SELECT matched_group_id,
                    count(*) public_rows,
                    count(DISTINCT ad_clone_id) clone_count,
                    count_if(evaluability_state = 'evaluable') evaluable_rows,
                    count_if(observation_state = 'positive') positives,
                    count_if(observation_state = 'negative') negatives,
                    count_if(evaluability_state <> 'evaluable') technical,
                    count_if(evaluability_state = 'evaluable') >= 2
                      AND count(DISTINCT CASE WHEN evaluability_state = 'evaluable'
                                             THEN ad_clone_id END) >= 2 has_two,
                    count_if(observation_state = 'positive') > 0
                      AND count_if(observation_state = 'negative') > 0
                      AND count_if(evaluability_state = 'evaluable') >= 2
                      AND count(DISTINCT CASE WHEN evaluability_state = 'evaluable'
                                             THEN ad_clone_id END) >= 2 contrast,
                    has_two AND count_if(evaluability_state = 'evaluable'
                                         AND reference_pair_usable)
                                = count_if(evaluability_state = 'evaluable') all_usable,
                    all_usable AND count_if(evaluability_state = 'evaluable'
                                            AND exact_future_training_pair_overlap) = 0
                        exact_pair_protected_expected,
                    exact_pair_protected_expected
                      AND count_if(evaluability_state = 'evaluable'
                                   AND uniref90_pair_overlap) = 0
                        family_pair_protected_expected,
                    all_usable AND count_if(evaluability_state = 'evaluable'
                                            AND exact_endpoint_overlap) = 0
                        exact_endpoint_protected_expected,
                    exact_endpoint_protected_expected
                      AND count_if(evaluability_state = 'evaluable'
                                   AND uniref90_endpoint_overlap) = 0
                        family_endpoint_protected_expected
                  FROM y2h_pair_audit
                  GROUP BY matched_group_id
                  HAVING count(DISTINCT ad_clone_id) >= 2
                )
                SELECT count(*)
                FROM matched_contrast_groups actual
                JOIN expected USING (matched_group_id)
                WHERE actual.public_row_count <> expected.public_rows
                   OR actual.distinct_clone_count <> expected.clone_count
                   OR actual.evaluable_row_count <> expected.evaluable_rows
                   OR actual.positive_count <> expected.positives
                   OR actual.explicit_negative_count <> expected.negatives
                   OR actual.technical_count <> expected.technical
                   OR actual.has_two_evaluable_isoforms <> expected.has_two
                   OR actual.has_positive_negative_contrast <> expected.contrast
                   OR actual.all_evaluable_pairs_reference_usable <>
                        expected.all_usable
                   OR actual.exact_pair_protected <>
                        expected.exact_pair_protected_expected
                   OR actual.uniref90_pair_protected <>
                        expected.family_pair_protected_expected
                   OR actual.exact_endpoint_protected <>
                        expected.exact_endpoint_protected_expected
                   OR actual.uniref90_endpoint_protected <>
                        expected.family_endpoint_protected_expected
                """
            ).fetchone()[0]
        )
        checks.require(
            "contrasts.independent_group_and_protection_recomputation",
            group_mismatches == 0,
            observed={"mismatched_groups": group_mismatches},
            expected={"mismatched_groups": 0},
        )
        group_metrics_row = connection.execute(
            """
            SELECT
              count(*) group_count,
              count_if(has_two_evaluable_isoforms) two_evaluable,
              count_if(has_positive_negative_contrast) contrasts,
              count_if(has_positive_negative_contrast AND in_reported_analysis)
                analysis_contrasts,
              count_if(has_positive_negative_contrast
                       AND all_evaluable_pairs_reference_usable) mapped,
              count_if(has_positive_negative_contrast AND exact_pair_protected)
                exact_pair_protected,
              count_if(has_positive_negative_contrast AND uniref90_pair_protected)
                family_pair_protected,
              count_if(has_positive_negative_contrast AND exact_endpoint_protected)
                exact_endpoint_protected,
              count_if(has_positive_negative_contrast
                       AND uniref90_endpoint_protected) family_endpoint_protected
            FROM matched_contrast_groups
            """
        ).fetchone()
        group_metric_names = (
            "matched_groups_with_two_or_more_public_isoforms",
            "groups_with_two_or_more_evaluable_isoforms",
            "positive_negative_evaluable_contrast_groups",
            "reported_analysis_positive_negative_contrast_groups",
            "contrast_groups_all_pairs_reference_usable",
            "contrast_groups_exact_pair_protected",
            "contrast_groups_uniref90_pair_protected",
            "contrast_groups_exact_endpoint_protected",
            "contrast_groups_uniref90_endpoint_protected",
        )
        group_metrics = {
            key: int(value)
            for key, value in zip(
                group_metric_names, group_metrics_row, strict=True
            )
        }
    finally:
        connection.close()

    findings = audit["findings"]
    reported_groups = findings["contamination"]["matched_isoform_contrasts"]
    report_consistent = (
        findings["source_universes"]["clone_cds_translation_concordant"]
        == source_metrics["clone_translation_concordant"]
        and findings["source_universes"][
            "clone_cds_translation_discordant_or_non_codon_length"
        ]
        == source_metrics["clone_translation_discordant"]
        and findings["y2h_semantics"]["outcome_counts"]
        == source_metrics["outcome_counts"]
        and findings["selection_and_filtering"]["analytical_evaluable_rows"]
        == source_metrics["analytical_evaluable_rows"]
        and findings["n2h"]["y2h_ordered_pair_crosswalk_rows"]
        == source_metrics["n2h_y2h_crosswalk_rows"]
        and math.isclose(
            findings["n2h"][
                "spearman_y2h_positive_indicator_vs_continuous_log2_nlr"
            ],
            source_metrics["n2h_spearman"],
            rel_tol=1e-12,
            abs_tol=1e-12,
        )
        and all(reported_groups[key] == value for key, value in group_metrics.items())
        and findings["disposition"]["decision"]
        == "external-only diagnostic candidate"
        and findings["disposition"]["benchmark_protocol_suitable_now"] is False
    )
    checks.require(
        "report.consequential_aggregates_and_disposition",
        report_consistent,
        observed={
            "consistent": report_consistent,
            "disposition": findings["disposition"]["decision"],
        },
        expected={
            "consistent": True,
            "disposition": "external-only diagnostic candidate",
        },
    )
    status = "pass" if checks.passed else "fail"
    report = {
        "schema_version": 1,
        "validator": "independent_tf_isoform_y2h_2025_v1",
        "status": status,
        "checks": checks.records,
        "check_counts": checks.counts(),
        "inventory": {
            "staging": staging_inventory,
            "canonical": canonical_inventory,
        },
        "independent_source_metrics": source_metrics,
        "independent_mapping_metrics": mapping_metrics,
        "independent_evidence_metrics": evidence_metrics,
        "independent_matched_contrast_metrics": group_metrics,
        "governance": {
            "training_labels_created": False,
            "training_data_integrated": False,
            "negatome_merged": False,
            "model_training_tuning_or_thresholding": False,
            "benchmark_constructed": False,
            "universal_nonbinding_interpretation": False,
            "return_to_governance_required": True,
        },
    }
    target = report_path or project_root / str(
        config["outputs"]["validation_report"]
    )
    target = _resolve_inside(
        project_root,
        target,
        project_root / "artifacts/validation",
        strict=False,
    )
    _write_report(target, report, project_root)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/tf_isoform_y2h_audit_v1.yaml"),
    )
    parser.add_argument("--report", type=Path)
    parser.add_argument("--staging-root", type=Path)
    parser.add_argument("--canonical-root", type=Path)
    parser.add_argument("--audit-report", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_validation(
        project_root=project_root_from(Path.cwd()),
        config_path=args.config,
        report_path=args.report,
        staging_root_override=args.staging_root,
        canonical_root_override=args.canonical_root,
        audit_report_override=args.audit_report,
    )
    print(
        json.dumps(
            {"status": result["status"], "check_counts": result["check_counts"]},
            sort_keys=True,
        )
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
