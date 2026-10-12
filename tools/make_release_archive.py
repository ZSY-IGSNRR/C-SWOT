# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Shengyu Zou and the contributors identified in AUTHORS.md.
"""Validate a clean public release, refresh checksums and create a new local ZIP."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

sys.dont_write_bytecode = True


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--output', type=Path, required=True,
                        help='New ZIP filename outside the repository directory')
    parser.add_argument('--allow-git-worktree', action='store_true',
                        help='Skip the root .git only; never bundle Git history')
    args = parser.parse_args()
    package, target = args.package.resolve(), args.output.resolve()
    if target.is_relative_to(package):
        parser.error('The ZIP must be outside the repository directory.')
    if target.suffix.lower() != '.zip':
        parser.error('The output must be a .zip filename.')
    if target.exists() or target.with_suffix('.zip.sha256').exists():
        parser.error('Output exists; choose a new archive filename.')
    command = [sys.executable, str(package / 'tools/verify_public_release.py'), '--package', str(package)]
    if args.allow_git_worktree:
        command.append('--allow-git-worktree')
    # Do not package anything until the field and file audit passes.
    result = subprocess.run(command, check=True, text=True, capture_output=True, encoding='utf-8')
    audit = json.loads(result.stdout)
    if not audit.get('passed'):
        raise ValueError('Public-release validation failed.')
    files = sorted(p for p in package.rglob('*') if p.is_file()
                   and p.name != 'SHA256SUMS.txt'
                   and p.relative_to(package).parts[0] != '.git')
    hashes = {p.relative_to(package).as_posix(): digest(p) for p in files}
    manifest = package / 'SHA256SUMS.txt'
    manifest.write_text(''.join(value + '  ' + rel + '\n' for rel, value in hashes.items()), encoding='utf-8')
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files + [manifest]:
            archive.write(path, package.name + '/' + path.relative_to(package).as_posix())
    with zipfile.ZipFile(target) as archive:
        if archive.testzip() is not None:
            raise ValueError('ZIP CRC validation failed.')
        for rel, value in hashes.items():
            if hashlib.sha256(archive.read(package.name + '/' + rel)).hexdigest() != value:
                raise ValueError('Archive content mismatch: ' + rel)
        if archive.read(package.name + '/SHA256SUMS.txt') != manifest.read_bytes():
            raise ValueError('Archived checksum manifest differs.')
    zip_hash = digest(target)
    target.with_suffix('.zip.sha256').write_text(zip_hash + '  ' + target.name + '\n', encoding='ascii')
    print(json.dumps({'archive_name': target.name, 'files': len(files) + 1,
                      'bytes': target.stat().st_size, 'sha256': zip_hash,
                      'zip_integrity_verified': True, 'uploaded': False}, indent=2))


if __name__ == '__main__':
    main()
