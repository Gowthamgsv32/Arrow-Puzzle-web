"""Which requests go to the AI agent versus the built-in commands."""

from personal_assistant.agent.agent import AgentReply
from personal_assistant.config import Settings
from personal_assistant.core import Brain
from personal_assistant.voice_loop import VoiceLoop


class Events:
    def __init__(self):
        self.heard, self.replies = [], []

    def on_status(self, *a):
        pass

    def on_level(self, *a):
        pass

    def on_heard(self, text, lang, accepted):
        self.heard.append((text, accepted))

    def on_reply(self, text, lang):
        self.replies.append(text)

    def on_quit(self):
        pass

    def on_step(self, text):
        pass

    def on_confirm(self, q):
        return False


class FakeAgent:
    def __init__(self):
        self.requests = []

    def run(self, text, lang):
        self.requests.append(text)
        return AgentReply("agent did it", "en")


def make_loop():
    loop = VoiceLoop(Settings(agent_enabled=True), Events(), voice=False)
    loop.brain = Brain(loop.settings)
    loop.agent = FakeAgent()
    return loop


def test_simple_spoken_commands_stay_local():
    loop = make_loop()
    loop._handle("what time is it", "en", typed=False)
    loop._handle("யூடியூப் திற", "ta", typed=False)
    assert loop.agent.requests == []
    assert len(loop.events.replies) == 2


def test_spoken_agent_task_needs_wake_word():
    loop = make_loop()
    loop._handle("summarize my open tab", "en", typed=False)  # background chatter
    assert loop.agent.requests == []
    assert loop.events.heard == [("summarize my open tab", False)]
    loop._handle("Assistant, summarize my open tab", "en", typed=False)
    assert loop.agent.requests == ["summarize my open tab"]


def test_tamil_wake_word():
    loop = make_loop()
    loop._handle("அசிஸ்டன்ட் chrome-ல் உள்ள tab-ஐ படி", "ta", typed=False)
    assert loop.agent.requests == ["chrome ல் உள்ள tab ஐ படி"]


def test_wake_word_with_simple_command_is_handled_locally():
    loop = make_loop()
    loop._handle("assistant what time is it", "en", typed=False)
    assert loop.agent.requests == []
    assert loop.events.replies[0].startswith("It is")


def test_typed_requests_go_to_agent_unless_simple():
    loop = make_loop()
    loop._handle("open the PR I was reviewing and copy the title", None, typed=True)
    loop._handle("open youtube", None, typed=True)
    assert loop.agent.requests == ["open the PR I was reviewing and copy the title"]
    assert loop.events.replies == ["agent did it", "Opening youtube."]


def test_open_unknown_target_goes_to_agent():
    loop = make_loop()
    loop._handle("assistant open my project in vs code", "en", typed=False)
    assert loop.agent.requests == ["open my project in vs code"]
