"""Live check of get_quick_panel / pick_quick_panel against a running Sublime Text.

Covers both recorders: the one sublime-mcp installs in its own plugin host, and the helper a package
in the Python 3.3 host runs (py33/mcp_commander_py33.py, installed when "install_py33_helper" is
true). For each case it opens a real panel, lists it, picks or cancels it, and reads back the index
the panel's own callback received.

The 3.3 cases are skipped, with the reason, when no Python 3.3 host is running (builds 4213+ ship
with it disabled) or the helper package is not in Packages.

    python tools/verify_quick_panels.py --port 9510
    python tools/verify_quick_panels.py --port 9510 --keep   # leave the probe package behind

Use a disposable instance: it writes a package "Py33 Panel Probe" into Packages and, for the pending
case, opens the native file dialog in it. The package is removed at the end unless --keep is given.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

PROBE_PACKAGE = "Py33 Panel Probe"
PROBE_MARKER = "3.3\n"
PICKS_NAME = "quick_panel_probe_picks.txt"
HELPER_PACKAGE = "MCP Commander Py33"

PROBE_SOURCE = '''import sublime
import sublime_plugin

PICKS = sublime.cache_path() + "/%s"


def _record(what, value):
    try:
        with open(PICKS, "a") as f:
            f.write(what + ":" + str(value) + "\\n")
    except Exception:
        pass


class ProbeOpenPanelCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.window.show_quick_panel(["alpha-one", "alpha-two", "alpha-three"], self.done)

    def done(self, index):
        _record("plain", index)


class ProbeNestedDialogCommand(sublime_plugin.WindowCommand):
    """A pick whose callback raises a native dialog: the pick has to answer pending."""

    def run(self):
        self.window.show_quick_panel(["nested-one", "nested-two"], self.done)

    def done(self, index):
        _record("nested", index)
        if index >= 0:
            self.window.run_command("prompt_open_file", {"initial_directory": "C:/Windows"})
''' % PICKS_NAME


def post(port, route, body=None, timeout=15):
    """One JSON bridge call. A failing handler answers {"error": ...} with HTTP 500."""
    req = urllib.request.Request(
        "http://127.0.0.1:%d/%s" % (port, route.lstrip("/")),
        data=json.dumps(body or {}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        return json.load(urllib.request.urlopen(req, timeout=timeout))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {"error": "HTTP %d" % e.code}
    except Exception as e:
        return {"error": "%s: %s" % (type(e).__name__, e)}


def eval_py(port, code, timeout=15):
    r = post(port, "eval_python", {"code": code}, timeout)
    if not r.get("ok", True):
        raise RuntimeError(r.get("error"))
    return r.get("output", "")


def instance_info(port):
    """paths and versions of the instance the bridge belongs to."""
    out = eval_py(port, "import sys, sublime\n"
                        "S = sys.modules['MCP Commander.sublime_mcp']\n"
                        "cur = sublime.Window.show_quick_panel\n"
                        "print(sublime.packages_path())\nprint(sublime.cache_path())\n"
                        "print(S.__version__)\n"
                        "print(sys.version.split()[0])\n"
                        "print(hasattr(cur, '_sublime_mcp_orig'), hasattr(cur, '_mcp_py33_orig'))\n")
    packages, cache, version, host, wrappers = out.strip().splitlines()[-5:]
    own, helper = wrappers.split()
    return {"packages": packages, "cache": cache, "version": version, "host": host,
            "own_recorder": own == "True", "helper_wrapper": helper == "True"}


def host_3_3_running():
    """Whether a plugin_host-3.3 process exists. A hint (the name is shared by every instance)."""
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "(Get-Process plugin_host-3.3 -ErrorAction SilentlyContinue | Measure-Object).Count"],
        capture_output=True, text=True).stdout.strip()
    return out.isdigit() and int(out) > 0


def wait_for(predicate, timeout=5.0, interval=0.1):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return False


class Probe:
    def __init__(self, port):
        self.port = port
        self.results = []

    def check(self, name, ok, detail):
        self.results.append({"check": name, "ok": bool(ok), "detail": detail})
        print("%s %s -- %s" % ("PASS" if ok else "FAIL", name, detail))
        return ok

    def skip(self, name, why):
        self.results.append({"check": name, "ok": None, "detail": why})
        print("SKIP %s -- %s" % (name, why))


def read_picks(cache, kind):
    """The indexes the probe package's callbacks recorded, for one panel kind."""
    path = os.path.join(cache, PICKS_NAME)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [line.strip().split(":", 1)[1] for line in f if line.startswith(kind + ":")]


