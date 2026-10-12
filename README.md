# SWOT discharge estimates: bilingual public release

[中文详细说明](README_zh.md) · [Detailed English documentation](README_en.md) · [中文发布指南](docs/GITHUB_RELEASE_zh.md) · [English release guide](docs/GITHUB_RELEASE_en.md)

**Version 1.1.0 — prepared locally on 2026-10-12.** This folder is a GitHub-ready draft. It has not been uploaded, and no repository URL, public release date or deposit DOI has been assigned. The scientific data, quality-control policies and frozen v15 models are the same as the corresponding public package.

This repository contains editable Chinese and English station viewers, released SWOT-derived discharge estimates, frozen station parameters, public inference/QC code, provenance and citation information. It supports inspection and replay of the released estimates. The underlying gauge-calibration observations and observation-level ground comparisons are excluded.

## Open the viewer

Download or clone the whole repository and open [index.html](index.html) in a modern browser. The viewer works offline; Python and an internet connection are unnecessary.

- [中文版网页](viewer/zh/index.html)
- [English viewer](viewer/en/index.html)

The default view contains stations with at least one discharge estimate in the selected QC variant: **542 stations** in each current variant. Enable **显示全部站点 / Show all stations** to browse the full **1,143-station** catalog. The list, map and coordinate-based nearest-station query follow this setting. Language switching retains it, and changing QC variant reevaluates which stations have calculated discharge. The setting affects the display only; the public data remain complete.

## Released variants

| QC variant | Retained station-overpass records | Records with Q estimates | QC exclusions |
| --- | ---: | ---: | ---: |
| Strict QC / 严格版 | 47,864 | 25,061 | 30,779 |
| Retained with flags / 保留标注版 | 78,643 | 41,098 | 0 |

Strict QC excludes a whole record before inference when its contributing satellite data fail overall quality, trigger an applicable WSE/width/slope Hampel flag, or lack complete original QC evidence. The retained variant keeps the existing archive and exposes its quality flags. Both use the same frozen models and existing slope-substitution logic; estimates on common records are identical. Stations without saved models retain an empty Q estimate. Full definitions and limitations appear in the detailed READMEs and viewer notes.

## Run the public code

The documented environment is Python 3.13 with NumPy 2.3.1 and pandas 2.3.1. From the repository root, create a separate environment:

```shell
python -m venv .venv
```

Activate `.venv` using the platform-specific instructions in the release guides, then install [requirements.txt](requirements.txt) and run:

```shell
python -m pip install -r requirements.txt
python code/frozen_model.py --input data/strict/all_observations.csv --models models --output strict_reproduced.csv
python code/frozen_model.py --input data/retained/all_observations.csv --models models --output retained_reproduced.csv
python code/rebuild_variants.py --output rebuilt_variants
```

Choose new output paths because the scripts protect existing outputs.

The code replays satellite inference from saved parameters and rebuilds the two released policies from public QC fields. It does not fit new station models or reproduce accuracy statistics that require restricted measured discharge. Reconstruction of upstream QC requires the separately supplied public satellite source records and contributor inventory described in the code.

These estimates are retrospective. Archived cross-date slope substitution and centered QC may use later observations. QC warnings describe satellite inputs and model applicability; they are not verified discharge errors.

## Verify the package or build the static site

For an extracted distribution ZIP without a `.git` directory, validate the public files and hashes with:

```shell
python tools/verify_public_release.py --package .
```

For a cloned repository or another local Git working tree, use:

```shell
python tools/verify_public_release.py --package . --allow-git-worktree
```

`--allow-git-worktree` exempts only the repository-root `.git` metadata. All other public-file, exclusion and integrity checks remain in force; the option does not authorize private files.

To prepare the static Pages directory locally, run:

```shell
python tools/build_site.py --output _site
```

Choose a new output directory if `_site` already exists. Building the site prepares local files only and does not publish them. Opening the root `index.html` directly remains sufficient for offline browsing.

## Repository contents

| Path | Contents |
| --- | --- |
| `viewer/` | Bilingual HTML/CSS/JavaScript, station payloads and offline land map |
| `data/` | Strict/retained combined and station CSVs; separate strict exclusion audit |
| `models/` | Essential frozen parameters and width anchors for 542 stations |
| `code/` | Public inference, QC reconstruction and policy rebuilding |
| `tools/` | Public-package validation and static-site preparation |
| `metadata/` | Variable definitions, counts, provenance and release metadata |
| `checks/` | Reproduction, privacy, integrity and browser verification records |
| `docs/` | Bilingual GitHub release and rights/usage guides |
| `.github/workflows/` | Public-release validation and manually triggered GitHub Pages deployment |

## Authors, license and citation

The ten study authors and their order are recorded in [AUTHORS.md](AUTHORS.md), based on manuscript v15. Original study software and viewer code use [MIT](LICENSE_CODE.txt). Original derived estimates, frozen parameters, QC annotations and documentation use [CC BY 4.0](LICENSE_DATA.txt), within the rights held by their creators. Upstream SWOT/SWORD/Hydrocron material keeps its source terms; the Natural Earth physical-land map is public domain. [LICENSE](LICENSE) lists these separate scopes.

MIT permits commercial reuse and requires preservation of its copyright and license notices. CC BY 4.0 permits commercial reuse with appropriate attribution, the license link and an indication of changes. An academic citation is requested for scholarly use; the code's MIT license does not separately require a paper citation. See [rights and usage](docs/RIGHTS_AND_USAGE_en.md) for attribution examples and the remaining authorship checks before public release.

Use [CITATION.cff](CITATION.cff), [CITATION.bib](CITATION.bib) and [CITATION.md](CITATION.md). The associated manuscript is identified as **unpublished v15**, with no invented journal citation or DOI. After a real repository and deposit exist, add their actual identifiers to the citation files.

## Prepare for GitHub and Pages

Use the bilingual [release guides](docs/GITHUB_RELEASE_en.md) to import the extracted folder into GitHub Desktop and review the files before publishing. The retained combined CSV is approximately 28.7 MiB and exceeds GitHub's browser-upload limit; Desktop/Git can handle the current files. Keep the ZIP outside the code repository and attach it to a Release if desired.

The included Pages workflow is manually triggered. Publishing a repository or pushing commits does not run that workflow automatically. No remote, repository, Release, Pages deployment or Zenodo deposit has been created by preparing this folder.
