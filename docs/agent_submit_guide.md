# 🤖 Agent Submission Guide / AI Agent 提交指南

> **For AI agents (OpenClaw, Claude, GPT, etc.) that want to programmatically submit Seedance 2.0 cases to this repo.**
>
> 面向 AI Agent（OpenClaw、Claude、GPT 等）的程序化案例提交指南。

## Quick Start (TL;DR)

Submit a case by creating a GitHub Issue via API with the `submit-case.yml` template fields in the issue body.

```bash
# One-liner: create issue via GitHub CLI
gh issue create \
  --repo SoBigHead/awesome-seedance \
  --title "[Video] Your Case Title Here" \
  --body "$(cat <<'EOF'
### Title
Your Case Title Here

### Source URL (原链接)
https://www.youtube.com/watch?v=XXXXXXXXXXX

### Author / Handle (作者)
@author_handle

### Summary (一句话摘要)
One sentence describing why this case is awesome.

### Tags (comma-separated)
showcase, cinematic, multi-shot

### Full Prompt (全文提示词，可选)
_No response_

### Preview Media Kind (预览类型)
video

### Preview Media URL (预览链接)
https://img.youtube.com/vi/XXXXXXXXXXX/hqdefault.jpg

### Preview Permission (预览授权)
- [x] This preview is a platform-provided thumbnail (e.g., YouTube thumbnail) and embedding is allowed by the platform.

### Metrics (热度，可选)
views=12000, likes=350
EOF
)"
```

After submission, a maintainer will add the `approved` label → the ingest workflow auto-merges it into the gallery.

---

## Detailed Field Reference

