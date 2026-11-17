"""Inventory the actual data packages, not an empty software-ecosystem scan."""
import argparse,hashlib,json
from pathlib import Path
from package_contract import identifier,metadata,package_hash,resources

def build(repository,directory):
 raw=(directory/'index.json').read_bytes()
 if len(raw)>1024*1024:raise ValueError('index exceeds limit')
 index=json.loads(raw);components=[]
 if len(index['entries'])>1024:raise ValueError('too many packages')
 core=json.loads((repository/'core/package-identities.json').read_text())
 for entry in index['entries']:
  name=identifier(entry['name'])
  if name in core:raise ValueError('core must not be in a catalog SBOM')
  package=repository/'catalog'/name;meta=metadata(package)
  if meta['version']!=entry['version'] or package_hash(package)!=entry['package_sha256']:raise ValueError('package inventory mismatch')
  asset=entry['asset']
  if Path(asset).name!=asset or '/' in asset or '\\' in asset:raise ValueError('invalid asset')
  data=(directory/asset).read_bytes()
  if len(data)!=entry['asset_bytes'] or hashlib.sha256(data).hexdigest()!=entry['asset_sha256']:raise ValueError('transport inventory mismatch')
  ref='skill:'+name+'@'+entry['version']
  components.append({'type':'data','bom-ref':ref,'name':name,'version':entry['version'],
   'licenses':[{'expression':meta['license']}],
   'hashes':[{'alg':'SHA-256','content':entry['asset_sha256']}],
   'properties':[{'name':'irmind:package:sha256','value':entry['package_sha256']}],
   'components':[{'type':'file','bom-ref':ref+':'+path,'name':path,'hashes':[{'alg':'SHA-256','content':hashlib.sha256(content).hexdigest()}]} for path,content in resources(package)]})
 return {'$schema':'https://cyclonedx.org/schema/bom-1.6.schema.json','bomFormat':'CycloneDX','specVersion':'1.6','version':1,
  'metadata':{'component':{'type':'data','name':'IRMind community skill catalog','version':index['release_tag'],
   'hashes':[{'alg':'SHA-256','content':hashlib.sha256(raw).hexdigest()}]}},'components':components}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--directory',type=Path,required=True);a=p.parse_args()
 root=Path(__file__).resolve().parents[1]
 (a.directory/'skills-SBOM.cdx.json').write_text(json.dumps(build(root,a.directory),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
