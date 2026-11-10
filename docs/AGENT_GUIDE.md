# Agent Guide for sublime-commander (MCP Commander)

How to use sublime-commander tools. Call `get_help` if you are unsure how to
save, close tabs, or run ST Python.

## Tool choice: the editor, because it is faster

Sublime Text is not a convenience wrapper. A sublime-commander call runs inside the editor process that
already holds the buffers; a shell command or a script pays process start-up and re-reads the same
bytes. Benchmarks on this project put the editor path up to 42x faster than the equivalent external
path for the same work.

For anything Sublime can do, the sublime-commander tool is the tool:

| job | use this | not this |
|---|---|---|
| find text | `project_search` (always pass `where`), or Find in Files (`find_in_folder` -> `find_all`) | shell grep, an external search tool |
| read a file | `str_replace_based_edit_tool(command="view")`, `get_active_file`, `get_view_chars` | any other file reader |
| change a file | `str_replace_based_edit_tool` then `save_file` | writing the file on disk behind the editor |
| buffer, selection, cursor | `get_active_file`, `get_selection`, `get_cursor_context` | |
| many small steps | one `batch` | a chain of round trips |

Everything else in the 379-tool catalog is one `discover_tools(query=...)` away: navigation,
selection, bookmarks, panels, menus, packages, screenshots, terminal tabs.

Two things are not reasons to leave the editor:

- "shelling out is quicker for me" -- it is not; that is what the 42x measures.
- "the editor call timed out once" -- a timeout is usually scope. `project_search` without `where`
  over a large tree is slow; the same pattern with `where=["*.md"]` answers at once. Narrow the
  call; do not abandon it.

Other tools -- a shell, a script, Python, a file writer -- are for what Sublime has no tool for:
builds, tests, git, network. Say which one and why, and prefer reading its output back in the editor.

Eight workflow tools are shown by default; the complete typed catalog (379
tools) remains available through `discover_tools` and `batch`. Prefer a named capability over
`run_command`, which often opens UI that steals focus from the agent chat.

On the first Sublime operation, call `get_help` once. The guide is long (about 16 KB):
`get_help(section="console")` returns only the sections whose heading contains that word, and
every `get_help` result lists the section headings.

ST tools use **1-based** line/column (`get_active_file`, `open_file`,
`goto_line`, `replace_lines`). Language-server tools use **0-based**. Subtract 1 when
passing an ST cursor into an `lsp_*` tool.

## Tools never wait; the agent does the waiting

No call sleeps, polls or blocks to produce a result. A command that starts work — a build, a
syntax test, a package install, a language server, anything that opens a panel or tab — returns at
once, and the result is read later, by you.

- Read it with the tool that owns it: `get_output_panel` (build or syntax-test results),
  `get_console` (tracebacks), `get_quick_panel`, `get_sheets`.
- You arrange the delay, not the editor: do other work, then ask again in a later call. Repeating
  a read is cheap; a blocked session is not.
- Never put a starting call and its read-back in one `batch`; the read runs immediately.
- A timeout is information about the editor, not a reason to wait longer. Look at state first
  (`get_sheets`, `list_native_windows`), then decide.

This is a rule, not a preference: a handler that sleeps, polls or blocks for a result is a defect.
If you are writing a sleep, a retry loop or a timeout to collect a result, stop and split the call
into a start and a read instead. Age is not an excuse for a tool that already does it.

## Quick start

Eight tools are listed and are called directly: `get_help`, `get_active_file`, `ui_screenshot`,
`project_search`, `str_replace_based_edit_tool`, `save_file`, `batch`, `discover_tools`.
Every other tool is hidden. Find it with `discover_tools`, run it with `batch`.
`discover_tools` never returns the eight listed tools, so do not search for them.

```
discover_tools(query="sort lines")                    # find a tool by words
discover_tools()                                      # or browse: categories -> subcategories -> tools
batch(calls=[{"tool": "sort_lines"}])                 # run it (also for a single call)
```

A new tab with text, sorted and upper-cased, then read back (one round trip):

```
batch(calls=[
  {"tool": "new_file"},
  {"tool": "insert", "args": {"characters": "pear\napple\nmango"}},
  {"tool": "select_all"},
  {"tool": "sort_lines"},
  {"tool": "upper_case"},
  {"tool": "get_active_file"}
])
```

Close that tab without saving. Name the tab (an untitled tab's name is its first line); a name that fits
several tabs is refused and lists them. Throwing away unsaved text asks the person first:

```
batch(calls=[{"tool": "close_file", "args": {"name": "pear", "discard": true}}])
```

- `insert` types at the cursor, so calling it twice puts the text in twice.
- Case commands (`upper_case`, `lower_case`, `title_case`, `swap_case`) act on the
  selection: `select_all` first. `sort_lines` sorts the whole buffer when nothing is selected.
- `get_active_file` returns untitled tabs too (`path` is null). It cuts `content` at 20000 characters
  (`truncated: true`, `size` gives the full length); pass `max_chars` for more, or read a part with
  `get_view_chars`.
- `close_file` on a modified tab without `discard` opens a native "Save Changes?" dialog that blocks
  every tool; see "When a native dialog blocks Sublime" below. Once, `set_scratch` followed
  by `close_file` in one `batch` was followed by Sublime exiting (cause not established).

A file on disk: create it, change it, save it, read it back, close it. The first four are
listed tools, called directly:

```
str_replace_based_edit_tool(command="create", path="C:\\dir\\notes.txt", file_text="hello world")
str_replace_based_edit_tool(command="str_replace", path=..., old_str="hello", new_str="goodbye")
save_file(path=...)
str_replace_based_edit_tool(command="view", path=...)
batch(calls=[{"tool": "close_file", "args": {"path": "..."}}])      # hidden tool, saved file: no prompt
```

`create` opens the new tab itself (no `open_file` needed) and fails if the file already exists;
the file reaches the disk when `save_file` runs. `str_replace` and `insert` edit the open tab, so
they also need `save_file`. `create` does not make missing folders, and `save_file` into a missing folder is
refused with an error (it used to answer ok while Sublime showed an "Unable to save" dialog). It returns at
once: the save is requested, not waited for — check `get_sheets` (`is_dirty`) and the result's
`native_dialogs` (a Save As prompt, an "Unable to save" error) before repeating. `get_sheets` and
`get_open_files` add `disk_differs: true` to a tab that
reads as clean but holds an empty buffer for a file that has content on disk: Sublime then counts the buffer as
modified and asks "Save changes?" on close. To open an existing file use
the hidden tool `open_file(path=...)`; it returns at once and Sublime loads the file asynchronously, so check
`get_sheets` (`is_focused`) before typing into it.

Hidden tools (everything except the eight) are only reachable through `batch`; calling one
directly gives "No such tool". `get_sheets` returns every tab's full settings (over 100 lines per
tab) unless you pass `settings=false`, which gives a compact list; the hidden `get_open_files`
returns just each tab's path, name and dirty flag.

