# sublime-commander — agent entry point

This file exists so a session that starts in this repo loads the rules before acting. The rules
themselves live elsewhere; this is the pointer plus the few facts that get re-derived wrongly.

## The package audit runs in its own repo

Read, in this order, before any package test, issue or PR:

1. `C:/Users/donal/projects/sublime-package-audit/CLAUDE.local.md`
2. `C:/Users/donal/projects/sublime-package-audit/.claude/skills/sublime-package-audit/SKILL.md`
3. `C:/Users/donal/projects/sublime-package-audit/PROCEDURE.md`
4. `C:/Users/donal/projects/sublime-package-audit/data/do_not_file.tsv`

Those skills sit under another project's `.claude/skills/`, so omp does not surface them as skills.
Reading them is a step, not an optional recall.

## The rig

Four portable installs exist under `C:/Users/donal/tools/`: `st_portable` and
`ST-portable-4215-omp-1`, `-omp-2`, `-omp-3`. Any could be driven — each declares its own `mcp_port`
in `Data/Packages/User/MCP Commander.sublime-settings` — but the audit uses **`st_portable`**, because
the baselines, hashes and every recorded result belong to that instance. Do not switch instances
mid-test and never carry evidence across.

- `st_portable` → the audit rig's MCP server, `http://127.0.0.1:9512/sse` (`mcp_port: 9512`,
  `http_port: 9510`). The `-omp-*` instances declare 9542 / 9552 / 9562; leave them alone.
- Before a test call, confirm the port from that instance's `MCP Commander.sublime-settings` and
  confirm `list_native_windows` returns the hwnd you just launched.
- Record both `Data/Packages/User` settings hashes before installing; after removal the same two
  hashes must match again. One window at a time.

## Dialogs

A modal dialog in the editor that hosts the agent session takes the window away from the person: the
agent's UI is a tab in that same Sublime, so while the dialog is up they are looking at it instead of
at the conversation, and any approval prompt waits behind it. Donald, 2026-11-08, after one was raised
on purpose to test the watcher: he could have handled it himself, and he should never have had to —
"while a file-open dialog is displayed, I cannot get to the GhostShell UI to handle a permission
prompt… it would have been session-bricked". So: **never raise a modal in the window that hosts the
session.** Exercise dialogs in a separate portable whose server is a different instance, or not at
all. When one appears anyway — from your own command or a package — answer it at once and say so;
never leave it up "just for a second".

For the mechanism: a native dialog blocks Sublime's main thread from inside the dispatch, so that call
cannot return until the dialog is answered. The caller watches: dispatch without awaiting, poll
`list_native_windows` (it needs no main thread), `dismiss_native_window` the dialog that appears, then
the dispatch returns. A step interrupted this way did not finish: read the console and re-run it.
sublime-commander is ST commands only and carries no policy; dialog choice is the caller's, and a dialog is
reported — never clicked by a watcher — unless the person asks for it.

## PRs and forks

No PR and no fork unless the maintainer's gate passes: a maintainer commit within 12 months and at
least one PR ever merged. Otherwise the finding is an issue comment only, starting
`omp - deepseek v4 flash reports:`. When the gate passes: fork under `dpc00`, branch `fix/<topic>`,
clone in `~/tools/forks` (not a scratch dir — that is where fork clones live and stay), verify the
patched files in the portable before pushing.

**Never delete an unmerged fork, and never delete its clone.** Fork and clone stay in
`~/tools/forks` until the pull request is merged (or the maintainer closes it unmerged and says so),
and only then are they removed. Donald, 2026-11-10: "never delete any unmerged fork" — after a clone
was deleted minutes after its PR was opened, which orphaned nothing but lost the working copy.

## Elsewhere in this repo

- `AGENT_GUIDE.md` — using sublime-commander's own tools; `docs/COMMAND_TOOLS.md` for the generated
  command tools.
- `skills/sublime-commander/SKILL.md` — the short tool briefing; `AGENT_GUIDE.md` is the full text.
- `docs/RELEASING.md` — cutting a release; `docs/PACKAGE_SKILLS.md` — documenting another package's
  controls as a skill.
- `.claude/memory/reference_condensed_all_notes_2026_10_31.md` — the dated one-notes file; its
  "Bug log" is where a halt, stall or wrong-tab action is recorded.
