#!/usr/bin/env python3
"""Compile and exercise repository packages against an immutable IRMind release."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from package_contract import compile_package, package_hash, packages, safe_data_path


def run(args, root):
    subprocess.run([str(arg) for arg in args], cwd=root, check=True, timeout=1800)


def copy_exact(source, target):
    data = source.read_bytes()
    if target.exists() and target.read_bytes() == data:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)


def overlay(repository, irmind):
    mapping = json.loads((repository / 'source-map.json').read_text())
    if mapping['format_version'] != 1 or len(mapping['files']) > 512:
        raise ValueError('unsupported source map')
    destinations = {}
    for row in mapping['files']:
        source = safe_data_path(repository, row['source'])
        target = safe_data_path(irmind, row['path'])
        if row['source'].startswith('core/'):
            if row['path'] != 'skills/' + row['source'][5:]:
                raise ValueError('core mirror path changed')
        elif row['source'].startswith('episodes/'):
            if not (row['path'].startswith('crates/testkit/fixtures/') or
                    row['path'].startswith('crates/modules/parser-json/tests/fixtures/')):
                raise ValueError('episode mirror escapes fixture directories')
            if target.suffix not in ('.json', '.jsonl', '.ndjson', '.log', '.txt', '.csv'):
                raise ValueError('episode mirror is not fixture data')
        else:
            raise ValueError('invalid source-map origin')
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if digest != row['sha256']:
            raise ValueError('source-map checksum mismatch')
        if row['path'] in destinations and destinations[row['path']] != digest:
            raise ValueError('conflicting fixture mirrors')
        destinations[row['path']] = digest
        copy_exact(source, target)


def validate(repository, irmind):
    for tree in ('core', 'catalog', 'episodes', 'metadata'):
        directory = repository / tree
        if directory.is_symlink():
            raise ValueError('linked data directory')
        for path in directory.rglob('*'):
            if path.is_symlink():
                raise ValueError('linked fixture or package')
            if path.is_file() and path.stat().st_size > 1_000_000:
                raise ValueError('synthetic fixture exceeds development limit')
    core = json.loads((repository / 'core/package-identities.json').read_text())
    observed = {path.parent.name: package_hash(path.parent) for path in packages(repository, 'core')}
    if core != observed:
        raise ValueError('core inventory does not match package bytes')
    catalog = packages(repository, 'catalog')
    if any(path.parent.name in core for path in catalog):
        raise ValueError('catalog package shadows a core name')
    command_specs = (irmind / 'crates/tui/src/case/command_registry/specs.rs').read_text()
    reserved = set(re.findall(r'name:\s*"([a-z0-9-]+)"', command_specs))
    if len(reserved) < 10:
        raise ValueError('released command registry changed; review the development adapter')
    if any(path.parent.name in reserved for path in catalog):
        raise ValueError('catalog package shadows a built-in command')
    run(['cargo', 'build', '-p', 'irmind', '--example', 'validate_skill',
         '--all-features', '--profile', 'ci', '--locked'], irmind)
    metadata = json.loads(subprocess.check_output(['cargo', 'metadata', '--format-version', '1',
                          '--no-deps', '--locked'], cwd=irmind, text=True))
    target = Path(metadata['target_directory']) / 'ci/examples'
    compiler = target / 'validate_skill'
    compiled = []
    for family in ('core', 'catalog'):
        for method in packages(repository, family):
            meta, digest = compile_package(compiler, method.parent)
            episode = repository / 'episodes' / family / meta['name'] / 'episode.json'
            if not episode.is_file():
                raise ValueError('package has no scripted synthetic episode')
            compiled.append({'family': family, 'name': meta['name'], 'sha256': digest})
    overlay(repository, irmind)
    adapter = irmind / 'crates/bin/examples/catalog_episode.rs'
    if adapter.exists() and adapter.read_bytes() != (repository / 'tools/episode_harness.rs').read_bytes():
        raise ValueError('release contains a different catalog adapter; review tool compatibility')
    copy_exact(repository / 'tools/episode_harness.rs', adapter)
    run(['cargo', 'build', '-p', 'irmind', '--example', 'catalog_episode',
         '--all-features', '--profile', 'ci', '--locked'], irmind)
    for row in compiled:
        run([target / 'catalog_episode', repository, row['family'], row['name']], irmind)
        row['scripted_episode'] = 'passed'
    # Exercise signed local admission as well when the production catalog is empty.
    # The test honestly uses Analyst origin; it does not invent publisher trust.
    with tempfile.TemporaryDirectory(prefix='catalog-template-') as temporary:
        sample = Path(temporary)
        name = 'community-example-method'
        shutil.copytree(repository / 'template/package', sample / 'catalog' / name)
        shutil.copytree(repository / 'template/episode', sample / 'episodes/catalog' / name)
        shutil.copytree(repository / 'template/private', sample / 'episodes/private')
        compile_package(compiler, sample / 'catalog' / name)
        run([target / 'catalog_episode', sample, 'catalog', name], irmind)
    # Compile the publisher adapter without a credential. Even local validation
    # launches its absence check with a fresh environment containing only PATH.
    signer_source = repository / 'tools/production_signer.rs'
    if signer_source.is_file():
        signer_adapter = irmind / 'crates/bin/examples/catalog_sign.rs'
        if signer_adapter.exists() and signer_adapter.read_bytes() != signer_source.read_bytes():
            raise ValueError('release contains a different signing adapter; use a clean checkout')
        copy_exact(signer_source, signer_adapter)
        run(['cargo', 'build', '-p', 'irmind', '--example', 'catalog_sign',
             '--all-features', '--profile', 'ci', '--locked'], irmind)
        absent = subprocess.run([str(target / 'catalog_sign')], env={'PATH': os.environ['PATH']},
                                capture_output=True, text=True, timeout=15)
        if absent.returncode != 1 or absent.stdout or absent.stderr != 'Catalog signing failed; no release should be published.\n':
            raise ValueError('signer must fail closed without its protected runtime secret')
    # Existing release tests also retain the detailed HuntEval and hostile-evidence checks.
    run(['cargo', 'nextest', 'run', '-p', 'irmind', '--test', 'skills_runtime',
         '--all-features', '--cargo-profile', 'ci', '--locked', '--test-threads', '4',
         '-E', 'test(three_bundled_methods_complete) | test(/^support::catalog::.*_episode$/) | '
               'test(rejects_hostile_evidence) | test(signed_untrusted_method)'], irmind)
    (repository / 'validation-results.json').write_text(json.dumps({
        'format_version': 1, 'compiler_commit': subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=irmind, text=True).strip(),
        'provider_calls': 0, 'packages': compiled, 'template_signed_admission': 'passed',
    }, indent=2) + '\n')
    print(f'Validated {len(core)} core and {len(catalog)} catalog packages with the released compiler.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--irmind', type=Path, required=True)
    args = parser.parse_args()
    try:
        validate(Path(__file__).resolve().parents[1], args.irmind.resolve())
    except (ValueError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
