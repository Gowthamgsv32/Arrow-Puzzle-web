"""Speech-to-text using faster-whisper (offline, supports Tamil and ~100 languages)."""

from __future__ import annotations

import numpy as np


class SpeechToText:
    def __init__(self, model_size: str, device: str, compute_type: str, languages: list[str]):
        from faster_whisper import WhisperModel

        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.languages = languages

    def transcribe(self, audio: np.ndarray) -> tuple[str, str | None]:
        """Return (text, language code). Language detection is restricted to the
        configured languages so short clips are not misdetected as e.g. Malayalam."""
        segments, info = self.model.transcribe(audio, beam_size=5, vad_filter=True)
        language = info.language
        if language not in self.languages:
            probs = dict(info.all_language_probs or [])
            language = max(self.languages, key=lambda code: probs.get(code, 0.0))
            segments, info = self.model.transcribe(
                audio, beam_size=5, vad_filter=True, language=language
            )
        text = " ".join(seg.text.strip() for seg in segments).strip()
        return text, (language if text else None)
