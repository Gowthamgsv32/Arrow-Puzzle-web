import pytest

from personal_assistant.agent.agent import AgentHooks, AgentReply
from personal_assistant.agent.hybrid import HybridAgent
from personal_assistant.agent.local import LOCAL_TOOLS, LocalAgent, to_ollama_tool
from personal_assistant.agent.tools import ToolBox
from personal_assistant.config import Settings


class FakeToolBox(ToolBox):
    def __init__(self):
        super().__init__(chrome=None, computer=None)
        self.calls = []

    def execute(self, call):
        self.calls.append((call.name, call.input))
        return "On branch main\nnothing to commit" if call.name == "run_command" else "OK"


class FakeOllama:
    def __init__(self, replies, models=("qwen2.5:7b",)):
        self.replies = list(replies)
        self.models = models
        self.requests = []

    def post(self, url, payload, timeout):
        assert url.endswith("/api/chat")
        self.requests.append(payload)
        return {"message": self.replies.pop(0), "done": True}

    def get(self, url, timeout):
        if self.models is None:
            raise OSError("connection refused")
        return {"models": [{"name": m} for m in self.models]}


def tool_call(name, **args):
    return {"role": "assistant", "content": "",
            "tool_calls": [{"function": {"name": name, "arguments": args}}]}


def make_local(server, hooks=None, toolbox=None):
    return LocalAgent(Settings(), hooks or AgentHooks(), toolbox or FakeToolBox(),
                      post=server.post, get=server.get)


def test_schema_conversion_makes_nullable_fields_optional():
    tool = to_ollama_tool({"name": "run_command", "description": "d", "input_schema": {
        "type": "object",
        "properties": {"command": {"type": "string"}, "cwd": {"type": ["string", "null"]}},
        "required": ["command", "cwd"], "additionalProperties": False}})
    params = tool["function"]["parameters"]
    assert params["required"] == ["command"]
    assert params["properties"]["cwd"] == {"type": "string"}
    names = {t["function"]["name"] for t in LOCAL_TOOLS}
    assert "chrome_run_javascript" not in names and "run_command" in names


def test_local_agent_runs_tools_and_answers():
    server = FakeOllama([
        tool_call("run_command", command="git status"),
        {"role": "assistant", "content": "Your repo is clean."},
    ])
    toolbox = FakeToolBox()
    steps = []
    reply = make_local(server, AgentHooks(on_step=steps.append), toolbox).run("git status", "en")
    assert reply.text == "Your repo is clean." and reply.unavailable is None
    assert toolbox.calls == [("run_command", {"command": "git status"})]
    assert steps == ["$ git status"]
    second = server.requests[1]
    assert second["model"] == "qwen2.5:7b" and second["stream"] is False
    assert second["messages"][0]["role"] == "system"
    assert second["messages"][-1] == {"role": "tool", "tool_name": "run_command",
                                      "content": "On branch main\nnothing to commit"}


def test_local_agent_asks_before_risky_commands():
    server = FakeOllama([
        tool_call("run_command", command="rm -rf build"),
        {"role": "assistant", "content": "Okay, I didn't delete it."},
    ])
    toolbox = FakeToolBox()
    asked = []
    make_local(server, AgentHooks(confirm=lambda q: asked.append(q) or False), toolbox).run(
        "delete build", "en")
    assert toolbox.calls == [] and len(asked) == 1
    assert server.requests[1]["messages"][-1]["content"] == "The user declined this action."


def test_local_agent_rejects_tools_it_does_not_have():
    server = FakeOllama([tool_call("left_click", coordinate=[1, 2]),
                         {"role": "assistant", "content": "I can't click."}])
    toolbox = FakeToolBox()
    make_local(server, toolbox=toolbox).run("click it", "en")
    assert toolbox.calls == []
    assert "unknown tool" in server.requests[1]["messages"][-1]["content"]


@pytest.mark.parametrize(
    ("models", "status"),
    [(("qwen2.5:7b",), "ready"), (("llama3.2:3b",), "no_model"), (None, "no_server")],
)
def test_status(models, status):
    assert make_local(FakeOllama([], models=models)).status() == status


class FakeClaude:
    def __init__(self, reply):
        self.reply, self.calls = reply, 0

    def run(self, request, language):
        self.calls += 1
        return self.reply


def test_hybrid_falls_back_to_local_when_offline():
    steps = []
    local = make_local(FakeOllama([{"role": "assistant", "content": "local answer"}]))
    claude = FakeClaude(AgentReply("I couldn't reach the AI service.", "en", "network"))
    agent = HybridAgent(Settings(), AgentHooks(on_step=steps.append), claude, local)
    assert agent.run("git status", "en").text == "local answer"
    assert "no internet" in steps[0]


def test_hybrid_uses_claude_when_it_works():
    local = make_local(FakeOllama([]))
    claude = FakeClaude(AgentReply("claude answer", "en"))
    agent = HybridAgent(Settings(), AgentHooks(), claude, local)
    assert agent.run("x", "en").text == "claude answer"
    assert local.messages == []


def test_hybrid_does_not_fall_back_for_refusals_or_other_errors():
    local = make_local(FakeOllama([]))
    claude = FakeClaude(AgentReply("Sorry, I can't help with that.", "en"))
    assert HybridAgent(Settings(), AgentHooks(), claude, local).run("x", "en").text.startswith(
        "Sorry")


def test_local_only_mode_tells_how_to_download_model():
    local = make_local(FakeOllama([], models=()))
    reply = HybridAgent(Settings(agent_brain="local"), AgentHooks(), None, local).run("x", "en")
    assert "ollama pull qwen2.5:7b" in reply.text


def test_real_http_path_against_fake_ollama_server():
    """Exercise the urllib code (no proxy, JSON) with a tiny HTTP server speaking Ollama's API."""
    import json
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    seen = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, obj):
            body = json.dumps(obj).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            self._send({"models": [{"name": "qwen2.5:7b"}]})

        def do_POST(self):
            seen.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            self._send({"message": {"role": "assistant", "content": "வணக்கம்!"}, "done": True})

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        settings = Settings(ollama_url=f"http://127.0.0.1:{server.server_port}")
        agent = LocalAgent(settings, AgentHooks(), FakeToolBox())
        assert agent.status() == "ready"
        reply = agent.run("வணக்கம்", "ta")
        assert reply.text == "வணக்கம்!" and reply.language == "ta"
        assert seen[0]["messages"][1]["content"] == "[Tamil] வணக்கம்"
    finally:
        server.shutdown()
