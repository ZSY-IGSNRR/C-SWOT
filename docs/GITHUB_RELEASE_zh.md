# GitHub 本地发布版：上传与网页部署指南

本文件夹已整理为可直接导入 Git 的公开发布草稿，科学版本为 **1.1.0**，准备日期为 **2026-10-12**。目前没有上传，也没有创建远程仓库、Release、GitHub Pages 或 Zenodo 记录。原始私有数据和论文文件不在此仓库内。

## 先在本地查看

解压整个发布包，保留目录结构，双击根目录 `index.html` 选择中英文网页。也可以分别打开 `viewer/zh/index.html` 和 `viewer/en/index.html`。网页可以离线运行，包含站点地图、经纬度查询和两种 QC 版本。默认显示当前版本有 Q 估算的 542 个站点；勾选“显示全部站点”后显示完整的 1,143 个站点。

网页上的 Q 全部是模型估算。公开文件排除了实测 Q、逐观测地面配对信息和实测误差；质量标签来自卫星输入和模型适用范围。严格版保留 47,864 条记录，其中 25,061 条有 Q 估算，另有 30,779 条排除记录单独保存。保留标注版有 78,643 条记录，其中 41,098 条有 Q 估算。

## 上传前补充真实身份与发布信息

作者和顺序已依据 v15 整理在 `AUTHORS.md` 和 `CITATION.cff` 中。发布负责人需核对作者拼写、实际代码与数据权利人，以及适用的共同作者或单位授权；当前文件没有声称这些权属已经逐项核实。只有查实后才补充单位、ORCID、通讯作者和贡献角色。代码采用 MIT，原创派生数据及说明采用 CC BY 4.0；两种许可均允许商业使用，具体义务见 `RIGHTS_AND_USAGE_zh.md`。

仓库建立后填写真实仓库地址；正式发布后填写真实发布日期。Zenodo DOI 和论文出版信息应在实际获得后更新。不要把准备日期写成已公开发布日期，也不要填写示例 DOI 或占位 ORCID。

## 推荐使用 GitHub Desktop

