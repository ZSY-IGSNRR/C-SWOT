# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Shengyu Zou and the contributors identified in AUTHORS.md.
"""Build the public static viewer using explicit paths, without publishing it."""
import argparse
from pathlib import Path
import shutil


def build(package, output):
    package, output = package.resolve(), output.resolve()
    if output == package or output in package.parents:
        raise ValueError('The output must not replace the package or an ancestor.')
    if output.exists():
        raise ValueError('Output exists; choose a new directory.')
    required = ['index.html', 'AUTHORS.md', 'CITATION.cff', 'CITATION.bib',
                'CITATION.md', 'LICENSE', 'LICENSE_CODE.txt', 'LICENSE_DATA.txt',
                'README.md', 'README_zh.md', 'README_en.md',
                'data/strict/excluded_observations.csv',
                'metadata/NATURAL_EARTH_NOTICE.txt', 'metadata/map_source.json',
                'metadata/source_products.csv', 'metadata/release_info.json']
    directories = ['viewer', 'docs']
    for rel in required + directories:
        if not (package / rel).exists():
            raise FileNotFoundError(rel)
    # Never stage raw sources, notebooks, manuscript files, Git history or credentials.
    for rel in directories:
        for source in (package / rel).rglob('*'):
            if source.is_symlink():
                raise ValueError('Symlinks are not supported: ' + source.relative_to(package).as_posix())
            if source.is_file() and source.suffix.lower() not in {'.html', '.css', '.js', '.md', '.txt'}:
                raise ValueError('Unexpected website file: ' + source.relative_to(package).as_posix())
    output.mkdir(parents=True)
    for rel in required:
        target = output / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(package / rel, target)
    for rel in directories:
        shutil.copytree(package / rel, output / rel)
    (output / '.nojekyll').write_text('', encoding='utf-8')
    return sum(p.is_file() for p in output.rglob('*'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    count = build(args.package, args.output)
    print(f'Staged {count} public website files. No upload or deployment occurred.')


if __name__ == '__main__':
    main()
