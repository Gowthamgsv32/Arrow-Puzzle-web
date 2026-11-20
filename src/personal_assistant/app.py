"""Entry point: the listen -> understand -> act -> reply loop."""

from __future__ import annotations

import argparse
import logging

from personal_assistant import skills
from personal_assistant.config import Settings
from personal_assistant.i18n import Locale, load_locales
from personal_assistant.intents import IntentMatcher

log = logging.getLogger("personal_assistant")


class Assistant:
    def __init__(self, settings: Settings, voice: bool):
        self.settings = settings
        self.voice = voice
        self.locales = load_locales(settings.languages)
        self.matcher = IntentMatcher(self.locales)
        self.stt = None
        self.tts = None
        if voice:
            from personal_assistant.audio.stt import SpeechToText
            from personal_assistant.audio.tts import TextToSpeech

            log.info("Loading Whisper model '%s'...", settings.whisper_model)
            self.stt = SpeechToText(
                settings.whisper_model,
                settings.whisper_device,
                settings.whisper_compute_type,
                settings.languages,
            )
            self.tts = TextToSpeech()

    def locale(self, code: str | None) -> Locale:
        return self.locales.get(code or "", self.locales[self.settings.default_language])

    def listen(self) -> tuple[str, str | None]:
        if not self.voice:
            return input("you> ").strip(), None
        from personal_assistant.audio.recorder import record

        input("\n[Press Enter, then speak]")
        print(self.locale(None).say("listening"))
        audio = record(self.settings.record_seconds, self.settings.sample_rate)
        text, lang = self.stt.transcribe(audio)
        print(f"you ({lang or '?'})> {text}")
        return text, lang

    def reply(self, text: str, locale: Locale) -> None:
        print(f"assistant> {text}")
        if self.tts and locale.tts_voice:
            try:
                self.tts.speak(text, locale.tts_voice)
            except Exception as exc:  # noqa: BLE001 - network / audio device problems shouldn't kill the loop
                log.warning("Text-to-speech failed: %s", exc)

    def run(self) -> None:
        while True:
            try:
                text, lang = self.listen()
            except (EOFError, KeyboardInterrupt):
                print()
                return
            if not text:
                continue
            intent = self.matcher.match(text, lang)
            locale = self.locale(intent.language)
            result = skills.handle(intent, locale)
            self.reply(result.reply, locale)
            if result.exit:
                return


def main() -> None:
    parser = argparse.ArgumentParser(description="Personal desktop assistant (English + Tamil).")
    parser.add_argument(
        "--text", action="store_true", help="type commands instead of speaking (no audio deps)"
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")

    Assistant(Settings.from_env(), voice=not args.text).run()


if __name__ == "__main__":
    main()
