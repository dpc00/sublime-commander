---
name: release
description: Cut a complete sublime-commander release — version strings, CHANGELOG, guide and skill updates committed in the tagged commit, then GitHub, PyPI and npm — with the two git commands that prove nothing was left behind. Use before and after every tag.
---

# Cutting a sublime-commander release

Ten releases have gone out incomplete. Every one was the same miss: something the release claimed —
a document, a skill, a note, a version string — was written but was **not in the commit the tag
points at**. It was committed afterwards, so the tag shipped the previous text.

## The invariant

> The tagged commit contains everything the release claims.

Version strings, the `CHANGELOG.md` section, and every guide, skill or note written for that release
are committed **in** the release commit, and the tag points at it.

## Sequence

1. **Finish the prose first**, in one commit: `CHANGELOG.md` section for the version, and whatever the
   change needs in `AGENT_GUIDE.md` (and `docs/AGENT_GUIDE.md`, which is the same text served by
   `get_help`), `skills/`, and `.claude/memory/` notes.
2. **Bump both version strings in that same commit**:
   - `sublime_mcp.py` → `__version__`
   - `server.json` → `version`
3. **Tag that commit** (`v<version>`), push `main` and the tag.
4. **Publish**: a GitHub release whose notes are the CHANGELOG section. There are no registry
   packages any more (the npm and PyPI proxies were removed on 2026-11-09).
5. **Prove it, and treat any output as a failed release**:
   ```
   git status --short            # nothing
   git log --oneline v<version>..HEAD   # nothing
   ```
   Also confirm `server.json` and the MCP server's own `version` reply both say `<version>`.
6. Say it is done only with that evidence, and say what was proved by running the package and what
   was not tested, with the reason.

## Traps seen

- There are no registry artifacts any more: releases are a tag and a GitHub release whose notes are
  the CHANGELOG section. That is not permission to tag early — readers get the guide *at the tag*, and
  the tag's copy is the one that must be current.
- A release was once tagged while the code fix it announced was only in the live package file and never
  committed. `git show v<version> --name-only` before publishing: the fix must be in the commit.
- `docs/AGENT_GUIDE.md` and `AGENT_GUIDE.md` are duplicates; updating one and not the other leaves the
  `get_help` text and the repo text disagreeing.
