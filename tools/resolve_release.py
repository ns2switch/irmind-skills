#!/usr/bin/env python3
"""Freeze the latest published IRMind tag, commit and compiler toolchain for one run."""
import base64
import json
import os
import re
import subprocess
import tomllib


def api(path):
    return json.loads(subprocess.check_output(['gh', 'api', path], text=True, timeout=20))


def resolve():
    releases = api('repos/ns2switch/irmind/releases?per_page=100')
    releases = [r for r in releases if not r['draft'] and r['published_at']]
    if not releases:
        raise ValueError('IRMind has no published release')
    latest = max(releases, key=lambda r: r['published_at'])
    tag = latest['tag_name']
    if not re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?', tag):
        raise ValueError('unsupported release tag')
    commit = api('repos/ns2switch/irmind/commits/' + tag)['sha']
    if not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('invalid release commit')
    file = api(f'repos/ns2switch/irmind/contents/rust-toolchain.toml?ref={commit}')
    toolchain = tomllib.loads(base64.b64decode(file['content']).decode())['toolchain']['channel']
    if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', toolchain):
        raise ValueError('release must pin its Rust toolchain')
    result = {'tag': tag, 'version': tag[1:], 'commit': commit, 'toolchain': toolchain}
    with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as output:
        for name, value in result.items():
            output.write(f'{name}={value}\n')
    print(json.dumps(result))


if __name__ == '__main__':
    resolve()
