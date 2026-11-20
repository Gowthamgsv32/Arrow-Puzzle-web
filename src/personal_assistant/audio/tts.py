"""Text-to-speech.

Online: Microsoft Edge neural voices (edge-tts) - natural English and Tamil voices.
Offline fallback: the voices installed in the operating system (pyttsx3: SAPI5 on Windows,
NSSpeechSynthesizer on macOS, eSpeak on Linux). Windows ships English voices; a Tamil voice
needs the Tamil speech pack (Settings > Time & language > Speech > Add voices).
"""

from __future__ import annotations

import asyncio
import io
import logging
import sys
import time

log = logging.getLogger(__name__)

OFFLINE_RETRY_SECONDS = 60  # after a network failure, skip the online voice for a minute


class TextToSpeech:
    def __init__(self, offline_engine=None):
        self._offline = offline_engine or OfflineVoice()
        self._online_failed_at = 0.0

    @property
    def using_offline(self) -> bool:
        return time.monotonic() - self._online_failed_at < OFFLINE_RETRY_SECONDS

    def speak(self, text: str, voice: str, language: str = "en") -> str:
        """Speak `text`. Returns which engine spoke: "online", "offline" or "none"."""
        if not self.using_offline:
            try:
                self._speak_online(text, voice)
                return "online"
            except Exception as exc:  # noqa: BLE001 - no internet, service down, audio error
                log.warning("Online voice failed (%s); using offline voice", exc)
                self._online_failed_at = time.monotonic()
        return "offline" if self._offline.speak(text, language) else "none"

    def _speak_online(self, text: str, voice: str) -> None:
        import sounddevice as sd
        import soundfile as sf

        mp3 = asyncio.run(_synthesize(text, voice))
        if not mp3:
            raise RuntimeError("edge-tts returned no audio")
        data, sample_rate = sf.read(io.BytesIO(mp3))
        sd.play(data, sample_rate)
        sd.wait()


async def _synthesize(text: str, voice: str) -> bytes:
    import edge_tts

    buf = io.BytesIO()
    communicate = edge_tts.Communicate(text, voice, connect_timeout=4, receive_timeout=20)
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    return buf.getvalue()


# Words that identify a language in OS voice names/ids/languages.
_LANGUAGE_HINTS = {
    "en": ("en", "english", "zira", "david", "mark", "hazel"),
    "ta": ("ta", "tamil", "valluvar", "pallavi"),
}


# Preferred accents, best first (matched against voice id/name).
_PREFERRED = {
    "en": ("en-in", "india", "heera", "ravi", "en-us", "zira", "david", "en-gb", "hazel"),
}


def pick_voice(voices, language: str):
    """Choose an installed OS voice for `language`, or None if there isn't one."""
    matches = _matching_voices(voices, language)
    for pref in _PREFERRED.get(language, ()):
        for v in matches:
            if pref in f"{getattr(v, 'name', '')} {getattr(v, 'id', '')}".lower():
                return v
    return matches[0] if matches else None


def _matching_voices(voices, language: str) -> list:
    hints = _LANGUAGE_HINTS.get(language, (language,))
    found = []
    for v in voices:
        langs = " ".join(
            (x.decode(errors="ignore") if isinstance(x, bytes) else str(x))
            for x in (getattr(v, "languages", None) or [])
        ).lower()
        name = f"{getattr(v, 'name', '')} {getattr(v, 'id', '')}".lower()
        tokens = set(name.replace("_", " ").replace("-", " ").replace("\\", " ").split())
        lang_codes = {part.split("-")[0].split("_")[0] for part in langs.split()}
        if hints[0] in lang_codes or any(h in tokens for h in hints[1:]) or (
            len(hints[0]) == 2 and f"{hints[0]}-" in name
        ):
            found.append(v)
    return found


class OfflineVoice:
    """Speaks with an operating-system voice. A new engine per call keeps it thread-safe."""

    def __init__(self, init_engine=None):
        self._init_engine = init_engine or _default_engine
        self._warned: set[str] = set()

    def speak(self, text: str, language: str) -> bool:
        try:
            engine = self._init_engine()
        except Exception as exc:  # noqa: BLE001 - no speech engine installed
            self._warn_once("engine", "No offline voice engine available: %s", exc)
            return False
        try:
            voice = pick_voice(engine.getProperty("voices") or [], language)
            if voice is None:
                if language != "en":
                    self._warn_once(language, "No offline %s voice installed; showing text only.",
                                    language)
                    return False
            else:
                engine.setProperty("voice", voice.id)
            engine.say(text)
            engine.runAndWait()
            return True
        except Exception as exc:  # noqa: BLE001
            log.warning("Offline voice failed: %s", exc)
            return False
        finally:
            try:
                engine.stop()
            except Exception:  # noqa: BLE001, S110
                pass

    def _warn_once(self, key: str, msg: str, *args) -> None:
        if key not in self._warned:
            self._warned.add(key)
            log.warning(msg, *args)


def _default_engine():
    if sys.platform == "win32":
        import comtypes

        comtypes.CoInitialize()  # SAPI is COM; each thread must initialise it
    import pyttsx3

    return pyttsx3.init()
