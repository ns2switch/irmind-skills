import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from build_index import build
from package_contract import package_hash, resources, safe_data_path


class RepositoryContracts(unittest.TestCase):
    def test_all_fifteen_core_packages_match_the_current_inventory(self):
        expected = json.loads((ROOT / 'core/package-identities.json').read_text())
        self.assertEqual(len(expected), 15)
        actual = {path.parent.name: package_hash(path.parent) for path in (ROOT / 'core').glob('*/SKILL.md')}
        self.assertEqual(actual, expected)

    def test_answers_and_episode_scripts_are_not_package_resources(self):
        for family in ('core', 'catalog'):
            for path in (ROOT / family).glob('*/SKILL.md'):
                names = [name for name, _ in resources(path.parent)]
                self.assertTrue(all(name == 'SKILL.md' or name.split('/')[0] in
                                    ('queries', 'rules', 'references') for name in names))
                self.assertFalse(any('ground-truth' in name or 'private' in name for name in names))
                self.assertTrue((ROOT / 'episodes' / family / path.parent.name / 'episode.json').is_file())

    def test_empty_catalog_never_indexes_the_core(self):
        if list((ROOT / 'catalog').glob('*/SKILL.md')):
            self.skipTest('catalog has community entries')
        with tempfile.TemporaryDirectory() as temporary:
            index = build(ROOT, Path('/unused'), Path(temporary), '1' * 64,
                          'v0.0.0-rehearsal', '2' * 40)
            self.assertEqual(json.loads(index)['entries'], [])
            self.assertNotIn(b'SKILL.md', index)

    def test_catalog_cannot_shadow_a_core_name_even_with_identical_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'core').mkdir()
            (root / 'catalog').mkdir()
            shutil.copyfile(ROOT / 'core/package-identities.json', root / 'core/package-identities.json')
            shutil.copytree(ROOT / 'core/linux-triage', root / 'catalog/linux-triage')
            with self.assertRaisesRegex(ValueError, 'shadow'):
                build(root, Path('/unused'), root / 'dist', '1' * 64, 'v0.0.0-rehearsal', '2' * 40)

    def test_untrusted_data_paths_cannot_escape_the_repository(self):
        for path in ('../secret', '/secret', 'core/../../secret', 'core\\secret', 'core//file'):
            with self.assertRaises(ValueError):
                safe_data_path(ROOT, path)

    def test_linked_data_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'private').mkdir()
            (root / 'public').symlink_to(root / 'private', target_is_directory=True)
            with self.assertRaises(ValueError):
                safe_data_path(root, 'public/answers.json')

    def test_public_episode_sources_are_basename_only_and_answers_stay_separate(self):
        for path in (ROOT / 'episodes/core').glob('*/episode.json'):
            data = json.loads(path.read_text())
            for source in data['files']:
                self.assertEqual(Path(source['file']).name, source['file'])
                self.assertTrue((path.parent / 'source' / source['file']).is_file())
            self.assertTrue((ROOT / 'episodes/private' / data['expected_file']).is_file())


if __name__ == '__main__':
    unittest.main()
