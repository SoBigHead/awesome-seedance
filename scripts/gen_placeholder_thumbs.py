#!/usr/bin/env python3
"""Generate safe placeholder thumbnails for cases that lack embeddable preview media.

Why:
- GitHub mobile/app often does NOT inline-play videos (even user-attachments).
- X/Twitter hotlinking is unreliable and permission unclear.

Approach:
- For items where we cannot (or should not) embed real preview media, generate a
  local SVG poster under assets/thumbs/<id>.svg.
- Set preview.poster to that path so README generator can always show a thumbnail.

This keeps the repo "preview-complete" without copying creator content.
"""

from __future__ import annotations

import json
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ITEMS = ROOT / "data" / "items.jsonl"
THUMBS = ROOT / "assets" / "thumbs"

W, H = 960, 540


def wrap_lines(s: str, max_chars: int, max_lines: int):
    s = " ".join((s or "").split())
    if not s:
        return [""]
    words = s.split(" ")
    lines = []
    cur = ""
    for w in words:
        nxt = (cur + " " + w).strip()
        if len(nxt) <= max_chars:
            cur = nxt
        else:
            if cur:
                lines.append(cur)
            cur = w
            if len(lines) >= max_lines:
                break
    if len(lines) < max_lines and cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
    # ellipsize last line if too long
    if lines and len(lines[-1]) > max_chars:
        lines[-1] = lines[-1][: max_chars - 1] + "…"
    return lines


def svg_for_item(item: dict) -> str:
    title = item.get("title") or "Untitled"
    author = item.get("author") or "Unknown"
    platform = item.get("platform") or "unknown"
    url = item.get("url") or ""
    tags = item.get("tags") or []

    # color by platform
    accent = {
        "x-twitter": "#1D9BF0",
        "youtube": "#FF0033",
        "bilibili": "#00A1D6",
        "reddit": "#FF4500",
        "github": "#24292e",
    }.get(platform, "#7C3AED")

    title_lines = wrap_lines(title, max_chars=42, max_lines=3)
    meta_line = f"by {author} · {platform}"
    tag_line = " ".join([f"#{t}" for t in tags[:6]])

    # escape xml
    title_lines = [html.escape(x) for x in title_lines]
    meta_line = html.escape(meta_line)
    tag_line = html.escape(tag_line)
    url_short = html.escape(url[:80] + ("…" if len(url) > 80 else ""))

    # layout
    y0 = 150
    dy = 56

    text_blocks = []
    for i, line in enumerate(title_lines):
        text_blocks.append(
            f'<text x="70" y="{y0 + i*dy}" font-size="44" font-weight="700" fill="#0B1220">{line}</text>'
        )

    meta_y = y0 + len(title_lines) * dy + 26

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#F8FAFC"/>
      <stop offset="100%" stop-color="#EEF2FF"/>
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="10" stdDeviation="12" flood-color="#000" flood-opacity="0.12"/>
    </filter>
  </defs>

  <rect width="{W}" height="{H}" rx="36" fill="url(#bg)"/>
  <rect x="48" y="48" width="{W-96}" height="{H-96}" rx="28" fill="#FFFFFF" filter="url(#shadow)"/>

  <rect x="70" y="78" width="260" height="46" rx="23" fill="{accent}"/>
  <text x="200" y="110" text-anchor="middle" font-size="22" font-weight="700" fill="#FFFFFF">Seedance 2.0 CASE</text>

  {''.join(text_blocks)}

  <text x="70" y="{meta_y}" font-size="22" fill="#334155">{meta_line}</text>
  <text x="70" y="{meta_y+36}" font-size="18" fill="#64748B">{tag_line}</text>
  <text x="70" y="{H-90}" font-size="16" fill="#94A3B8">{url_short}</text>
</svg>
"""


def main():
    THUMBS.mkdir(parents=True, exist_ok=True)

    lines = ITEMS.read_text("utf-8").splitlines()
    out_lines = []
    changed = 0
    created = 0

    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        item = json.loads(raw)
        if item.get("id", "").startswith("example-"):
            out_lines.append(json.dumps(item, ensure_ascii=False))
            continue

        preview = item.get("preview") or {}
        platform = item.get("platform") or ""

        # Create placeholders for X/Twitter and any item lacking any thumbnail reference
        needs_placeholder = platform == "x-twitter" or not preview.get("poster")

        if needs_placeholder:
            svg_path = THUMBS / f"{item['id']}.svg"
            if not svg_path.exists():
                svg_path.write_text(svg_for_item(item), encoding="utf-8")
                created += 1

            # Attach poster path (safe local asset)
            if preview.get("poster") != f"assets/thumbs/{item['id']}.svg":
                preview.setdefault("kind", preview.get("kind") or "image")
                preview.setdefault("ok", False)
                preview["poster"] = f"assets/thumbs/{item['id']}.svg"
                preview["note"] = (preview.get("note") or "").strip() or "generated safe placeholder poster"
                item["preview"] = preview
                changed += 1

        out_lines.append(json.dumps(item, ensure_ascii=False))

    ITEMS.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"created {created} svg posters, updated {changed} items")


if __name__ == "__main__":
    main()
