---
name: release
description: Cut a complete sublime-mcp release — version strings, CHANGELOG, guide and skill updates committed in the tagged commit, then GitHub, PyPI and npm — with the two git commands that prove nothing was left behind. Use before and after every tag.
---

# Cutting a sublime-mcp release

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
2. **Bump all four version strings in that same commit**:
   - `sublime_mcp.py` → `__version__`
   - `server.json` → `version`
   - `packages/python-proxy/pyproject.toml` → `version`
   - `packages/node-proxy/package.json` → `version`
3. **Tag that commit** (`v<version>`), push `main` and the tag.
4. **Publish**: GitHub release whose notes are the CHANGELOG section; PyPI (`twine upload` of the
   wheel and sdist); npm (`npm publish` — needs the owner's browser auth, so ask for it and wait).
5. **Prove it, and treat any output as a failed release**:
   ```
   git status --short            # nothing
   git log --oneline v<version>..HEAD   # nothing
   ```
   Also confirm the published versions agree: `server.json`, the PyPI release list, and
   `npm view sublime-mcp version` must all be `<version>`, and npm's `gitHead` must be the tagged
   commit.
6. Say it is done only with that evidence, and say what was proved by running the package and what
   was not tested, with the reason.

## Traps seen

- The wheel (7 files) and the npm tarball (5 files) contain **no markdown at all**, so registry users
  get no guide. That is not permission to tag early: repo readers and the GitHub release page get the
  guide *at the tag*, and the tag's copy is the one that must be current.
- A release was once tagged while the code fix it announced was only in the live package file and never
  committed. `git show v<version> --name-only` before publishing: the fix must be in the commit.
- `docs/AGENT_GUIDE.md` and `AGENT_GUIDE.md` are duplicates; updating one and not the other leaves the
  `get_help` text and the repo text disagreeing.
