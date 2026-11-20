from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from personal_assistant.i18n import Locale
from personal_assistant.intents import Intent


@dataclass(frozen=True)
class SkillResult:
    reply: str
    exit: bool = False


SkillFn = Callable[[Intent, Locale], SkillResult]
REGISTRY: dict[str, SkillFn] = {}


def skill(name: str) -> Callable[[SkillFn], SkillFn]:
    def register(fn: SkillFn) -> SkillFn:
        REGISTRY[name] = fn
        return fn

    return register


def handle(intent: Intent, locale: Locale) -> SkillResult:
    fn = REGISTRY.get(intent.name)
    if fn is None:
        return SkillResult(locale.say("unknown"))
    return fn(intent, locale)
