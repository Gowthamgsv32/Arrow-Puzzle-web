"""Tool definitions sent to Claude, plus execution and the "ask before risky actions" rules."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from personal_assistant.agent import system
from personal_assistant.agent.chrome import Chrome
from personal_assistant.agent.computer import TOOLSET_NAME, ActionError, ComputerController


def _schema(props: dict, nullable: tuple[str, ...] = ()) -> dict:
    """Strict JSON schema: every property listed in `required`; optional ones are nullable."""
    properties = {}
    for name, spec in props.items():
        spec = dict(spec)
        if name in nullable:
            spec["type"] = [spec["type"], "null"]
        properties[name] = spec
    return {
        "type": "object",
        "properties": properties,
        "required": list(props),
        "additionalProperties": False,
    }


S = {"type": "string"}
I = {"type": "integer"}

CUSTOM_TOOLS: list[dict] = [
    {
        "name": "run_command",
        "description": (
            "Run a shell command on the user's computer and return its exit code and output "
            "(stdout+stderr, truncated to 20k chars). Non-interactive: never run commands that "
            "wait for input or never exit (servers, watchers) - use open_terminal for those. "
            "Commands that change things (installs, deletes, git commit/push, writes) are shown "
            "to the user for approval first."
        ),
        "input_schema": _schema(
            {"command": S, "cwd": S, "timeout_seconds": I}, nullable=("cwd", "timeout_seconds")
        ),
    },
    {
        "name": "open_terminal",
        "description": "Open a visible terminal window for the user, optionally in a folder and "
                       "running a command (for dev servers, watchers, interactive tools).",
        "input_schema": _schema({"cwd": S, "command": S}, nullable=("cwd", "command")),
    },
    {
        "name": "chrome_list_tabs",
        "description": "List open Google Chrome tabs (id, title, url). The first one is the "
                       "tab the user used most recently. Starts Chrome if it is not running.",
        "input_schema": _schema({}),
    },
    {
        "name": "chrome_open_tab",
        "description": "Open a URL in a new Chrome tab and focus it.",
        "input_schema": _schema({"url": S}),
    },
    {
        "name": "chrome_switch_tab",
        "description": "Bring a Chrome tab to the front.",
        "input_schema": _schema({"tab_id": S}),
    },
    {
        "name": "chrome_close_tab",
        "description": "Close a Chrome tab.",
        "input_schema": _schema({"tab_id": S}),
    },
    {
        "name": "chrome_navigate",
        "description": "Load a URL in an existing tab (null tab_id = most recent tab).",
        "input_schema": _schema({"tab_id": S, "url": S}, nullable=("tab_id",)),
    },
    {
        "name": "chrome_read_tab",
        "description": "Return the title, URL and visible text of a Chrome tab (null tab_id = "
                       "most recent tab). Use this instead of screenshots to read pages.",
        "input_schema": _schema({"tab_id": S}, nullable=("tab_id",)),
    },
    {
        "name": "chrome_run_javascript",
        "description": "Evaluate JavaScript in a Chrome tab and return the JSON result "
                       "(e.g. click an element by selector, extract links, fill a form). "
                       "Requires user approval.",
        "input_schema": _schema({"tab_id": S, "code": S}, nullable=("tab_id",)),
    },
    {
        "name": "clipboard_read",
        "description": "Return the text currently on the clipboard.",
        "input_schema": _schema({}),
    },
    {
        "name": "clipboard_write",
        "description": "Put text on the clipboard (the user can then paste it anywhere).",
        "input_schema": _schema({"text": S}),
    },
    {
        "name": "read_file",
        "description": "Read a UTF-8 text file (truncated at 60k characters).",
        "input_schema": _schema({"path": S}),
    },
    {
        "name": "write_file",
        "description": "Create or overwrite a text file. Requires user approval.",
        "input_schema": _schema({"path": S, "content": S}),
    },
    {
        "name": "list_directory",
        "description": "List files in a folder (null = the user's workspace folder).",
        "input_schema": _schema({"path": S}, nullable=("path",)),
    },
    {
        "name": "open",
        "description": "Open a URL, file, folder or application by name with the OS default "
                       "handler (e.g. 'code', 'notepad', 'C:/projects', 'https://github.com').",
        "input_schema": _schema({"target": S}),
    },
]
for _tool in CUSTOM_TOOLS:
    _tool["strict"] = True

COMPUTER_TOOLSET = {"type": "computer_toolset_20260801"}

# Read-only commands that run without asking. Anything chained/redirected still asks.
_SAFE_COMMAND = re.compile(
    r"^\s*(git\s+(status|log|diff|show|branch|remote\s+-v|rev-parse|blame)|ls|dir|pwd|echo|"
    r"cat|type|head|tail|wc|where|which|whoami|date|tree|"
    r"Get-ChildItem|Get-Content|Get-Location|Get-Process|"
    r"python3?\s+--version|node\s+(-v|--version)|npm\s+(-v|--version|ls|outdated)|"
    r"pip3?\s+(list|show|--version|freeze))\b",
    re.IGNORECASE,
)
_CHAINING = re.compile(r"[;&|<>`]|\$\(")


def command_is_safe(command: str) -> bool:
    return bool(_SAFE_COMMAND.match(command)) and not _CHAINING.search(command)


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict
    toolset: str | None = None

    @property
    def is_computer(self) -> bool:
        return self.toolset == TOOLSET_NAME


@dataclass
class Approval:
    """What to ask the user before a call runs (None = run without asking)."""

    question: str


def approval_for(call: ToolCall, auto_approve: bool) -> Approval | None:
    if auto_approve:
        return None
    args = call.input
    if call.name == "run_command" and not command_is_safe(args.get("command", "")):
        where = f"\nin {args['cwd']}" if args.get("cwd") else ""
        return Approval(f"Run this command?\n\n{args.get('command')}{where}")
    if call.name == "write_file":
        preview = (args.get("content") or "")[:400]
        return Approval(f"Write file {args.get('path')}?\n\n{preview}")
    if call.name == "chrome_run_javascript":
        return Approval(f"Run JavaScript in Chrome?\n\n{(args.get('code') or '')[:600]}")
    return None


def describe(call: ToolCall) -> str:
    """One-line description of a call for the activity feed."""
    a = call.input
    if call.is_computer:
        if "coordinate" in a:
            return f"{call.name.replace('_', ' ')} at {tuple(a['coordinate'])}"
        if call.name == "type":
            text = a.get("text", "")
            return f"type “{text[:40]}{'…' if len(text) > 40 else ''}”"
        if call.name == "key":
            return f"press {a.get('text')}"
        return call.name.replace("_", " ")
    if call.name == "run_command":
        return f"$ {a.get('command')}"
    for key in ("url", "path", "target", "tab_id", "command"):
        if a.get(key):
            return f"{call.name.replace('_', ' ')}: {a[key]}"
    return call.name.replace("_", " ")


@dataclass
class ToolBox:
    chrome: Chrome = field(default_factory=Chrome)
    computer: ComputerController | None = None

    def execute(self, call: ToolCall):
        """Return tool_result content (str or list of blocks). Raises on failure."""
        if call.is_computer:
            if self.computer is None:
                self.computer = ComputerController()
            return self.computer.execute(call.name, call.input)
        a = call.input
        c = self.chrome
        match call.name:
            case "run_command":
                return system.run_command(a["command"], a.get("cwd"),
                                          a.get("timeout_seconds") or 120)
            case "open_terminal":
                return system.open_terminal(a.get("cwd"), a.get("command"))
            case "chrome_list_tabs":
                return json.dumps(c.tabs(), ensure_ascii=False, indent=1)
            case "chrome_open_tab":
                return json.dumps(c.open(a["url"]))
            case "chrome_switch_tab":
                c.activate(a["tab_id"])
                return "OK"
            case "chrome_close_tab":
                c.close(a["tab_id"])
                return "OK"
            case "chrome_navigate":
                c.navigate(a.get("tab_id"), a["url"])
                return "OK"
            case "chrome_read_tab":
                return c.read(a.get("tab_id"))
            case "chrome_run_javascript":
                return json.dumps(c.evaluate(a.get("tab_id"), a["code"]), ensure_ascii=False,
                                  default=str)[:20_000]
            case "clipboard_read":
                return system.clipboard_get()
            case "clipboard_write":
                return system.clipboard_set(a["text"])
            case "read_file":
                return system.read_file(a["path"])
            case "write_file":
                return system.write_file(a["path"], a["content"])
            case "list_directory":
                return system.list_directory(a.get("path"))
            case "open":
                return system.open_target(a["target"])
        raise ActionError(f"Unknown tool: {call.name}")
