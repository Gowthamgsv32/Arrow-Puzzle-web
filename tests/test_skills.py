from personal_assistant import skills
from personal_assistant.i18n import load_locales
from personal_assistant.intents import IntentMatcher


def run(text):
    locales = load_locales(["en", "ta"])
    intent = IntentMatcher(locales).match(text)
    return skills.handle(intent, locales[intent.language or "en"])


def test_exit_skill():
    assert run("bye").exit
    assert run("நிறுத்து").exit


def test_time_reply_localized():
    assert run("what time is it").reply.startswith("It is")
    assert run("மணி என்ன").reply.startswith("இப்போது நேரம்")


def test_open_without_target_asks():
    assert run("open").reply == "What should I open?"
