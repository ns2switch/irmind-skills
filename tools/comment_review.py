"""Trusted workflow_run reporter. Untrusted artifacts are bounded JSON, never code."""
import io
import json
import os
from pathlib import Path
import re
import urllib.request
import urllib.parse
import zipfile

REPO = 'ns2switch/irmind-skills'
MARKER = '<!-- irmind-skill-review-v1 -->'
NAMES = re.compile(r'[a-z][a-z0-9-]{0,63}')
CODES = {'unsupported-source','unsupported-mapping','core-name-collision','version-not-increased',
         'executable-resource','non-data-resource','missing-or-invalid-coverage',
         'invalid-coverage-fields','invalid-coverage','invalid-repository-data',
         'unusual-tools','instruction-like-text','partial-coverage'}


def render(report, conclusion, url):
    if set(report) != {'format_version','packages','warnings','blocking'} or report['format_version'] != 1:
        raise ValueError('unsupported report')
    lines = [MARKER, '## Skill validation summary', '', f'Workflow result: **{conclusion}** · [Full validation run]({url})', '',
             'The released Rust compiler and scripted episodes are authoritative. Heuristic notices require human review.', '',
             '| Package | Version | Sources / mappings | Coverage |', '|---|---|---|---|']
    rows = report['packages']
    if not isinstance(rows,list) or len(rows)>1024: raise ValueError('invalid package count')
    for row in rows:
        if set(row) != {'family','name','version','sources','mappings','coverage'}: raise ValueError('invalid row')
        if row['family'] not in ('core','catalog') or not NAMES.fullmatch(row['name']) or not re.fullmatch(r'[0-9A-Za-z.+-]{1,64}',row['version']):
            raise ValueError('invalid identity')
        if row['coverage'] not in ('core','complete','partial','unavailable'): raise ValueError('invalid coverage')
        modules=[]
        for group in ('sources','mappings'):
            if not isinstance(row[group],list) or len(row[group])>32: raise ValueError('invalid modules')
            for item in row[group]:
                if not NAMES.fullmatch(item): raise ValueError('invalid module')
                modules.append(item)
        lines.append(f"| {row['family']}/{row['name']} | {row['version']} | {', '.join(modules)} | {row['coverage']} |")
    for key,title in [('blocking','Blocking checks'),('warnings','Human-review notices (non-blocking)')]:
        issues=report[key]
        if not isinstance(issues,list) or len(issues)>1024: raise ValueError('invalid notices')
        lines.extend(['',f'### {title}', ''])
        if not issues: lines.append('None.')
        for row in issues:
            if set(row)!={'name','code'} or not NAMES.fullmatch(row['name']) or row['code'] not in CODES:
                raise ValueError('invalid notice')
            lines.append(f"- `{row['name']}`: `{row['code']}`")
    body='\n'.join(lines)+'\n'
    if len(body.encode())>60000: raise ValueError('comment exceeds limit')
    return body


def unpack(data):
    if len(data)>262144: raise ValueError('artifact exceeds limit')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        entries=archive.infolist()
        if len(entries)!=1 or entries[0].filename!='review-results.json' or entries[0].file_size>262144 or entries[0].flag_bits&1:
            raise ValueError('invalid artifact shape')
        # Never extract any entry, open a path, or execute artifact content.
        content=archive.read(entries[0])
        if len(content)>262144: raise ValueError('report exceeds limit')
        return json.loads(content)


class ArtifactRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, location):
        parsed=urllib.parse.urlsplit(location)
        host=parsed.hostname or ''
        if parsed.scheme!='https' or parsed.username or parsed.password or not any(host.endswith(suffix) for suffix in ('.blob.core.windows.net','.actions.githubusercontent.com','.githubusercontent.com')):
            raise ValueError('unexpected artifact download host')
        redirected=super().redirect_request(request,response,code,message,headers,location)
        if redirected is None:raise ValueError('unexpected artifact redirect')
        # Signed download URLs authenticate independently of the GitHub API.
        redirected.remove_header('Authorization')
        return redirected


def api(path, method='GET', payload=None, binary=False):
    if not path.startswith('https://api.github.com/'):
        path='https://api.github.com/repos/'+REPO+'/'+path
    req=urllib.request.Request(path, method=method, data=None if payload is None else json.dumps(payload).encode(), headers={
        'Authorization':'Bearer '+os.environ['GH_TOKEN'], 'Accept':'application/vnd.github+json', 'User-Agent':'irmind-skill-review'})
    opener=urllib.request.build_opener(ArtifactRedirect()) if binary else urllib.request.build_opener()
    with opener.open(req,timeout=30) as response:
        data=response.read(262145 if binary else 2000001)
    if len(data)>(262144 if binary else 2000000): raise ValueError('API response exceeds limit')
    return data if binary else json.loads(data)


def main():
    event=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    run=event['workflow_run']
    if event['repository']['full_name']!=REPO or run['event']!='pull_request' or run['status']!='completed': return
    # Resolve the PR from the run; never trust a PR number in the uploaded report.
    prs=run['pull_requests']
    if len(prs)!=1: return
    number=int(prs[0]['number']); pr=api(f'pulls/{number}')
    if pr['state']!='open' or pr['base']['repo']['full_name']!=REPO or pr['head']['sha']!=run['head_sha']: return
    artifacts=api(f'actions/runs/{int(run["id"])}/artifacts')['artifacts']
    matches=[a for a in artifacts if a['name']=='skill-review-summary' and not a['expired']]
    if len(matches)!=1 or matches[0]['size_in_bytes']>262144: return
    report=unpack(api(f'actions/artifacts/{int(matches[0]["id"])}/zip',binary=True))
    conclusion=run['conclusion']
    if conclusion not in ('success','failure','cancelled','timed_out','action_required','neutral','skipped','stale','startup_failure'): raise ValueError('unknown result')
    body=render(report,conclusion,f'https://github.com/{REPO}/actions/runs/{int(run["id"])}')
    existing=api(f'issues/{number}/comments?per_page=100')
    mine=[c for c in existing if c['user']['login']=='github-actions[bot]' and c['body'].startswith(MARKER)]
    if mine: api(f'issues/comments/{int(mine[0]["id"])}','PATCH',{'body':body})
    else: api(f'issues/{number}/comments','POST',{'body':body})


if __name__=='__main__': main()