## Batch (cuts round trips)

Each call pays a trip through ST's main-thread scheduler. For 2+ independent
calls, use `batch` (max 50; cannot call itself):

```
batch(calls=[
  {"tool": "get_active_file"},
  {"tool": "get_selection"},
  {"tool": "get_cursor_context", "args": {"lines": 20}}
])
```

Returns `{"results": [...]}` in call order. A failed call is `{"error": ...}`
in its slot; the rest still run.

## Finding tools (discover_tools)

`discover_tools()` lists the categories (`app`, `editing`, `files`, `packages_and_dev`, `project`,
`read`, `run`, `search`, `selection`, `settings`, `tabs`, `view`); `category="editing"` opens one,
`category="editing/lines"` lists its tools with schemas; `query="upper case"` searches all tools.
Run any result with `batch(calls=[{"tool": "<name>", "args": {...}}])`.

## Editing

`str_replace_based_edit_tool` edits the **buffer**, not disk. Always save:

1. `str_replace_based_edit_tool(command="str_replace", path=..., old_str=..., new_str=...)`
2. `save_file(path=...)` — omit `path` to save the active file

Skip save and ST looks edited while `git diff` is empty.

- Disk `edit`/`write` on a file ST has open → `revert_file(name=...)` (or `index`) so the buffer reloads;
  it asks the person first, and a name that fits several tabs is refused.
- Short plain text into an empty tab: `insert` is fine. Indented or large multi-line
  content: use `replace_lines(begin, end, text)`, because `insert` (and
  `view.run_command("insert", ...)`) auto-indents every line and piles indentation.
- `str_replace` `old_str` must match **exactly once**.
- A tab can be **read-only** (`get_sheets` → `is_read_only: true`; the Package
  Control Messages tab right after an install is one). A package that writes into
  "the active view" — Glue's `glue_writer`, many insert-style plugins — then writes
  nothing, with no error and no console line, and may even rename that tab. Start
  such a test from an editable buffer (`new_file`) and check `is_read_only` before
  blaming the package.
- Commands: `str_replace`, `insert` (after 1-based `insert_line`; `0` = start),
  `create`, `view`.

## Closing tabs

A dirty view makes `close_file` open ST's save prompt. Save first, or pass `discard: true`
(it asks the person). Always give `name` (or `index`, or `path`): with none of them `close_file`
closes the ACTIVE tab, which the person may be typing in. A `name` that fits several tabs is
refused with the list of matches. It returns at once and does not wait to see whether the tab went: check
`get_sheets` (the tab is gone) and `native_dialogs` (Sublime may be asking "Save changes before closing?",
which can happen even when `get_sheets` says `is_dirty: false`, for example a file created after its tab was
opened), or a host hook may have refused the close. Do not repeat the call before you have looked: each repeat
raises another dialog. Answer the dialog (Windows: `dismiss_native_window`; WSL/Linux: on screen).

## eval_python

Asks the person first (see "Destructive tools ask the person first"); prefer a dedicated tool.
Runs in ST's plugin host. Use `print(expr)` — top-level `return` is a syntax
error; bare expressions produce no output. In scope: `sublime`, `window`,
`view`. Timeout is 5s (main-thread).

`eval_python_latest` is **system** Python on PATH, not the ST host — no
`sublime`/`window`/`view`.

## Common tools

```
get_active_file()                  # path, content (first 20000 chars), 1-based line/col, is_dirty, syntax
get_cursor_context(lines=10)       # ±N lines, numbered
get_selection()                    # highlighted text
get_sheets()                       # every tab: stable id, group/index, selection/focus, path/name
get_sheet_content(index=2)         # untitled / scratch / terminal tabs too
open_file(path=..., line=42, col=1)
save_all()
revert_file(name="notes.txt")      # asks the person; name or index, else the active view
project_search(pattern=..., where=...)  # starts ST Find-in-Files and returns at once
project_search_results(pattern=...)     # reads the matches written so far (complete: bool)
discover_tools()                        # categories; see "Finding tools"
get_commands()                     # command ids, scopes, packages, palette captions
```

`project_search` `where` accepts folder paths, `*.py`, `-*.md`, `${project}`,
`${open_files}`, `${folder:Name}` — or a list of those, which is joined with commas
(measured 2026-11-09: a list used to be passed to Sublime unchanged and silently ignored).

## Typing into a GhostShell terminal tab (a shell, Claude Code and other agent CLIs)

GhostShell has no command for sending text into a terminal tab (removed 2026-10-19: `ai_terminal_send_string`,
`ai_terminal_send_string_window`, `ai_terminal_queue_input`, `ai_terminal_queue_input_to`). Do it the way a person does:
select the tab, type, send the Return, go back to your own tab. Always send the Return: there is no "leave the line".
A command that then waits for the person (an npm login) is still sent; watch the tab and say what it waits for.

1. **Find the target.** `get_sheets(settings=false)`: a shell console (`Dos Console`, `PowerShell`, `Bash`, `WSL Bash` or
   `C:\Windows\system32\cmd.exe`) or an agent console; never your own tab (the one with `is_focused: true`). Take the id and the
   index from this read: a new tab is inserted at index 1 and moves the others, and an agent renames its own tab.
2. **Read it, then decide.** `get_sheet_content(index=<target index>)`. It is free only if the text ENDS with the prompt and nothing
   after it (`C:\path>`, `PS C:\path>`, `...$`, or an empty `❯` line in omp); that test works for every console. The tab name helps
   for some: `cmd.exe` shows ` - <command>` while it runs, an agent shows `π <glyph> <project>` (a spinner frame = working, `>` =
   idle), PowerShell and bash keep a plain name. If it is busy, wait and read again. If no suitable console exists, open one with
   `run_command` `ai_terminal_open_here` and `{"profile": "<name>", "paths": ["<directory>"]}` (tested with Dos Console,
   PowerShell, Bash, WSL Bash and omp; the prompt appears after 3 to 12 s) and wait for it.
3. **One batch: focus, check, type with the Return, go back.** Your permission prompts are shown in your own tab, so a call
   must never leave the console tab in front:

```
batch(calls=[
  {"tool": "focus_sheet",  "args": {"id": <target id>}},
  {"tool": "get_sheets",   "args": {"settings": false}},     # target must show is_focused: true here
  {"tool": "ui_type_text", "args": {"text": "<command>\n", "settle_ms": 600}},   # in cmd.exe the newline is the Return
  {"tool": "focus_sheet",  "args": {"id": <your own id>}},
  {"tool": "get_sheets",   "args": {"settings": false}}])    # you are back
```
4. **Watch it.** `get_sheet_content(index=<target index>)` and `get_sheets` again: running = no prompt at the end of the text;
   finished = the prompt at the end. Quote the echoed command, its output, and say the console is back at its prompt.
