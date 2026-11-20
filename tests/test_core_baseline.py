import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from resolve_core_baseline import core_baseline


class CoreBaseline(unittest.TestCase):
    candidate = '1' * 40
    released = '2' * 40

    def fake(self, protected=True, comparison='ahead', result='success'):
        def get(path):
            if path.endswith('/branches/main'):
                return {'protected': protected, 'commit': {'sha': '3' * 40}}
            if '/compare/' in path:
                return {'status': comparison}
            if '/actions/workflows/ci.yml/runs' in path:
                return {'workflow_runs': [{
                    'head_sha': self.candidate,
                    'head_branch': 'main',
                    'event': 'push',
                    'conclusion': result,
                }]}
            self.fail('unexpected lookup')
        return get

    def test_normal_validation_uses_the_published_release(self):
        self.assertEqual(core_baseline('', self.released), self.released)

    def test_reviewed_candidate_needs_protected_main_and_green_push(self):
        self.assertEqual(
            core_baseline(self.candidate, self.released, self.fake()),
            self.candidate,
        )
        for get in (self.fake(protected=False), self.fake(comparison='diverged'),
                    self.fake(result='failure')):
            with self.assertRaises(ValueError):
                core_baseline(self.candidate, self.released, get)

    def test_mutable_ref_is_rejected(self):
        with self.assertRaises(ValueError):
            core_baseline('main', self.released, self.fake())
