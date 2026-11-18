from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class ReleasePolicyTests(unittest.TestCase):
 def test_environment_must_have_a_reviewer_and_only_version_tags(self):
  from release_config import validate_environment
  good={'protection_rules':[{'type':'required_reviewers','reviewers':[{'type':'User','reviewer':{'login':'ns2switch'}}]}], 'deployment_branch_policy':{'protected_branches':False,'custom_branch_policies':True}}
  tags={'branch_policies':[{'type':'tag','name':'v*'}]}
  validate_environment(good,tags)
  for bad in ({},dict(good,protection_rules=[]),dict(good,deployment_branch_policy=None)):
   with self.assertRaises(ValueError):validate_environment(bad,tags)
  for rules in ([],[{'type':'branch','name':'main'}],[{'type':'tag','name':'*'}]):
   with self.assertRaises(ValueError):validate_environment(good,{'branch_policies':rules})
 def test_readonly_protection_check_cannot_request_a_deployment_or_signing_secret(self):
  s=(ROOT/'.github/workflows/check-release-protection.yml').read_text()
  self.assertNotIn('environment:',s);self.assertNotIn('secrets.',s)
  self.assertNotIn('contents: write',s);self.assertNotIn('id-token: write',s)
  self.assertIn('actions: read',s)
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