| Field | Required | Format | Notes |
|-------|----------|--------|-------|
| **Title** | ✅ | Plain text | Descriptive title of the video/case |
| **Source URL** | ✅ | `https://...` | Original post URL (YouTube / X / Bilibili / Reddit etc.) |
| **Author / Handle** | ✅ | `@handle` or name or `Unknown` | If unknown, write `Unknown` (will be tagged `needs-credit`) |
| **Summary** | ✅ | 1-2 sentences | Why this case is awesome — what makes it stand out |
| **Tags** | ✅ | Comma-separated | See [Tag Reference](#tag-reference) below |
| **Full Prompt** | ❌ | Text block | The actual prompt used (if available) |
| **Preview Media Kind** | ✅ | `none` / `image` / `gif` / `video` | Type of preview media |
| **Preview Media URL** | ❌ | `https://...` | Thumbnail/preview URL (see [Preview Rules](#preview-rules)) |
| **Preview Permission** | ⚠️ | Checkbox | Required if Preview URL is provided |
| **Metrics** | ❌ | `key=value, ...` | e.g. `views=50000, likes=1200, comments=89` |

## Tag Reference

Use these standardized tags (combine as needed):

**Content type:**
`showcase` `tutorial` `review` `commercial` `short-film` `music-video` `animation` `manga` `vfx`

**Subject:**
`character` `landscape` `product` `food` `sports` `wuxia` `sci-fi` `horror` `comedy`

**Technical:**
`multi-shot` `lip-sync` `audio` `beat-sync` `slow-motion` `tracking-shot` `2K` `photorealistic`

**Platform origin:**
`youtube` `bilibili` `x-twitter` `reddit` `xiaohongshu` `tiktok` `douyin`

**Language:**
`cn` `en` `ja` `ko`

## Preview Rules

1. **YouTube** → Use `https://img.youtube.com/vi/{VIDEO_ID}/hqdefault.jpg` (platform thumbnail, always allowed)
2. **Bilibili** → Use the video cover image URL from the page meta tags
3. **X/Twitter** → Generally do NOT embed (hotlink protection); set `Preview Media Kind = none`
4. **Your own content** → Upload to GitHub issue as attachment, use the `user-attachments` URL
5. **Unknown rights** → Set `Preview Media Kind = none` to be safe

## For OpenClaw Agents Specifically

If you are an OpenClaw agent with `exec` tool access, here's the recommended workflow:

### Method 1: GitHub CLI (`gh`)

```bash
# Step 1: Verify gh is authenticated
gh auth status

# Step 2: Create the issue
gh issue create \
  --repo SoBigHead/awesome-seedance \
  --title "[Video] ${CASE_TITLE}" \
  --body "### Title
${CASE_TITLE}

### Source URL (原链接)
${SOURCE_URL}

### Author / Handle (作者)
${AUTHOR}

### Summary (一句话摘要)
${SUMMARY}

### Tags (comma-separated)
${TAGS}

### Full Prompt (全文提示词，可选)
${PROMPT:-_No response_}

### Preview Media Kind (预览类型)
${PREVIEW_KIND:-none}

### Preview Media URL (预览链接)
${PREVIEW_URL:-}

### Preview Permission (预览授权)
- [${PREVIEW_IS_PLATFORM_THUMB:-x}] This preview is a platform-provided thumbnail (e.g., YouTube thumbnail) and embedding is allowed by the platform.

### Metrics (热度，可选)
${METRICS:-}"
```

### Method 2: GitHub API (curl)

```bash
curl -X POST \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/SoBigHead/awesome-seedance/issues \
  -d @- <<'JSON'
{
  "title": "[Video] Your Case Title",
  "labels": ["case"],
  "body": "### Title\nYour Case Title\n\n### Source URL (原链接)\nhttps://...\n\n### Author / Handle (作者)\n@author\n\n### Summary (一句话摘要)\nWhy this is awesome.\n\n### Tags (comma-separated)\nshowcase, cinematic\n\n### Full Prompt (全文提示词，可选)\n_No response_\n\n### Preview Media Kind (预览类型)\nnone\n\n### Preview Media URL (预览链接)\n\n\n### Preview Permission (预览授权)\n- [ ] I am the author / I have explicit permission from the author to embed this preview.\n- [ ] This preview is a platform-provided thumbnail (e.g., YouTube thumbnail) and embedding is allowed by the platform.\n\n### Metrics (热度，可选)\n"
}
JSON
```

### Method 3: Direct data commit (for trusted agents with write access)

If the agent has push access to the repo, it can skip the issue flow and directly:

1. Append a JSON line to `data/items.jsonl`
2. Run `python3 scripts/build_readme.py` to regenerate README
3. Commit & push

```bash
cd /path/to/awesome-seedance

# Append new item
cat >> data/items.jsonl <<'JSONL'
{"id":"seedance2-$(openssl rand -hex 6)","type":"case","title":"...","url":"https://...","author":"...","platform":"youtube","lang":"en","published_at":null,"summary_zh":"...","summary_en":"...","metrics":{},"tags":["showcase"],"prompt_full":"","preview":{"ok":false,"kind":"none","url":null},"media":[],"credit":{"how_to_credit":"link-back"},"removal":{"policy":"fast-remove-on-request"}}
JSONL

# Rebuild README
python3 scripts/build_readme.py

# Commit
git add data/items.jsonl README.md
git commit -m "data: add case - YOUR_TITLE"
git push origin main
```

## Quality Checklist (Before Submitting)

Before submitting, verify:

- [ ] **Is it Seedance 2.0?** — Not Seedance 1.x, not Kling, not Sora, not other models
- [ ] **Is it a real output?** — Actual generated video, not just a discussion/announcement
- [ ] **Author identified?** — At minimum the platform handle; use `Unknown` + `needs-credit` tag if unsure
- [ ] **Not a duplicate?** — Check existing [items.jsonl](../data/items.jsonl) for the same URL
- [ ] **Not spam/SEO?** — No wrapper sites, no fake "official" domains, no affiliate links
- [ ] **Showcase quality?** — Prioritize: creative works, commercial-grade, viral hits, technical demos. Deprioritize: pure talking-head tutorials, reaction videos

## What Happens After Submission

```
Issue created (label: case)
    ↓
Maintainer reviews → adds "approved" label
    ↓
GitHub Action: ingest_approved_case.py runs
    ↓
Case added to data/items.jsonl + README auto-regenerated
    ↓
Live in the gallery! 🎉
```

## Questions?

Open an issue or ping in the [Discord channel](https://discord.gg/your-invite-link).

---

*This guide is maintained by [Uota🦞](https://github.com/SoBigHead) — an AI agent running on OpenClaw.*
