from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class ReleasePolicyTests(unittest.TestCase):
 def test_seed_is_scoped_to_one_protected_signer_step(self):
  s=(ROOT/'.github/workflows/release.yml').read_text()
  self.assertEqual(s.count('secrets.CATALOG_ED25519_SEED_HEX'),1)
  before,publish=s.split('  publish:\n')
  self.assertNotIn('secrets.',before)
  self.assertIn('environment: release',publish)
  self.assertIn("startsWith(github.ref, 'refs/tags/v')",publish)
  self.assertIn('ulimit -c 0',publish)
  self.assertNotIn('set -x',publish)
  self.assertNotIn('CATALOG_ED25519_SEED_HEX',(ROOT/'tools/synthetic_signer.rs').read_text())
 def test_pr_workflows_cannot_use_release_or_secrets(self):
  for f in ['validate.yml','review-comment.yml']:
   s=(ROOT/'.github/workflows'/f).read_text()
   self.assertNotIn('secrets.',s);self.assertNotIn('environment: release',s)
  s=(ROOT/'.github/workflows/review-comment.yml').read_text()
  self.assertIn("ref: ${{ github.event.repository.default_branch }}",s)
 def test_current_example_answers_are_outside_the_signed_transport(self):
  from package_contract import resources
  files=resources(ROOT/'catalog/aws-ec2-cryptomining')
  self.assertEqual([p for p,_ in files],['SKILL.md'])
  self.assertNotIn(b'EC2_EVALUATOR_ONLY',b''.join(b for _,b in files))
if __name__=='__main__':unittest.main()
