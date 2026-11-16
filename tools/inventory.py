#!/usr/bin/env python3
"""Refresh or check data-only core commitments and the explicit IRMind fixture mirror."""
import argparse
import hashlib
import json
from pathlib import Path

from package_contract import package_hash, packages, resources, safe_data_path


def inventory(root, write=False):
    values = {method.parent.name: package_hash(method.parent) for method in packages(root, 'core')}
    target = root / 'core/package-identities.json'
    expected = json.dumps(values, indent=2) + '\n'
    if write:
        target.write_text(expected)
    elif target.read_text() != expected:
        raise ValueError('stale core package inventory')
    original = json.loads((root / 'source-map.json').read_text())
    rows = [row for row in original['files'] if not row['source'].startswith('core/')]
    for name in values:
        for path, data in resources(root / 'core' / name):
            rows.append({'source': f'core/{name}/{path}', 'path': f'skills/{name}/{path}',
                         'sha256': hashlib.sha256(data).hexdigest()})
    for row in rows:
        row['sha256'] = hashlib.sha256(safe_data_path(root, row['source']).read_bytes()).hexdigest()
    expected = json.dumps({'format_version': 1, 'files': sorted(rows, key=lambda row: row['source'])}, indent=2) + '\n'
    target = root / 'source-map.json'
    if write:
        target.write_text(expected)
    elif target.read_text() != expected:
        raise ValueError('stale source mirror hashes')
    print(f'{len(values)} core package commitments and {len(rows)} mirror entries match.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    inventory(Path(__file__).resolve().parents[1], args.write)
