"""Runtime settings, loaded from environment variables (and an optional .env file)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    from personal_assistant.paths import env_file, user_data_dir

    load_dotenv(env_file())
    load_dotenv(user_data_dir() / ".env")


def _flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    languages: list[str] = field(default_factory=lambda: ["en", "ta"])
    default_language: str = "en"
    whisper_model: str = "small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    sample_rate: int = 16_000
    # Continuous-listening voice activity detection
    vad_min_rms: float = 0.010  # absolute floor for "this is speech" (raise in noisy rooms)
    vad_silence_ms: int = 700  # pause length that ends a sentence
    vad_max_seconds: float = 15.0  # hard cap per utterance
    # Act only on commands that start with this word (empty = act on everything)
    wake_word: str = ""
    # AI agent (Claude) for everything beyond the built-in commands
    agent_enabled: bool = False
    agent_model: str = "claude-opus-5-5"
    agent_effort: str = "medium"  # low | medium | high | xhigh | max
    agent_max_steps: int = 40
    # In always-listening mode, agent tasks must start with one of these words so that
    # background conversation is never sent to the AI. Empty = send every unmatched sentence.
    agent_wake_word: str = "assistant,அசிஸ்டன்ட்,அசிஸ்டென்ட்"
    auto_approve: bool = False  # True = never ask before risky commands (not recommended)
    # Which brain: "auto" (Claude, local model as fallback), "claude" or "local"
    agent_brain: str = "auto"
    local_model: str = "qwen2.5:7b"  # any Ollama model with tool support
    ollama_url: str = "http://127.0.0.1:11434"

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
            vad_min_rms=float(os.getenv("PA_VAD_MIN_RMS", "0.010")),
            vad_silence_ms=int(os.getenv("PA_VAD_SILENCE_MS", "700")),
            vad_max_seconds=float(os.getenv("PA_VAD_MAX_SECONDS", "15")),
            wake_word=os.getenv("PA_WAKE_WORD", "").strip(),
            agent_enabled=_flag("PA_AGENT", default=bool(os.getenv("ANTHROPIC_API_KEY"))),
            agent_model=os.getenv("PA_AGENT_MODEL", "claude-opus-5-5"),
            agent_effort=os.getenv("PA_AGENT_EFFORT", "medium"),
            agent_max_steps=int(os.getenv("PA_AGENT_MAX_STEPS", "40")),
            agent_wake_word=os.getenv(
                "PA_AGENT_WAKE_WORD", "assistant,அசிஸ்டன்ட்,அசிஸ்டென்ட்"
            ).strip(),
            auto_approve=_flag("PA_AUTO_APPROVE", default=False),
            agent_brain=os.getenv("PA_AGENT_BRAIN", "auto").strip().lower() or "auto",
            local_model=os.getenv("PA_LOCAL_MODEL", "qwen2.5:7b").strip(),
            ollama_url=os.getenv("PA_OLLAMA_URL", "http://127.0.0.1:11434").strip(),
        )
