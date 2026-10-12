# GitHub release preparation and deployment guide

This folder is a local GitHub-ready draft of scientific version **1.1.0**, prepared on **2026-10-12**. It has not been uploaded. No remote repository, Release, GitHub Pages deployment or Zenodo record has been created. The private research files and manuscript are outside this repository.

## Inspect locally

Extract the complete folder and preserve its directory structure. Open the root `index.html` to select a language, or open `viewer/en/index.html` and `viewer/zh/index.html` directly. The viewer works offline and includes a station map, coordinate-based nearest-station query and two QC policies. Its default view shows the 542 stations with Q estimates in the current variant; **Show all stations** reveals the complete 1,143-station catalog.

Every displayed Q is a model estimate. Public files exclude measured discharge, observation-level gauge matching and measured errors. Quality flags describe satellite inputs and model applicability. Strict QC retains 47,864 records, including 25,061 Q estimates, with 30,779 excluded records kept separately. The retained-with-flags variant contains 78,643 records, including 41,098 Q estimates.

## Complete verified release information

`AUTHORS.md` and `CITATION.cff` contain the ten authors in manuscript-v15 order. The responsible author should confirm name spellings, actual code/data rights holders and applicable coauthor or institutional authorization before public release. This preparation does not certify those rights. Add affiliations, ORCIDs, contact details and contribution roles only after verification.

Software uses MIT; original derived data and documentation use CC BY 4.0. Both permit commercial reuse under their respective conditions. See `RIGHTS_AND_USAGE_en.md`. Add the actual repository URL after creating the repository and the actual release date after public release. Add a Zenodo DOI and manuscript publication record only when assigned; do not substitute the preparation date or example identifiers.

## Use GitHub Desktop

1. Install and sign into [GitHub Desktop](https://desktop.github.com/). Keep the extracted release folder separate from private research files. Do not upload only a ZIP as the source repository.
2. Use **File → Add local repository** to select this folder. If it is not a Git repository, use Desktop's **create a repository here** option to initialize the existing folder. Keep the supplied files and avoid overwriting the README or licenses with templates.
3. Review the Changes list before committing. Include only the public package. Leave environment folders, caches and generated replay outputs ignored.
4. Make an initial local commit, for example `Prepare public v1.1.0 release`. Verify your actual Git author identity.
5. Click **Publish repository** only when ready to create the remote repository. Choose your real account, repository name and visibility. A private repository can be used for preliminary review. Preparing files locally does not perform this step.
6. Update the citation files and documentation with verified public identifiers, and keep the original archive and hashes outside the repository.

The retained combined CSV is approximately 28.7 MiB, above GitHub's 25 MiB browser-upload limit. The current files can be committed through Desktop/Git. Recheck file limits if future versions grow. [Official file-size guidance](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)

## Validate public files and hashes

For a distribution ZIP extracted without a `.git` directory, run:

```shell
python tools/verify_public_release.py --package .
```

For a cloned repository or an initialized local Git working tree, run:

```shell
python tools/verify_public_release.py --package . --allow-git-worktree
```

`--allow-git-worktree` exempts only the repository-root `.git` metadata. Other public-scope, restricted-content and integrity checks remain active; the option does not permit additional private files. Exclude `.git` and private research files from a distribution ZIP.

## Deploy the bilingual viewer manually

The supplied Pages workflow uses `workflow_dispatch`. Commits and pushes do not automatically trigger it.

1. When ready to make the viewer public, choose **GitHub Actions** under the repository's **Settings → Pages → Build and deployment → Source**. Pages availability depends on repository visibility and account plan.
2. Open **Actions**, select the supplied Pages workflow and use **Run workflow** on the actual branch containing this release. The branch need not be named `main`.
3. After success, obtain the real site address from the workflow or Pages settings. Check both language routes, QC switching, station filtering, map interactions and CSV download.
4. Add the real viewer address to README and the real repository URL to the citation metadata.

Use the workflow name present in the repository configuration. Deploy only this reviewed public folder. [Official Pages Actions guidance](https://docs.github.com/en/pages/getting-started-with-github-pages/using-github-pages-with-github-actions)

To prepare the static site locally:

```shell
python tools/build_site.py --output _site
```

Choose a new output directory if `_site` already exists. This command prepares local site files without uploading or publishing them. Directly opening the root `index.html` remains sufficient for offline viewing.

## Create an immutable research record

To freeze a formal public version, tag the approved commit and create a GitHub Release. Check whether `v1.1.0` already exists before using it; preserve existing formal versions. Include the QC counts, exclusions and frozen-model interpretation in the release notes. Attach a distribution ZIP to the Release if useful, keeping it outside the source tree.

Zenodo can archive public GitHub Releases and assign a DOI. Enabling the integration and publishing a Release are later actions for the responsible author; neither occurred during this local preparation. Once assigned, record the version-specific DOI and distinguish it from a concept DOI covering multiple versions. [Official GitHub–Zenodo guidance](https://docs.github.com/en/repositories/archiving-a-github-repository/referencing-and-citing-content)

## Run public inference and policy rebuilding

The documented environment is Python 3.13, NumPy 2.3.1 and pandas 2.3.1. From the folder root on Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python code/frozen_model.py --input data/strict/all_observations.csv --models models --output strict_reproduced.csv
python code/frozen_model.py --input data/retained/all_observations.csv --models models --output retained_reproduced.csv
python code/rebuild_variants.py --output rebuilt_variants
```

If PowerShell does not permit activation, call `.\.venv\Scripts\python.exe` directly in place of `python` in subsequent commands. Changing system execution policy is unnecessary. On macOS/Linux, activate with `source .venv/bin/activate`, or call `.venv/bin/python` directly. Use new output paths.

These programs replay the frozen station estimates and rebuild the policies from public QC fields. They do not refit calibration models or reproduce accuracy statistics requiring restricted measured discharge. Upstream QC reconstruction requires separately supplied satellite records and contributor inventory, with restricted ground observations excluded.

## Repackage after local edits

Run release validation on a clean public folder. Keep environments, calculation outputs and caches outside it. `.gitignore` does not remove local files; the release validator inspects the files actually present.

After updating metadata or documentation, run the following from the repository root. The archive must be outside the repository and must not exist. This command refreshes `SHA256SUMS.txt`, checks each archived file and creates a ZIP `.sha256` file. It does not upload anything.

```shell
python tools/make_release_archive.py --output ../SWOT_public_updated.zip
```

For a Git working directory with a root `.git`, append `--allow-git-worktree`. Git history is always excluded from the archive; all other files remain subject to the public-release audit.
