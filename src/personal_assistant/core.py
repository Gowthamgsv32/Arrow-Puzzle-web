"""The assistant's "brain": text in -> intent -> skill -> localized reply. No I/O here."""

from __future__ import annotations

from dataclasses import dataclass

from personal_assistant import skills
from personal_assistant.config import Settings
from personal_assistant.i18n import Locale, load_locales
from personal_assistant.intents import IntentMatcher

# Built-in commands that are always handled locally (instant, free, offline).
SIMPLE_INTENTS = {"greet", "time", "date", "exit"}


@dataclass(frozen=True)
class Response:
    reply: str
    locale: Locale
    intent: str
    exit: bool = False
    argument: str = ""

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
        return Response(result.reply, locale, intent.name, result.exit, intent.argument)

    def match(self, text: str, language: str | None = None):
        return self.matcher.match(text, language)

    def is_simple(self, text: str, language: str | None = None) -> bool:
        """True if a built-in skill fully handles this (so the AI agent isn't needed)."""
        from personal_assistant.skills.builtin import APPS, WEBSITES

        intent = self.matcher.match(text, language)
        if intent.name in SIMPLE_INTENTS:
            # "hello, open my repo in VS Code" is more than a greeting
            return len(intent.argument.split()) <= 2
        if intent.name == "open":
            return intent.phrase_at_edge and (intent.argument in WEBSITES or intent.argument in APPS)
        return False

    def is_confident(self, text: str, language: str | None = None) -> bool:
        """Built-in command clearly meant (used for always-listening speech)."""
        if self.is_simple(text, language):
            return True
        intent = self.matcher.match(text, language)
        return (
            intent.name in ("open", "search")
            and intent.phrase_at_edge
            and 1 <= len(intent.argument.split()) <= 5
        )
