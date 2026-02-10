#!/usr/bin/env python3
"""Generate README.md case sections from data/items.jsonl.

Design goals:
- README is the primary gallery.
- **Every case should have a visible thumbnail** (even if we can't inline-play video).
- Inline video is best-effort:
  - GitHub web: a bare `github.com/user-attachments/...` URL renders a player.
  - GitHub mobile/app: often shows only a link → thumbnail still matters.

Rules:
- If we have an embeddable preview image/GIF (and permission), show it.
- If preview is a user-attachments video, show BOTH:
  - a clickable thumbnail (poster)
  - the bare user-attachments URL (for web inline player)
- If we cannot safely embed media (e.g., X/Twitter), fall back to a **local placeholder poster**.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ITEMS = ROOT / "data" / "items.jsonl"
HEADER = ROOT / "README_HEADER.md"
README = ROOT / "README.md"


def load_items():
    items = []
    for line in ITEMS.read_text("utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        # skip example placeholder
        if obj.get("id", "").startswith("example-"):
            continue
        items.append(obj)
    return items


def youtube_id(url: str):
    """Extract YouTube video ID from URL."""
    m = re.search(r"(?:v=|youtu\.be/)([\w-]{11})", url or "")
    return m.group(1) if m else None


def is_user_attachments(url: str) -> bool:
    return "user-attachments/assets" in (url or "")


def select_thumbnail(item: dict) -> str | None:
    """Select the best thumbnail URL for a case.

    Preference:
    1) embeddable preview image/GIF URL (preview.ok + preview.url) — except user-attachments video
    2) preview.poster (local asset or external allowed)
    3) YouTube platform thumbnail derived from the main URL
    4) local placeholder assets/thumbs/<id>.svg if exists
    """
    url = item.get("url", "")
    preview = item.get("preview", {}) or {}

    prev_url = preview.get("url") or ""
    kind = (preview.get("kind") or "image").lower()

    if preview.get("ok") and prev_url and not (kind == "video" and is_user_attachments(prev_url)):
        return prev_url

    poster = preview.get("poster")
    if poster:
        return poster

    if "youtube.com" in url or "youtu.be" in url:
        vid = youtube_id(url)
        if vid:
            return f"https://img.youtube.com/vi/{vid}/hqdefault.jpg"

    local_svg = ROOT / "assets" / "thumbs" / f"{item.get('id')}.svg"
    if local_svg.exists():
        return f"assets/thumbs/{item.get('id')}.svg"

    return None


def author_link(url: str, author: str) -> str:
    if "youtube.com" in (url or ""):
        # channel is unknown from URL; keep as plain text
        return author
    if "x.com" in (url or "") or "twitter.com" in (url or ""):
        handle = author.lstrip("@").strip() or "Unknown"
        return f"[@{handle}](https://x.com/{handle})"
    return author


def build_case_md(idx: int, item: dict) -> str:
    title = item.get("title", "Untitled")
    url = item.get("url", "")
    author = item.get("author", "Unknown")
    tags = item.get("tags", [])
    summary = item.get("summary_zh") or item.get("summary_en") or ""

    preview = item.get("preview", {}) or {}
    prev_url = (preview.get("url") or "").strip()
    kind = (preview.get("kind") or "image").lower()

    lines = []
    lines.append(f"### Case {idx}: [{title}]({url})（by {author_link(url, author)}）")
    lines.append("")

    # Always try to show a thumbnail
    thumb = select_thumbnail(item)
    if thumb:
        lines.append(f'<a href="{url}"><img src="{thumb}" width="480" alt="{title}"></a>')
        lines.append("")

    # Inline video (best-effort): user-attachments only
    if preview.get("ok") and kind == "video" and is_user_attachments(prev_url):
        # Bare URL = GitHub web auto-renders inline video player
        lines.append(prev_url)
        lines.append("")

    # Tags
    if tags:
        tag_str = " ".join(f"`{t}`" for t in tags)
        lines.append(f"**Tags:** {tag_str}")
        lines.append("")

    # Summary
    if summary:
        lines.append(f"> {summary}")
        lines.append("")

    return "\n".join(lines)


def main():
    items = load_items()

    header = HEADER.read_text("utf-8").rstrip() if HEADER.exists() else "# 🎬 Awesome Seedance\n\nA curated gallery of Seedance 2.0 video cases."

    parts = [header, ""]

    parts.append("## 🎥 Seedance 2.0 Cases")
    parts.append("")

    if not items:
        parts.append("*No cases yet. [Submit one!](../../issues/new?template=submit-case.yml)*")
        parts.append("")
    else:
        for i, item in enumerate(items, 1):
            parts.append(build_case_md(i, item))

    parts.append("## 🤝 Contributing")
    parts.append("")
    parts.append("Found an amazing Seedance 2.0 video? [Submit a Case](../../issues/new?template=submit-case.yml)!")
    parts.append("")
    parts.append("---")
    parts.append("")
    parts.append(
        "*Auto-generated from [data/items.jsonl](data/items.jsonl). "
        "Do not edit the Cases section manually.*"
    )
    parts.append("")

    README.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {README} ({len(items)} cases)")


if __name__ == "__main__":
    main()
