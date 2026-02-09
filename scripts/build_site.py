#!/usr/bin/env python3
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'items.jsonl'
OUT = ROOT / 'site' / 'items.json'

items = []
for line in DATA.read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if not line:
        continue
    items.append(json.loads(line))

OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'wrote {OUT} ({len(items)} items)')
