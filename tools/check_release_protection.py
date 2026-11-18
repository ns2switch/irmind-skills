"""Read protection metadata without referencing or entering any environment."""
import json
import subprocess
from release_config import validate_environment


def check():
    def get(suffix):
        result = subprocess.run(['gh', 'api', '-H', 'X-GitHub-Api-Version: 2026-03-10',
            'repos/ns2switch/irmind-skills/environments/release' + suffix],
            capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise ValueError('Release protection could not be verified; no signing environment was entered.')
        return json.loads(result.stdout)
    validate_environment(get(''), get('/deployment-branch-policies'))
    print('Required maintainer review and v* tag-only deployments verified. No signing environment or secret was accessed.')


if __name__ == '__main__':
    try:
        check()
    except (ValueError, OSError, subprocess.SubprocessError):
        raise SystemExit('Release protection could not be verified; no signing environment was entered.') from None
