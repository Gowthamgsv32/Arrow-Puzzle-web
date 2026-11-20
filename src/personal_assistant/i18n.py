"""Locale loading.

Every supported language is a single YAML file in ``locales/<code>.yaml``.
Adding a new language (Hindi, Telugu, ...) means adding one file - no code changes.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

import yaml

LOCALES_DIR = Path(__file__).parent / "locales"


@dataclass(frozen=True)
class Locale:
    code: str
    name: str
    tts_voice: str
    intents: dict[str, list[str]]  # intent name -> trigger phrases
    responses: dict[str, list[str]]  # response key -> templates

    def say(self, key: str, **kwargs: object) -> str:
        options = self.responses.get(key) or [key]
        return random.choice(options).format(**kwargs)


def load_locale(code: str, directory: Path = LOCALES_DIR) -> Locale:
    path = directory / f"{code}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"No locale file for language '{code}' at {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return Locale(
        code=code,
        name=data.get("name", code),
        tts_voice=data.get("tts_voice", ""),
        intents={k: list(v) for k, v in (data.get("intents") or {}).items()},
        responses={
            k: [v] if isinstance(v, str) else list(v)
            for k, v in (data.get("responses") or {}).items()
        },
    )


def load_locales(codes: list[str], directory: Path = LOCALES_DIR) -> dict[str, Locale]:
    return {code: load_locale(code, directory) for code in codes}


def available_languages(directory: Path = LOCALES_DIR) -> list[str]:
    return sorted(p.stem for p in directory.glob("*.yaml"))
