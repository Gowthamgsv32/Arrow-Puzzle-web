"""Terminal, clipboard, file-system and app-launch helpers used by the agent's tools."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

MAX_OUTPUT = 20_000


def default_workspace() -> Path:
    return Path(os.getenv("PA_WORKSPACE") or Path.home()).expanduser()


def _windows_shell() -> str:
    """PowerShell 7 (pwsh) if installed - it supports `&&` - else Windows PowerShell 5.1."""
    return "pwsh" if shutil.which("pwsh") else "powershell"


def shell_name() -> str:
    if sys.platform == "win32":
        if _windows_shell() == "pwsh":
            return "PowerShell 7"
        return "Windows PowerShell 5.1 (no `&&`/`||`: chain with `;` or `if ($?) { ... }`)"
    return os.path.basename(os.getenv("SHELL", "bash"))


def run_command(command: str, cwd: str | None, timeout: int = 120) -> str:
    workdir = Path(cwd).expanduser() if cwd else default_workspace()
    if not workdir.is_dir():
        return f"Error: directory not found: {workdir}"
    if sys.platform == "win32":
        args = [_windows_shell(), "-NoProfile", "-NonInteractive", "-Command", command]
        flags = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
        shell = False
    else:
        args, flags, shell = command, 0, True
    try:
        proc = subprocess.run(
            args, check=False, cwd=workdir, shell=shell, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=max(1, min(timeout, 1800)), creationflags=flags,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired as exc:
        out = (exc.stdout or "") + (exc.stderr or "")
        return f"Timed out after {timeout}s.\n{_clip(str(out))}"
    out = proc.stdout + (("\n[stderr]\n" + proc.stderr) if proc.stderr.strip() else "")
    return f"exit code {proc.returncode} (cwd: {workdir})\n{_clip(out) or '(no output)'}"


def open_terminal(cwd: str | None, command: str | None) -> str:
    workdir = str(Path(cwd).expanduser() if cwd else default_workspace())
    if sys.platform == "win32":
        if shutil.which("wt"):
            args = ["wt", "-d", workdir]
            if command:
                args += ["powershell", "-NoExit", "-Command", command]
        else:
            args = ["cmd", "/c", "start", "powershell", "-NoExit", "-Command",
                    f"Set-Location '{workdir}'" + (f"; {command}" if command else "")]
        subprocess.Popen(args)
    elif sys.platform == "darwin":
        script = f'cd {_q(workdir)}' + (f"; {command}" if command else "")
        subprocess.Popen(["osascript", "-e",
                          f'tell application "Terminal" to do script "{script}"',
                          "-e", 'tell application "Terminal" to activate'])
    else:
        term = next((t for t in ("x-terminal-emulator", "gnome-terminal", "konsole", "xterm")
                     if shutil.which(t)), None)
        if not term:
            return "Error: no terminal emulator found."
        args = [term]
        if command:
            args += ["-e", f"bash -c {_q(command + '; exec bash')}"]
        subprocess.Popen(args, cwd=workdir, start_new_session=True)
    return f"Opened a terminal in {workdir}."


def clipboard_get() -> str:
    import pyperclip

    return pyperclip.paste() or "(clipboard is empty or not text)"


def clipboard_set(text: str) -> str:
    import pyperclip

    pyperclip.copy(text)
    return f"Copied {len(text)} characters to the clipboard."


def read_file(path: str, max_chars: int = 60_000) -> str:
    p = Path(path).expanduser()
    if not p.is_file():
        return f"Error: not a file: {p}"
    text = p.read_text(encoding="utf-8", errors="replace")
    if len(text) > max_chars:
        return text[:max_chars] + f"\n[…truncated, file has {len(text)} characters]"
    return text


def write_file(path: str, content: str) -> str:
    p = Path(path).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} characters to {p}."


def list_directory(path: str | None) -> str:
    p = Path(path).expanduser() if path else default_workspace()
    if not p.is_dir():
        return f"Error: not a directory: {p}"
    entries = sorted(p.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
    lines = [f"{e.name}/" if e.is_dir() else e.name for e in entries[:500]]
    more = f"\n… and {len(entries) - 500} more" if len(entries) > 500 else ""
    return f"{p}\n" + "\n".join(lines) + more


def open_target(target: str) -> str:
    """Open a URL, file, folder or application with the OS default handler."""
    import webbrowser

    if target.startswith(("http://", "https://")):
        webbrowser.open(target)
        return f"Opened {target} in the default browser."
    path = Path(target).expanduser()
    try:
        if sys.platform == "win32":
            os.startfile(str(path) if path.exists() else target)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            args = ["open", str(path)] if path.exists() else ["open", "-a", target]
            subprocess.run(args, check=True)
        else:
            exe = shutil.which(target)
            subprocess.Popen([exe] if exe else ["xdg-open", str(path)], start_new_session=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        return f"Error: could not open {target}: {exc}"
    return f"Opened {target}."


def _clip(text: str) -> str:
    if len(text) <= MAX_OUTPUT:
        return text.strip()
    half = MAX_OUTPUT // 2
    return f"{text[:half]}\n[… {len(text) - MAX_OUTPUT} characters omitted …]\n{text[-half:]}"


def _q(s: str) -> str:
    return "'" + s.replace("'", "'\\''") + "'"
