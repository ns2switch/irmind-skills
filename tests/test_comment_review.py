import io,json,sys,unittest,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from comment_review import render,unpack
class ReporterTests(unittest.TestCase):
 def sample(self): return {'format_version':1,'packages':[{'family':'catalog','name':'example','version':'1.0.0','sources':['parser-json'],'mappings':['mapping-cloudtrail'],'coverage':'partial'}],'warnings':[{'name':'example','code':'partial-coverage'}],'blocking':[]}
 def test_no_raw_methodology_is_rendered(self):
  self.assertIn('partial-coverage',render(self.sample(),'success','https://github.com/ns2switch/irmind-skills/actions/runs/1'))
  r=self.sample();r['packages'][0]['name']='[click](https://other.example)'
  with self.assertRaises(ValueError):render(r,'success','x')
 def test_zip_is_never_extracted_and_paths_are_rejected(self):
  b=io.BytesIO()
  with zipfile.ZipFile(b,'w') as z:z.writestr('../review-results.json','{}')
  with self.assertRaises(ValueError):unpack(b.getvalue())
 def test_huge_report_and_unknown_notice_rejected(self):
  with self.assertRaises(ValueError):unpack(b'a'*262145)
  r=self.sample();r['warnings'][0]['code']='arbitrary attacker content'
  with self.assertRaises(ValueError):render(r,'failure','x')
if __name__=='__main__':unittest.main()
