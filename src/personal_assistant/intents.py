"""Language-agnostic intent matching.

Trigger phrases come from the locale files. Whatever text remains after removing
the matched phrase becomes the intent's argument. That works for English
("open youtube") and Tamil, where the verb usually comes last ("யூடியூப் திற").
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from personal_assistant.i18n import Locale


@dataclass(frozen=True)
class Intent:
    name: str
    argument: str
    language: str
    text: str
    phrase: str = ""  # the trigger phrase that matched

    @property
    def phrase_at_edge(self) -> bool:
        """Command word starts or ends the sentence ("open X" / "X திற"), not buried mid-sentence."""
        norm = normalize(self.text)
        return bool(self.phrase) and (norm.startswith(self.phrase) or norm.endswith(self.phrase))


def normalize(text: str) -> str:
    """Lower-case, drop punctuation, collapse whitespace.

    Only Unicode *punctuation* is removed, so Tamil vowel signs and the virama
    (combining marks) are preserved.
    """
    text = unicodedata.normalize("NFC", text).casefold()
    text = "".join(" " if unicodedata.category(ch).startswith("P") else ch for ch in text)
    return re.sub(r"\s+", " ", text).strip()


class IntentMatcher:
    def __init__(self, locales: dict[str, Locale]):
        # (language, intent, normalized phrase), longest phrase first so that
        # "what is the date" beats a shorter overlapping trigger.
        self._triggers = sorted(
            (
                (lang, intent, normalize(phrase))
                for lang, locale in locales.items()
                for intent, phrases in locale.intents.items()
                for phrase in phrases
            ),
            key=lambda t: len(t[2]),
            reverse=True,
        )

    def match(self, text: str, language: str | None = None) -> Intent:
        norm = normalize(text)
        candidates = self._triggers
        if language:
            # Prefer the spoken language, but still allow mixed-language commands.
            candidates = sorted(candidates, key=lambda t: t[0] != language)
        for lang, intent, phrase in candidates:
            if phrase and _contains_phrase(norm, phrase):
                argument = _remove_phrase(norm, phrase)
                return Intent(intent, argument, language or lang, text, phrase)
        return Intent("unknown", norm, language or "", text)


def _contains_phrase(text: str, phrase: str) -> bool:
    return f" {phrase} " in f" {text} "


def _remove_phrase(text: str, phrase: str) -> str:
    return re.sub(r"\s+", " ", f" {text} ".replace(f" {phrase} ", " ", 1)).strip()
