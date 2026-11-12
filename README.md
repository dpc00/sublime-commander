# sublime-commander

MCP server for Sublime Text 4 — lets AI agents read and control a running editor.

[![Support on Patreon](https://img.shields.io/badge/Support-Patreon-orange)](https://www.patreon.com/dpchitester)

## What it is

sublime-commander is a Sublime Text plugin that speaks the [Model Context Protocol](https://modelcontextprotocol.io). An agent connects to it over HTTP and works with the editor you already have open: it reads files, edits text, runs commands, and — on Windows — sees the screen and answers dialogs.

It runs inside Sublime's own plugin host, so there is no automation layer in between and no helper process to keep alive. Everything an agent does goes through Sublime's API, which means it sees the same tabs, selections, panels and menus you do.

## Table of contents

- [Install](#install)
- [Usage](#usage)
- [Configuration](#configuration)
- [Security](#security)
- [Requirements](#requirements)
- [Maintainers](#maintainers)
- [Contributing](#contributing)
- [License](#license)

## Install

### 1. Install the plugin

The repository root *is* the Sublime package. Clone it and link it into Sublime's `Packages` directory as `sublime-commander`, then restart Sublime so the plugin loads.

```cmd
:: Windows
mklink /J "%APPDATA%\Sublime Text\Packages\sublime-commander" "C:\path\to\sublime-commander"
```

```bash
# macOS
ln -s "$(pwd)" "$HOME/Library/Application Support/Sublime Text/Packages/sublime-commander"

# Linux
ln -s "$(pwd)" "$HOME/.config/sublime-text/Packages/sublime-commander"
```

The server starts with Sublime. `MCP Commander: Server Status` in the Command Palette starts, stops and reports it.

### 2. Point your agent at it

```json
{ "mcpServers": { "sublime-commander": { "type": "http", "url": "http://127.0.0.1:9502/mcp" } } }
```

On macOS and Linux the port is `9503`. Clients that predate streamable HTTP can use `"type": "sse"` with `http://127.0.0.1:9502/sse`.

### 3. Check the connection

`MCP Commander: Connection Doctor` in the Command Palette reports the HTTP bridge, the MCP handshake and the tool catalog.

## Usage

A connected agent gets eight tools immediately — `get_help`, `discover_tools`, `batch`, `get_active_file`, `project_search`, `save_file`, `str_replace_based_edit_tool` and `ui_screenshot` — and finds everything else through `discover_tools`. That catalog covers editing and navigation, tabs and windows, Sublime commands by id, project state, quick panels and menus, the console, and the regions and phantoms a package drew. `batch` runs several of them in one request.

```text
discover_tools(query="screenshot")
batch(calls=[{tool: "get_sheets", args: {}}, {tool: "get_console", args: {lines: 20}}])
```

If you are writing the agent side, read [AGENT_GUIDE.md](AGENT_GUIDE.md) first: it is the order the tools should be used in, including the traps. The same guidance ships as a skill in `skills/sublime-commander`; [docs/PACKAGE_SKILLS.md](docs/PACKAGE_SKILLS.md) turns a one-off investigation of any other Sublime package — a debugger, a language server — into a small reusable skill instead of another MCP server.

## Configuration

Settings live in `MCP Commander.sublime-settings` (Preferences › Package Settings › MCP Commander).

| what | Windows | macOS / Linux | key |
|---|---|---|---|
| MCP streamable HTTP `/mcp` and legacy SSE `/sse` | 9502 | 9503 | `mcp_port` |
| HTTP bridge (REST routes) | 9500 | 9501 | `http_port` |

## Security

Both servers listen on **`127.0.0.1` and do not authenticate by default**. One tool, `eval_python`, runs arbitrary code in Sublime's process, so an agent connected here can do anything you can do with that editor. Treat the connection as you would your own login session.

These settings change that posture:

- **`auth_token`** — require `Authorization: Bearer <token>` on every request. This is the only control that helps against another process, or another user, on the same machine. Use a long random value and give the same value to every client.
- **`allow_lan_access`** — bind `0.0.0.0` so other devices can connect. Still unauthenticated unless `auth_token` is set. Use it only for a specific client that cannot reach `127.0.0.1`, such as WSL without localhost forwarding.
- **`disabled_tools`** — refuse and hide named tools, for example `["eval_python", "run_command"]`.

Browsers are refused on the default configuration: the tool endpoints send no `Access-Control-Allow-Origin`, and with no token set they reject any request whose `Origin` or `Host` names something other than loopback. Command-line and desktop clients send no `Origin` and are unaffected. None of this stops a process already running as you; `auth_token` is the answer to that.

## Requirements

- Sublime Text 4 (developed against build 4215). Sublime Text 3 is not supported.
- Windows, macOS or Linux. The `ui_*` and native-dialog tools are **Windows only** and are hidden elsewhere.
- Python 3.8 or newer in Sublime's plugin host. Panels opened by older Python 3.3 packages are reachable with `"install_py33_helper": true` (off by default).

## Maintainers

[Donald Chitester](https://github.com/dpc00).

## Contributing

Issues and pull requests are welcome at [dpc00/sublime-commander](https://github.com/dpc00/sublime-commander/issues). For a bug, the useful report is the tool call, what you expected, and what came back — plus the relevant lines from `View > Show Console`.

Changes are recorded in [CHANGELOG.md](CHANGELOG.md) with the reason and how the fix was verified.

## License

MIT © Donald Chitester. See [LICENSE](LICENSE).
