# How to cite this release

## Current local draft

The scientific package version is **1.1.0**, prepared locally on **2026-10-12**. Preparation is distinct from public release: there is currently no assigned repository URL, public release date or deposit DOI. The citations below identify the draft honestly and should be updated with the real published record before use in a final paper.

**Package:** Shengyu Zou, Zhenwu Xu, Jingyi Tian, Jiao Wang, Zixuan Tang, Xian Wang, Zhen Huang, Haoshan Wei, Ping Miao, Yongqiang Zhang. *SWOT satellite discharge estimates with strict and retained quality-control variants accompanying manuscript v15* (Version 1.1.0) [Dataset and accompanying software; local release draft].

**Associated manuscript:** Shengyu Zou, Zhenwu Xu, Jingyi Tian, Jiao Wang, Zixuan Tang, Xian Wang, Zhen Huang, Haoshan Wei, Ping Miao, Yongqiang Zhang. *Estimating Streamflow Across Major Chinese Rivers Using SWOT Satellite Data and Sparse Ground Observations*. Unpublished manuscript, version v15.

The manuscript citation describes an unpublished work. WRR volume, issue, pages, acceptance status and DOI are not asserted. When a published article exists, replace the manuscript entry with its verified bibliographic record. Cite both the package and the article when their separate contributions are used.

## Machine-readable files

- [CITATION.cff](CITATION.cff) supplies the complete author order, package version, licenses and associated unpublished manuscript. Keeping this file at the GitHub repository root enables GitHub's citation interface.
- [CITATION.bib](CITATION.bib) supplies a package entry and a separate unpublished-manuscript entry. It contains no fabricated DOI or repository URL.

Academic citation is requested for scholarly reuse. License obligations remain component-specific: software redistribution requires retaining the MIT notice, while reuse of original data/documentation requires appropriate CC BY attribution and identification of changes.

## Upstream data credit

The principal satellite source is [SWOT RiverSP, Version D](https://doi.org/10.5067/SWOT-RIVERSP-D). Additional access/reference resources recorded in [metadata/source_products.csv](metadata/source_products.csv) are [Hydrocron 1.6.4](https://doi.org/10.5281/zenodo.15831782) and [SWORD 17b](https://doi.org/10.5281/zenodo.15299138). Use each source's own preferred citation when it contributes to your analysis. The offline basemap credit is **Made with Natural Earth**; the physical-land data are public domain.

## After public release

1. Add the actual public repository address to `repository-code` in `CITATION.cff` and to the package's `url` in `CITATION.bib`.
2. Add the real public release date to `date-released` and the corresponding publication year to the BibTeX package entry.
3. Add the version-specific Zenodo DOI to `doi` once assigned. For this exact version, use its version DOI; record a concept DOI separately if one is also assigned.
4. Confirm author spellings/order and add verified affiliations and ORCIDs where appropriate. Never use placeholder identity numbers.
5. Add the actual manuscript publication or preprint record when available. Keep package and article citations distinct.
6. Regenerate file hashes and the distribution archive after metadata changes, and retain the release tag and commit identifier with the archived record.

GitHub citation behavior: [official documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files).
