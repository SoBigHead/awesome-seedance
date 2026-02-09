import re
from typing import Dict

SECTION_RE = re.compile(r'^###\s+(.*?)\s*$', re.M)

def parse_issue_form(body: str) -> Dict[str, str]:
    """Parse GitHub Issue Forms rendered markdown (### Heading + value blocks)."""
    if not body:
        return {}

    # Find headings positions
    matches = list(SECTION_RE.finditer(body))
    out: Dict[str, str] = {}
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        val = body[start:end].strip('\n').strip()
        # Normalize common placeholder empty
        if val in {'_No response_', 'No response', 'N/A'}:
            val = ''
        out[title] = val
    return out

def checkbox_checked(body: str, contains: str) -> bool:
    if not body:
        return False
    # Example: - [x] I confirm ...
    pat = re.compile(r'^-\s+\[x\]\s+.*' + re.escape(contains) + r'.*$', re.I | re.M)
    return bool(pat.search(body))
