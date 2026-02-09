#!/usr/bin/env python3
"""Lightweight hourly discovery.

Outputs markdown snippet for a feed issue.
Sources (best-effort):
- HN Algolia: 'seedance 2.0' stories
- Reddit search JSON: 'seedance 2.0' top/new (may be rate-limited)
- GitHub repos: seedance2 prompts/tools (not cases but useful)

This is a *candidate* feed only; nothing is auto-added.
"""

import json
import os
import textwrap
import urllib.parse
import urllib.request
from datetime import datetime, timezone


def fetch_json(url: str, headers=None, timeout=20):
    req = urllib.request.Request(url, headers=headers or {'User-Agent': 'awesome-seedance-bot/1.0'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def hn_hits(q: str, n=8):
    url = 'https://hn.algolia.com/api/v1/search?' + urllib.parse.urlencode({
        'query': q,
        'tags': 'story',
        'hitsPerPage': n,
    })
    data = fetch_json(url)
    hits = []
    for h in data.get('hits', []):
        title = h.get('title')
        points = h.get('points')
        comments = h.get('num_comments')
        obj = h.get('objectID')
        link = f'https://news.ycombinator.com/item?id={obj}'
        created = h.get('created_at')
        hits.append((title, link, points, comments, created))
    return hits


def reddit_hits(q: str, n=8):
    url = 'https://www.reddit.com/search.json?' + urllib.parse.urlencode({
        'q': q,
        'sort': 'new',
        't': 'day',
        'limit': n,
    })
    headers = {'User-Agent': 'awesome-seedance-bot/1.0'}
    data = fetch_json(url, headers=headers)
    out = []
    for ch in data.get('data', {}).get('children', []):
        d = ch.get('data', {})
        title = d.get('title')
        score = d.get('score')
        comments = d.get('num_comments')
        permalink = d.get('permalink')
        link = 'https://www.reddit.com' + permalink
        created = d.get('created_utc')
        out.append((title, link, score, comments, created))
    return out


def gh_repos(q: str, n=6):
    # Use GitHub search API via unauthenticated https (works in Actions with token too, but keep simple)
    # We'll just output query for humans; actual harvesting is manual.
    return [(q, f'https://github.com/search?q={urllib.parse.quote(q)}&type=repositories')]


def main():
    now = datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M %Z')
    lines = [f'## Hourly candidates — {now}', '']

    lines.append('### Hacker News (Algolia)')
    for title, link, points, comments, created in hn_hits('Seedance 2.0', 8):
        lines.append(f'- **{points} pts / {comments} comments** — [{title}]({link}) ({created})')
    lines.append('')

    lines.append('### Reddit (best-effort)')
    try:
        for title, link, score, comments, _ in reddit_hits('Seedance 2.0', 8):
            lines.append(f'- **{score} score / {comments} comments** — [{title}]({link})')
    except Exception as e:
        lines.append(f'- (reddit fetch failed: `{e}`)')
    lines.append('')

    lines.append('### GitHub (related repos)')
    for _, link in gh_repos('seedance2 prompts', 1):
        lines.append(f'- Search: {link}')
    for _, link in gh_repos('awesome seedance2', 1):
        lines.append(f'- Search: {link}')

    print('\n'.join(lines))


if __name__ == '__main__':
    main()