def open_until_recorded(port, command, attempts=25):
    """Run command and wait until its panel is recorded (a command can be dispatched a moment later)."""
    post(port, "run_command", {"command": command})
    for _ in range(attempts):
        listed = post(port, "get_quick_panel", {"limit": 5})
        if "items" in listed:
            return listed
        time.sleep(0.1)
    return listed


def run_own_host(p, cache):
    """Panels opened in sublime-mcp's own plugin host: eval_python runs there."""
    code = ("import sublime\n"
            "p = r'%s'\n"
            "def cb(i):\n"
            "    open(p, 'a').write('own:%%s\\n' %% i)\n"
            "sublime.active_window().show_quick_panel(['own-one', 'own-two'], cb)\n"
            "print('opened')\n") % os.path.join(cache, PICKS_NAME).replace("\\", "/")

    eval_py(p.port, code)
    listed = post(p.port, "get_quick_panel", {"text": "own-t"})
    p.check("own host: text filter", listed.get("items") == ["own-two"],
            "text 'own-t' returned %r" % (listed.get("items"),))

    picked = post(p.port, "pick_quick_panel", {"text": "own-one"})
    seen = wait_for(lambda: "0" in read_picks(cache, "own"))
    p.check("own host: pick by text", picked.get("picked") == 0 and seen,
            "answer %r, callback saw %r" % (picked, read_picks(cache, "own")))

    after = post(p.port, "get_quick_panel", {})
    p.check("own host: record cleared", "error" in after, "%r" % (after.get("error") or after,))

    eval_py(p.port, code)
    cancelled = post(p.port, "pick_quick_panel", {"index": -1})
    seen = wait_for(lambda: "-1" in read_picks(cache, "own"))
    p.check("own host: cancel", cancelled.get("picked") == -1 and seen,
            "answer %r, callback saw %r" % (cancelled, read_picks(cache, "own")))


def run_3_3_host(p, cache, info):
    if not os.path.isdir(os.path.join(info["packages"], HELPER_PACKAGE)):
        p.skip("3.3 host: list/pick/cancel",
               "no %r package in Packages: install_py33_helper is off, or the package could not be "
               "written (the Sublime console says why)" % HELPER_PACKAGE)
        return False
    if not host_3_3_running():
        p.skip("3.3 host: list/pick/cancel",
               "no plugin_host-3.3 process: builds 4213+ disable it unless "
               "\"disable_plugin_host_3.3\": false, and a package written while Sublime runs only "
               "loads at the next start")
        return False
    if info["helper_wrapper"]:
        p.check("3.3 host: helper stays out of this host", False,
                "show_quick_panel in the bridge host carries the helper's wrapper: it would hide "
                "sublime-mcp's own recorder, so unhooking that one would silently stop working")
        return False
    p.check("3.3 host: helper stays out of this host", True,
            "bridge host %s has sublime-mcp's wrapper only" % info["host"])

    listed = open_until_recorded(p.port, "probe_open_panel")
    p.check("3.3 host: list", listed.get("items") == ["alpha-one", "alpha-two", "alpha-three"],
            "listing %r" % (listed.get("items") or listed,))

    picked = post(p.port, "pick_quick_panel", {"text": "alpha-three"})
    seen = wait_for(lambda: "2" in read_picks(cache, "plain"))
    p.check("3.3 host: pick by text", picked.get("picked") == 2 and seen,
            "answer %r, callback saw %r" % (picked, read_picks(cache, "plain")))

    open_until_recorded(p.port, "probe_open_panel")
    cancelled = post(p.port, "pick_quick_panel", {"index": -1})
    seen = wait_for(lambda: "-1" in read_picks(cache, "plain"))
    p.check("3.3 host: cancel", cancelled.get("picked") == -1 and seen,
            "answer %r, callback saw %r" % (cancelled, read_picks(cache, "plain")))
    return True


