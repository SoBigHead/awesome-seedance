# Media preview policy (预览媒体政策)

We want the gallery to be *useful* and *decent*.

## Default
- Always keep the original source link as the primary reference.
- We only embed preview media (image/GIF/video) when it is allowed.

## When preview is allowed
Preview is allowed only when the submitter confirms at least one of:
- They are the original author.
- They have explicit permission from the author.
- The platform explicitly allows embedding/previewing.

In such case, set:
- `preview.ok = true`
- Fill `preview.kind` and `preview.url`

## When preview is NOT allowed
- Leave `preview.ok = false`.
- Only include the source link.

## Takedown
If you are the content owner and want removal, please use the **Removal Request** issue form.
