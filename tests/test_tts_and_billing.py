from types import SimpleNamespace

import anthropic
import httpx2
import pytest
from anthropic import DefaultHttpxClient

from personal_assistant.agent.agent import DeveloperAgent, is_billing_error
from personal_assistant.audio.tts import OfflineVoice, TextToSpeech, pick_voice
from personal_assistant.config import Settings

# ---- offline voice ---------------------------------------------------------------------

ZIRA = SimpleNamespace(id="HKEY\\TTS_MS_EN-US_ZIRA_11.0", name="Microsoft Zira Desktop",
                       languages=[])
VALLUVAR = SimpleNamespace(id="ta-IN-Valluvar", name="Microsoft Valluvar", languages=["ta-IN"])
ESPEAK_EN = SimpleNamespace(id="gmw/en", name="English", languages=[b"\x05en-gb"])


class FakeEngine:
    def __init__(self, voices):
        self.voices, self.said, self.voice = voices, [], None

    def getProperty(self, name):
        return self.voices

    def setProperty(self, name, value):
        self.voice = value

    def say(self, text):
        self.said.append(text)

    def runAndWait(self):
        pass

    def stop(self):
        pass


def test_pick_voice():
    assert pick_voice([VALLUVAR, ZIRA], "en") is ZIRA
    assert pick_voice([ZIRA, VALLUVAR], "ta") is VALLUVAR
    assert pick_voice([ZIRA], "ta") is None
    assert pick_voice([ESPEAK_EN], "en") is ESPEAK_EN
    caribbean = SimpleNamespace(id="gmw/en-029", name="English (Caribbean)", languages=[])
    us = SimpleNamespace(id="gmw/en-US", name="English (America)", languages=[])
    assert pick_voice([caribbean, us], "en") is us


def test_falls_back_to_offline_voice_and_remembers():
    engine = FakeEngine([ZIRA])
    tts = TextToSpeech(OfflineVoice(lambda: engine))
    calls = []

    def no_internet(text, voice):
        calls.append(text)
        raise OSError("Cannot connect to host speech.platform.bing.com")

    tts._speak_online = no_internet
    assert tts.speak("It is 9 AM.", "en-IN-NeerjaNeural", "en") == "offline"
    assert tts.speak("Goodbye!", "en-IN-NeerjaNeural", "en") == "offline"
    assert calls == ["It is 9 AM."]  # second reply didn't wait on the network again
    assert engine.said == ["It is 9 AM.", "Goodbye!"] and engine.voice == ZIRA.id


def test_tamil_without_tamil_voice_shows_text_only():
    engine = FakeEngine([ZIRA])
    assert OfflineVoice(lambda: engine).speak("வணக்கம்", "ta") is False
    assert engine.said == []  # never reads Tamil with an English voice


def test_missing_engine_does_not_crash():
    def broken():
        raise RuntimeError("eSpeak not installed")

    assert OfflineVoice(broken).speak("hi", "en") is False


# ---- billing errors --------------------------------------------------------------------

def _agent(status, error_type, message):
    def handler(request):
        return httpx2.Response(status, json={"type": "error",
                                             "error": {"type": error_type, "message": message}})

    client = anthropic.Anthropic(api_key="k", max_retries=0, http_client=DefaultHttpxClient(
        transport=httpx2.MockTransport(handler)))
    return DeveloperAgent(Settings(agent_enabled=True), client=client)


@pytest.mark.parametrize(
    ("status", "etype", "message", "expected"),
    [
        (400, "invalid_request_error",
         "Your credit balance is too low to access the Anthropic API.", "credit"),
        (402, "billing_error", "Payment required", "credit"),
        (429, "rate_limit_error", "You have reached your specified API usage limits.", "credit"),
        (429, "rate_limit_error", "Number of requests has exceeded your rate limit.", "busy"),
        (529, "overloaded_error", "Overloaded", "busy"),
        (401, "authentication_error", "invalid x-api-key", "key"),
    ],
)
def test_api_errors_are_explained(status, etype, message, expected):
    reply = _agent(status, etype, message).run("hello", "en").text
    words = {"credit": "credit is used up", "busy": "busy", "key": "ANTHROPIC_API_KEY"}
    assert words[expected] in reply


def test_out_of_credit_in_tamil():
    reply = _agent(400, "invalid_request_error", "Your credit balance is too low").run("x", "ta")
    assert "கிரெடிட்" in reply.text


def test_is_billing_error_ignores_other_errors():
    assert not is_billing_error(ValueError("credit balance"))


def test_online_voice_is_tried_first_right_after_boot(monkeypatch):
    monkeypatch.setattr("personal_assistant.audio.tts.time.monotonic", lambda: 5.0)
    tts = TextToSpeech(OfflineVoice(lambda: FakeEngine([ZIRA])))
    spoken = []
    tts._speak_online = lambda text, voice: spoken.append(text)
    assert tts.speak("hi", "en-IN-NeerjaNeural", "en") == "online"
    assert spoken == ["hi"]
