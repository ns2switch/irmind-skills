"""Independent public-key verification using OpenSSL; never consumes a signing seed."""
import argparse,hashlib,json,re,subprocess,tempfile
from pathlib import Path
PUBLIC='fb2015c83d13fe018e270a7fe73bf7bccfdb622565e30f7ade436637c3b2c25b'
KEY_ID='f04daae3f8243ed76452d5f787ea527c8fbec895ca0c91a35f453f6677575e4f'
REPO='ns2switch/irmind-skills'
def verify_index(directory):
 directory=Path(directory)
 raw=(directory/'index.json').read_bytes();sig=(directory/'index.ed25519').read_bytes()
 if len(raw)>1024*1024 or len(sig)!=64:raise ValueError('index/signature exceeds bounds')
 index=json.loads(raw)
 if index['catalog']!=REPO or index['key_id']!=KEY_ID or hashlib.sha256(bytes.fromhex(PUBLIC)).hexdigest()!=KEY_ID:raise ValueError('unexpected public identity')
 if not re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+(?:-[a-z0-9.-]+)?',index['release_tag']):raise ValueError('invalid release tag')
 with tempfile.TemporaryDirectory(prefix='catalog-public-verification-') as temp:
  root=Path(temp)
  (root/'public.der').write_bytes(bytes.fromhex('302a300506032b6570032100'+PUBLIC))
  (root/'preimage').write_bytes(b'irmind-skill-catalog-index-v1\0'+len(raw).to_bytes(8,'big')+raw)
  result=subprocess.run(['openssl','pkeyutl','-verify','-pubin','-keyform','DER','-inkey',str(root/'public.der'),'-rawin','-in',str(root/'preimage'),'-sigfile',str(directory/'index.ed25519')],capture_output=True,timeout=15)
  if result.returncode:raise ValueError('Ed25519 index signature is invalid')
 return index

def verify(directory,ed25519_only=False):
 directory=Path(directory);index=verify_index(directory)
 entries=index['entries']
 if len(entries)>1024:raise ValueError('too many entries')
 for entry in entries:
  name=entry['asset']
  if not re.fullmatch(r'[A-Za-z0-9_.-]{1,128}',name) or name in ('.','..'):raise ValueError('invalid asset name')
  data=(directory/name).read_bytes()
  if len(data)>1024*1024 or len(data)!=entry['asset_bytes'] or hashlib.sha256(data).hexdigest()!=entry['asset_sha256']:raise ValueError('asset hash mismatch')
 if not ed25519_only:
  lines=(directory/'SHA256SUMS').read_text(encoding='ascii').splitlines();seen=set()
  for line in lines:
   m=re.fullmatch(r'([0-9a-f]{64})  ([A-Za-z0-9_.-]{1,128})',line)
   if not m or m[2] in seen or m[2] in ('.','..'):raise ValueError('invalid checksum manifest')
   seen.add(m[2]);p=directory/m[2]
   if hashlib.sha256(p.read_bytes()).hexdigest()!=m[1]:raise ValueError('payload checksum mismatch')
  required={'index.json','index.ed25519','skills-SBOM.spdx.json'}|{e['asset'] for e in entries}
  if not required<=seen:raise ValueError('missing payload checksums')
  identity=f'https://github.com/{REPO}/.github/workflows/release.yml@refs/tags/{index["release_tag"]}'
  for name in sorted(seen|{'SHA256SUMS'}):
   p=directory/name
   subprocess.run(['cosign','verify-blob',str(p),'--bundle',str(p)+'.sigstore.json','--certificate-identity',identity,'--certificate-oidc-issuer','https://token.actions.githubusercontent.com'],check=True,timeout=60)
   subprocess.run(['gh','attestation','verify',str(p),'-R',REPO],check=True,timeout=60)
 print(f'Verified Ed25519 index and {len(entries)} package asset(s).')
 return index
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--directory',type=Path,required=True);p.add_argument('--ed25519-only',action='store_true');a=p.parse_args();verify(a.directory,a.ed25519_only)
