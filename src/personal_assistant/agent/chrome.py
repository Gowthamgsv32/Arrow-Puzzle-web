"""Controls Google Chrome through the Chrome DevTools Protocol (CDP).

Chrome only allows remote debugging on a non-default profile, so the assistant runs
Chrome with its own profile folder. Sign in to your accounts there once; it persists.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from personal_assistant.paths import user_data_dir

# Never send localhost DevTools traffic through a system HTTP proxy.
_NO_PROXY = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class ChromeError(Exception):
    pass


_SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:(?!\d)")


def normalize_url(url: str) -> str:
    """'github.com' -> 'https://github.com'; 'localhost:3000' -> 'http://localhost:3000';
    URLs that already have a scheme (https:, data:, chrome:, file:) are left alone."""
    url = url.strip()
    if _SCHEME.match(url):
        return url
    if url.startswith(("localhost", "127.0.0.1")):
        return "http://" + url
    return "https://" + url


def find_chrome() -> str | None:
    if os.getenv("PA_CHROME_PATH"):
        return os.environ["PA_CHROME_PATH"]
    candidates: list[str | Path] = []
    if sys.platform == "win32":
        for base in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
            if os.getenv(base):
                candidates.append(Path(os.environ[base]) / "Google/Chrome/Application/chrome.exe")
    elif sys.platform == "darwin":
        candidates.append("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    else:
        for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
            if found := shutil.which(name):
                candidates.append(found)
    return next((str(c) for c in candidates if Path(c).exists()), None)


class Chrome:
    def __init__(self, port: int = 9222, chrome_path: str | None = None,
                 profile_dir: Path | None = None, headless: bool = False):
        self.port = port
        self.chrome_path = chrome_path
        self.profile_dir = profile_dir or (user_data_dir() / "chrome-profile")
        self.headless = headless
        self._msg_id = 0
        self._last_tab: str | None = None  # last tab the assistant opened or switched to

    # ---- lifecycle ---------------------------------------------------------------------
    def is_running(self) -> bool:
        try:
            self._http("/json/version")
            return True
        except ChromeError:
            return False

    def ensure_running(self) -> None:
        if self.is_running():
            return
        exe = self.chrome_path or find_chrome()
        if not exe:
            raise ChromeError("Google Chrome was not found. Set PA_CHROME_PATH in .env.")
        args = [
            exe,
            f"--remote-debugging-port={self.port}",
            f"--user-data-dir={self.profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
        ]
        if self.headless:
            args += ["--headless=new", "--no-sandbox"]
        flags = 0
        if sys.platform == "win32":
            flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
        subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=flags, start_new_session=sys.platform != "win32")
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if self.is_running():
                return
            time.sleep(0.3)
        raise ChromeError(f"Chrome did not open its debugging port {self.port}.")

    # ---- tabs --------------------------------------------------------------------------
    def tabs(self) -> list[dict]:
        self.ensure_running()
        pages = [t for t in self._http("/json/list") if t.get("type") == "page"]
        return [{"id": t["id"], "title": t.get("title", ""), "url": t.get("url", "")}
                for t in pages]

    def open(self, url: str) -> dict:
        self.ensure_running()
        url = normalize_url(url)
        tab = self._http("/json/new?" + urllib.parse.quote(url, safe=":/?&=#%,"), method="PUT")
        self.activate(tab["id"])
        self.wait_loaded(tab["id"])
        return {"id": tab["id"], "url": url}

    def activate(self, tab_id: str) -> None:
        self._http(f"/json/activate/{tab_id}", parse=False)
        self._last_tab = tab_id

    def wait_loaded(self, tab_id: str | None, timeout: float = 15) -> None:
        """Wait until the page has navigated away from about:blank and finished loading."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                state = self.evaluate(tab_id, "[document.readyState, location.href]")
            except ChromeError:
                state = None
            if state and state[0] == "complete" and state[1] != "about:blank":
                return
            time.sleep(0.2)

    def close(self, tab_id: str) -> None:
        self._http(f"/json/close/{tab_id}", parse=False)

    def navigate(self, tab_id: str | None, url: str) -> None:
        url = normalize_url(url)
        tab = self._tab(tab_id)
        self._cdp(tab, "Page.navigate", {"url": url})
        time.sleep(0.3)
        self.wait_loaded(tab["id"])

    def read(self, tab_id: str | None = None, max_chars: int = 40_000) -> str:
        """Visible text of a tab (the most recently used tab by default)."""
        tab = self._tab(tab_id)
        text = self.evaluate(
            tab["id"],
            "document.title + '\\n' + location.href + '\\n\\n' + "
            "(document.body ? document.body.innerText : '')",
        )
        text = str(text or "")
        if len(text) > max_chars:
            text = text[:max_chars] + f"\n\n[…truncated, {len(text) - max_chars} more characters]"
        return text

    def evaluate(self, tab_id: str | None, expression: str):
        tab = self._tab(tab_id)
        result = self._cdp(tab, "Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True,
        })
        if "exceptionDetails" in result:
            detail = result["exceptionDetails"]
            message = detail.get("exception", {}).get("description") or detail.get("text")
            raise ChromeError(f"JavaScript error: {message}")
        return result.get("result", {}).get("value")

    # ---- internals -----------------------------------------------------------------------
    def _tab(self, tab_id: str | None) -> dict:
        self.ensure_running()
        pages = [t for t in self._http("/json/list") if t.get("type") == "page"]
        if not pages:
            raise ChromeError("Chrome has no open tabs.")
        if tab_id is None:
            # The tab the assistant last opened/switched to, if the user hasn't moved on;
            # otherwise Chrome's list order (most recently focused first).
            visible = [t for t in pages[:15] if self._visible(t)]
            for t in visible:
                if t["id"] == self._last_tab:
                    return t
            return (visible or pages)[0]
        for t in pages:
            if t["id"] == tab_id:
                return t
        raise ChromeError(f"No tab with id {tab_id}. Call chrome_list_tabs for current ids.")

    def _visible(self, tab: dict) -> bool:
        try:
            result = self._cdp(tab, "Runtime.evaluate", {
                "expression": "document.visibilityState", "returnByValue": True})
        except Exception:  # noqa: BLE001 - tab closing, crashed or busy
            return False
        return result.get("result", {}).get("value") == "visible"

    def _cdp(self, tab: dict, method: str, params: dict) -> dict:
        import websocket

        ws_url = tab.get("webSocketDebuggerUrl")
        if not ws_url:
            raise ChromeError("Tab is not debuggable (is DevTools already attached to it?).")
        ws = websocket.create_connection(ws_url, timeout=20, suppress_origin=True)
        try:
            self._msg_id += 1
            ws.send(json.dumps({"id": self._msg_id, "method": method, "params": params}))
            while True:
                msg = json.loads(ws.recv())
                if msg.get("id") == self._msg_id:
                    if "error" in msg:
                        raise ChromeError(msg["error"].get("message", str(msg["error"])))
                    return msg.get("result", {})
        finally:
            ws.close()

    def _http(self, path: str, method: str = "GET", parse: bool = True):
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", method=method)
        try:
            with _NO_PROXY.open(req, timeout=5) as resp:
                body = resp.read().decode("utf-8", "replace")
        except (urllib.error.URLError, OSError) as exc:
            raise ChromeError(f"Chrome debugging port {self.port} not reachable: {exc}") from exc
        return json.loads(body) if parse else body
