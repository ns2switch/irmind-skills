#!/usr/bin/env python3
"""Build a canonical rehearsal index from catalog/ only; never publish a release."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from package_contract import canonical, compile_package, packages, resources


def build(repository, compiler, output, key_id, tag, commit):
    if not re.fullmatch('[0-9a-f]{64}', key_id) or not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('invalid public key or commit identity')
    if not re.fullmatch(r'v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:-[a-z0-9.-]+)?', tag):
        raise ValueError('invalid frozen release tag')
    reserved = set(json.loads((repository / 'core/package-identities.json').read_text()))
    output.mkdir(parents=True, exist_ok=True)
    entries = []
    for method in packages(repository, 'catalog'):
        name = method.parent.name
        if name in reserved:
            raise ValueError('catalog cannot shadow a core name')
        metadata, digest = compile_package(compiler, method.parent)
        extra = json.loads((repository / 'metadata' / (name + '.json')).read_text())
        if set(extra) != {'minimum_irmind_version', 'mappings', 'coverage'}:
            raise ValueError('unsupported catalog metadata')
        if extra['coverage']['status'] not in ('complete', 'partial', 'unavailable'):
            raise ValueError('unsupported coverage status')
        if len(extra['coverage']['description'].encode()) > 512 or len(extra['mappings']) > 32:
            raise ValueError('catalog metadata exceeds limits')
        transport = canonical({'format_version': 1, 'files': [
            {'path': path, 'contents': data.decode('utf-8')}
            for path, data in resources(method.parent)
        ]})
        if len(transport) > 1024 * 1024:
            raise ValueError('transport asset exceeds limit')
        asset = f'{name}-{metadata["version"]}.skill.json'
        if len(asset) > 128 or not re.fullmatch(r'[A-Za-z0-9_.-]+', asset):
            raise ValueError('invalid asset basename')
        (output / asset).write_bytes(transport)
        entries.append({
            'name': name, 'version': metadata['version'], 'package_sha256': digest,
            'asset': asset, 'asset_sha256': hashlib.sha256(transport).hexdigest(),
            'asset_bytes': len(transport), 'minimum_irmind_version': extra['minimum_irmind_version'],
            'target_schema': metadata['target_schema'], 'interpreter': 'irmind-skill-interpreter-v1',
            'sources': sorted(metadata.get('sources', [])), 'mappings': sorted(extra['mappings']),
            'coverage': {'status': extra['coverage']['status'], 'description': extra['coverage']['description']},
        })
    index = canonical({'format_version': 1, 'catalog': 'ns2switch/irmind-skills', 'key_id': key_id,
                       'release_tag': tag, 'release_commit': commit, 'release_sequence': 1,
                       'entries': entries})
    if len(index) > 1024 * 1024 or len(entries) > 1024:
        raise ValueError('index exceeds limits')
    (output / 'index.json').write_bytes(index)
    return index


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--key-id', required=True)
    parser.add_argument('--tag', default='v0.0.0-rehearsal')
    parser.add_argument('--commit', required=True)
    args = parser.parse_args()
    index = build(Path(__file__).resolve().parents[1], args.compiler.resolve(), args.output.resolve(),
                  args.key_id, args.tag, args.commit)
    print(f'Built catalog-only index with {len(json.loads(index)["entries"])} entries.')
