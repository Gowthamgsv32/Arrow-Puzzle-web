"""Always-listening loop shared by the desktop UI and the terminal mode.

Microphone frames -> voice activity detection -> Whisper -> Brain -> spoken reply.
UI code plugs in through the ``Events`` callbacks, which are called from the
loop's own thread.
"""

from __future__ import annotations

import logging
import queue
import threading
from typing import Protocol

from personal_assistant.config import Settings
from personal_assistant.core import Brain
from personal_assistant.intents import normalize

log = logging.getLogger(__name__)

# UI states
LOADING, LISTENING, HEARING, THINKING, SPEAKING, MUTED, ERROR = (
    "loading", "listening", "hearing", "thinking", "speaking", "muted", "error"
)


class Events(Protocol):
    def on_status(self, state: str, detail: str = "") -> None: ...
    def on_level(self, level: float) -> None: ...
    def on_heard(self, text: str, language: str | None, accepted: bool) -> None: ...
    def on_reply(self, text: str, language: str) -> None: ...
    def on_quit(self) -> None: ...


def strip_wake_word(text: str, wake_words: list[str]) -> str | None:
    """Return the command after a wake word, or None if no wake word was said.
    With no wake words configured every utterance is a command."""
    if not wake_words:
        return text
    norm = normalize(text)
    for word in wake_words:
        w = normalize(word)
        if norm == w or norm.startswith(w + " "):
            return norm[len(w):].strip()
    return None


class VoiceLoop:
    def __init__(
        self,
        settings: Settings,
        events: Events,
        *,
        voice: bool = True,
        exit_quits: bool = False,
    ):
        self.settings = settings
        self.events = events
        self.voice = voice
        self.exit_quits = exit_quits
        self.wake_words = [w for w in settings.wake_word.split(",") if w.strip()]
        self._queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._stop = threading.Event()
        self._muted = False
        self._speaking = False
        self._state = ""

    # ---- called from other threads -------------------------------------------------
    def submit_text(self, text: str) -> None:
        self._queue.put(("text", text))

    def set_muted(self, muted: bool) -> None:
        self._queue.put(("mute", muted))

    def stop(self) -> None:
        self._stop.set()

    # ---- loop ------------------------------------------------------------------------
    def run(self) -> None:
        try:
            self._run()
        except Exception as exc:
            log.exception("Voice loop crashed")
            self._status(ERROR, str(exc))

    def _run(self) -> None:
        self.brain = Brain(self.settings)
        self.stt = self.tts = mic = None
        if self.voice:
            from personal_assistant.audio.listener import Microphone
            from personal_assistant.audio.stt import SpeechToText
            from personal_assistant.audio.tts import TextToSpeech
            from personal_assistant.audio.vad import UtteranceSegmenter, rms

            self._status(LOADING, f"Loading speech model '{self.settings.whisper_model}'…")
            self.stt = SpeechToText(
                self.settings.whisper_model,
                self.settings.whisper_device,
                self.settings.whisper_compute_type,
                self.settings.languages,
            )
            self.tts = TextToSpeech()
            segmenter = UtteranceSegmenter(
                sample_rate=self.settings.sample_rate,
                min_rms=self.settings.vad_min_rms,
                silence_ms=self.settings.vad_silence_ms,
                max_seconds=self.settings.vad_max_seconds,
            )
            mic = Microphone(self._on_frame, self.settings.sample_rate)
            mic.start()
        self._status(MUTED if self._muted else LISTENING)

        try:
            while not self._stop.is_set():
                try:
                    kind, payload = self._queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                if kind == "mute":
                    self._muted = bool(payload)
                    if self.voice:
                        segmenter.reset()
                    self._status(MUTED if self._muted else LISTENING)
                elif kind == "text":
                    self._handle(str(payload), None, typed=True)
                elif kind == "audio" and not self._muted:
                    frame = payload
                    self.events.on_level(rms(frame))
                    utterance = segmenter.feed(frame)
                    if segmenter.in_speech:
                        self._status(HEARING)
                    elif utterance is not None:
                        self._status(THINKING)
                        text, lang = self.stt.transcribe(utterance)
                        if text:
                            self._handle(text, lang, typed=False)
                        segmenter.reset()
                        self._drain_audio()
                        if not self._stop.is_set():
                            self._status(MUTED if self._muted else LISTENING)
                    elif self._state == HEARING:
                        self._status(LISTENING)
        finally:
            if mic:
                mic.stop()

    def _on_frame(self, frame) -> None:
        if not self._speaking and not self._muted:
            self._queue.put(("audio", frame))

    def _drain_audio(self) -> None:
        """Drop audio captured while we were transcribing/speaking (it's our own voice)."""
        keep = []
        while True:
            try:
                item = self._queue.get_nowait()
            except queue.Empty:
                break
            if item[0] != "audio":
                keep.append(item)
        for item in keep:
            self._queue.put(item)

    def _handle(self, text: str, language: str | None, typed: bool) -> None:
        command = text if typed else strip_wake_word(text, self.wake_words)
        if command is None:
            self.events.on_heard(text, language, accepted=False)
            return
        response = self.brain.process(command, language)
        # In always-listening mode, ignore chatter that isn't a command.
        accepted = typed or response.understood
        if language is None and response.understood:
            language = response.locale.code
        self.events.on_heard(text, language, accepted=accepted)
        if not accepted:
            return
        self.events.on_reply(response.reply, response.locale.code)
        self._speak(response.reply, response.locale.tts_voice)
        if response.intent == "exit":
            if self.exit_quits:
                self._stop.set()
                self.events.on_quit()
            else:  # "goodbye" puts the assistant to sleep; click the mic to wake it
                self._muted = True
                self._status(MUTED)
        elif typed and not self._stop.is_set():
            self._status(MUTED if self._muted else LISTENING)

    def _speak(self, text: str, voice: str) -> None:
        if not self.tts or not voice:
            return
        self._status(SPEAKING)
        self._speaking = True
        try:
            self.tts.speak(text, voice)
        except Exception as exc:  # noqa: BLE001 - offline / audio device issues shouldn't stop listening
            log.warning("Text-to-speech failed: %s", exc)
        finally:
            self._speaking = False

    def _status(self, state: str, detail: str = "") -> None:
        if state != self._state or detail:
            self._state = state
            self.events.on_status(state, detail)
