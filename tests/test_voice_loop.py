import threading
import time

from personal_assistant.config import Settings
from personal_assistant.core import Brain
from personal_assistant.voice_loop import VoiceLoop, strip_wake_word


class Recorder:
    def __init__(self):
        self.heard, self.replies, self.states, self.quit = [], [], [], False

    def on_status(self, state, detail=""):
        self.states.append(state)

    def on_level(self, level):
        pass

    def on_heard(self, text, language, accepted):
        self.heard.append((text, accepted))

    def on_reply(self, text, language):
        self.replies.append((text, language))

    def on_quit(self):
        self.quit = True


def test_strip_wake_word():
    assert strip_wake_word("Open YouTube", []) == "Open YouTube"
    assert strip_wake_word("Assistant, open YouTube", ["assistant"]) == "open youtube"
    assert strip_wake_word("open YouTube", ["assistant"]) is None
    assert strip_wake_word("உதவியாளர் யூடியூப் திற", ["assistant", "உதவியாளர்"]) == "யூடியூப் திற"


def run_loop(loop, inputs):
    events = loop.events
    t = threading.Thread(target=loop.run, daemon=True)
    t.start()
    for text in inputs:
        loop.submit_text(text)
    deadline = time.time() + 3
    while t.is_alive() and len(events.replies) < len(inputs) and time.time() < deadline:
        time.sleep(0.02)
    time.sleep(0.1)
    loop.stop()
    t.join(2)


def test_typed_commands_get_replies_in_their_language():
    ev = Recorder()
    run_loop(VoiceLoop(Settings(), ev, voice=False), ["hello", "மணி என்ன"])
    assert [lang for _, lang in ev.replies] == ["en", "ta"]
    assert ev.replies[1][0].startswith("இப்போது நேரம்")


def test_spoken_chatter_is_ignored():
    ev = Recorder()
    loop = VoiceLoop(Settings(), ev, voice=False)
    loop.brain = Brain(Settings())
    loop._handle("so I told him about the weekend", "en", typed=False)
    assert ev.heard == [("so I told him about the weekend", False)]
    assert ev.replies == []


def test_goodbye_pauses_listening_in_gui_mode():
    ev = Recorder()
    loop = VoiceLoop(Settings(), ev, voice=False)
    run_loop(loop, ["goodbye"])
    assert "muted" in ev.states
    assert not ev.quit


def test_goodbye_quits_in_cli_mode():
    ev = Recorder()
    run_loop(VoiceLoop(Settings(), ev, voice=False, exit_quits=True), ["bye"])
    assert ev.quit