def run_pending_case(p, cache):
    """A pick whose callback opens a native dialog: pending, then the dialog is read and closed."""
    listed = open_until_recorded(p.port, "probe_nested_dialog")
    if "items" not in listed:
        p.check("pending: nested panel", False, "not recorded: %r" % (listed,))
        return
    answer = post(p.port, "pick_quick_panel", {"index": 1}, timeout=20)
    p.check("pending: answer says pending", answer.get("pending") is True, "%r" % (answer,))

    windows = post(p.port, "list_native_windows", {}, timeout=10)
    dialogs = [w for w in windows.get("windows", []) if w.get("kind") == "dialog"]
    p.check("pending: dialog listed", bool(dialogs),
            "%r" % ([{"title": w.get("title"), "messages": (w.get("messages") or [])[:1]}
                     for w in dialogs],))
    if not dialogs:
        return
    closed = post(p.port, "dismiss_native_window", {"action": "cancel"}, timeout=10)
    p.check("pending: dialog dismissed", closed.get("closed") is True, "%r" % (closed,))
    wait_for(lambda: "1" in read_picks(cache, "nested"), timeout=8)


def run_setting_listener(p, info):
    """Turning install_py33_helper off must stop the bridge at once, with no reload."""
    settings_file = os.path.join(info["packages"], "User", "MCP Commander.sublime-settings")
    with open(settings_file, encoding="utf-8") as f:
        original = f.read()
    if '"install_py33_helper": true' not in original:
        p.skip("settings listener", "install_py33_helper is not true in %s" % settings_file)
        return
    flag = "import sys; S = sys.modules['MCP Commander.sublime_mcp']; print(S._PY33_HELPER_ENABLED)\n"

    def enabled():
        return "True" in eval_py(p.port, flag)

    try:
        with open(settings_file, "w", encoding="utf-8", newline="") as f:
            f.write(original.replace('"install_py33_helper": true', '"install_py33_helper": false'))
        off = wait_for(lambda: not enabled(), timeout=5)
        p.check("settings listener: off", off,
                "install_py33_helper false was %s" % ("noticed" if off else "ignored"))
    finally:
        with open(settings_file, "w", encoding="utf-8", newline="") as f:
            f.write(original)
    on = wait_for(enabled, timeout=5)
    p.check("settings listener: back on", on,
            "install_py33_helper true was %s" % ("noticed" if on else "ignored"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9510, help="the JSON bridge port (http_port)")
    ap.add_argument("--keep", action="store_true", help="leave the probe package in Packages")
    args = ap.parse_args()

    try:
        info = instance_info(args.port)
    except Exception as e:
        print("cannot reach the bridge on port %d: %s" % (args.port, e))
        return 2
    print("sublime-mcp %s in the Python %s host; packages %s"
          % (info["version"], info["host"], info["packages"]))

    probe = Probe(args.port)
    picks = os.path.join(info["cache"], PICKS_NAME)
    if os.path.exists(picks):
        os.remove(picks)
    folder = os.path.join(info["packages"], PROBE_PACKAGE)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, ".python-version"), "w", newline="\n") as f:
        f.write(PROBE_MARKER)  # these panels have to come from a package that really runs in 3.3
    with open(os.path.join(folder, "probe_panel.py"), "w", encoding="utf-8", newline="\n") as f:
        f.write(PROBE_SOURCE)
    try:
        run_own_host(probe, info["cache"])
        if run_3_3_host(probe, info["cache"], info):
            run_pending_case(probe, info["cache"])
        else:
            probe.skip("pending: answer says pending", "no Python 3.3 host (see above)")
        run_setting_listener(probe, info)
    finally:
        if not args.keep:
            shutil.rmtree(folder, ignore_errors=True)
        if os.path.exists(picks):
            os.remove(picks)

    failed = [r for r in probe.results if r["ok"] is False]
    print("\n%d checks: %d passed, %d failed, %d skipped"
          % (len(probe.results), sum(1 for r in probe.results if r["ok"]), len(failed),
             sum(1 for r in probe.results if r["ok"] is None)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
