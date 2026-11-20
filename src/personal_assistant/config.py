"""Runtime settings, loaded from environment variables (and an optional .env file)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


@dataclass(frozen=True)
class Settings:
    languages: list[str] = field(default_factory=lambda: ["en", "ta"])
    default_language: str = "en"
    whisper_model: str = "small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    record_seconds: float = 5.0
    sample_rate: int = 16_000

    @classmethod
    def from_env(cls) -> Settings:
        _load_dotenv()
        langs = [c.strip() for c in os.getenv("PA_LANGUAGES", "en,ta").split(",") if c.strip()]
        default = os.getenv("PA_DEFAULT_LANGUAGE", langs[0] if langs else "en")
        if default not in langs:
            langs.insert(0, default)
        return cls(
            languages=langs,
            default_language=default,
            whisper_model=os.getenv("PA_WHISPER_MODEL", "small"),
            whisper_device=os.getenv("PA_WHISPER_DEVICE", "cpu"),
            whisper_compute_type=os.getenv("PA_WHISPER_COMPUTE_TYPE", "int8"),
            record_seconds=float(os.getenv("PA_RECORD_SECONDS", "5")),
        )
