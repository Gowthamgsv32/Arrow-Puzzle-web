"""Chrome DevTools control against a real headless Chromium (skipped if none installed),
plus terminal/file helpers."""

import glob
import os
import sys
import urllib.parse

import pytest

from personal_assistant.agent import system
from personal_assistant.agent.chrome import Chrome, find_chrome, normalize_url


def _chromium() -> str | None:
    hits = glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")
    return hits[0] if hits else find_chrome()


@pytest.fixture(scope="module")
def chrome(tmp_path_factory):
    exe = os.getenv("PA_TEST_CHROME") or _chromium()
    if not exe or sys.platform == "win32":
        pytest.skip("no Chromium available")
    c = Chrome(port=9339, chrome_path=exe, profile_dir=tmp_path_factory.mktemp("profile"),
               headless=True)
    c.ensure_running()
    yield c
    for t in c.tabs():
        c.close(t["id"])


def test_open_read_eval_close(chrome):
    html = "<title>Build status</title><h1>All 51 tests passed</h1><a href='/x'>details</a>"
    tab = chrome.open("data:text/html," + urllib.parse.quote(html))
    assert any(t["id"] == tab["id"] for t in chrome.tabs())
    text = chrome.read(tab["id"])
    assert text.startswith("Build status")
    assert "All 51 tests passed" in text
    assert chrome.evaluate(tab["id"], "document.querySelectorAll('a').length") == 1
    assert chrome.evaluate(tab["id"], "Promise.resolve(6 * 7)") == 42
    with pytest.raises(Exception, match="JavaScript error"):
        chrome.evaluate(tab["id"], "nope.nope")
    chrome.close(tab["id"])
    assert all(t["id"] != tab["id"] for t in chrome.tabs())


def test_read_defaults_to_most_recent_tab(chrome):
    chrome.open("data:text/html,<p>first</p>")
    chrome.open("data:text/html,<p>second one</p>")
    assert "second one" in chrome.read()


def test_run_command_captures_output_and_exit_code(tmp_path):
    out = system.run_command("echo hello && exit 3", str(tmp_path))
    assert "exit code 3" in out and "hello" in out


def test_run_command_bad_cwd():
    assert system.run_command("echo hi", "/definitely/not/here").startswith("Error")


def test_file_roundtrip(tmp_path):
    target = tmp_path / "notes" / "todo.md"
    system.write_file(str(target), "வணக்கம்\n- ship it")
    assert system.read_file(str(target)) == "வணக்கம்\n- ship it"
    assert "notes/" in system.list_directory(str(tmp_path))


def test_normalize_url():
    assert normalize_url("github.com/me") == "https://github.com/me"
    assert normalize_url("localhost:3000") == "http://localhost:3000"
    assert normalize_url("data:text/html,hi") == "data:text/html,hi"
    assert normalize_url("chrome://settings") == "chrome://settings"
    assert normalize_url("http://x.dev") == "http://x.dev"
