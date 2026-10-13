"""Download and pin the public Kitronik driver; retain its MIT notice."""
from pathlib import Path
import urllib.request,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
REPO='KitronikLtd/micropython-microbit-kitronik-MOVE-motor'
def read(url):
    return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mini-IPHOREOS-build'}),timeout=30).read()
commit=json.loads(read('https://api.github.com/repos/'+REPO+'/commits/master'))['sha']
listing=json.loads(read('https://api.github.com/repos/'+REPO+'/git/trees/'+commit+'?recursive=1'))['tree']
print([x['path'] for x in listing if x['type']=='blob'])
manifest={'repository':'https://github.com/'+REPO,'commit':commit,'files':{}}
for name in ['KitronikMOVEMotor.py','MOVEMotor.py','README.md','LICENSE']:
    if not any(x['path']==name for x in listing): continue
    raw=read('https://raw.githubusercontent.com/'+REPO+'/'+commit+'/'+name)
    out=ROOT/'firmware'/name if name=='KitronikMOVEMotor.py' else ROOT/'docs'/('VENDOR_'+name)
    out.write_bytes(raw)
    manifest['files'][str(out.relative_to(ROOT))]={'sha256':hashlib.sha256(raw).hexdigest()}
for item in listing:
    if 'ultra' in item['path'].lower() or 'distance' in item['path'].lower():
        print(item['path']); print(read('https://raw.githubusercontent.com/'+REPO+'/'+commit+'/'+item['path']).decode())
(ROOT/'docs/vendor_manifest.json').write_text(json.dumps(manifest,indent=2))
print('Pinned driver',commit)
