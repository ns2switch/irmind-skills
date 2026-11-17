"""Validate public immutable release configuration before reaching a signing environment."""
import json,os,re,subprocess
from pathlib import Path
CONFIG = {'format_version','tag','release_sequence','key_id','public_key'}
def main():
 c=json.loads(Path('catalog-release.json').read_text())
 if set(c)!=CONFIG or c['format_version']!=1 or not isinstance(c['release_sequence'],int) or not 1<=c['release_sequence']<=2**64-1:raise ValueError('invalid configuration')
 if not re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+(?:-[a-z0-9.-]+)?',c['tag']) or os.environ['GITHUB_REF']!='refs/tags/'+c['tag']:raise ValueError('release must execute the configured tag')
 import hashlib
 if hashlib.sha256(bytes.fromhex(c['public_key'])).hexdigest()!=c['key_id']:raise ValueError('key identity mismatch')
 releases=json.loads(subprocess.check_output(['gh','api','repos/ns2switch/irmind-skills/releases?per_page=100']))
 if len(releases)>=100:raise ValueError('release history requires pagination review before publishing')
 for release in releases:
  if release['tag_name']==c['tag'] and not release['draft']:raise ValueError('release already published; never overwrite it')
  if not release['draft']:
   import tempfile
   from verify_release import verify_index
   with tempfile.TemporaryDirectory(prefix='previous-public-index-') as tmp:
    subprocess.run(['gh','release','download',release['tag_name'],'-R','ns2switch/irmind-skills','-p','index.json','-p','index.ed25519','-D',tmp],check=True)
    previous=verify_index(Path(tmp))
    if c['release_sequence']<=previous['release_sequence']:raise ValueError('release sequence must increase')
 with open(os.environ['GITHUB_OUTPUT'],'a') as out:
  for key in ('tag','release_sequence','key_id'):out.write(f'{key}={c[key]}\n')
 print('Public release configuration validated; no private key requested.')
if __name__=='__main__':main()
