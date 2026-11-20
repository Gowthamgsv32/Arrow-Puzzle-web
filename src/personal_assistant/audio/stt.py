"""Speech-to-text using faster-whisper (offline, supports Tamil and ~100 languages)."""

from __future__ import annotations

import numpy as np

from personal_assistant.intents import normalize

# Whisper tends to "hear" these in silence or background noise.
HALLUCINATIONS = {
    "thank you",
    "thanks for watching",
    "thank you for watching",
    "you",
    "subtitles by the amara org community",
    "நன்றி",
}


class SpeechToText:
    def __init__(self, model_size: str, device: str, compute_type: str, languages: list[str]):
        from faster_whisper import WhisperModel

        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.languages = languages

    def transcribe(self, audio: np.ndarray) -> tuple[str, str | None]:
        """Return (text, language). Detection is restricted to the configured
        languages so short clips are not misdetected as e.g. Malayalam."""
        segments, info = self._run(audio, None)
        language = info.language
        if language not in self.languages:
            probs = dict(info.all_language_probs or [])
            language = max(self.languages, key=lambda code: probs.get(code, 0.0))
            segments, info = self._run(audio, language)
        text = " ".join(
            seg.text.strip()
            for seg in segments
            if not (seg.no_speech_prob > 0.6 and seg.avg_logprob < -1.0)
        ).strip()
        if normalize(text) in HALLUCINATIONS:
            text = ""
        return text, (language if text else None)

    def _run(self, audio: np.ndarray, language: str | None):
        segments, info = self.model.transcribe(
            audio,
            language=language,
            beam_size=5,
            vad_filter=True,
            condition_on_previous_text=False,
        )
        return list(segments), info

