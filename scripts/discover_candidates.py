#!/usr/bin/env python3
"""Hourly candidate discovery (C-strategy: ~50/50 CN vs Global, with heavy X focus).

This script generates a markdown snippet posted into the "Candidate Feed (hourly)" issue.
It should be:
- High-signal: links you can turn into cases
- Low-risk: best-effort crawling, never blocks the pipeline

Sources:
- X/Twitter: via Bing RSS (site:x.com) (reliable without X API)
- CN: Bilibili API + Bing RSS for zhihu/wechat/xhs (best-effort)
- Global: Hacker News Algolia + Bing RSS for youtube
- GitHub: repo searches for tools/prompts/wrappers

NOTE: This is a candidate feed only; NOTHING is auto-added.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

UA = "Mozilla/5.0 (compatible; awesome-seedance-bot/1.0)"


def _fetch_bytes(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _safe(fn, fallback):
    try:
        return fn()
    except Exception as e:
        return fallback(e)


def bing_rss(query: str, n: int = 10):
    """Bing search RSS; good for finding social links without JS scraping."""
    url = "https://www.bing.com/search?format=rss&q=" + urllib.parse.quote(query)

    def _run():
        xml = _fetch_bytes(url, timeout=25)
        root = ET.fromstring(xml)
        items = []
        for it in root.findall("./channel/item"):
            title = (it.findtext("title") or "").strip()
            link = (it.findtext("link") or "").strip()
            pub = (it.findtext("pubDate") or "").strip()
            if title and link:
                items.append((title, link, pub))
        return items[:n]

    return _safe(_run, lambda e: [(f"(bing rss failed: {e})", url, "")])


def hn_algolia(q: str, n: int = 8):
    url = "https://hn.algolia.com/api/v1/search?" + urllib.parse.urlencode(
        {"query": q, "tags": "story", "hitsPerPage": n}
    )

    def _run():
        data = json.loads(_fetch_bytes(url, timeout=20))
        hits = []
        for h in data.get("hits", [])[:n]:
            title = h.get("title")
            points = h.get("points")
            comments = h.get("num_comments")
            link = f"https://news.ycombinator.com/item?id={h.get('objectID')}"
            created = h.get("created_at")
            hits.append((title, link, points, comments, created))
        return hits

    return _safe(_run, lambda e: [(f"(hn failed: {e})", url, 0, 0, "")])


def bilibili_video_search(keyword: str, n: int = 8):
    # Newest first
    url = (
        "https://api.bilibili.com/x/web-interface/search/type?"
        + urllib.parse.urlencode(
            {
                "search_type": "video",
                "keyword": keyword,
                "order": "pubdate",
                "page": 1,
            }
        )
    )

    def _run():
        data = json.loads(_fetch_bytes(url, timeout=20))
        res = []
        for v in (data.get("data") or {}).get("result", [])[:n]:
            title = (v.get("title") or "").replace('<em class="keyword">', "").replace("</em>", "")
            arcurl = v.get("arcurl")
            play = v.get("play")
            author = v.get("author")
            pubdate = v.get("pubdate")
            res.append((title, arcurl, play, author, pubdate))
        return res

    return _safe(_run, lambda e: [(f"(bilibili failed: {e})", url, 0, "", "")])


def gh_repo_search_link(q: str) -> str:
    return f"https://github.com/search?q={urllib.parse.quote(q)}&type=repositories"


def main():
    now = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")
    lines = [f"## Hourly Discovery (C: 50/50 + heavy X) — {now}", ""]

    # 1) X/Twitter — priority
    lines.append("### 🐦 X / Twitter (priority, via Bing RSS)")
    x_queries = [
        'site:x.com seedance 2.0',
        'site:x.com seedance2',
        'site:x.com (seedance 2.0) (teaser OR demo OR showcase OR prompt)',
    ]
    seen = set()
    x_items = []
    for q in x_queries:
        for title, link, pub in bing_rss(q, n=6):
            if link in seen:
                continue
            seen.add(link)
            x_items.append((title, link, pub))
    for title, link, pub in x_items[:12]:
        lines.append(f"- [{title}]({link}) ({pub})")
    lines.append("")

    # 2) CN (aim ~50%)
    lines.append("### 🇨🇳 CN cases (Bilibili + search)")
    for title, link, play, author, _ in bilibili_video_search("Seedance 2.0", n=8):
        lines.append(f"- **{play} views** — [{title}]({link}) (by {author})")

    cn_search_queries = [
        'site:xiaohongshu.com Seedance 2.0',
        'site:mp.weixin.qq.com Seedance 2.0',
        'site:zhihu.com Seedance 2.0 Seedance',
    ]
    for q in cn_search_queries:
        lines.append(f"\n**Search:** `{q}`")
        for title, link, pub in bing_rss(q, n=3):
            lines.append(f"- [{title}]({link}) ({pub})")
    lines.append("")

    # 3) Global
    lines.append("### 🌍 Global (HN + YouTube via search)")
    for title, link, points, comments, created in hn_algolia("Seedance 2.0", n=6):
        lines.append(f"- **{points} pts / {comments} comments** — [{title}]({link}) ({created})")

    yt_q = 'site:youtube.com Seedance 2.0'
    lines.append(f"\n**Search:** `{yt_q}`")
    for title, link, pub in bing_rss(yt_q, n=6):
        lines.append(f"- [{title}]({link}) ({pub})")

    lines.append("")

    # 4) GitHub (tools/wrappers)
    lines.append("### 🧰 GitHub (tools / wrappers / prompts)")
    for q in [
        "seedance2 prompts",
        "seedance2 api",
        "seedance2 wrapper",
        "awesome seedance2",
    ]:
        lines.append(f"- Search: {gh_repo_search_link(q)}")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
