"""Agent loop tests through the real Anthropic SDK with a mocked HTTP transport."""

import json

import anthropic
import httpx2
import pytest
from anthropic import DefaultHttpxClient

from personal_assistant.agent.agent import NOT_EXECUTED, AgentHooks, DeveloperAgent
from personal_assistant.agent.computer import ActionError, parse_keys, scale_factor
from personal_assistant.agent.tools import CUSTOM_TOOLS, ToolBox, command_is_safe
from personal_assistant.config import Settings


def message(content, stop_reason="tool_use"):
    return {
        "id": "msg_test",
        "type": "message",
        "role": "assistant",
        "model": "claude-opus-5-5",
        "content": content,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {"input_tokens": 10, "output_tokens": 5},
    }


def tool_use(id_, name, input_, toolset=None):
    block = {"type": "tool_use", "id": id_, "name": name, "input": input_}
    if toolset:
        block["toolset_name"] = toolset
    return block


class Server:
    """Replays scripted responses and records every request body."""

    def __init__(self, responses, status=200):
        self.responses = list(responses)
        self.requests = []
        self.status = status

    def __call__(self, request):
        self.requests.append(
            {"body": json.loads(request.content), "headers": dict(request.headers)}
        )
        if self.status != 200:
            return httpx2.Response(self.status, json={
                "type": "error", "error": {"type": "authentication_error", "message": "bad key"}})
        return httpx2.Response(200, json=self.responses.pop(0))