5. **End a console you launched; never just close it.** A tab opened with `ai_terminal_open_here` keeps its shell alive in a
   separate GhostShell broker process, so closing the tab or quitting Sublime leaves an orphan the person must kill in Task Manager.
   Use `run_command` `ai_terminal_end_session` ("End Session (Kill + Close)") with `{"group": 0, "index": <tab index>}`, tabs from the
   highest index down, then `get_sheets` and `list_native_windows` to see the tabs gone and no dialog open (tested 2026-10-30: five
   tabs ended this way). A console that was already open before you started is not yours to end. Plain text tabs: `close_file`.

Tested 2026-10-30 on build 4215: in a `cmd.exe` tab `echo CR_TEST_1` and `ping -n 6 127.0.0.1 & echo DONE_2`; in launched tabs
(Dos Console `start chrome "https://www.google.com/search?q=..."`, PowerShell, Git Bash, WSL Bash) a command with a `sleep`; in an omp
tab a short message (text, then Return in the same batch), which it answered. Each: command and output in the tab, prompt back.

- **Guard the focus.** Sheet ids change when Sublime restarts (the cmd tab went from id 284 to 12), so call `get_sheets` in the
  same turn. If the first `get_sheets` in the batch does not show the target focused, the text went to your own tab. (Not
  `eval_python`: it asks the person on every call.)
- **`ok` is not proof.** Read the target tab back and quote the line before saying it was sent.
- **A line typed without a Return is not shown** in `get_sheet_content` right away (76 characters typed, text unchanged): one more
  reason to always send the Return.
- **Claude Code and other agent tabs** read a burst of text as a paste and take an Enter in the same read as part of it (text of 60
  characters or fewer still submitted; 120 or more stayed in the box, measured 2026-10-17). Type the text with no newline and a
  `settle_ms` of 400 or more, then `ui_press_key` (`key="Return"`, `method="post"`) in the same batch.
- **Escape: do not type a raw `\x1b`.** Use `ui_press_key` with `method="post"` (`Escape`, `Return`, arrows).
- `cls` in a cmd.exe tab clears the tab text that `get_sheet_content` returns, so read what you need first.
- A string typed before the shell has printed its prompt is dropped: confirm the prompt before typing.

## Packages, menus, palette and input panels (no eval_python needed)

Call these through `batch`; find more with `discover_tools`.

```
get_menu_items(caption="Command Palette")     # menu items with their command and args (filters: menu, caption, command)
run_command(command="show_overlay", args={"overlay": "command_palette", "text": "Install Package"})
get_command_palette(caption="Install")        # palette entries (filters: package, command, caption)
drive_input_panel(text="<name>", action="submit")   # fill and submit/cancel an open input panel
```

- `click_menu_item` runs an installed menu item by caption path, e.g.
  `path="Tools > Command Palette..."`; the end of the path is enough when it is unique. Most
  built-in items have no caption in the menu file, so use the command name: `Selection > select_all`.
  (Or find the item with `get_menu_items` and `run_command` its command and args.)
- `show_overlay` opens Goto Anything (`overlay="goto"`) or the command palette
  (`overlay="command_palette"`), with the same arguments as Sublime's own keymap. To move through an
  open completion popup use `move` (`by="lines"`, `forward=true` or `false`): Sublime has no separate
  next/previous command for it (tried on build 4215).
