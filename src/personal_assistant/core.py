"""The assistant's "brain": text in -> intent -> skill -> localized reply. No I/O here."""

from __future__ import annotations

from dataclasses import dataclass

from personal_assistant import skills
from personal_assistant.config import Settings
from personal_assistant.i18n import Locale, load_locales
from personal_assistant.intents import IntentMatcher


@dataclass(frozen=True)
class Response:
    reply: str
    locale: Locale
    intent: str
    exit: bool = False

    @property
    def understood(self) -> bool:
        return self.intent != "unknown"


class Brain:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.locales = load_locales(settings.languages)
        self.matcher = IntentMatcher(self.locales)

    def locale(self, code: str | None) -> Locale:
        return self.locales.get(code or "", self.locales[self.settings.default_language])

    def process(self, text: str, language: str | None = None) -> Response:
        intent = self.matcher.match(text, language)
        locale = self.locale(intent.language)
        result = skills.handle(intent, locale)
        return Response(result.reply, locale, intent.name, result.exit)
