"""A fully local "brain" for the agent: an open-weight model served by Ollama
(https://ollama.com) on this computer. Free, private and works offline.

It uses the same tools and approval rules as the Claude agent, except screen/mouse
control (local models on a laptop CPU are too slow and too weak at reading screenshots).
"""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from collections.abc import Callable

from personal_assistant.agent.agent import (
    IDLE_RESET_SECONDS,
    LANG_NAMES,
    AgentHooks,
    AgentReply,
    build_system_prompt,
    reply_language,
)
from personal_assistant.agent.tools import CUSTOM_TOOLS, ToolBox, ToolCall, approval_for, describe

log = logging.getLogger(__name__)

# Fewer tools = better choices from a small model.
LOCAL_TOOL_NAMES = (
    "run_command", "open_terminal", "chrome_list_tabs", "chrome_open_tab", "chrome_switch_tab",
    "chrome_close_tab", "chrome_read_tab", "clipboard_read", "clipboard_write", "read_file",
    "write_file", "list_directory", "open",
)
MAX_RESULT_CHARS = 6_000  # keep tool output inside a small context window
MAX_HISTORY_MESSAGES = 40

_NO_PROXY = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def to_ollama_tool(tool: dict) -> dict:
    """Anthropic-style strict schema -> Ollama/JSON-schema function (nullable -> optional)."""
    schema = tool["input_schema"]
    props, required = {}, []
    for name, spec in schema["properties"].items():
        spec = dict(spec)
        if isinstance(spec.get("type"), list):
            spec["type"] = next(t for t in spec["type"] if t != "null")
        else:
            required.append(name)
        props[name] = spec
    return {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": {"type": "object", "properties": props, "required": required},
        },
    }


LOCAL_TOOLS = [to_ollama_tool(t) for t in CUSTOM_TOOLS if t["name"] in LOCAL_TOOL_NAMES]


def _http_post(url: str, payload: dict, timeout: float) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with _NO_PROXY.open(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _http_get(url: str, timeout: float) -> dict:
    with _NO_PROXY.open(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


class LocalAgent:
    def __init__(self, settings, hooks: AgentHooks | None = None,
                 toolbox: ToolBox | None = None,
                 post: Callable[[str, dict, float], dict] = _http_post,
                 get: Callable[[str, float], dict] = _http_get):
        self.settings = settings
        self.hooks = hooks or AgentHooks()
        self.toolbox = toolbox or ToolBox()
        self._post, self._get = post, get
        self.url = settings.ollama_url.rstrip("/")
        self.model = settings.local_model
        self.system_prompt = build_system_prompt() + (
            "\n\nYou are running as a small local model without screen or mouse control. "
            "If a task needs clicking or seeing the screen, say that it needs the online "
            "assistant. Always use a tool instead of guessing file contents or command output."
        )
        self.messages: list[dict] = []
        self._last_used = 0.0

    # ---- availability ------------------------------------------------------------------
    def status(self) -> str:
        """"ready", "no_server" (Ollama not running) or "no_model" (model not pulled)."""
        try:
            tags = self._get(f"{self.url}/api/tags", 2)
        except (urllib.error.URLError, OSError, ValueError):
            return "no_server"
        names = {m.get("name", "") for m in tags.get("models", [])}
        wanted = self.model if ":" in self.model else f"{self.model}:latest"
        return "ready" if wanted in names or self.model in names else "no_model"

    def available(self) -> bool:
        return self.status() == "ready"

    def reset(self) -> None:
        self.messages = []

    # ---- loop --------------------------------------------------------------------------
    def run(self, request: str, language: str | None) -> AgentReply:
        lang = language or self.settings.default_language
        if (time.monotonic() - self._last_used > IDLE_RESET_SECONDS
                or len(self.messages) > MAX_HISTORY_MESSAGES):
            self.reset()
        self._last_used = time.monotonic()
        self.messages.append(
            {"role": "user", "content": f"[{LANG_NAMES.get(lang, lang)}] {request}"}
        )
        for _ in range(min(self.settings.agent_max_steps, 12)):
            if self.hooks.is_cancelled():
                return AgentReply("Okay, I stopped." if lang == "en" else "சரி, நிறுத்திவிட்டேன்.",
                                  lang)
            try:
                response = self._post(f"{self.url}/api/chat", {
                    "model": self.model,
                    "messages": [{"role": "system", "content": self.system_prompt},
                                 *self.messages],
                    "tools": LOCAL_TOOLS,
                    "stream": False,
                    "keep_alive": "30m",  # stay loaded: reloading is slow on a CPU
                    "options": {"num_ctx": 8192, "temperature": 0.2},
                }, 600)
            except (urllib.error.URLError, OSError, ValueError) as exc:
                log.warning("Local model failed: %s", exc)
                return AgentReply(_LOCAL_DOWN.get(lang, _LOCAL_DOWN["en"]), lang,
                                  unavailable="network")
            message = response.get("message", {})
            calls = message.get("tool_calls") or []
            self.messages.append({"role": "assistant", "content": message.get("content", ""),
                                  **({"tool_calls": calls} if calls else {})})
            if not calls:
                text = (message.get("content") or "").strip()
                return AgentReply(text or "Done.", reply_language(text, lang))
            for i, call in enumerate(calls):
                fn = call.get("function", {})
                args = fn.get("arguments") or {}
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except ValueError:
                        args = {}
                result = self._run_tool(ToolCall(f"local_{i}", fn.get("name", ""), args))
                self.messages.append({"role": "tool", "tool_name": fn.get("name", ""),
                                      "content": result})
        return AgentReply("This is taking too many steps, so I stopped.", lang)

    def _run_tool(self, call: ToolCall) -> str:
        if call.name not in LOCAL_TOOL_NAMES:
            return f"Error: unknown tool {call.name}"
        approval = approval_for(call, self.settings.auto_approve)
        self.hooks.on_step(describe(call))
        if approval and not self.hooks.confirm(approval.question):
            return "The user declined this action."
        try:
            result = self.toolbox.execute(call)
        except Exception as exc:  # noqa: BLE001 - errors go back to the model
            return f"Error: {exc}"
        text = result if isinstance(result, str) else json.dumps(result)
        if len(text) > MAX_RESULT_CHARS:
            text = text[:MAX_RESULT_CHARS] + "\n[…truncated]"
        return text


_LOCAL_DOWN = {
    "en": "The local AI model isn't responding. Make sure Ollama is running.",
    "ta": "உள்ளூர் AI மாடல் பதிலளிக்கவில்லை. Ollama இயங்குகிறதா என்று பார்க்கவும்.",
}
