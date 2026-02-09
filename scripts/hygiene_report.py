#!/usr/bin/env python3
import json
import pathlib
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
ITEMS = ROOT / 'data' / 'items.jsonl'
OUT = ROOT / 'reports' / 'hygiene.md'
OUT.parent.mkdir(parents=True, exist_ok=True)

items=[]
for line in ITEMS.read_text(encoding='utf-8').splitlines():
    line=line.strip()
    if not line:
        continue
    items.append(json.loads(line))

unknown=[it for it in items if str(it.get('author','')).lower()=='unknown']
needs_credit=[it for it in items if 'needs-credit' in (it.get('tags') or [])]
no_preview=[it for it in items if not (it.get('preview') or {}).get('ok')]

# duplicates by url
by_url=defaultdict(list)
for it in items:
    by_url[it.get('url')].append(it)
dup=[(u,v) for u,v in by_url.items() if u and len(v)>1]

# tag stats
tag_counter=Counter()
for it in items:
    for t in it.get('tags') or []:
        tag_counter[t]+=1

lines=[]
lines.append('# Hygiene report')
lines.append('')
lines.append(f'- Total items: **{len(items)}**')
lines.append(f'- Unknown author: **{len(unknown)}**')
lines.append(f'- needs-credit tag: **{len(needs_credit)}**')
lines.append(f'- No embedded preview: **{len(no_preview)}**')
lines.append(f'- Duplicate URLs: **{len(dup)}**')
lines.append('')

lines.append('## Top tags')
for t,c in tag_counter.most_common(20):
    lines.append(f'- `{t}`: {c}')
lines.append('')

if needs_credit:
    lines.append('## Needs credit (top 20)')
    for it in needs_credit[:20]:
        lines.append(f"- {it.get('title')} — {it.get('url')} (issue: {it.get('source_issue','')})")
    lines.append('')

if dup:
    lines.append('## Duplicate URLs')
    for u, lst in dup[:20]:
        lines.append(f'- {u}')
        for it in lst:
            lines.append(f"  - {it.get('id')} {it.get('title')}")
    lines.append('')

OUT.write_text('\n'.join(lines), encoding='utf-8')
print('wrote', OUT)
