import hashlib,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build_sbom import build
from package_contract import canonical,metadata,package_hash,resources
class DataSbomTests(unittest.TestCase):
 def test_catalog_packages_and_resources_are_inventoried_without_answers_or_core(self):
  name='aws-ec2-cryptomining';pkg=ROOT/'catalog'/name;meta=metadata(pkg)
  transport=canonical({'format_version':1,'files':[{'path':p,'contents':b.decode()} for p,b in resources(pkg)]})
  asset=name+'-'+meta['version']+'.skill.json'
  entry={'name':name,'version':meta['version'],'package_sha256':package_hash(pkg),'asset':asset,'asset_bytes':len(transport),'asset_sha256':hashlib.sha256(transport).hexdigest()}
  with tempfile.TemporaryDirectory() as tmp:
   directory=Path(tmp);(directory/asset).write_bytes(transport);(directory/'index.json').write_bytes(canonical({'release_tag':'v0.1.0','entries':[entry]}))
   first=build(ROOT,directory);self.assertEqual(first,build(ROOT,directory));self.assertEqual(first['specVersion'],'1.6')
   self.assertEqual(first['components'][0]['name'],name);self.assertEqual(first['components'][0]['components'][0]['name'],'SKILL.md')
   self.assertNotIn('private',json.dumps(first));self.assertNotIn('windows-triage',json.dumps(first))
   (directory/asset).write_bytes(transport+b' ')
   with self.assertRaises(ValueError):build(ROOT,directory)
if __name__=='__main__':unittest.main()
