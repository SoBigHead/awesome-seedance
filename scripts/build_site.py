#!/usr/bin/env python3
"""Build the gallery site: JSONL → JSON + copy assets."""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JSONL = ROOT / "data" / "items.jsonl"
SITE = ROOT / "site"
OUT = SITE / "data.json"

def main():
    items = []
    with open(JSONL, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))

    # Sort by added_at descending (newest first)
    items.sort(key=lambda x: x.get("added_at", ""), reverse=True)

    # Extract all unique tags and platforms for filters
    all_tags = sorted({t for item in items for t in item.get("tags", [])})
    all_platforms = sorted({item.get("platform", "unknown") for item in items})

    output = {
        "meta": {
            "total": len(items),
            "tags": all_tags,
            "platforms": all_platforms,
        },
        "items": items,
    }

    SITE.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, separators=(",", ":"))
    print(f"✓ {len(items)} items → {OUT} ({OUT.stat().st_size // 1024}KB)")

    # Copy assets/thumbs → site/assets/thumbs
    src_thumbs = ROOT / "assets" / "thumbs"
    dst_thumbs = SITE / "assets" / "thumbs"
    if src_thumbs.exists():
        if dst_thumbs.exists():
            shutil.rmtree(dst_thumbs)
        shutil.copytree(src_thumbs, dst_thumbs)
        count = len(list(dst_thumbs.iterdir()))
        print(f"✓ {count} thumbnails → {dst_thumbs}")

    # Copy assets/previews → site/assets/previews
    src_prev = ROOT / "assets" / "previews"
    dst_prev = SITE / "assets" / "previews"
    if src_prev.exists():
        if dst_prev.exists():
            shutil.rmtree(dst_prev)
        shutil.copytree(src_prev, dst_prev)
        count = len(list(dst_prev.iterdir()))
        print(f"✓ {count} previews → {dst_prev}")

if __name__ == "__main__":
    main()
