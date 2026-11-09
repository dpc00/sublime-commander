---
name: screenshot-routing
description: Take a screenshot of the Sublime Text instance that hosts this MCP server, detect pickers and dialogs a package leaves open, and diagnose "no window" errors. Covers sublime-commander's own tools only.
---

# Screenshots, prompts and window state (sublime-commander tools)

Scope: the Sublime that hosts this MCP server, reached through sublime-commander's own tools. Capturing any
other process is not sublime-commander's job and is not covered here.

## Which call to use

| what you want | call |
|---|---|
| the editor window, or part of it | `ui_screenshot` |
| a dialog, menu or popup | `ui_screenshot` with `kind` (`dialog`, `menu`) |
| the truth about a native window (title, buttons, message text) | `list_native_windows` |
| text state — sheets, selection, file contents, syntax | `get_sheets`, `get_selection`, `get_active_file` |

`ui_screenshot`:

- select with `window_title` (substring), `hwnd`, or `kind`;
- always pass `max_width` (900 reads a popup fine) and `region` when only part matters;
- `inline=false` when you only need the file rather than the image;
- it does not wait on a stuck UI thread: `the window is not answering` means the window failed a
  WM_NULL check and was not asked to render — wait for Sublime to be idle and retry;
- a `fallback: "screen"` in the result means `PrintWindow` missed its 2.5 s deadline and the picture was
  copied off the desktop, so anything covering the window is in it.

## A prompt on screen means the work is not done

A picker or dialog left up means the package is waiting for an answer; treat the step as unfinished.

- ST4 input-handler pickers are invisible to `window.views()`, `active_view()`, the UIA tree and
  `list_native_windows` — only a screenshot shows them.
- Native modals do appear in `list_native_windows`, with their text and buttons, and it works while
  the main thread is blocked.
- Answer a modal with `dismiss_native_window {"hwnd":…, "action":"button", "button":"Yes"}`. It needs
  no focus and works while Sublime is blocked; an AX `press()` on the same button silently does nothing.

## Empty window list = wrong process, not a broken tool

`{"error": "no window ...", "windows": []}` means the client is talking to a windowless Sublime
process, typically a leftover from before a restart.

1. The bridge port must show exactly one listening PID.
2. A windowless `sublime_text.exe` with a large working set is a zombie: kill it and its `plugin_host` child.
3. Re-run the same call; it works with no other change.

## Look at pixels only when the state is graphical

Pickers, popups, dialogs, layout, colour: a screenshot. Tab lists, selection, file contents, window
titles: the text tools. Taking a picture of something a text tool already answers wastes a round trip
and invites wrong conclusions from a stale frame.
