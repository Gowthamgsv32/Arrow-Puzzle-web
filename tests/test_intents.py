import pytest

from personal_assistant.i18n import available_languages, load_locales
from personal_assistant.intents import IntentMatcher, normalize


@pytest.fixture(scope="module")
def matcher():
    return IntentMatcher(load_locales(["en", "ta"]))


@pytest.mark.parametrize(
    ("text", "intent", "argument"),
    [
        ("Hello!", "greet", ""),
        ("What time is it?", "time", ""),
        ("Open YouTube", "open", "youtube"),
        ("search for weather in Chennai", "search", "weather in chennai"),
        ("goodbye", "exit", ""),
        ("வணக்கம்", "greet", ""),
        ("மணி என்ன?", "time", ""),
        ("யூடியூப் திற", "open", "யூடியூப்"),
        ("சென்னை வானிலை தேடு", "search", "சென்னை வானிலை"),
        ("நிறுத்து", "exit", ""),
    ],
)
def test_match(matcher, text, intent, argument):
    result = matcher.match(text)
    assert result.name == intent
    assert result.argument == argument


def test_detected_language_is_kept(matcher):
    assert matcher.match("Open YouTube", "en").language == "en"
    assert matcher.match("யூடியூப் திற").language == "ta"


def test_unknown(matcher):
    assert matcher.match("blah blah").name == "unknown"


def test_normalize_keeps_tamil_marks():
    assert normalize("  வணக்கம்!! ") == "வணக்கம்"


def test_all_locales_define_same_keys():
    locales = load_locales(available_languages())
    en = locales["en"]
    for code, loc in locales.items():
        assert set(loc.intents) == set(en.intents), code
        assert set(loc.responses) == set(en.responses), code
        assert loc.tts_voice, code
