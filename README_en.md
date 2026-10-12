# SWOT discharge estimates: strict and retained QC variants

[GitHub release guide](docs/GITHUB_RELEASE_en.md) · [Copyright and citation](viewer/en/about.html)

Version 1.1.0, prepared locally on 2026-10-12; no upload has occurred. Both variants use the same frozen v15 station models. The catalog contains 1,143 stations; 542 have saved models. Eligible records from stations without a model remain with an empty discharge estimate.

| Variant | Overpass records | Estimated discharge | QC exclusions |
| --- | ---: | ---: | ---: |
| Strict QC / 严格版 | 47,864 | 25,061 | 30,779 |
| Retained / 保留标注版 | 78,643 | 41,098 | 0 |

Open index.html to choose a language and QC policy, or use viewer/en/index.html and viewer/zh/index.html directly. The viewer runs offline, without Python or network access. By default it shows only stations with at least one discharge estimate in the selected QC version (542 stations in each current variant). Select "Show all stations" to browse all 1,143 catalog stations. The station list, map points and nearest-station query follow this setting. Language switching preserves it; QC switching evaluates availability in the selected version. This setting affects the viewer only; released data files remain complete. The map opens at the station extent, offers a world view, and supports station selection and nearest-station queries from longitude/latitude. Station names retain their source spelling; controls, status, flags and notes are bilingual.

## Policy definitions

Strict QC filters each station-overpass record before model prediction. An overall-quality failure in any actual contributing node or original same-overpass reach, or any applicable WSE/width/slope Hampel flag, excludes the whole record. Overall quality accepts node_q/reach_q codes 0 and 1; these are satellite quality codes. Existing station Hampel flags and full-satellite-series flags are included. Forty records lack complete original same-overpass QC evidence and are excluded with an explicit Unverified QC flag.

The 30,779 exclusions remain in data/strict/excluded_observations.csv with satellite inputs, QC evidence and reasons. This file contains no discharge predictions or model intermediates, and its records never enter the strict prediction calls. Historical calibration parameters and geometry remain frozen; this policy has neither recleaned the historical calibration samples nor recalibrated or reevaluated manuscript accuracy.

The retained policy keeps all 78,643 existing archived station-overpass records and preserves the width/area and slope logic. Existing archive means the archive available to this study: raw node records excluded earlier upstream have not been restored. Common records have identical discharge estimates in both variants.

As explicitly selected for this release, both policies preserve the archived slope substitution after QC. A missing/nonpositive same-overpass slope may have been replaced by the nearest positive reach slope from another time, without a maximum temporal separation. Source dates can precede or follow the current overpass. Slope replacement labels, source times and offsets remain explicit. A missing/nonpositive archived input slope instead invokes the saved positive station reference and the distinct Slope reference label.

## Flags and screening

Tables use concise labels such as Quality anomaly, WSE anomaly, Width anomaly, Slope anomaly, Hydraulic extrapolation, Slope replacement, Area floor, Unverified QC and No model. Definitions appear in the viewer notes and metadata/flag_definitions.csv; point/table selection exposes the relevant variables. Applicability and curve/reference-deviation labels alone do not cause strict exclusion; the actual exclusion gates are overall quality, Hampel flags and evidence completeness.

Original node/reach Hampel processing reproduces upstream QC within each pass: centered seven-row windows, at least three values, a rolling median and a second rolling median of absolute deviations, and a three-scale threshold. Existing station flags come from the archive. The full satellite sequence uses centered eleven-row local exact MAD windows, a three-scale threshold, and WSE/width/log10(slope) scale floors of 0.02 m, 1 m and 0.05. Screening depends on satellite inputs only. A warning is an inspection prompt rather than a verified discharge error.

## Public scope and interpretation

Released CSV/JSON and viewer scripts exclude measured discharge, gauge matching dates/classes/status, observation-level measured errors, training NSE/R², and outcome-based flags or selection. Q_estimated is a model estimate. Frozen parameters retain earlier gauge-calibration constraints; their release is not an observation-level ground comparison. WSE is expressed in the study datum already used by v15, rather than unadjusted official absolute elevation.

The package provides retrospective reconstructions. Cross-date slopes and centered QC can use later information. These results do not constitute live prediction or an independent forward temporal test. Unmatched predictions do not provide accuracy-validation samples. The variants compare QC policies; improved accuracy under strict QC has not been established by this release.

## Files and reproduction

- data/strict and data/retained: combined and station CSVs, with exclusions kept separately.
- models: an allowlisted set of essential parameters and width anchors for 542 stations.
- metadata: catalog, definitions, counts and map provenance.
- viewer: editable bilingual HTML/CSS/JavaScript and offline station payloads.
- code/frozen_model.py: inference using satellite inputs and saved parameters only.
- code/reconstruct_source_qc.py: original same-overpass QC recovery; source satellite records and contributor inventory must be supplied separately, without restricted ground data.
- checks: prediction, privacy, integrity and browser checks; SHA256SUMS.txt provides file hashes.

Computation used Python 3.13, NumPy 2.3.1 and pandas 2.3.1. Viewing requires only a modern browser. From the package directory:

```shell
python code/frozen_model.py --input data/strict/all_observations.csv --models models --output strict_reproduced.csv
python code/frozen_model.py --input data/retained/all_observations.csv --models models --output retained_reproduced.csv
```

Use new output filenames. The script calculates only the supplied variant records; it never merges in the exclusion audit. Row identifiers and explicit QC columns support direct policy verification.


To rebuild both policies from the complete public archive:

```shell
python code/rebuild_variants.py --output rebuilt_variants
```

## License, citation and deposit preparation

Study-authored code uses MIT; original documentation, released frozen parameters and derived estimates use CC BY 4.0. Upstream materials retain their terms. The offline physical-land map is Natural Earth 110m land 4.1.0, public domain, without national boundaries. Archived station coordinates have not been resurveyed; nearest-station distances use a spherical approximation. See the licenses, CITATION.cff and map provenance. The source SWOT Version D DOI is 10.5067/SWOT-RIVERSP-D.

Deposit the ZIP as a Dataset and verify the real author list in CITATION.cff and the local metadata/zenodo_metadata.json draft. Authors and the associated title were checked against v15. No deposit DOI is assigned; add the actual DOI and publication date after Zenodo assigns them. The original private package and manuscript are unchanged.
