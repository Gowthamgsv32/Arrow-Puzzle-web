"""Chooses the brain for each task: Claude (online, most capable) and/or a local model.

PA_AGENT_BRAIN:
  auto   (default) Claude when it works; the local model takes over when Claude can't be
         reached, credit is used up, or there is no API key.
  claude Claude only.
  local  Local model only: free, private, offline (no screen/mouse control).
"""

from __future__ import annotations

import logging

from personal_assistant.agent.agent import AgentHooks, AgentReply

log = logging.getLogger(__name__)

FALLBACK_REASONS = {"network", "no_credit", "no_key", "busy"}
_REASON_TEXT = {
    "network": "no internet",
    "no_credit": "API credit used up",
    "no_key": "no API key",
    "busy": "service busy",
}


class HybridAgent:
    def __init__(self, settings, hooks: AgentHooks, claude=None, local=None):
        self.settings = settings
        self.hooks = hooks
        self.claude = claude
        self.local = local

    @property
    def description(self) -> str:
        parts = []
        if self.claude:
            parts.append(f"Claude ({self.settings.agent_model})")
        if self.local:
            role = "fallback" if self.claude else "only"
            parts.append(f"local {self.settings.local_model} ({role})")
        return " + ".join(parts)

    def run(self, request: str, language: str | None) -> AgentReply:
        if self.claude is None:
            return self._run_local(request, language)
        reply = self.claude.run(request, language)
        if reply.unavailable in FALLBACK_REASONS and self.local:
            status = self.local.status()
            if status == "ready":
                self.hooks.on_step(
                    f"Claude unavailable ({_REASON_TEXT[reply.unavailable]}) → "
                    f"local model {self.settings.local_model}"
                )
                return self.local.run(request, language)
            log.info("Local fallback not ready: %s", status)
        return reply

    def _run_local(self, request: str, language: str | None) -> AgentReply:
        status = self.local.status()
        if status == "no_model":
            return AgentReply(
                f"The local model isn't downloaded yet. Run: ollama pull {self.local.model}",
                "en", unavailable="error")
        if status == "no_server":
            return AgentReply("Ollama isn't running. Start the Ollama app, then try again.",
                              "en", unavailable="network")
        return self.local.run(request, language)


def build_agent(settings, hooks: AgentHooks):
    """Return a HybridAgent, or None if neither Claude nor a local model is set up."""
    claude = local = None
    if settings.agent_brain != "local" and settings.agent_enabled:
        from personal_assistant.agent.agent import DeveloperAgent

        claude = DeveloperAgent(settings, hooks)
    if settings.agent_brain != "claude":
        from personal_assistant.agent.local import LocalAgent

        candidate = LocalAgent(settings, hooks, toolbox=claude.toolbox if claude else None)
        # In auto mode, only keep the local brain if Ollama is installed and running.
        if settings.agent_brain == "local" or candidate.status() != "no_server":
            local = candidate
    if claude is None and local is None:
        return None
    return HybridAgent(settings, hooks, claude, local)
