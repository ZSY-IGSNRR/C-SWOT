# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Shengyu Zou and the contributors identified in AUTHORS.md.
"""Validate the public archive without reading any restricted source data.

Default checks use only the Python standard library. Optional --replay imports
NumPy and pandas to reproduce both complete public prediction tables. This is a
field/structure audit, not a determination of copyright or institutional rights.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True

MODEL_FIELDS = {
    "n", "beta", "WSE0", "width0", "depth0", "A0", "train_wse_min",
    "train_wse_max", "train_slope_fallback", "curve_wse", "curve_width",
}
SATELLITE_FIELDS = {
    "station_id", "name", "row_id", "source_row_id", "datetime", "longitude",
    "latitude", "cycle_id", "pass_id", "first_node_id", "node_record_count",
    "unique_node_count", "WSE", "width_observed", "slope_observed",
    "slope_source_time_utc", "slope_time_difference_days", "strict_eligible",
    "source_qc_complete", "same_overpass_reach_found", "participating_node_ids",
    "same_overpass_reach_ids", "overall_bad", "wse_hampel", "width_hampel",
    "slope_hampel",
}
PREDICTION_FIELDS = {
    "Q_estimated", "width_used", "slope_used", "area", "area_position",
    "slope_was_repaired", "prediction_status", "model_available", "WSE_domain",
    "is_out_of_domain", "labels", "is_suspect",
}
ROW_FIELDS = {
    "row_id", "source_row_id", "datetime", "WSE", "width_observed", "width_used",
    "slope_observed", "slope_used", "Q_estimated", "labels", "is_suspect",
    "is_out_of_domain", "prediction_status", "slope_source_time_utc",
    "slope_time_difference_days",
}
STATION_FIELDS = {
    "station_id", "name", "longitude", "latitude", "counts", "data_files",
}
COUNTS_FIELDS = {"rows", "computed", "suspect", "out_of_domain", "excluded"}
PAYLOAD_FIELDS = {"station_id", "name", "variant", "rows", "model", "counts"}
FORBIDDEN_FIELDS = {
    "q_observed", "observed_q", "q_obs", "q_measured", "measured_q", "q_ground",
    "ground_q", "q_ground_truth", "discharge_observed", "observed_discharge",
    "measured_discharge", "gauge_q", "gauge_z", "gauge_date",
    "gauge_match_delta_days", "gauge_match_class", "gauge_exact_day_match",
    "gauge_error_factor", "absolute_error_if_gauge", "is_high_error_observed",
    "high_error_observed", "has_positive_gauge", "gauge_value_status",
    "train_nse", "train_r2", "train_valid_count", "train_q_min", "train_q_max",
    "train_sample_count", "training_sample_count", "calibration_sample_count",
    "training_nse", "training_r2", "q_source_column", "input_gauge_date",
    "input_gauge_q", "input_gauge_z", "input_gauge_match_delta_days",
    "input_gauge_match_class", "input_gauge_exact_day_match", "paired_q",
    "q_paired", "q_reference", "reference_q", "q_in_situ", "insitu_q",
}
BLOCKED_SUFFIXES = {
    ".doc", ".docx", ".xls", ".xlsx", ".xlsm", ".parquet", ".pkl",
    ".pickle", ".pyc", ".pyo", ".zip", ".7z", ".rar", ".sqlite", ".db",
}
BLOCKED_NAMES = {".git", ".env", "__pycache__", ".aws", ".ssh"}
TEXT_SUFFIXES = {
    ".py", ".js", ".json", ".csv", ".txt", ".md", ".html", ".css",
    ".cff", ".yml", ".yaml", ".toml", ".ini", ".cfg",
}
PRIVATE_PATH = re.compile(
    r"(?i)(?:[A-Z]:[/\\](?:Users|SWOT[^/\\\s]*)[/\\]|"
    r"/(?:Users|home)/[^/\s]+/|\\\\[^\\\s]+\\(?:Users|home)\\)"
)
SECRET_PATTERNS = [
    re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{40,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]


class ValidationError(ValueError):
    """A public-package check failed; messages contain relative paths only."""


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def canonical(key):
    name = re.sub(r"(?<=[a-z])(?=[A-Z])", "_", str(key)).lower()
    return re.sub(r"[^a-z0-9]+", "_", name).strip("_")


def check_keys(value, where):
    if isinstance(value, dict):
        for key, item in value.items():
            norm = canonical(key)
            require(norm not in FORBIDDEN_FIELDS, f"Restricted field at {where}: {key}")
            # Broad field families cover ground-pair metadata and training outcomes.
            require(not norm.startswith(("gauge_", "input_gauge_", "paired_")),
                    f"Restricted field family at {where}: {key}")
            check_keys(item, where)
    elif isinstance(value, list):
        for item in value:
            check_keys(item, where)


def read_payload(path):
    text = path.read_text(encoding="utf-8").strip()
    match = re.fullmatch(r"window\.(SWOT_CATALOG|SWOT_STATION_DATA|SWOT_WORLD_LAND)\s*=\s*(.*);", text, re.S)
    require(match is not None, f"Unexpected payload wrapper: {path.name}")
    return json.loads(match.group(2))


def read_csv(path, allowed=None):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames is not None, f"Missing CSV header: {path.name}")
        if allowed is not None:
            require(set(reader.fieldnames) == allowed, f"Unexpected CSV fields: {path.name}")
        rows = list(reader)
    require(all(None not in row for row in rows), f"Malformed CSV rows: {path.name}")
    return rows


def parse_bool(value):
    require(value.lower() in {"true", "false", "1", "0"}, "Invalid public boolean")
    return value.lower() in {"true", "1"}


def compare_value(csv_value, payload_value, field):
    if field == "labels":
        return (csv_value.split("|") if csv_value else []) == payload_value
    if field in {"is_suspect", "is_out_of_domain"}:
        return parse_bool(csv_value) == payload_value
    if field in {"datetime", "prediction_status", "slope_source_time_utc"}:
        return (csv_value or None) == (payload_value or None)
    if not csv_value or csv_value.lower() in {"nan", "none"}:
        return payload_value is None
    try:
        return payload_value is not None and float(csv_value) == float(payload_value)
    except (TypeError, ValueError):
        return csv_value == str(payload_value)


def same_provenance(left, right, field):
    if left == right:
        return True
    if field in {"WSE", "width_observed", "slope_observed", "slope_time_difference_days", "longitude", "latitude"}:
        try:
            return math.isclose(float(left), float(right), rel_tol=1e-12, abs_tol=1e-15)
        except ValueError:
            return False
    return False


def validate_models(root):
    models = {}
    for path in sorted((root / "models").glob("*.json")):
        model = json.loads(path.read_text(encoding="utf-8"))
        require(set(model) == MODEL_FIELDS, f"Model fields differ: models/{path.name}")
        x, y = model["curve_wse"], model["curve_width"]
        require(len(x) == len(y) > 0, f"Invalid model curve: models/{path.name}")
        require(all(math.isfinite(v) for v in x + y), f"Nonfinite model curve: models/{path.name}")
        require(all(b > a for a, b in zip(x, x[1:])), f"Unsorted curve: models/{path.name}")
        require(all(v > 0 for v in y), f"Nonpositive curve width: models/{path.name}")
        require(model["n"] > 0 and model["train_slope_fallback"] > 0,
                f"Invalid hydraulic parameter: models/{path.name}")
        models[path.stem] = model
    require(len(models) > 0, "No public frozen models found")
    return models


def validate_data(root, models):
    catalog = json.loads((root / "metadata/station_catalog.json").read_text(encoding="utf-8"))
    viewer_catalog = read_payload(root / "viewer/data/catalog.js")
    require(viewer_catalog["stations"] == catalog, "Viewer and metadata station catalogs differ")
    stations = {station["station_id"]: station for station in catalog}
    require(len(stations) == len(catalog), "Duplicate station IDs in catalog")
    require(set(models) <= set(stations), "Model has no station catalog entry")
    require(set(viewer_catalog) == {"stations", "flag_definitions", "summary", "exclusions_file"},
            "Unexpected catalog payload fields")
    for station in catalog:
        require(set(station) == STATION_FIELDS, "Unexpected station catalog fields")
        require(set(station["counts"]) == {"strict", "retained"}, "Missing station variant count")
        for variant, counts in station["counts"].items():
            require(set(counts) == COUNTS_FIELDS, "Unexpected station count fields")
            require(station["data_files"][variant] == f"{variant}/{station['station_id']}.js",
                    "Unexpected station payload reference")
    frames, stats, scripts = {}, {}, 1
    for variant in ("strict", "retained"):
        table = read_csv(root / f"data/{variant}/all_observations.csv", SATELLITE_FIELDS | PREDICTION_FIELDS)
        by_id, groups = {}, {sid: [] for sid in stations}
        for row in table:
            require(row["row_id"] not in by_id, f"Duplicate row in {variant}")
            require(row["station_id"] in groups, f"Unknown station in {variant}")
            by_id[row["row_id"]] = row
            groups[row["station_id"]].append(row)
            if variant == "strict":
                require(parse_bool(row["strict_eligible"]) and parse_bool(row["source_qc_complete"]),
                        "Strict row has incomplete or rejected quality evidence")
                require(not any(parse_bool(row[k]) for k in ("overall_bad", "wse_hampel", "width_hampel", "slope_hampel")),
                        "Strict row fails the quality gate")
        computed = 0
        for sid, rows in groups.items():
            csv_path = root / f"data/{variant}/stations/{sid}.csv"
            require(read_csv(csv_path, SATELLITE_FIELDS | PREDICTION_FIELDS) == rows,
                    f"Station CSV differs: data/{variant}/stations/{sid}.csv")
            payload_path = root / f"viewer/data/{variant}/{sid}.js"
            payload = read_payload(payload_path)
            scripts += 1
            require(set(payload) == PAYLOAD_FIELDS, f"Unexpected station payload fields: {variant}/{sid}")
            require(payload["station_id"] == sid and payload["variant"] == variant,
                    f"Incorrect station payload identity: {variant}/{sid}")
            require(payload["model"] == models.get(sid, {}), f"Viewer model differs: {variant}/{sid}")
            require(len(payload["rows"]) == len(rows), f"Viewer row count differs: {variant}/{sid}")
            for source, displayed in zip(rows, payload["rows"]):
                require(set(displayed) == ROW_FIELDS, f"Unexpected viewer row fields: {variant}/{sid}")
                require(all(compare_value(source[field], displayed[field], field) for field in ROW_FIELDS),
                        f"Viewer row differs from CSV: {variant}/{sid}")
            counts = stations[sid]["counts"][variant]
            finite_count = sum(bool(row["Q_estimated"]) and math.isfinite(float(row["Q_estimated"])) for row in rows)
            computed += finite_count
            require(counts["rows"] == len(rows) and counts["computed"] == finite_count,
                    f"Catalog counts differ: {variant}/{sid}")
            require(counts["suspect"] == sum(bool(row["labels"]) for row in rows),
                    f"Catalog label counts differ: {variant}/{sid}")
            require(counts["out_of_domain"] == sum(parse_bool(row["is_out_of_domain"]) for row in rows),
                    f"Catalog domain counts differ: {variant}/{sid}")
            require(payload["counts"] == counts, f"Viewer counts differ: {variant}/{sid}")
        require({p.stem for p in (root / f"data/{variant}/stations").glob("*.csv")} == set(stations),
                f"Unexpected station CSV membership: {variant}")
        require({p.stem for p in (root / f"viewer/data/{variant}").glob("*.js")} == set(stations),
                f"Unexpected station payload membership: {variant}")
        frames[variant] = by_id
        stats[variant] = {"rows": len(table), "computed": computed,
                          "stations_with_estimates": sum(s["counts"][variant]["computed"] > 0 for s in catalog)}
    excluded = read_csv(root / "data/strict/excluded_observations.csv", SATELLITE_FIELDS | {"exclusion_flags"})
    excluded_ids = {row["row_id"] for row in excluded}
    strict_ids, retained_ids = set(frames["strict"]), set(frames["retained"])
    require(len(excluded_ids) == len(excluded), "Duplicate strict-excluded row")
    require(strict_ids.isdisjoint(excluded_ids) and strict_ids | excluded_ids == retained_ids,
            "Strict/excluded partition differs from retained archive")
    for row_id in strict_ids:
        require(frames["strict"][row_id] == frames["retained"][row_id], "Common variant row differs")
    for row in excluded:
        require(all(same_provenance(row[key], frames["retained"][row["row_id"]][key], key) for key in SATELLITE_FIELDS),
                "Excluded satellite provenance differs")
        require(not parse_bool(row["strict_eligible"]), "Excluded row is marked eligible")
    summary = json.loads((root / "metadata/summary.json").read_text(encoding="utf-8"))
    require(summary["station_count"] == len(stations) and summary["modeled_stations"] == len(models),
            "Published station/model summary differs")
    for variant in stats:
        require(summary[f"{variant}_records"] == stats[variant]["rows"] and
                summary[f"{variant}_computed"] == stats[variant]["computed"], "Published prediction summary differs")
    require(summary["strict_excluded"] == len(excluded), "Published exclusion summary differs")
    return {"station_count": len(stations), "frozen_models": len(models), "variants": stats,
            "excluded_records": len(excluded), "station_payload_scripts_checked": scripts,
            "csv_viewer_values_identical": True, "strict_retained_common_rows_identical": True,
            "excluded_table_has_no_prediction_fields": True, "strict_quality_gate_passes": True}


def scan_files(root, allow_git_worktree=False):
    counts = {"csv_headers_checked": 0, "json_files_checked": 0, "payload_scripts_checked": 0, "files_checked": 0}
    counts["root_git_metadata_ignored"] = allow_git_worktree and (root / ".git").exists()
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if allow_git_worktree and path.relative_to(root).parts[0] == ".git":
            continue
        require(not path.is_symlink(), f"Symlink is outside public archive scope: {rel}")
        require(not any(part in BLOCKED_NAMES or part.startswith(".env.") for part in path.relative_to(root).parts),
                f"Private/build directory or file: {rel}")
        if not path.is_file():
            continue
        counts["files_checked"] += 1
        require(path.suffix.lower() not in BLOCKED_SUFFIXES, f"Unsupported private/build/archive file: {rel}")
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in {"LICENSE", ".gitignore", ".gitattributes", ".nojekyll"}:
            text = path.read_text(encoding="utf-8-sig")
            require(PRIVATE_PATH.search(text) is None, f"Local/private path in text: {rel}")
            require(not any(pattern.search(text) for pattern in SECRET_PATTERNS), f"Possible credential/private key: {rel}")
        if path.suffix.lower() == ".csv":
            with path.open(encoding="utf-8-sig", newline="") as stream:
                header = next(csv.reader(stream), None)
            require(header is not None and len(set(header)) == len(header), f"Invalid CSV header: {rel}")
            check_keys(dict.fromkeys(header), rel)
            counts["csv_headers_checked"] += 1
        elif path.suffix.lower() == ".json":
            check_keys(json.loads(path.read_text(encoding="utf-8")), rel)
            counts["json_files_checked"] += 1
        elif path.suffix.lower() == ".js" and (path.is_relative_to(root / "viewer/data") or
                path.read_text(encoding="utf-8").lstrip().startswith("window.SWOT_WORLD_LAND=")):
            check_keys(read_payload(path), rel)
            counts["payload_scripts_checked"] += 1
    return counts


def checksum_manifest(root, manifest, immutable_only=False):
    checked, expected_paths = 0, set()
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, rel = line.split("  ", 1)
        if immutable_only and not rel.startswith(("data/", "models/", "viewer/data/")):
            continue
        path = root / rel
        require(not Path(rel).is_absolute() and path.resolve().is_relative_to(root.resolve()),
                "Unsafe checksum manifest path")
        require(path.is_file(), f"Checksum target missing: {rel}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        require(actual == expected, f"Checksum mismatch: {rel}")
        checked += 1
        expected_paths.add(rel)
    require(checked > 0, "Checksum manifest contains no applicable files")
    if immutable_only:
        actual_paths = {p.relative_to(root).as_posix() for base in ("data", "models", "viewer/data")
                        for p in (root / base).rglob("*") if p.is_file()}
        require(actual_paths == expected_paths, "Immutable data/model/payload file membership changed")
    return checked


def replay_predictions(root, models):
    import numpy as np
    import pandas as pd
    spec = importlib.util.spec_from_file_location("public_frozen_model", root / "code/frozen_model.py")
    require(spec is not None and spec.loader is not None, "Missing public inference core")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = {}
    for variant in ("strict", "retained"):
        frame = pd.read_csv(root / f"data/{variant}/all_observations.csv", dtype={"station_id": str})
        predictions = np.full(len(frame), np.nan)
        for sid, group in frame.groupby("station_id"):
            if sid in models:
                predictions[group.index] = module.apply_model(models[sid], group.WSE, group.slope_observed)["Q_estimated"]
        saved = frame.Q_estimated.to_numpy(float)
        require(np.allclose(predictions, saved, rtol=1e-10, atol=1e-8, equal_nan=True),
                f"Standalone inference differs: {variant}")
        result[variant] = {"rows": len(frame), "replayed_predictions": int(np.isfinite(predictions).sum()),
                           "maximum_absolute_roundoff": float(np.nanmax(abs(predictions - saved)))}
    result["runtime"] = {"python": sys.version.split()[0], "numpy": np.__version__, "pandas": pd.__version__}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--package", type=Path, default=Path("."), help="Public repository root (default: current directory)")
    parser.add_argument("--output", type=Path, help="Optional JSON report destination; default prints only")
    parser.add_argument("--replay", action="store_true", help="Replay all public predictions; requires NumPy and pandas")
    parser.add_argument("--checksums", action="store_true", help="Also verify the current SHA256SUMS.txt")
    parser.add_argument("--allow-git-worktree", action="store_true", help="Ignore only root .git metadata for a clone/CI checkout; omit for release-archive validation")
    parser.add_argument("--reference-manifest", type=Path, help="Compare immutable data/models/viewer data with an earlier public checksum manifest")
    args = parser.parse_args()
    root = args.package.resolve()
    report = {
        "passed": False,
        "scan_scope": "All CSV headers, JSON object keys, viewer JSON payload keys, exact public model/row schemas, CSV-viewer agreement, QC partitions, local-path and common credential patterns, and prohibited files. This audit does not establish legal rights or detect every possible secret/identifying value.",
        "restricted_source_data_read": False,
        "parameter_refits": 0,
    }
    try:
        require(root.is_dir(), "Public package directory does not exist")
        report["file_scan"] = scan_files(root, args.allow_git_worktree)
        models = validate_models(root)
        report["data_consistency"] = validate_data(root, models)
        if args.reference_manifest:
            report["unchanged_public_data_model_payload_files"] = checksum_manifest(root, args.reference_manifest, True)
        if args.replay:
            report["standalone_replay"] = replay_predictions(root, models)
        if args.checksums:
            report["checksum_files_verified"] = checksum_manifest(root, root / "SHA256SUMS.txt")
        report["passed"] = True
    except (ValidationError, OSError, ValueError, KeyError, ImportError,
            TypeError, AttributeError, IndexError, OverflowError) as exc:
        # Keep local paths out of distributable reports, including system errors.
        message = str(exc) if isinstance(exc, ValidationError) else f"{type(exc).__name__}: invalid/missing public input or dependency"
        report["failure"] = message
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
