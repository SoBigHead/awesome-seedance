#!/usr/bin/env python3
"""Convert an approved 'Submit a Case' issue into an items.jsonl entry + optional thumbnail.

Workflow expectation:
- Trigger: issues:labeled (label=approved)
- This script reads $GITHUB_EVENT_PATH
- Writes changes into repo working tree (append to data/items.jsonl, add thumbnail under site/assets/thumbs/)
"""

import hashlib
import json
import os
import pathlib
import re
import sys
import urllib.request
from datetime import datetime, timezone

from issue_parse import parse_issue_form, checkbox_checked

ROOT = pathlib.Path(__file__).resolve().parents[1]
ITEMS = ROOT / 'data' / 'items.jsonl'
THUMBS_DIR = ROOT / 'site' / 'assets' / 'thumbs'
THUMBS_DIR.mkdir(parents=True, exist_ok=True)

APPROVE_LABEL = 'approved'
NEEDS_CREDIT_TAG = 'needs-credit'

# Pillow will be installed in CI. Locally it might not exist.
try:
    from PIL import Image
except Exception:
    Image = None


def sha1(s: str) -> str:
    return hashlib.sha1(s.encode('utf-8')).hexdigest()


def safe_get(d, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def load_event(path: str) -> dict:
    return json.loads(pathlib.Path(path).read_text(encoding='utf-8'))


def download(url: str, out_path: pathlib.Path, max_mb: int = 10) -> None:
    req = urllib.request.Request(url, headers={'User-Agent': 'awesome-seedance-bot/1.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read(max_mb * 1024 * 1024 + 1)
        if len(data) > max_mb * 1024 * 1024:
            raise RuntimeError(f'preview too large > {max_mb}MB')
        out_path.write_bytes(data)


def make_thumbnail(in_path: pathlib.Path, out_path: pathlib.Path, width: int = 480) -> None:
    if Image is None:
        raise RuntimeError('Pillow not available. Ensure pillow is installed.')

    with Image.open(in_path) as im:
        # If GIF, use first frame
        try:
            im.seek(0)
        except Exception:
            pass

        im = im.convert('RGB')
        w, h = im.size
        if w > width:
            new_h = int(h * (width / w))
            im = im.resize((width, new_h))
        out_path.parent.mkdir(parents=True, exist_ok=True)
        im.save(out_path, format='WEBP', quality=80, method=6)


def main():
    event_path = os.environ.get('GITHUB_EVENT_PATH')
    if not event_path:
        print('GITHUB_EVENT_PATH not set', file=sys.stderr)
        return 2

    ev = load_event(event_path)
    issue = ev.get('issue') or {}
    labels = [l.get('name') for l in issue.get('labels', []) if isinstance(l, dict)]

    if APPROVE_LABEL not in labels:
        print('not approved label, skip')
        return 0

    body = issue.get('body') or ''
    fields = parse_issue_form(body)

    title = (fields.get('Title') or '').strip()
    url = (fields.get('Source URL (原链接)') or '').strip()
    author = (fields.get('Author / Handle (作者)') or '').strip() or 'Unknown'
    summary = (fields.get('Summary (一句话摘要)') or '').strip()
    tags_raw = (fields.get('Tags (comma-separated)') or '').strip()
    prompt_full = (fields.get('Full Prompt (全文提示词，可选)') or '').strip()

    preview_kind = (fields.get('Preview Media Kind (预览类型)') or 'none').strip()
    preview_url = (fields.get('Preview Media URL (预览链接)') or '').strip()

    # Permission checkbox text fragment (as in issue template)
    preview_ok = checkbox_checked(body, 'I confirm I am the author')

    if not url:
        raise RuntimeError('Missing Source URL')

    base_id = sha1(url)[:12]
    item_id = f'seedance2-{base_id}'

    tags = [t.strip() for t in re.split(r'[,\n]+', tags_raw) if t.strip()]
    if not tags:
        tags = ['case']

    if author.lower() == 'unknown' and NEEDS_CREDIT_TAG not in tags:
        tags.append(NEEDS_CREDIT_TAG)

    preview = {"ok": False, "kind": "image", "url": None, "note": None}

    # If a preview is provided AND permission checked, we try to store a local thumbnail for stability.
    # For now, we only process image/gif links.
    if preview_url and preview_ok and preview_kind in {'image', 'gif'}:
        import tempfile
        tmp = Path(tempfile.mkdtemp(prefix='seedance_preview_'))
        raw_path = tmp / (item_id + '_raw')
        download(preview_url, raw_path)

        thumb_rel = f'assets/thumbs/{item_id}.webp'
        thumb_abs = ROOT / 'site' / thumb_rel
        make_thumbnail(raw_path, thumb_abs)

        preview = {
            "ok": True,
            "kind": "image",
            "url": thumb_rel,
            "note": "embedded with submitter permission",
        }

    item = {
        "id": item_id,
        "type": "case",
        "title": title or url,
        "url": url,
        "author": author,
        "platform": "unknown",
        "lang": "unknown",
        "published_at": None,
        "summary_zh": summary,
        "summary_en": summary,
        "metrics": {},
        "tags": tags,
        "prompt_full": prompt_full,
        "preview": preview,
        "media": [],
        "credit": {"how_to_credit": "link-back"},
        "removal": {"policy": "fast-remove-on-request"},
        "added_at": datetime.now(timezone.utc).isoformat(),
        "source_issue": safe_get(issue, 'html_url'),
    }

    # De-dupe by id
    existing = ITEMS.read_text(encoding='utf-8').splitlines() if ITEMS.exists() else []
    for line in existing:
        try:
            obj = json.loads(line)
            if obj.get('id') == item_id:
                print(f'item already exists: {item_id}')
                return 0
        except Exception:
            continue

    with ITEMS.open('a', encoding='utf-8') as f:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

    print(f'added item {item_id}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
