# Personal Assistant

A voice-controlled desktop personal assistant that understands **English** and **தமிழ் (Tamil)**,
designed so more languages can be added by dropping in a single file.

## Why Python

| Need | Python ecosystem |
|---|---|
| Speech-to-text in Tamil + English (offline) | `faster-whisper` (OpenAI Whisper, ~100 languages incl. Tamil) |
| Natural Tamil/English voices | `edge-tts` (`ta-IN-PallaviNeural`, `ta-IN-ValluvarNeural`, `en-IN-NeerjaNeural`) |
| Wake word ("Hey Assistant") | `openWakeWord`, `porcupine` |
| LLM / AI brain | Official SDKs for Claude, OpenAI, local models (Ollama, llama.cpp) |
| Desktop automation | `pyautogui`, `pywinauto`, `subprocess`, `webbrowser` |
| Desktop UI later | PySide6 / Qt, or a tray icon with `pystray` |
| Packaging | PyInstaller / Briefcase → `.exe`, `.app`, Linux binary |

The heavy work (speech recognition) runs in optimised C++/CUDA inside `faster-whisper`, so Python's
speed is not the bottleneck.

## Project layout

```
src/personal_assistant/
├── app.py              # listen → understand → act → reply loop
├── config.py           # settings from env / .env
├── i18n.py             # loads locales/*.yaml
├── intents.py          # language-agnostic intent matching
├── locales/
│   ├── en.yaml         # English phrases, replies, TTS voice
│   └── ta.yaml         # Tamil phrases, replies, TTS voice
├── skills/
│   ├── base.py         # @skill registry
│   └── builtin.py      # greet, time, date, open app/site, web search, exit
└── audio/
    ├── recorder.py     # microphone capture
    ├── stt.py          # speech-to-text (faster-whisper)
    └── tts.py          # text-to-speech (edge-tts)
tests/
```

## Setup

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -e ".[voice,dev]"
cp .env.example .env        # optional: tweak languages / model size
```

## Run

```bash
personal-assistant           # voice mode: press Enter, then speak
personal-assistant --text    # type commands (no microphone needed)
```

The first voice run downloads the Whisper model (`small` ≈ 460 MB). Use `medium` or
`large-v3` in `.env` for better Tamil accuracy if your machine (or GPU) can handle it.
Text-to-speech uses Edge neural voices and needs an internet connection.

### Example commands

| English | தமிழ் |
|---|---|
| hello | வணக்கம் |
| what time is it | மணி என்ன |
| what is the date | இன்று தேதி என்ன |
| open youtube | யூடியூப் திற |
| search for weather in Chennai | சென்னை வானிலை தேடு |
| goodbye | நிறுத்து |

The assistant replies in the language you spoke.

## Adding a language

1. Copy `src/personal_assistant/locales/en.yaml` to e.g. `hi.yaml` (Hindi) and translate the
   phrases and responses. Pick a voice from `edge-tts --list-voices`.
2. Add the code to `PA_LANGUAGES` in `.env` (e.g. `PA_LANGUAGES=en,ta,hi`).

`tests/test_intents.py` checks every locale defines the same intents and responses.

## Adding a skill

```python
# src/personal_assistant/skills/builtin.py (or a new module imported in skills/__init__.py)
@skill("weather")
def weather(intent, locale):
    return SkillResult(locale.say("weather", city=intent.argument))
```

Then add `weather` trigger phrases and a `weather` response to every locale file.

## Roadmap

- [ ] Wake word instead of push-to-talk
- [ ] Voice activity detection (stop recording when you stop speaking)
- [ ] LLM fallback for questions the built-in skills don't cover
- [ ] Offline TTS option
- [ ] System tray app + desktop packaging (PyInstaller)
- [ ] More languages

## Development

```bash
pytest
ruff check .
```