class FakeToolBox(ToolBox):
    def __init__(self, fail=()):
        super().__init__(chrome=None, computer=None)
        self.calls = []
        self.fail = set(fail)

    def execute(self, call):
        self.calls.append((call.name, call.input))
        if call.name in self.fail:
            raise ActionError(f"{call.name} broke")
        if call.name == "screenshot":
            return [{"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                                  "data": "iVBORw0KGgo="}}]
        return "OK"


def make_agent(server, hooks=None, toolbox=None):
    client = anthropic.Anthropic(
        api_key="test-key",
        http_client=DefaultHttpxClient(transport=httpx2.MockTransport(server)),
        max_retries=0,
    )
    return DeveloperAgent(Settings(agent_enabled=True), hooks or AgentHooks(), client=client,
                          toolbox=toolbox or FakeToolBox())


def test_full_turn_with_computer_and_terminal_tools():
    server = Server([
        message([
            {"type": "text", "text": "Checking the screen."},
            tool_use("t1", "screenshot", {}, "computer"),
            tool_use("t2", "left_click", {"coordinate": [100, 200]}, "computer"),
            tool_use("t3", "run_command", {"command": "git status", "cwd": None,
                                           "timeout_seconds": None}),
        ]),
        message([tool_use("t4", "run_command", {"command": "rm -rf build", "cwd": None,
                                                "timeout_seconds": None})]),
        message([{"type": "text", "text": "முடிந்தது, build கோப்புறையை நீக்கவில்லை."}],
                stop_reason="end_turn"),
    ])
    asked, steps = [], []
    hooks = AgentHooks(on_step=steps.append,
                       confirm=lambda q: asked.append(q) or False)
    toolbox = FakeToolBox()
    agent = make_agent(server, hooks, toolbox)

    reply = agent.run("build folder-ஐ நீக்கு", "ta")

    assert reply.language == "ta"
    assert reply.text.startswith("முடிந்தது")
    # safe command ran without asking; rm asked and was declined (never executed)
    assert [c[0] for c in toolbox.calls] == ["screenshot", "left_click", "run_command"]
    assert len(asked) == 1 and "rm -rf build" in asked[0]
    assert "$ git status" in steps

    first = server.requests[0]["body"]
    assert first["model"] == "claude-opus-5-5"
    assert first["thinking"] == {"type": "adaptive"}
    assert first["output_config"] == {"effort": "medium"}
    assert first["fallbacks"] == "default"
    assert {"type": "computer_toolset_20260801"} in first["tools"]
    assert all(t.get("strict") for t in first["tools"] if "name" in t)
    assert first["messages"][0]["content"] == "[Tamil] build folder-ஐ நீக்கு"
    assert "server-side-fallback-2026-07-01" in server.requests[0]["headers"]["anthropic-beta"]

    results = server.requests[1]["body"]["messages"][-1]["content"]
    assert [r["tool_use_id"] for r in results] == ["t1", "t2", "t3"]
    assert results[0]["toolset_name"] == "computer" and results[0]["content"][0]["type"] == "image"
    assert results[1]["toolset_name"] == "computer"
    assert "toolset_name" not in results[2]

    declined = server.requests[2]["body"]["messages"][-1]["content"][0]
    assert declined["is_error"] is True and "declined" in declined["content"]


def test_computer_failure_skips_rest_of_batch_but_not_other_tools():
    server = Server([
        message([
            tool_use("a", "left_click", {"coordinate": [1, 1]}, "computer"),
            tool_use("b", "type", {"text": "hi"}, "computer"),
            tool_use("c", "clipboard_read", {}),
        ]),
        message([{"type": "text", "text": "Could not click."}], stop_reason="end_turn"),
    ])
    toolbox = FakeToolBox(fail={"left_click"})
    make_agent(server, toolbox=toolbox).run("click it", "en")
    results = server.requests[1]["body"]["messages"][-1]["content"]
    assert results[0]["is_error"] and "broke" in results[0]["content"]
    assert results[1] == {"type": "tool_result", "tool_use_id": "b", "toolset_name": "computer",
                          "content": NOT_EXECUTED, "is_error": True}
    assert results[2]["content"] == "OK"
    assert [c[0] for c in toolbox.calls] == ["left_click", "clipboard_read"]


def test_cancel_stops_before_next_request():
    cancelled = {"v": False}

    def step(_):
        cancelled["v"] = True

    server = Server([message([tool_use("a", "screenshot", {}, "computer")])])
    agent = make_agent(server, AgentHooks(on_step=step, is_cancelled=lambda: cancelled["v"]))
    reply = agent.run("do things", "en")
    assert reply.text == "Okay, I stopped."
    assert len(server.requests) == 1


def test_bad_api_key_gives_spoken_hint():
    reply = make_agent(Server([], status=401)).run("hello", "ta")
    assert "ANTHROPIC_API_KEY" in reply.text and reply.language == "ta"


def test_history_is_kept_between_requests():
    server = Server([
        message([{"type": "text", "text": "One."}], stop_reason="end_turn"),
        message([{"type": "text", "text": "Two."}], stop_reason="end_turn"),
    ])
    agent = make_agent(server)
    agent.run("first", "en")
    agent.run("second", "en")
    roles = [m["role"] for m in server.requests[1]["body"]["messages"]]
    assert roles == ["user", "assistant", "user"]


@pytest.mark.parametrize(
    ("command", "safe"),
    [
        ("git status", True),
        ("git log --oneline -5", True),
        ("Get-ChildItem", True),
        ("ls -la", True),
        ("git push --force", False),
        ("rm -rf /", False),
        ("ls; rm -rf ~", False),
        ("cat secrets > /tmp/x", False),
        ("echo $(whoami)", False),
        ("npm install", False),
    ],
)
def test_command_safety(command, safe):
    assert command_is_safe(command) is safe


def test_strict_schemas_are_valid():
    for tool in CUSTOM_TOOLS:
        schema = tool["input_schema"]
        assert schema["additionalProperties"] is False
        assert set(schema["required"]) == set(schema["properties"])


def test_key_parsing():
    assert parse_keys("ctrl+shift+Tab") == ["ctrl", "shift", "tab"]
    assert parse_keys("Return") == ["enter"]
    assert parse_keys("alt+F4") == ["alt", "f4"]
    assert parse_keys("ctrl++") == ["ctrl", "+"]
    assert parse_keys("Page_Down") == ["pagedown"]


def test_screenshot_scaling_fits_limits():
    for w, h in [(1920, 1080), (2560, 1440), (3840, 2160), (1280, 720)]:
        s = scale_factor(w, h)
        assert max(w, h) * s <= 1568 + 1
        assert (w * s) * (h * s) <= 1_150_000 * 1.01
    assert scale_factor(1024, 768) == 1.0
