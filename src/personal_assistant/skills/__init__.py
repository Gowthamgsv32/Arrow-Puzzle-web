"""Skills turn a matched intent into an action and a spoken reply.

To add a skill: write a function ``(intent, locale) -> SkillResult`` and register
it with ``@skill("intent_name")``. Add the trigger phrases to each locale file.
"""

from personal_assistant.skills import builtin  # noqa: F401  (registers built-in skills)
from personal_assistant.skills.base import REGISTRY, SkillResult, handle, skill

__all__ = ["REGISTRY", "SkillResult", "handle", "skill"]
