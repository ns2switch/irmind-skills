"""Accept only the reviewed core candidate from the protected engine branch."""
import os
import re

from resolve_release import api


def core_baseline(candidate, release, get=api):
    if not candidate:
        return release
    if not re.fullmatch(r'[0-9a-f]{40}', candidate):
        raise ValueError('core candidate must be a full commit')
    root = 'repos/ns2switch/irmind'
    branch = get(root + '/branches/main')
    if branch.get('protected') is not True:
        raise ValueError('IRMind main must be protected')
    main = branch['commit']['sha']
    if get(f'{root}/compare/{candidate}...{main}')['status'] not in ('ahead', 'identical'):
        raise ValueError('core candidate is not on IRMind main')
    runs = get(f'{root}/actions/workflows/ci.yml/runs?branch=main&event=push'
               f'&head_sha={candidate}&status=success&per_page=10')['workflow_runs']
    if not any(run['head_sha'] == candidate and run['head_branch'] == 'main'
               and run['event'] == 'push' and run['conclusion'] == 'success'
               for run in runs):
        raise ValueError('core candidate has no green automatic main CI')
    return candidate


if __name__ == '__main__':
    released = os.environ['IRMIND_PUBLISHED_COMMIT']
    candidate = os.environ.get('IRMIND_CORE_CANDIDATE', '')
    commit = core_baseline(candidate, released)
    with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as output:
        output.write(f'commit={commit}\n')
        output.write(f'temporary={str(bool(candidate)).lower()}\n')