1. 下载并登录 [GitHub Desktop](https://desktop.github.com/)，保留解压后的独立文件夹。不要将 ZIP 本身作为整个代码仓库上传。
2. 在 Desktop 中通过 **File → Add local repository** 选择该文件夹。若提示尚不是 Git 仓库，可使用其 **create a repository here** 入口，在现有文件夹中创建本地仓库。保留现有 README、许可证和目录，不用模板覆盖它们。
3. 在 Changes 中检查将提交的文件，确认只有此公开版内容。不要从私有研究目录整体导入。运行后产生的环境目录、缓存和输出应保持在忽略范围内。
4. 做首次本地提交，例如 `Prepare public v1.1.0 release`。检查真实 Git 身份信息；不要以工具或软件名称作为研究作者。
5. **只有准备公开时**才点击 **Publish repository**，选择真实仓库名、所属账号与可见性。需要先审核的可以先建私有仓库；公开许可并不意味着本地文件已经自动上传。
6. 公布前核对 `CITATION.cff`、`CITATION.bib`、`CITATION.md` 和 README 中的真实标识信息。保留本地原包和校验值。

`data/retained/all_observations.csv` 约 28.7 MiB，超过 GitHub 网页上传单文件 25 MiB 限制。当前文件可以通过 GitHub Desktop/Git 提交；无需为了浏览器上传随意拆分数据。后续增大的文件需重新检查 GitHub 限制。[GitHub 官方说明](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)

## 检查公开文件与校验值

从 ZIP 解压且没有 `.git` 目录的本地发布包，用以下命令检查：

```shell
python tools/verify_public_release.py --package .
```

clone 下来的仓库，或已经初始化 Git 的本地仓库，应使用：

```shell
python tools/verify_public_release.py --package . --allow-git-worktree
```

`--allow-git-worktree` 仅允许仓库根目录的 `.git` 元数据，其他公开范围、受限内容排除和完整性检查仍然执行。它不会放行其他私有文件。不要将 `.git` 或私有研究文件打包进公开 ZIP。

## 手动部署中英文网页

仓库中附有手动触发的 Pages 工作流，触发方式为 `workflow_dispatch`。提交和推送不会自动执行此部署。

1. 准备让网页公开时，在仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。能否使用 Pages 取决于仓库可见性和账号方案。
2. 打开 **Actions**，选择仓库提供的 Pages 工作流，点击 **Run workflow**，选择真实包含此发布版的分支并手动运行。不需要假定分支叫 `main`。
3. 成功后，从工作流或 Pages 设置取得实际网页地址，分别检查中英文入口、QC 切换、站点筛选、地图和 CSV 下载。
4. 将真实网页地址加入 README；将真实仓库地址加入引用信息。不要提前写未经生成的在线地址。

工作流的具体名称以仓库中的配置为准。公开网页应只部署此经过检查的公开版文件，不应指向私有工作目录。[GitHub Pages 官方说明](https://docs.github.com/en/pages/getting-started-with-github-pages/using-github-pages-with-github-actions)

也可以先在本地准备静态站点目录：

```shell
python tools/build_site.py --output _site
```

`_site` 已存在时应换一个新的输出目录。此命令只整理本地站点文件，不执行上传或发布；离线阅览仍可直接打开根目录 `index.html`。

## 正式 Release 与 Zenodo

在需要固定正式版本时，可以为确认的提交建立版本标签并创建 GitHub Release。使用 `v1.1.0` 前先检查该标签是否已存在；已有正式版本不要覆盖。发布说明应保留两种 QC 记录数、排除范围和冻结模型的解释。ZIP 可以作为 Release 附件，放在源码仓库目录之外。

Zenodo 可以归档公开 GitHub Release，并为归档记录提供 DOI。启用联动和创建 Release 均为后续由发布负责人执行的公开操作，本次本地整理没有进行。取得 DOI 后，更新引用文件与说明，区分具体版本 DOI 和覆盖多个版本的 concept DOI。[GitHub–Zenodo 官方说明](https://docs.github.com/en/repositories/archiving-a-github-repository/referencing-and-citing-content)

## 运行公开代码

推荐 Python 3.13。在 PowerShell 中进入此文件夹后运行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python code/frozen_model.py --input data/strict/all_observations.csv --models models --output strict_reproduced.csv
python code/frozen_model.py --input data/retained/all_observations.csv --models models --output retained_reproduced.csv
python code/rebuild_variants.py --output rebuilt_variants
```

如果 PowerShell 不允许激活环境，可以直接用 `.\.venv\Scripts\python.exe` 代替后续命令中的 `python`，无需修改系统执行策略。输出目录或文件必须尚不存在。

以上程序重放冻结模型的公开推算，并使用公开 QC 字段重建两种版本。它们不重新率定模型，也不计算需要受限实测 Q 的论文精度。上游 QC 重建还需要另行提供程序要求的卫星来源记录和节点贡献清单，二者应继续排除受限地面数据。

## 更新文件后重新打包

请在干净的公开目录运行校验；环境、计算输出和缓存保留在仓库外。`.gitignore` 不会自动清除本地文件，发布包校验仍会检查实际文件。

修改引用或说明后，在此目录运行下列命令。输出 ZIP 必须在仓库目录外且尚不存在；命令会刷新 `SHA256SUMS.txt`，逐文件验证 ZIP，并生成 ZIP 的 `.sha256` 文件，不会上传。

```shell
python tools/make_release_archive.py --output ../SWOT_public_updated.zip
```

若操作的是含根 `.git` 的 Git 工作目录，可追加 `--allow-git-worktree`。打包始终排除 Git 历史，其他文件继续接受公开范围核查。
