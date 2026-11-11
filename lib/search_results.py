"""Pure helpers for parsing Sublime Text's native Find Results buffer."""

import re


_SUMMARY_RE = re.compile(
    r"(?:\d+ match(?:es)?(?: (?:in|across) \d+ files?)?|No results found|Search (?:cancelled|aborted))\s*$",
    re.IGNORECASE,
)
_RESULT_RE = re.compile(r"^\s+(\d+):\s?(.*)$")
_HEADER_RE = re.compile(r'^\s*Searching\b.*?\bfor "(.*)"(?P<flags>(?: \([^)]*\))*)\s*$', re.MULTILINE)


def search_is_complete(text):
    """Return True once Sublime has appended a terminal search summary.

    Only the last non-empty line can be the summary, and it must be nothing but the summary:
    matching the end of the whole text let a running search look finished, because a MATCH line
    whose own text ends in "12 matches" (or "No results found") ended the text (measured
    2026-11-11: `.../doc.md:\\n    7: see 12 matches\\n` answered True while the panel had written
    no summary). A caller then read a half-written result list as final, with `total` short.
    """
    lines = [line for line in (text or "").splitlines() if line.strip()]
    if not lines:
        return False
    return bool(_SUMMARY_RE.fullmatch(lines[-1].strip()))


_MAX_PARSE = 50000


def panel_search_pattern(text):
    """The pattern the results panel is actually showing, from its own header line.

    Returns (pattern, is_regex) or None when no header has been written yet. A caller that
    reads the panel without this check can attribute the previous search's matches to its own
    pattern (found 2026-11-10: reading after a search that had not written anything yet returned
    the earlier search's match, with complete: true)."""
    m = _HEADER_RE.search((text or ""))
    if not m:
        return None
    return m.group(1), "regex" in (m.group("flags") or "").lower()


def parse_find_results(text, pattern="", regex=False, case_sensitive=False, hard_limit=_MAX_PARSE):
    """Convert ST's Find Results text into stable, structured matches.

    Every match in the text is parsed; the caller slices to its own limit. Stopping at the
    caller's limit here made a complete result set of exactly that size look truncated
    (found 2026-11-10: 8 matches, limit 8, complete summary, truncated: true).
    ``hard_limit`` only bounds a pathological panel."""
    matches = []
    current_path = None
    flags = 0 if case_sensitive else re.IGNORECASE
    compiled = None
    if pattern:
        try:
            compiled = re.compile(pattern if regex else re.escape(pattern), flags)
        except re.error:
            compiled = None

    for line in (text or "").splitlines():
        if line and not line[0].isspace() and line.endswith(":"):
            candidate = line[:-1]
            if not candidate.lower().startswith("searching "):
                current_path = candidate
            continue
        result = _RESULT_RE.match(line)
        if not result or not current_path:
            continue
        line_number = int(result.group(1))
        preview = result.group(2)
        found = compiled.search(preview) if compiled else None
        matches.append({
            "path": current_path,
            "line": line_number,
            "col": found.start() + 1 if found else 1,
            "text": preview,
        })
        if len(matches) >= max(1, int(hard_limit)):
            break
    return matches

# reload probe 2283889471952
