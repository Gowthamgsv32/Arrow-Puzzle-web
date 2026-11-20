"""Per-user writable locations (logs, settings) that also work inside a frozen .exe."""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "PersonalAssistant"


def user_data_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    path = base / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def env_file() -> Path:
    """`.env` next to the .exe when frozen, otherwise the current directory."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).with_name(".env")
    return Path.cwd() / ".env"