- `drive_input_panel` works on input panels (prompts such as "Packages to install
  (comma-separated)"). If several agents share the Sublime, call `claim_resource`
  with `resource="input_panel"` first.
- Quick panels a package opened with `show_quick_panel` (the Package Control
  pickers, any "pick one" list): `get_quick_panel` lists the items — `text` keeps
  the ones whose first line contains it, `limit`/`offset` page a big list, and
  `wait_ms` (up to 60000) waits for a list that loads slowly, e.g. 15000 for the
  Install Package list — and `pick_quick_panel` picks by `index` or by `text` (must
  match exactly one item) and runs the package's own callback; `index=-1` cancels.
  They see only panels opened by packages: the command palette and Goto Anything are
  Sublime's own and give an error.
- `context_menu` opens a native menu that blocks the main thread; see the next
  section.

### Input panels and prompt boxes

A prompt (`window.show_input_panel`: Goto Line, `new_file_at`'s name box,
`rename_file`, Package Control's "Packages to install (comma-separated)", a
package's own shell line) is not a tab — `get_open_files` never lists it, and
posted keys do not reach it.

- Open it (the `prompt_*` wrapper, `new_file_at` / `new_folder` / `rename_file`, or
  the package's own command) and confirm `get_active_panel` says `"input"`.
- **One call fills and submits:** `drive_input_panel(text="…", action="submit")`
  fires the panel's `on_done`; afterwards `get_active_panel` is `null`. `action="cancel"`
  fires `on_cancel`. It also reaches panels opened by a package in the legacy Python
  3.3 host.
- A panel left open by an earlier call makes the next submit land nowhere: the text
  appears in the box, the call answers `ok`, and the panel stays open. If
  `get_active_panel` says `"input"` and you did not just open it, run
  `hide_panel(cancel=true)` first and check for `null`.
- A package may re-open its prompt after every command (Glue 0.9.5): a blank box
  after a command that worked is the next prompt, not a failed submit — hide it with
  `hide_panel(cancel=true)` when you are done.

## Find in Files

Where scope, include and exclude patterns, and the option flags. `project_search` runs the same
engine and exposes none of them. It starts the search and returns at once;
`project_search_results(pattern=...)` reads what has been written and says `complete` when the
search has finished.

`where` takes the Where box's own syntax, or a list of paths and globs, which is joined with
commas. Left empty it searches the window's folders, and those folders are passed to the engine by
name rather than left for the editor to resolve: a project set in the same `batch` as the search
otherwise answered `0 matches` with `complete: true`, because the editor had not picked the project
up yet. A window with no folders gets an error saying to pass `where`, never an empty result.
`project_search_results` reports `returned`, `total` and `truncated`, and `truncated` is true only
when matches were actually dropped by `limit`. It reads the one shared results panel, so it checks
the panel's own header against the pattern and `regex` flag you pass: a read for a search that has
not started yet is refused with `panel_pattern` rather than answered with the previous search's
matches.

In order:              # one toggle per call, panel focused
find_all                                                          # runs it; panel closes
get_output_panel                                                  # reads find_results
```

**Where** is comma-separated entries; each one is a folder or a file pattern, never a pattern on a
path: `C:\proj\*.py` answers `ERROR: Unable to open file`. `*` matches any characters except `/`,
`?` exactly one; no character classes, no `**` (`sublimetext.com/docs/file_patterns.html`).

- no `/` in the entry: matched against the file or directory **name**: `*.md`
- `/` in the entry: matched against the **whole path**, and `*` then matches `/` as well
- trailing `/`: that directory and everything under it: `-docs/`
- leading `/`: absolute path; `//`: relative to the project root
- leading `-`: exclude: `-*.min.js`, `-*node_modules*`

**Flags.** `toggle_regex` (`.` becomes a wildcard, `^` `$` `|` work), `toggle_case_sensitive`,
`toggle_whole_word`, `toggle_preserve_case`, `toggle_show_context` (results gain the surrounding
lines, `..` marks the gaps), `toggle_in_selection` (Find panel only). A toggle answers `ok` and
changes nothing unless the panel is open with the caret in the Find box: batched with `find_all`, or
called after the panel closed, it is a no-op, and every count after it is wrong.

**The results header names the flags in force** — `Searching 5 files for "x" (regex, case sensitive,
whole word)`. Check it before trusting a count (2026-11-06): `get.quick.panel` gave 7 matches with
regex on, 0 off; `Get.quick.panel` 0 with case sensitive on, 7 off; `panel` with whole word gave 11
standalone hits instead of the ones inside `get_quick_panel`.

## Removing packages, making folders, saving to disk

Observed on build 4200 (2026-10-07).

- **Remove a package:** call `run_command(command="remove_package")`. Do not open
  the palette with the text "Remove Package": the palette ranks
  "Remove Channel" first, and its Return opens the channel list. The list that
  `remove_package` opens also contains `MCP Commander` and other packages, so
  type the package name to filter the list and check the highlighted entry before
  confirming. A list opened right after a removal is stale until the status bar
  says "Package X successfully removed".
- **Make a folder:** there is no tool that creates a folder at a path.
  `run_command(command="new_folder", args={"dirs": ["<parent>"]})` then
  `drive_input_panel(text="<name>", action="submit")` does it. `str_replace_based_edit_tool`
  `create` does not create missing folders.
- **Files reach the disk only after `save_file`** (or `save_all`); `create` alone leaves an
  unsaved tab.

## Deleting files and folders

- **Delete files and folders:** both ask the person first (see "Destructive tools ask the person
  first"). Pass `files` to `delete_file` and `dirs` (a list) to
  `delete_folder`; any other argument name, such as `path`, is dropped and the call still
  returns ok without deleting. Check the disk afterwards. As with the Side Bar menu, the
  confirmation is always shown, even with `prompt: false`. They open a Windows
  confirmation ("permanently delete" when the drive has no Recycle Bin) for every
  item, block the main thread until it is answered, and can stall at "99% complete".
  Use `list_native_windows`, then answer each dialog. The Windows file-operation progress window
  ("Preparing to recycle", "Discovered N items", title "N% complete", class `OperationStatusWindow`, kind
  `other`) is listed too, `ui_screenshot` with its `hwnd` shows it, and `dismiss_native_window` with
  `action="close"` (or `cancel`) asks Windows to cancel the operation (its title becomes "Canceling -
  0% complete"); tested on build 4215 with a 150,000-file folder. The "main-thread timeout" message names it
  as the blocker. A progress window that has already finished is no longer a window: the call then
  answers "not a visible window of this Sublime Text process".
- **Tabs of deleted files:** if files vanish while they are open (for example because a package
  folder was removed), closing each tab raises a "Save Deleted File?" dialog; answer No.

## Reading the console

- **Read the console:** `get_console` with the default mode, and `mode="captured"`, can miss
  Sublime's own output (load errors such as a plugin's SyntaxError, and anything printed by
  Python 3.3-host plugins). `mode="visible"` returns the whole console (the last 200 lines by
  default; `tail=N` for N lines, `tail=0` for all; the result says `lines_total` and
  `truncated`). It clicks into the console and copies it, so the window must be in front; if it
  is not, it fails at once with a clear message and changes nothing. Pass `force_focus=true` on
  every visible call to raise the window first. A read then takes about 150 ms (measured on
  Windows 11, 2026-10-19: 99 of 100 reads on portable 4215 and 92 of 100 on 4200 succeeded; the
  rest were focus refusals that sent no input; no wrong text). Do not fall back to opening the
  panel with `show_panel` and reading the screen.
- **When the raise is refused.** Windows lets a process take the foreground only if it received
  the last input event, started the foreground process, or the foreground lock timeout has
  expired. So the first raise on a freshly started Sublime usually fails, and a raise also fails
  while the user is typing or clicking in another window. The error says "could not give the
  Sublime Text window the keyboard focus; no input was sent": nothing was sent, so call again a
  moment later. Later raises on the same instance succeed because the click and keys of the
  previous capture count as input.
- **Crash history (do not repeat it as fact).** On 2026-10-04 a loop that killed and relaunched
  portable 4200 for each capture (12 per variant) crashed it 2 times in 12 with the raise used
  here (CoreMessaging.dll), and 5 to 8 times in 12 with variants that attach thread input; those
  logs were not kept. On 2026-10-19 about 1,000 raises on portables 4200 and 4215, long-running
  and freshly relaunched, gave no crash and no new dump file. The cause of the earlier crashes
  is unknown, and no crash of the user's main Sublime from `force_focus` has been recorded.
  The two dumps on hand (4200 on 2026-10-16, 4215 on 2026-10-18; read with `cdbX64.exe`, no
  symbols) are both access violations on a Sublime worker thread, every frame in
  `sublime_text.exe`: a read of address 0x8 (null object) on 4200 and a jump to a data address
  on 4215. No frame is in user32, the clipboard, Python or a plugin, and the dumps carry no
  mark of `get_console`, so nothing ties them to `force_focus`.
- **The console is only partly readable.** `get_console` in the default and `captured` modes
  misses Sublime's own error output (tracebacks printed after an install, `ImportError`).
  `get_output_panel` for the console is the same as `get_console` in the default mode, so it
  also misses those errors when the window is not in front. A visible capture that succeeds
  prints one "[sublime-commander] console capture marker" line into the console; one that fails for
  lack of focus leaves nothing behind.

## Silent failures and timeouts

- **`run_command` returns `{"ok": true}` even when the command does not exist** or the
  package that provides it did not load. Check for a visible effect.
- **A "main-thread timeout" says what it found.** On Windows the message now lists the native
  dialog, menu or window that is open ("A native window blocks Sublime's main thread ...:
  "Delete File" (dialog)"), or says that none is open and the main thread is busy, for example
  while a large package loads or installs, or right after the `exit` command. Answer a dialog with
  `dismiss_native_window`; for a busy thread call again in a few seconds. Off Windows the message
  can only say a dialog may be blocking. (Before this change every timeout blamed a dialog.)
  The tool may still have worked: a `create` or `save_file` that timed out while a package was
  installing had in fact gone through, so check the state before repeating it.
- **Unknown arguments used to be dropped silently.** `delete_file` with `path` returned ok and
  deleted nothing (it takes `files`), and `get_commands(query=...)` returned all commands
  (58 KB) because its filters are `package` and `command`. A result now carries a `warning`
  that names the argument and lists the valid ones, but a command that the tool only passes on
  to Sublime can still drop one, so check the result and the tool's schema in `discover_tools`.
- **Quick panels and tabs are per window, and commands open new windows.** `get_sheets` now lists
  every window (id, folders, tab count, which is active) and takes `window=<id>`; `get_quick_panel`
  and `pick_quick_panel` look in every window, not only the active one. Both matter because a
  command can leave its UI in — or create — a window other than the one you were reading:
  `open_folder`, `new_window`, and PackageDev's Create Package (which makes an empty package folder
  and opens a new window on it, correctly) all switch the active window, and until 2026-11-08 the
  tools then described the wrong window and reported "nothing happened" or "no recorded quick
  panel" while the picker was on screen.
- **A dialog a package opens lives in the plugin-host process, not in sublime_text.exe.** Until
  1.18.7 `list_native_windows` and `dismiss_native_window` walked only `sublime_text.exe`'s windows,
  so a dialog raised from Python — `sublime.ok_cancel_dialog`, or ColorHelper's OS colour picker
  through `ctypes` — was invisible: it could not be read, could not be dismissed, and a callback
  blocked inside it looked like a plain hang. Both now walk the plugin host too, so the picker shows
  as `dialog "Color"` with its buttons and answers to `dismiss_native_window`. Measured on 4215:
  before, five such dialogs sat unlisted in `plugin_host-3.14` while the tools reported none; after,
  the dialog was listed within 2 s, `dismiss_native_window` cancelled it and the package's worker
  thread returned. Dialogs raised by the *other* host (Python 3.3) are still not covered.
  **Dismiss an unread dialog with the default `cancel`.** `action: "ok"` clicks the first OK-like
  label, and "Yes" counts: on Emmet's telemetry prompt it meant "Yes, enable telemetry", and on a
  `Save Changes?` it meant "Yes" (2026-11-08). Read the button labels from `list_native_windows`
  first and name one with `action: "button"` when the choice matters.
- **Every tool result carries `native_dialogs` while one is open.** The reply gains `native_dialogs`
  (hwnd, title, buttons, messages) whenever a native dialog is open at the moment the call
  finishes — including the call that timed out because of it — so a dialog that appears while a
  step runs (the unregistered-copy reminder after a save, a package's error box, a chooser) does not
  wait for the person to point at it. Read it and answer it before the next step, with
  `dismiss_native_window`; never `action: "ok"` on labels you have not read.
- **A dialog's fields are windows of their own.** Every dialog now carries `controls`: each Edit,
  ComboBox, ListBox, list view and tree view under it, with `hwnd`, class, control id, parent class,
  text and rect. The File name box of a common Open/Save dialog is the Edit nested in the
  ComboBoxEx32 on that row (control id 1148 on build 4215; ids vary by dialog). Fill it with
  `ui_set_text(hwnd=<that Edit>, text="C:\\path\\file.png")`, which sets the value with WM_SETTEXT
  and returns it read back, then click the dialog's button with `dismiss_native_window`
  (`action: "button"`, `button: "Open"`). Measured 2026-11-09 on 4215: `ui_type_text` at the
  dialog's own hwnd reached no control, and with this pair Image Link Insertion's chooser inserted
  its link on the first try. A control that takes keystrokes can still be named directly in
  `ui_type_text`.
- **`get_view_regions` sees regions, not gutter icons.** It returns what a plugin stored with
  `view.add_regions(key, ...)`; a package that draws marks in the gutter through its own theme
  (GitGutter's changed/inserted/deleted lines) leaves nothing there. Measured 2026-11-09: with
  `one/two/three/four/five` committed and lines 2 and 5 changed, GitGutter marked both in the
  gutter and `get_view_regions` returned `[]` for `git_gutter`, `git_gutter_modified`,
  `git_gutter_inserted` and `git_gutter_deleted`. Use `ui_screenshot` for those marks, and look at
  the picture rather than inferring from an empty region list.
- **A file a package opened as a preview is an open tab too.** `open_file(path, TRANSIENT)` — Goto
  Anything, and packages such as Jekyll 4.0's edit-config — gives a view that is valid, active and
  holds the file's text, yet `window.views()` and `window.sheets()` do not list it. Until 1.18.6
  `get_sheets` therefore said nothing was open while the file was in front of you, and `close_file`
  by name answered ok without closing it. All of them see it now (`type: "PreviewSheet"`,
  `preview: true`) and close it; `close_file` by path always worked.
- **An untouched untitled buffer is listed too, as a placeholder.** A window's first tab is a view
  the window shows but `window.sheets()` and `window.views()` leave out, while
  `window.selected_sheets_in_group()` returns it — so `get_sheets` answered `sheets: []`
  with `selected_sheet_ids: [16]` and `active_sheet_id: 16`, and `get_open_files` answered
  `files: []`, with a tab plainly on screen. Both list it now with `placeholder: true`, and the
  described window's sheet count matches its list. Type one character and it becomes an ordinary
  sheet, which is how the two states were told apart (measured 2026-11-08, the same shape as the
  preview case above).
- **`run_command` hands its `args` straight to Sublime**, which raises for a keyword it does not
  know: `open_folder {"dir": ...}` gives `TypeError: OpenFolderCommand.run() got an unexpected
  keyword argument 'dir'. Did you mean 'dirs'?` in the console while the tool still answers `ok`
  (`dirs` takes a list). Check the command's own signature — `view_resource` takes no arguments at
  all — instead of guessing, and read the console after a command that should have had an effect.

## Installs, restarts and quick panels

- **Drive Package Control by command name, not through the command palette.** `run_command
  install_package`, `remove_package`, `enable_package`, `disable_package` and `list_packages` open
  the same pickers the palette entries do. The palette route is a trap: `show_overlay
  {"overlay": "command_palette", "text": "Package Control: Remove Package"}` followed by Return runs
  whatever entry is highlighted, which is not necessarily the one typed — measured once, it ran the
  channel remover, opened its list of channel URLs, and would have deleted a channel if an item had
  been picked. If you must use the palette, read `get_quick_panel` before picking and confirm the
  list is the one you asked for.
- **Language-server packages installed during a session** start their server only
  after Sublime restarts, and many need a separate syntax package and a Node or binary
  download, so the status can read "(installing...)" for minutes.
- **Installs can take minutes, and the status text does not tell you when they end.** Large
  packages (SublimeCodeIntel has hundreds of files) and packages with libraries (EasyClangComplete
  fetches seven, one by one) keep "Installing package ..." in the status bar until the very
  end. Watch the real state instead: the package folder or `.sublime-package`, its
  `package-metadata.json`, and `get_command_palette(package=...)`, which stays empty until the
  commands are registered. The package manager logs "Package X successfully installed" last.
- **After `run_command exit` and a new start,** three things happen. A package manager dialog
  "Sublime Text needs to be restarted for installed or updated libraries" can open (answer OK);
  an "Update Available" window can open and disable the main window (close it; its buttons are
  not accessible elements, use its Close button); and the sublime-commander server may or may not
  reconnect by itself (the first restart did, the second did not and needed `/mcp`). A key press
  sent right after a restart is refused until the window has been focused with a click on its
  title bar. Replacing a package between Python hosts (release on 3.3, master on 3.8) in the
  same session gives false "No module named" errors; restart Sublime first.
- **Quick panels:** several packages ask for a decision in a quick panel (FileManager's delete asks
  "Confirm - Send item to trash"; the package manager's pickers). `get_quick_panel` lists the items of
  the panel and `pick_quick_panel` picks one (by index or text) or cancels it with index -1.
  They see panels opened by packages in sublime-commander's own plugin host (Python 3.8, and 3.14 on
  builds 4213+). Panels from the Python 3.3 host are visible only when the user has set
  `"install_py33_helper": true` in `MCP Commander.sublime-settings` (off by default): sublime-commander
  then writes a small package, "MCP Commander Py33", into Packages with a `.python-version` file
  holding `3.3`, which is what puts it in that host. **Sublime loads a new package at startup**, so
  a helper written while Sublime runs answers nothing until it is restarted, and builds 4213+ ship
  with the 3.3 host itself off (`"disable_plugin_host_3.3": false` in Preferences turns it on).
  When nothing in the 3.3 host answers, the error says which of those two it is. Older packages
  (no `.python-version`) run wherever the build puts them, so their panels are recorded normally
  when the 3.3 host is off; the command palette and
  Goto Anything give an error, and then the keyboard is the only way. Picking runs the package's own callback, so pick only items you mean to run (some
  pickers open files, folders or browser tabs). If the callback raises a modal dialog (Jekyll's remove
  commands: "Confirm Delete"), `pick_quick_panel` returns at once with `started: true` and does not wait
  for the callback: the dialog appears in the next result's `native_dialogs`, and the callback's outcome in
  `get_quick_panel` (`last_pick`). Answer the dialog with `dismiss_native_window` (or Return on its hwnd),
  then check the result. A callback that had already run returns its real result; in the 3.3 host a missing
  or unloaded helper is "no recorded quick panel" instead. `drive_input_panel` only fills input panels.
  **The package manager's Install Package / Remove Package lists take up to ~15 s to appear after
  Enter** (the status bar says "Loading packages..."): pass `wait_ms` (at most 60000) to
  `pick_quick_panel` or `get_quick_panel`, for example `pick_quick_panel(text="Bicep",
  wait_ms=30000)`, and the call waits for the panel instead of failing with "no recorded quick
  panel". Without `wait_ms` that error carries a hint.
- **What a highlighting plugin drew:** `get_view_regions(key="ifdef")` returns the regions stored
  with `view.add_regions(key, ...)` (begin, end, first 80 characters); name several keys with
  commas. Sublime cannot list the keys, so read the plugin's source for them. Built-in example:
  after `toggle_bookmark`, key `bookmarks`.
- **A tab drawn with phantoms** (GhostShell's omp tab: the buffer is only blank lines, the content is
  in hundreds of phantoms): `get_view_phantoms(name="omp", html=false, last=20, max_chars=500)`
  returns the newest panels as plain text. Without `html=false` and `last` the answer is about
  290 KB. It works for any package that lists its `PhantomSet` in a module-level `_phantom_sets`
  dict (view id to set); GhostShell does since 2026-10-14.
- **Syntax names:** `get_active_file` and `get_sheets` give `syntax` (the name, or the file name
  when the syntax file has no `name:` line, as with Bicep) and `get_active_file` also gives
  `syntax_path`. A view whose syntax was set through a legacy path (`Packages/CSS/CSS.tmLanguage`,
  which old Python 3.3 packages use) has no `view.syntax()` in the API although Sublime shows it;
  both tools then report it from the view's `syntax` setting (`syntax: "CSS"`, `syntax_path` the
  legacy path) instead of `null`.
- **`focus_sheet` echo:** it returns the sheet without its view settings (they were about 7 KB on
  every call); pass `settings: true` to get them, as `get_sheets` does.
- **Scope names differ between Sublime builds.** In build 4200 the C syntax scopes `#ifdef` as
  `keyword.control.import`; in 4215 it is `keyword.control.directive.conditional`. A package that
  selects by scope can work on one build and do nothing on the other: check the scopes with
  `get_scope_at_cursor` on the build the user runs before calling it a defect.
- **PowerShell pipes add a byte-order mark.** `Get-Content file | tool -` feeds the tool a BOM and
  tools that read stdin may report a parse error; redirect the file instead (`tool - < file`)
  from Bash or cmd.
- **`exit`** replies first and closes Sublime 300 ms later, so the call returns `ok` and the
  connection then drops (restart, then reconnect the server).

## Destructive tools ask the person first

These calls do not run until the person says yes: `delete_file`, `delete_folder`, `revert`,
`revert_file`, `close_window`, `close_workspace`, `remove_folder`, `exit`, `eval_python`, `close_file`
with `discard`, and `run_command` of any of those commands. Inside a `batch`, one such call makes the
whole batch ask once, before any call of it runs.

- Your client shows an Accept / Decline question (Claude Code: in the terminal) and repeats the call
  for you. You see only the final result. Nothing is changed before the person accepts.
- A result starting **"Denied, nothing was changed"** means the person declined, or your client cannot be
  asked. Do not retry, rename an argument, or reach the same effect through another tool or `eval_python`.
  Tell the person what you wanted to do and why.
- Pick the right target before asking: the question names the target, and a vague name (`close_file name="test"`
  matches the first tab containing "test") can ask about the wrong tab.
- The setting `require_consent_for_destructive` turns this off (read at plugin start); it is on by default.
  The direct HTTP bridge cannot ask, so it refuses these calls outright (403, "Denied, nothing was
  changed"); `eval_python` stays open there.

## Tools with side effects

Every tool is a Sublime command passed straight through, so each does exactly what the command does in
the editor. Know these before calling a tool you have not used (checked on 1.14.3, build 4215):

- **They open a web page in the default browser:** `html_print` (the active tab as an HTML file), `open_in_browser`,
  `open_url`, `purchase_license`, `upgrade_license`. Close the browser window afterwards. `open_context_url`
  acts on a link under a right-click, so called alone it does nothing. `show_changelog`, `show_license_window`,
  `show_about_window`, `show_progress_window` and `update_check` open Sublime windows ("Changelog", "Enter License",
  "Sublime Text", "Indexing Status", "Update"); `dismiss_native_window` with `action="close"` closes them.
- **They quit Sublime:** `exit` and `hot_exit` (hot exit keeps unsaved buffers for the next start). `close_window` and `close_all` leave Sublime running with an empty window.
- **They change settings or create files:** `increase_font_size`, `decrease_font_size` (adds `font_size`),
  `ignore_word`, `add_word` (add `ignored_words`, `added_words`), `set_setting`, `open_file_settings`
  (creates an empty settings file in `User` and makes it the active tab, which the browser tools above then use).
- **They open a native dialog and block the main thread until it is closed:** the `prompt_*` tools
  (`prompt_open_file`, `prompt_open_folder`, `prompt_add_folder`, `prompt_save_as`, ...), `save`, `save_file`
  on an untitled buffer, `save_project_and_workspace_as`, `save_workspace_as`, `save_macro` (after a recorded
  macro), `primary_j_changed` ("Key Binding Changed"), `close_folder_list` ("Confirm Remove Folders": Remove or
  Cancel), `delete_file` and `delete_folder` with `prompt=true` (OK or Cancel), `remove_license` ("Remove license key?":
  Remove or Cancel; it removes the licence) and the `sublime_merge_*` tools when Sublime Merge is not installed
  ("Sublime Merge Not Found": Download or Cancel). The call returns "main-thread timeout after 5s"; `list_native_windows` shows the
  dialog and `dismiss_native_window` closes it. Open, Select Folder and Save As have Cancel, not OK: answer
  Cancel (`action="button", button="Cancel"`); OK on a dialog with no OK button fails and leaves the
  main thread blocked. `run_command` with `context_menu` opens a popup menu that blocks the same way.
- **Find and replace in files:** there is no tool for it; use `run_command` with Sublime's own commands. First `show_panel` with `{"panel": "find_in_files", "pattern": ..., "replace_pattern": ..., "where": ..., "regex": false, "case_sensitive": false, "whole_word": false, "preserve_case": false}` (the Replace box is filled by `replace_pattern`), then `replace_all`. Sublime asks "Confirm Replace": answer it with `dismiss_native_window` (`action="button"`, `button="Replace"` or `"Cancel"`). On Replace, the changes are made in the matching files' open buffers (the files open with unsaved changes); write them with `save_all`. For one file use `{"panel": "replace", ...}` with the same arguments and then `replace_all`. To search without the panel use `project_search`.
- **Tools that depend on state you must set first:** `focus_by_index` needs several tabs selected;
  `move_to_group` needs the target group to exist and the layout to have settled; `toggle_overwrite` changes how
  typed keys (`ui_type_text`) land, not `insert`; `toggle_save_all_on_build` decides whether `build` saves
  every modified file first; `next_modification`, `prev_modification`, `revert_hunk` and `revert_modification`
  need a saved file with unsaved edits; `close_deleted_files` closes a tab only after Sublime has noticed the
  file is gone.
- **They install packages:** sublime-commander has no tool for it, because installing is Package Control's job (and
  Package Control may not be installed). Open its picker with `run_command show_overlay`
  (`{"overlay": "command_palette", "text": "Package Control: Install Package"}`) and answer with
  `pick_quick_panel` (`wait_ms` for the list that is still loading). The libraries a package depends on come
  from `satisfy_libraries`. A package loads the moment it is installed, so to install one that needs libraries
  (its libraries are named in its install message): add the package to `ignored_packages`, install it
  through the picker, run `satisfy_libraries`, then remove it from `ignored_packages`.
- **They ask a question in an overlay or picker, and wait for the answer:** `rename_file`, `rename_path`,
  `new_file_at`, `new_folder`, `view_resource`, `show_overlay`, `prompt_goto_line`, `select_color_scheme`,
  `select_theme`, `set_file_type`, `set_build_system`, `paste_from_history`, `build` (when the build system has
  variants, such as Python), `open_recent_*` (they take `index`, 0 being the most recent),
  `goto_symbol_in_project`, `prompt_select_workspace`. Answer with `ui_type_text` and `ui_press_key`
  (`Return` to accept, `Escape` to cancel, `Down` to move), then check the result. A picker opened by a plugin
  can also be read with `get_quick_panel` and answered with `pick_quick_panel`. `rename_file` pre-selects the
  base name, so typing replaces only that part. `edit_settings` opens its two views in a new window;
  `new_file_at` opens an unsaved buffer for the new name.
- **Pickers and the Find panel are drawn by Sublime, not Windows:** `list_native_windows` does not list them;
  `ui_screenshot` shows them. Look at the screen before you restart, kill or close anything, and answer what
  is waiting first.
- **Before closing several tabs:** call `close_file` once per tab with its `name`, or use the `close_all`
  command; do not call `Sheet.close()` repeatedly in one `eval_python` call.
- **"This is an unregistered copy" dialog:** Sublime shows this purchase reminder now and then, for example
  after a save. Read it, then close it with `dismiss_native_window`.
- **`goto_definition`, `goto_reference`, `auto_complete_goto_definition`** use Sublime's symbol index, which
  needs `index_files` true. `lookup_symbol` searches the open files.
- **Macros:** play a `.sublime-macro` file with `run_macro_file` (file="Packages/User/name.sublime-macro").
  `toggle_record_macro` records keys typed by a person.
- `ui_click`, `ui_hover` and `ui_press_key` with `method="input"` need the target window uncovered and the
  person at the keyboard idle for `min_idle_s` (default 8); pass `wait_idle_s` (up to 120) to wait, or a
  smaller `min_idle_s`. `ui_press_key` with the default `post` method needs neither.

## When a native dialog blocks Sublime (Linux, macOS, WSL)

`list_native_windows` and `dismiss_native_window` are Windows only, so off Windows a dialog shows up as
"main-thread timeout after 5s" (the message says so) and only the person, or a computer-use client, can answer it.
Under WSL (WSLg) a computer-use client sees each dialog as its own window titled " (Ubuntu)": `list_apps`,
`get_window_state` with an image snapshot shows the message (read it, it is often the finding), then `click` at the
button's position in the picture. Tools that do not need the main thread (`get_console`, `get_help`) keep
answering. Seen on the WSL Sublime 4215: Save Changes, Unable to save, Error loading syntax file, and a package's
own "cannot find perltidy" message. Do not repeat a call that raised a dialog before you have answered it.

## When a native dialog blocks Sublime (Windows)

If a tool call fails with "main-thread timeout after 5s", or a command just
opened a native dialog or menu, Sublime's main thread is blocked and almost
every tool will time out. Two tools still work, because they never use the main
thread:

```
list_native_windows()                     # dialogs/menus with buttons + message text + controls,
                                          # main_thread_blocked, blocked_by (the tool)
dismiss_native_window()                   # default action "cancel": Cancel/No, else close
dismiss_native_window(action="ok")        # OK / Yes / the default button (this CONFIRMS)
dismiss_native_window(action="button", button="Remove")   # a named button
dismiss_native_window(hwnd=..., action="close")           # a specific window
ui_set_text(hwnd=<Edit from controls>, text="C:\\path\\file.png")   # fill a dialog's field
```

The default action is `cancel`: on the `delete_file` confirmation it clicks
**No**, on `remove_license` it clicks **Cancel**. `action="ok"` clicks OK / Yes /
the default button, which confirms the action (on `delete_file` the file is
deleted; on `remove_license` the license is removed). The tools act only on windows of the Sublime Text process, and they are Windows
only (they use Win32). Verified on all 16 blocking commands with
`tools/verify_native_dialogs.py`: each froze Sublime, was listed and dismissed
by these tools, and Sublime answered again.

**Looking at and driving Sublime's own windows (Windows only).** `ui_screenshot`,
`ui_press_key`, `ui_type_text`, `ui_click` and `ui_hover` work on the windows of the Sublime Text
process only, and need no OS permission prompt, so they also work from a remote session.
`ui_screenshot` takes a picture of one window (it works for a window behind others, and for dialogs) and
returns the image itself, first in the reply, also through `batch`. Choose the window with `window_title`
(part of its title), `kind` (`dialog` or `menu`, for an open native dialog or menu, which a plain screenshot
does not show; the reply lists them as `open_popups_not_in_picture`) or `hwnd`; `tab` shows a tab that is not in front for the picture and puts the front
tab back; `region` crops, `scale` zooms (2 doubles the size) and `max_width` shrinks; `save_dir` also keeps
the PNG and reports `saved_path`; `inline=false` returns only a file path, for a client that cannot show
images.
`ui_press_key(key="Return")` and `ui_type_text(text="cel")` post the key or characters to the window
without moving focus or the pointer, for example to pick an entry in the command palette or a quick
panel: open the palette with `run_command show_overlay`, then Return, type the filter, Return. Input
is handled asynchronously, so each call waits `settle_ms` (default 150 ms, up to 5000) afterwards, and
`ui_screenshot` waits 200 ms first.
`ui_screenshot` will not hang the editor: it asks the window for a `WM_NULL` first (1500 ms) and refuses
an unresponsive window with an explanation, and the render itself is bounded at 2.5 s — if it overruns,
the picture is copied off the desktop instead (`fallback: "screen"`, and anything covering the window is
in it). Before this, a busy UI thread made the call wait inside `PrintWindow` and the editor looked hung.

A popup that its own trigger opened closes between calls, so a screenshot in a later call shows
nothing (or a stale frame from a background window). Put the trigger and the picture in **one**
batch: `ui_type_text(text="io", settle_ms=600)` → `run_command auto_complete {"api_completions_only":
false}` → `ui_screenshot(settle_ms=300)`. Text added with `insert` never opens the completion popup;
the prefix has to be typed with `ui_type_text`.

Sublime draws its own editor, palette and popups, so it ignores posted mouse messages and posted
keys carry no Ctrl/Shift/Alt state (a posted Ctrl+Shift+P arrives as a plain "p"). For those cases
the tools use the REAL mouse and keyboard, which would disturb the person using the computer, so
they are gated: `ui_click(x, y)` (x, y are pixels in the `ui_screenshot` picture), `ui_hover(x, y,
screenshot=true)` and `ui_press_key(..., method="input")` are refused unless the person has been idle
for `min_idle_s` seconds (default 8) and the target window is the one under the point at that moment;
the pointer is put back afterwards. A refusal says how long the person has been idle; wait and try
again, pass `wait_idle_s` (up to 120) to wait for them to stop typing instead of giving up, or use keys,
`pick_quick_panel` and editor commands instead. Native popups (an open menu, the `#32768` windows in
`list_native_windows`) are windows of the process too: pass the menu's own `hwnd` to `ui_screenshot`,
`ui_hover` and `ui_click` (x, y count from the menu's top-left corner) to read and click it; a click
on the editor window's coordinates is refused while the menu is in front of that point. `method="input"` also needs the
window in front, and activates it with a real click on its title bar (same gate). Never inject real
input while the person may be using the computer, and never use `SendMessage` from a plugin to a
Sublime window: it waits for the UI thread and can deadlock Sublime (the tools only use `PostMessage`).
The default window is the first editor window of the Sublime process, which on a person's own Sublime
may be the window that hosts your session; pass `hwnd` of the window you mean.

**A dialog that appears after `run_command` has returned.** `ok` from `run_command` only
means the command was dispatched. A command that shows its dialog from a timer, a worker
thread or `sublime.error_message` does so a moment later, so a `list_native_windows` in the
same `batch` can come back without it (seen with several packages'
error dialogs). Pass `settle_ms` (for example 300): `run_command` then waits up to that long
and returns every dialog that was not open before the command as `dialogs`, with the same
fields as `list_native_windows`. Without `settle_ms` nothing changes. When `get_console`
fails for lack of focus while a dialog is open, the error now names the dialog.

**Task dialogs.** The message of a Windows task dialog (one whose buttons have custom text, such as
"Install <package>" / "Cancel") is read through UI Automation when the dialog has no ordinary
static text, so `messages` carries it (tested on build 4215 with a dialog from a Python plugin:
`["dlgtest: choose Install or Cancel"]`). Before this, `messages` came back empty for these dialogs
and only a computer-use client could read them. If `messages` is still empty, take a
`ui_screenshot` of the dialog's `hwnd`. `dismiss_native_window` with `action="button"` and the
button's text clicks it; a message box can take a second or two to close, so list the windows
again before assuming it did not. The first click on a dialog that is not yet active (Package Control's
restart message right after Sublime starts) can be dropped; `dismiss_native_window` then clicks once more
and says `retried: true` in its result.

**Closing a tab that has no path.** `close_file(name="...")` (partial, case-insensitive) or
`close_file(index=N)` closes that tab (a name that fits several tabs is refused, with the list);
with none of `path`, `name`, `index` it refuses and lists the open tabs (it no longer closes the active tab). `run_command` with `command="close"` and `scope="view"` returns ok and closes
nothing.

## More

The 160 tools generated from Sublime's command list, what each was observed to do, and
known issues are in `docs/COMMAND_TOOLS.md` in the repository.

