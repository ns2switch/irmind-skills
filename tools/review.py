"""Bounded, data-only reviewer checks; the released Rust compiler stays authoritative."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import tomllib

from package_contract import identifier, metadata, package_hash, packages, resources

COMMON_TOOLS = {'graph_summary', 'text_search', 'entity_lookup', 'entity_timeline',
                'neighbors', 'path', 'raw_records', 'case_add_finding'}
WARNINGS = {
    'unusual-tools': 'Declared tools exceed the usual local investigation set for this category.',
    'instruction-like-text': 'Instruction-like wording needs a human policy review.',
    'partial-coverage': 'Coverage is partial or unavailable; review the stated limitations.',
}
INSTRUCTION = re.compile(r'\b(?:ignore|bypass|override)\b.{0,48}\b(?:policy|instructions|scope|approval)\b|\b(?:ask|request)\b.{0,48}\b(?:approval|approve)\b', re.I)


def semver(value):
    if not isinstance(value, str) or len(value) > 64:
        raise ValueError('invalid version')
    m = re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?', value)
    if not m: raise ValueError('invalid version')
    suffix = []
    if m[4]:
        for item in m[4].split('.'):
            if not item or (item.isdigit() and len(item) > 1 and item[0] == '0'):
                raise ValueError('invalid prerelease')
            suffix.append((0, int(item)) if item.isdigit() else (1, item))
    return tuple(map(int, m.group(1, 2, 3))) + (int(m[4] is None), tuple(suffix))


def supported(irmind):
    cargo = tomllib.loads((irmind / 'crates/bin/Cargo.toml').read_text(encoding='utf-8'))
    features = cargo['features']; enabled = set(); pending = ['default']
    while pending:
        feature = pending.pop()
        if feature in enabled: continue
        enabled.add(feature)
        pending.extend(features.get(feature, []))
    modules = {name for name in enabled if name.startswith(('parser-', 'siem-', 'edr-', 'cloud-', 'storage-', 'mapping-'))}
    for feature in enabled:
        if feature.startswith('dep:irmind-mod-mapping-'):
            modules.add(feature.removeprefix('dep:irmind-mod-'))
    if 'parser-json' not in modules or len(modules) < 10:
        raise ValueError('released module registry changed; review the adapter')
    return modules


def review(root, baseline, irmind):
    modules = supported(irmind)
    result = {'format_version': 1, 'packages': [], 'blocking': [], 'warnings': []}
    core = {path.parent.name for path in packages(root, 'core')}
    methods = [(family, path) for family in ('core', 'catalog') for path in packages(root, family)]
    if len(methods) > 1024: raise ValueError('too many packages')
    for family, path in methods:
        name = identifier(path.parent.name); meta = metadata(path.parent)
        semver(meta['version']); digest = package_hash(path.parent)
        row = {'family': family, 'name': name, 'version': meta['version'],
               'sources': meta.get('sources', []), 'mappings': [], 'coverage': 'core'}
        def block(code): result['blocking'].append({'name': name, 'code': code})
        def warn(code): result['warnings'].append({'name': name, 'code': code})
        for relative, _ in resources(path.parent):
            resource = path.parent / relative
            if resource.stat().st_mode & 0o111: block('executable-resource')
            if relative != 'SKILL.md' and (relative.split('/')[0] not in ('queries', 'rules', 'references') or resource.suffix not in ('.md', '.txt', '.json', '.toml', '.yaml', '.yml', '.csv')):
                block('non-data-resource')
        if family == 'catalog' and name in core: block('core-name-collision')
        if not row['sources'] or len(row['sources']) > 32 or any(source not in modules or source.startswith('mapping-') for source in row['sources']):
            block('unsupported-source')
        if set(meta.get('tools', [])) - COMMON_TOOLS: warn('unusual-tools')
        body = path.read_text(encoding='utf-8').split('+++', 2)[2]
        for line in body.splitlines():
            if INSTRUCTION.search(line) and not re.search(r'\b(?:never|must not|do not|cannot)\b', line, re.I):
                warn('instruction-like-text'); break
        if family == 'catalog':
            extra = root / 'metadata' / (name + '.json')
            if not extra.is_file() or extra.is_symlink() or extra.stat().st_size > 16000:
                block('missing-or-invalid-coverage')
            else:
                data = json.loads(extra.read_text(encoding='utf-8'))
                if set(data) != {'minimum_irmind_version', 'mappings', 'coverage'}:
                    block('invalid-coverage-fields')
                else:
                    semver(data['minimum_irmind_version'])
                    mappings = data['mappings']; coverage = data['coverage']
                    if not isinstance(mappings, list) or len(mappings) > 32 or any(item not in modules or not item.startswith('mapping-') for item in mappings):
                        block('unsupported-mapping')
                    row['mappings'] = mappings
                    if set(coverage) != {'status', 'description'} or coverage['status'] not in ('complete', 'partial', 'unavailable') or not isinstance(coverage['description'], str) or len(coverage['description'].encode()) > 512:
                        block('invalid-coverage')
                    else:
                        row['coverage'] = coverage['status']
                        if coverage['status'] != 'complete': warn('partial-coverage')
        old = baseline / family / name
        if (old / 'SKILL.md').is_file() and package_hash(old) != digest:
            if semver(meta['version']) <= semver(metadata(old)['version']): block('version-not-increased')
        result['packages'].append(row)
    if len(result['blocking']) > 1024 or len(result['warnings']) > 1024:
        raise ValueError('review result exceeds limits')
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path('.'))
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--irmind', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    try:
        result = review(args.root.resolve(), args.baseline.resolve(), args.irmind.resolve())
    except (OSError, ValueError, KeyError, TypeError, IndexError):
        result = {'format_version': 1, 'packages': [], 'warnings': [],
                  'blocking': [{'name': 'repository', 'code': 'invalid-repository-data'}]}
    args.output.write_text(json.dumps(result, ensure_ascii=True, indent=2) + '\n', encoding='utf-8')
    print(f'Reviewed {len(result["packages"])} packages; {len(result["blocking"])} blocking checks, {len(result["warnings"])} human-review notices.')
    raise SystemExit(bool(result['blocking']))


if __name__ == '__main__': main()
