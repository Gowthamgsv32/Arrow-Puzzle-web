"""Built-in skills: greeting, time, date, open apps/sites, web search, exit."""

from __future__ import annotations

import datetime as dt
import os
import platform
import shutil
import subprocess
import urllib.parse
import webbrowser

from personal_assistant.i18n import Locale
from personal_assistant.intents import Intent
from personal_assistant.skills.base import SkillResult, skill

# Spoken names (any language) -> URL. Extend freely.
WEBSITES = {
    "youtube": "https://www.youtube.com",
    "யூடியூப்": "https://www.youtube.com",
    "google": "https://www.google.com",
    "கூகுள்": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "ஜிமெயில்": "https://mail.google.com",
    "whatsapp": "https://web.whatsapp.com",
    "வாட்ஸ்அப்": "https://web.whatsapp.com",
}

# Spoken names -> executable / app name per OS.
APPS = {
    "calculator": {"Windows": "calc", "Darwin": "Calculator", "Linux": "gnome-calculator"},
    "கால்குலேட்டர்": {"Windows": "calc", "Darwin": "Calculator", "Linux": "gnome-calculator"},
    "notepad": {"Windows": "notepad", "Darwin": "TextEdit", "Linux": "gedit"},
    "நோட்பேட்": {"Windows": "notepad", "Darwin": "TextEdit", "Linux": "gedit"},
}

TAMIL_WEEKDAYS = ["திங்கள்", "செவ்வாய்", "புதன்", "வியாழன்", "வெள்ளி", "சனி", "ஞாயிறு"]


@skill("greet")
def greet(intent: Intent, locale: Locale) -> SkillResult:
    return SkillResult(locale.say("greet"))


@skill("time")
def tell_time(intent: Intent, locale: Locale) -> SkillResult:
    return SkillResult(locale.say("time", time=dt.datetime.now().strftime("%I:%M %p").lstrip("0")))


@skill("date")
def tell_date(intent: Intent, locale: Locale) -> SkillResult:
    today = dt.date.today()
    if locale.code == "ta":
        text = f"{TAMIL_WEEKDAYS[today.weekday()]}, {today.day}/{today.month}/{today.year}"
    else:
        text = today.strftime("%A, %d %B %Y")
    return SkillResult(locale.say("date", date=text))


@skill("open")
def open_target(intent: Intent, locale: Locale) -> SkillResult:
    target = intent.argument.strip()
    if not target:
        return SkillResult(locale.say("open_missing"))
    if target in WEBSITES:
        webbrowser.open(WEBSITES[target])
        return SkillResult(locale.say("opening", target=target))
    if _launch_app(APPS.get(target, {}).get(platform.system(), target)):
        return SkillResult(locale.say("opening", target=target))
    return SkillResult(locale.say("open_failed", target=target))


@skill("search")
def search_web(intent: Intent, locale: Locale) -> SkillResult:
    query = intent.argument.strip()
    if not query:
        return SkillResult(locale.say("search_missing"))
    webbrowser.open("https://www.google.com/search?q=" + urllib.parse.quote_plus(query))
    return SkillResult(locale.say("searching", query=query))


@skill("exit")
def exit_assistant(intent: Intent, locale: Locale) -> SkillResult:
    return SkillResult(locale.say("exit"), exit=True)


def _launch_app(name: str) -> bool:
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(name)  # type: ignore[attr-defined]
            return True
        if system == "Darwin":
            return subprocess.run(["open", "-a", name], check=False).returncode == 0
        exe = shutil.which(name)
        if exe:
            subprocess.Popen([exe], start_new_session=True)
            return True
    except OSError:
        pass
    return False
