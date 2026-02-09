# items.jsonl schema (v0)

Each line in `data/items.jsonl` is a JSON object.

## Required fields
- `id` (string): unique id
- `type` (string): `case|prompt|template|review|tool|official`
- `title` (string)
- `url` (string): original source link (primary reference)
- `author` (string): can be `Unknown`
- `tags` (string[]): at least 1
- `summary_zh` / `summary_en` (string): one-liner

## Optional fields
- `platform` (string)
- `lang` (string)
- `published_at` (string|null): ISO-8601
- `metrics` (object): `upvotes/comments/views/stars/...`
- `prompt_full` (string)

## Preview embedding (IMPORTANT)
`preview` (object):
- `ok` (bool): **true only if the submitter is the author / has permission / embedding is allowed by the platform**
- `kind` (string): `image|gif|video`
- `url` (string|null): preview media URL (small thumbnail/GIF/video)
- `note` (string|null): short note about permission/source

If `author == "Unknown"`, the item should also include a `needs-credit` tag.

## Removal
`removal.policy` defaults to `fast-remove-on-request`.
