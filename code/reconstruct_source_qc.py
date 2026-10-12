# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Shengyu Zou and the contributors identified in AUTHORS.md.
"""Rebuild satellite-only, same-overpass QC evidence for archived station rows.

No gauge or discharge measurements are read.  RiverSP ``node_q`` and
``reach_q`` are categorical overall-quality codes, not discharge values.
The archive's median/first QC columns and slope-fallback source are never used
as evidence for the quality of its original same-overpass reach.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

QUALITY = {
    "accepted_node_q": [0, 1],
    "accepted_reach_q": [0, 1],
    "hampel_window": 3,
    "hampel_sigma": 3.0,
}
KEY = ["_day", "_cycle", "_pass"]
SOURCE_COLUMNS = {
    "station_id", "node_id", "reach_id", "reach_id_x", "reach_id_y",
    "cycle_id", "pass_id", "swot_date", "time_str", "time_utc",
    "node_record_count", "unique_node_count", "reach_slope_source",
    "reach_slope_source_time_utc", "reach_slope_fallback_used",
    "reach_slope_match_delta_seconds",
}
PARTICIPANT_COLUMNS = {
    "node_id", "reach_id", "reach_id_x", "cycle_id", "pass_id",
    "time_str", "time_utc",
}
RAW_COLUMNS = {
    "node_id", "reach_id", "cycle_id", "pass_id", "time_str",
    "wse", "width", "slope", "node_q", "reach_q",
}
QC_COLUMNS = PARTICIPANT_COLUMNS | {
    "qc_overall_quality_ok", "qc_hampel_wse", "qc_hampel_width",
    "qc_hampel_slope", "qc_time_ok",
}

# In-memory caches are keyed by absolute input path, mtime, and size.  Every
# raw/QC feature file is parsed at most once during a build, even for nodes
# shared by multiple stations.  No original or intermediary file is modified.
_FILE_CACHE: dict[tuple[str, int, int, str], pd.DataFrame] = {}


def _ids(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)


def _read(path: Path, columns: set[str], kind: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    stat = path.stat()
    key = (str(path.resolve()), stat.st_mtime_ns, stat.st_size, kind)
    if key not in _FILE_CACHE:
        # usecols is a strict allowlist; gauge_Q, gauge_Z and all dschg/SoS
        # discharge columns cannot enter memory, the returned frame or cache.
        frame = pd.read_csv(path, usecols=lambda c: c in columns, dtype="string")
        _FILE_CACHE[key] = frame
    return _FILE_CACHE[key].copy()


def _keys(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    time = frame.get("time_str", frame.get("time_utc", pd.Series(pd.NA, index=frame.index)))
    frame["_time"] = pd.to_datetime(time, errors="coerce", utc=True)
    day = frame.get("swot_date", frame["_time"])
    frame["_day"] = pd.to_datetime(day, errors="coerce", utc=True).dt.floor("D")
    for original, key in [("cycle_id", "_cycle"), ("pass_id", "_pass")]:
        frame[key] = _ids(frame.get(original, pd.Series(pd.NA, index=frame.index)))
    for column in ["node_id", "reach_id", "reach_id_x", "reach_id_y"]:
        if column in frame:
            frame[column] = _ids(frame[column])
    return frame


def _truth(series: pd.Series) -> pd.Series:
    text = series.astype("string").str.lower()
    return text.map({"true": True, "false": False, "1": True, "0": False,
                     "1.0": True, "0.0": False}).astype("boolean")


def _hampel(values: pd.Series) -> pd.Series:
    # Exact quality.py implementation: a second centered rolling median of
    # deviations, not a freshly computed median deviation in each window.
    # read_csv(dtype="string") preserves IDs, but to_numeric then yields
    # pandas nullable Float64. Original quality.py uses numpy float/NaN:
    # comparisons at missing measurements are False, not pd.NA.
    values = values.astype("float64")
    median = values.rolling(7, center=True, min_periods=3).median()
    absolute = (values - median).abs()
    mad = absolute.rolling(7, center=True, min_periods=3).median()
    scale = 1.4826 * mad
    return (absolute > 3.0 * scale) & scale.gt(0)


def _feature_qc(outputs: Path, feature_id: str, profile: str) -> pd.DataFrame:
    """Return all raw rows with recomputed flags, or surviving QC evidence."""
    raw_path = outputs / "raw" / profile / f"{feature_id}.csv"
    raw = _read(raw_path, RAW_COLUMNS, "raw")
    stat_key = None
    if raw_path.exists():
        stat = raw_path.stat()
        stat_key = (str(raw_path.resolve()), stat.st_mtime_ns, stat.st_size, "flags")
        if stat_key in _FILE_CACHE:
            return _FILE_CACHE[stat_key].copy()
    if not raw.empty:
        frame = _keys(raw).sort_values("_time").reset_index(drop=True)
        qcolumn = "node_q" if profile == "node_d" else "reach_q"
        # These are the exact quality codes used by quality.py's
        # qc_overall_quality_ok = numeric_code.isin([0, 1]).
        if qcolumn in frame:
            quality_code = pd.to_numeric(frame[qcolumn], errors="coerce")
            frame["_overall_bad"] = ~quality_code.isin([0, 1])
        else:
            frame["_overall_bad"] = pd.Series(pd.NA, index=frame.index, dtype="boolean")
        required = ["wse", "width"] + (["slope"] if profile == "reach_d" else [])
        frame["_flags_complete"] = (qcolumn in raw) and all(c in raw for c in required)
        for column in ["wse", "width", "slope"]:
            flag = pd.Series(False, index=frame.index, dtype="boolean")
            if column in raw:
                numeric = pd.to_numeric(frame[column], errors="coerce").mask(
                    lambda s: s <= -1.0e10
                )
                # quality.py sorts each feature globally, then computes each
                # pass's Hampel on the full raw sequence before any exclusion.
                for indices in frame.groupby("_pass", dropna=False).groups.values():
                    flag.loc[indices] = _hampel(numeric.loc[indices])
            elif column != "slope" or profile == "reach_d":
                flag[:] = pd.NA
            frame[f"_{column}_bad"] = flag
        frame["_evidence"] = "raw_reconstructed"
        keep = [*KEY, "_time", "_overall_bad", "_wse_bad", "_width_bad",
                "_slope_bad", "_flags_complete", "_evidence"]
        frame = frame[keep]
        if stat_key is not None:
            _FILE_CACHE[stat_key] = frame
        return frame.copy()

    # A QC file proves only its surviving rows; absence from it is not proof
    # of rejection. Missing raw files remain explicitly distinguishable.
    surviving = _read(outputs / "qc" / profile / f"{feature_id}.csv", QC_COLUMNS, "qc")
    if surviving.empty:
        return pd.DataFrame()
    frame = _keys(surviving)
    overall = frame.get("qc_overall_quality_ok", pd.Series(pd.NA, index=frame.index))
    frame["_overall_bad"] = ~_truth(overall)
    for column in ["wse", "width", "slope"]:
        name = f"qc_hampel_{column}"
        frame[f"_{column}_bad"] = (
            _truth(frame[name]) if name in frame else
            pd.Series(False if profile == "node_d" and column == "slope" else pd.NA,
                      index=frame.index, dtype="boolean")
        )
    names = ["qc_overall_quality_ok", "qc_hampel_wse", "qc_hampel_width"]
    if profile == "reach_d":
        names += ["qc_hampel_slope"]
    frame["_flags_complete"] = all(c in surviving for c in names)
    frame["_evidence"] = "qc_survivor_only"
    return frame[[*KEY, "_time", "_overall_bad", "_wse_bad", "_width_bad",
                  "_slope_bad", "_flags_complete", "_evidence"]]


def _any(values: Any) -> Any:
    # Groups contain only 1--3 participant nodes in normal archives. Scalar
    # iteration avoids constructing many tiny pandas frames/series per row.
    seen = False
    unknown = False
    for value in values:
        seen = True
        if pd.isna(value):
            unknown = True
        elif bool(value):
            return True
    return pd.NA if unknown or not seen else False


def _station_nodes(mapping: pd.DataFrame) -> pd.DataFrame:
    frame = mapping.copy()
    if "within_max_distance" in frame:
        frame = frame[_truth(frame["within_max_distance"]).fillna(False)]
    frame = frame[frame["node_id"].notna()]
    if "neighbor_offset" in frame:
        offsets = pd.to_numeric(frame["neighbor_offset"], errors="coerce")
        frame = frame[offsets.abs().le(1)].copy()
        frame["_offset"] = offsets.loc[frame.index].abs()
        frame["_signed"] = offsets.loc[frame.index]
        frame = frame.sort_values(["_offset", "_signed"])
    elif "selection_role" in frame:
        frame["_order"] = frame["selection_role"].ne("nearest")
        frame = frame.sort_values("_order")
    return frame.drop_duplicates("node_id").head(3)


def _participants(outputs: Path, nodes: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for item in nodes.itertuples():
        node_id = str(item.node_id)
        path = outputs / "fused" / "node_reach" / f"{node_id}.csv"
        frame = _read(path, PARTICIPANT_COLUMNS, "participant")
        layer = "fused_node_reach"
        if not path.exists():
            frame = _read(outputs / "qc" / "node_d" / f"{node_id}.csv",
                          PARTICIPANT_COLUMNS, "participant_qc")
            layer = "qc_node_d_fallback"
        if frame.empty:
            continue
        frame = _keys(frame)
        frame["node_id"] = frame.get("node_id", pd.Series(node_id, index=frame.index))
        frame["_reach"] = frame.get("reach_id_x", frame.get("reach_id"))
        # Never use reach_id_y: it represents the QC-filtered attachment.
        if frame["_reach"].isna().any():
            frame["_reach"] = frame["_reach"].fillna(str(item.reach_id))
        frame["_reach"] = _ids(frame["_reach"])
        frame["_participant_layer"] = layer
        raw_qc = _feature_qc(outputs, node_id, "node_d")
        if not raw_qc.empty:
            # Exact node time distinguishes actual contributing rows when a
            # cycle/pass/day contains duplicate acquisitions.
            evidence = raw_qc.drop_duplicates([*KEY, "_time"], keep=False)
            frame = frame.merge(evidence, on=[*KEY, "_time"], how="left", validate="many_to_one")
        else:
            for name in ["_overall_bad", "_wse_bad", "_width_bad", "_slope_bad", "_flags_complete", "_evidence"]:
                frame[name] = pd.NA
        parts.append(frame)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def _summaries(frame: pd.DataFrame, participants: bool = False) -> dict:
    """Aggregate tiny groups with scalar values; avoid one DataFrame per row."""
    if frame.empty:
        return {}
    flags = ["_overall_bad", "_wse_bad", "_width_bad", "_slope_bad"]
    columns = [*KEY, *flags, "_flags_complete", "_evidence"]
    if participants:
        columns += ["node_id", "_reach"]
    summaries: dict = {}
    for values in frame[columns].itertuples(index=False, name=None):
        key = tuple(values[:3])
        item = summaries.setdefault(key, {
            "count": 0, "complete": True, "evidence": set(),
            "nodes": set(), "reaches": set(),
            **{flag: False for flag in flags},
        })
        item["count"] += 1
        for flag, value in zip(flags, values[3:7]):
            item[flag] = _any([item[flag], value])
        item["complete"] &= pd.notna(values[7]) and bool(values[7])
        if pd.notna(values[8]):
            item["evidence"].add(values[8])
        if participants:
            if pd.notna(values[9]):
                item["nodes"].add(values[9])
            if pd.notna(values[10]):
                item["reaches"].add(values[10])
    return summaries


def _one_station(outputs: Path, path: Path, nodes: pd.DataFrame) -> pd.DataFrame:
    source = _keys(_read(path, SOURCE_COLUMNS, "source"))
    source["source_row_id"] = np.arange(len(source), dtype=int)
    source["station_id"] = path.stem
    participant = _participants(outputs, nodes)
    records = []
    grouped = _summaries(participant, participants=True)
    reach_frames = {
        reach: _feature_qc(outputs, reach, "reach_d")
        for reach in ([] if participant.empty else participant["_reach"].dropna().unique())
    }
    reach_groups = {reach: _summaries(frame) for reach, frame in reach_frames.items()}
    for row in source.itertuples(index=False, name=None):
        values = dict(zip(source.columns, row))
        key = tuple(values[c] for c in KEY)
        part = grouped.get(key)
        expected = pd.to_numeric(values.get("node_record_count"), errors="coerce")
        expected_unique = pd.to_numeric(values.get("unique_node_count"), errors="coerce")
        count_ok = part is not None and pd.notna(expected) and part["count"] == expected
        unique_ok = (part is not None and pd.notna(expected_unique)
                     and len(part["nodes"]) == expected_unique)
        reaches = [] if part is None else sorted(part["reaches"])
        reach_parts = [reach_groups.get(reach, {}).get(key) for reach in reaches]
        reach_found = bool(reaches) and all(item is not None for item in reach_parts)
        matched_reach = [item for item in reach_parts if item is not None]
        node_complete = part is not None and part["complete"]
        reach_complete = reach_found and all(item["complete"] for item in matched_reach)
        keys_valid = pd.notna(values["_day"]) and all(pd.notna(values[c]) for c in ["_cycle", "_pass"])
        complete = bool(count_ok and unique_ok and node_complete and reach_complete and keys_valid)
        bads = {}
        for level, summaries in [("node", [] if part is None else [part]), ("reach", matched_reach)]:
            for flag in ["overall", "wse", "width", "slope"]:
                bads[f"raw_{level}_{flag}_bad"] = _any([item[f"_{flag}_bad"] for item in summaries])
        for flag in ["wse", "width", "slope"]:
            bads[f"{flag}_hampel_bad"] = _any([
                bads[f"raw_node_{flag}_bad"], bads[f"raw_reach_{flag}_bad"]
            ])
        overall_bad = _any([bads["raw_node_overall_bad"], bads["raw_reach_overall_bad"]])
        any_bad = _any([overall_bad, *[bads[f"{f}_hampel_bad"] for f in ["wse", "width", "slope"]]])
        strict_ok = bool(complete and pd.notna(any_bad) and not any_bad)
        records.append({
            "station_id": path.stem, "source_row_id": values["source_row_id"],
            "same_overpass_reach_found": reach_found,
            "source_qc_complete": complete, "strict_qc_eligible": strict_ok,
            "source_node_record_count": expected,
            "participating_node_record_count": 0 if part is None else part["count"],
            "participant_count_matches_archive": bool(count_ok and unique_ok),
            "participating_node_ids": "|".join([] if part is None else sorted(part["nodes"])),
            "same_overpass_reach_ids": "|".join(reaches),
            "same_overpass_raw_reach_rows": sum(item["count"] for item in matched_reach),
            "node_evidence_sources": "|".join([] if part is None else sorted(part["evidence"])),
            "reach_evidence_sources": "|".join(sorted(set().union(*(item["evidence"] for item in matched_reach)))),
            "overall_quality_bad": overall_bad, "hampel_any_bad": _any([
                bads[f"{f}_hampel_bad"] for f in ["wse", "width", "slope"]
            ]), **bads,
        })
    result = pd.DataFrame(records)
    for column in result:
        if column.endswith("_bad"):
            result[column] = result[column].astype("boolean")
    return result


def build_qc_audit(project: str | Path, output: str | Path | None) -> pd.DataFrame:
    """Return one satellite-only audit row per original station archive row.

    ``project`` is the fusion project root or its ``outputs`` directory.
    ``output`` is a writable directory for qc_audit_notes.json, or None.
    The returned frame is joined on station_id + zero-based source_row_id.
    Unknown QC remains nullable; strict_qc_eligible is False when incomplete.
    """
    project = Path(project)
    outputs = project if (project / "fused").exists() else project / "outputs"
    mapping = _read(outputs / "inventory" / "station_feature_map.csv", {
        "station_id", "node_id", "reach_id", "within_max_distance",
        "neighbor_offset", "selection_role",
    }, "inventory")
    for column in ["station_id", "node_id", "reach_id"]:
        mapping[column] = _ids(mapping[column])
    maps = {str(station): _station_nodes(frame) for station, frame in mapping.groupby("station_id")}
    archive = outputs / "fused" / "station_overpasses_datum_adjusted"
    frames = [_one_station(outputs, path, maps.get(path.stem, mapping.iloc[:0]))
              for path in sorted(archive.glob("*.csv"))]
    result = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    notes = {
        "schema_version": 1,
        "project": str(project.resolve()),
        "join": ["station_id", "source_row_id"],
        "source_row_id": "zero-based position in the original station archive CSV, before filtering",
        "quality": QUALITY,
        "participant_mapping": "inventory maximum 3 nodes, fused/node_reach same UTC day + cycle_id + pass_id; exact node time for raw QC; archive counts verified",
        "reach_mapping": "each actual participant's reach_id_x (or original reach_id), same UTC day + cycle_id + pass_id; never slope fallback source",
        "hampel": "exact quality.py: sorted full raw feature sequence, per pass, centered 7 rows, min_periods=3, rolling median of absolute deviations, sigma=3, scale=1.4826",
        "unknown_policy": "nullable bad flags; source_qc_complete=False; strict_qc_eligible=False",
        "qc_missing_raw_policy": "existing QC survivors may supply explicit flags, labelled qc_survivor_only; a missing QC row cannot prove rejection",
        "forbidden_data": "gauge_Q, gauge_Z, other gauge measurements and dschg/SoS discharge values excluded by read allowlists",
        "overall_quality_codes": "node_q/reach_q are categorical RiverSP overall quality codes used by quality.py, not measured discharge",
        "rows": len(result),
        "stations": int(result["station_id"].nunique()) if len(result) else 0,
        "source_qc_complete_rows": int(result["source_qc_complete"].sum()) if len(result) else 0,
        "strict_qc_eligible_rows": int(result["strict_qc_eligible"].sum()) if len(result) else 0,
        "same_overpass_reach_missing_rows": int((~result["same_overpass_reach_found"]).sum()) if len(result) else 0,
        "participant_count_mismatch_rows": int((~result["participant_count_matches_archive"]).sum()) if len(result) else 0,
        "bad_flag_counts": {c: int(result[c].fillna(False).sum()) for c in result if c.endswith("_bad")},
        "unknown_flag_counts": {c: int(result[c].isna().sum()) for c in result if c.endswith("_bad")},
        "cache_entries": len(_FILE_CACHE),
    }
    result.attrs["qc_audit_notes"] = notes
    if output is not None:
        target = Path(output)
        target.mkdir(parents=True, exist_ok=True)
        (target / "qc_audit_notes.json").write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
