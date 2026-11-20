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

## Download & install (Windows)

1. Open the repo's **Actions** tab → latest **Build Windows app** run → download the
   `PersonalAssistant-…-windows` artifact (or grab it from **Releases** once a `v*` tag is pushed).
2. Run `PersonalAssistant-Setup-x.y.z.exe`. No admin rights needed. Tick
   *"Start automatically when I sign in to Windows"* if you want it always on.
   A portable `.zip` is included too: unzip and run `PersonalAssistant.exe`.
3. On first launch it downloads the speech model (`small` ≈ 460 MB), then the orb turns blue:
   **just speak** — no button, no wake word.

Closing the window keeps it listening in the system tray (right-click the tray icon → *Quit*).
Click the mic button to pause/resume. Saying "goodbye" / "நிறுத்து" also pauses it.

### How always-listening works

```
microphone ─► voice activity detection ─► Whisper (en/ta) ─► intent ─► skill ─► spoken reply
             (waits for you to pause)                         │
                                                   not a command? → ignored quietly
```

The mic is ignored while the assistant is speaking, so it doesn't hear itself. Background
conversation that doesn't match a command is shown faded in the chat and not acted on. For a
stricter mode set a wake word (`PA_WAKE_WORD=assistant`) in `.env`.

| Orb colour | Meaning |
|---|---|
| Blue/violet | Listening |
| Cyan ripples | Hearing you |
| Amber spinner | Thinking (transcribing) |
| Green | Speaking |
| Grey | Paused / loading |

## Project layout

```
src/personal_assistant/
├── app.py              # entry: desktop UI (default), --cli, --text, --selftest
├── voice_loop.py       # always-listening loop: mic → VAD → STT → brain → TTS
├── core.py             # Brain: text → intent → skill → localized reply
├── config.py           # settings from env / .env
├── i18n.py, intents.py # locale files + language-agnostic intent matching
├── locales/            # en.yaml, ta.yaml  (one file per language)
├── skills/             # greet, time, date, open app/site, web search, exit
├── audio/
│   ├── listener.py     # continuous microphone stream
│   ├── vad.py          # splits the stream into utterances
│   ├── stt.py          # faster-whisper speech-to-text
│   └── tts.py          # edge-tts neural voices
└── gui/                # PySide6 window, animated orb, chat bubbles, tray icon
packaging/              # launcher, icon, Inno Setup installer script
assistant.spec          # PyInstaller build
```

## Run from source

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -e ".[gui,voice,dev]"
personal-assistant              # desktop app, always listening
personal-assistant --text       # desktop app, typing only
personal-assistant-cli --cli    # terminal, always listening
```

Settings live in `.env` (see `.env.example`). Use `PA_WHISPER_MODEL=medium` for better Tamil
accuracy if your PC can handle it. Voices use Edge neural TTS and need internet.

## Build the .exe yourself

On Windows:

```bash
pip install -e ".[gui,voice,build]"
pyinstaller assistant.spec --noconfirm        # → dist\PersonalAssistant\PersonalAssistant.exe
iscc /DAppVersion=0.2.0 packaging\installer.iss   # optional installer (needs Inno Setup 6)
```

To publish a release: `git tag v0.2.0 && git push origin v0.2.0` — the workflow attaches the
installer and portable zip to a GitHub Release.

### Example commands

| English | தமிழ் |
|---|---|
| hello | வணக்கம் |
| what time is it | மணி என்ன |
| what is the date | இன்று தேதி என்ன |
| open youtube | யூடியூப் திற |
| search for weather in Chennai | சென்னை வானிலை தேடு |
| goodbye (pauses listening) | நிறுத்து |

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

- [x] Always-listening with voice activity detection
- [x] Desktop UI, tray icon, Windows installer
- [ ] Neural wake word ("Hey Assistant") with openWakeWord
- [ ] LLM fallback for questions the built-in skills don't cover
- [ ] Offline TTS option
- [ ] More languages

## Development

```bash
pytest
ruff check .
```
