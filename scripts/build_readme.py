#!/usr/bin/env python3
"""Generate README.md case sections from data/items.jsonl.

Reads a header template (README_HEADER.md) and appends auto-generated
case entries from the JSONL data file.
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


def build_case_md(idx: int, item: dict) -> str:
    """Build markdown block for one case."""
    title = item.get("title", "Untitled")
    url = item.get("url", "")
    author = item.get("author", "Unknown")
    tags = item.get("tags", [])
    summary = item.get("summary_zh") or item.get("summary_en") or ""
    preview = item.get("preview", {})
    thumb_path = preview.get("url", "")

    # Author link: try to reconstruct platform link
    author_link = ""
    if "youtube.com" in url:
        author_link = f"[{author}]({url})"
    elif "x.com" in url or "twitter.com" in url:
        author_link = f"[@{author}](https://x.com/{author})"
    else:
        author_link = author

    lines = []
    lines.append(f"### Case {idx}: [{title}]({url})（by {author_link}）")
    lines.append("")

    # Inline preview
    # NOTE: GitHub README sanitizer strips <video> tags entirely.
    # For user-attachments URLs: bare URL on its own line → GitHub auto-renders as video player.
    # For everything else: clickable thumbnail image.
    if preview.get("ok"):
        prev_url = preview.get("url") or ""
        kind = (preview.get("kind") or "image").lower()

        if "user-attachments/assets" in prev_url:
            # Bare URL = GitHub auto-renders inline video player
            lines.append(prev_url)
            lines.append("")
        elif kind == "video":
            # Non-user-attachments video: fall back to clickable thumbnail
            poster = preview.get("poster")
            yt_id = youtube_id(url)
            thumb = poster or (f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg" if yt_id else None)
            if thumb:
                lines.append(f'<a href="{url}"><img src="{thumb}" width="480" alt="{title}"></a>')
                lines.append("")
        else:
            # Image preview
            lines.append(f'<a href="{url}"><img src="{prev_url}" width="480" alt="{title}"></a>')
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


def build_menu(items) -> str:
    """Build table-of-contents menu."""
    lines = ["## 📑 Menu", ""]
    lines.append("- [🎬 Introduction](#-introduction)")
    lines.append("- [📑 Menu](#-menu)")
    lines.append("- [🎥 Seedance 2.0 Cases](#-seedance-20-cases)")
    lines.append("- [🤝 Contributing](#-contributing)")
    lines.append("")

    for i, item in enumerate(items, 1):
        title = item.get("title", "Untitled")
        author = item.get("author", "Unknown")
        # Build anchor
        anchor_text = f"case-{i}-{title}by-{author}"
        # Simplified anchor (GitHub auto-generates from heading)
        lines.append(f"  - [Case {i}: {title}（by {author}）](#case-{i})")
    lines.append("")
    return "\n".join(lines)


def main():
    items = load_items()

    # Read header template
    if HEADER.exists():
        header = HEADER.read_text("utf-8").rstrip()
    else:
        header = "# 🎬 Awesome Seedance\n\nA curated gallery of Seedance 2.0 video cases."

    parts = [header, ""]

    # Cases section
    parts.append("## 🎥 Seedance 2.0 Cases")
    parts.append("")

    if not items:
        parts.append("*No cases yet. [Submit one!](../../issues/new?template=submit-case.yml)*")
        parts.append("")
    else:
        for i, item in enumerate(items, 1):
            parts.append(build_case_md(i, item))

    # Contributing section
    parts.append("## 🤝 Contributing")
    parts.append("")
    parts.append("Found an amazing Seedance 2.0 video? [Submit a Case](../../issues/new?template=submit-case.yml)!")
    parts.append("")
    parts.append("---")
    parts.append("")
    parts.append("*Auto-generated from [data/items.jsonl](data/items.jsonl). "
                 "Do not edit the Cases section manually.*")
    parts.append("")

    README.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {README} ({len(items)} cases)")


if __name__ == "__main__":
    main()
