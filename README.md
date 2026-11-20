# Personal Assistant

A voice-controlled desktop assistant for developers that understands **English** and
**தமிழ் (Tamil)**. Simple commands run instantly on your PC; anything else goes to an **AI agent
(Claude)** that operates your computer: mouse, keyboard, terminal, Chrome tabs, clipboard and files.

## AI agent: what you can ask

Say **"assistant, …"** (or **"அசிஸ்டன்ட், …"**), or just type in the box:

- "assistant, read my open Chrome tab and summarize it"
- "assistant, open the GitHub PR tabs and tell me which ones have failing checks"
- "assistant, run the tests in my api project and tell me what failed"
- "assistant, copy the error from the terminal and search it on Google"
- "assistant, close all the YouTube tabs"
- "அசிஸ்டன்ட், git status காட்டு"
- "assistant, open VS Code and click Run on the debug panel"

| Capability | How |
|---|---|
| Mouse, keyboard, any app on screen | Claude computer-use toolset (screenshots, click, drag, scroll, type, key combos, zoom) |
| Terminal | `run_command` captures output (PowerShell on Windows); `open_terminal` for servers/watchers |
| Chrome tabs | List / open / switch / close / navigate / **read page text** / run JavaScript (DevTools protocol) |
| Copy & paste | Clipboard read/write + `ctrl+c` / `ctrl+v` |
| Files | Read, write, list folders; open files, folders and apps |

**Setup:** put `ANTHROPIC_API_KEY=sk-ant-…` in `.env` (next to the `.exe`, or in
`%LOCALAPPDATA%\PersonalAssistant\.env`). The agent uses `claude-opus-5-5`; set
`PA_AGENT_EFFORT=low` for faster, cheaper answers.

**Chrome:** the assistant drives a Chrome window with its own profile (Chrome only allows remote
control on a separate profile). The first time it opens Chrome, sign in to your accounts there;
it remembers them. Use that window for browsing you want the assistant to see.

### Local AI brain (free, offline, private)

Alongside Claude, the agent can use an open-weight model running on your own PC through
[Ollama](https://ollama.com). By default Claude does the work and the local model **takes over
automatically** when there is no internet, the API credit is used up, or there is no API key.

1. Install Ollama from ollama.com (it runs in the background).
2. Download a model, in a terminal:
   `ollama pull qwen2.5:7b` (≈4.7 GB; best quality on a 32 GB laptop) or
   `ollama pull qwen2.5:3b` (≈2 GB; about twice as fast).
3. Start the assistant. The activity feed shows e.g.
   `AI brain: Claude (claude-opus-5-5) + local qwen2.5:7b (fallback)`.

| `.env` setting | Effect |
|---|---|
| `PA_AGENT_BRAIN=auto` (default) | Claude first, local model when Claude is unavailable |
| `PA_AGENT_BRAIN=local` | Local model only: nothing leaves your PC, no cost |
| `PA_AGENT_BRAIN=claude` | Claude only |
| `PA_LOCAL_MODEL=qwen2.5:3b` | Use a different Ollama model (it must support tool calling) |

What to expect on a laptop **without a separate graphics card** (e.g. Intel i7 + Iris Xe):
the model runs on the CPU at roughly 4–8 words per second for a 7B model, so each step takes
10–40 seconds. It handles terminal, file, clipboard and Chrome-tab tasks; it **cannot** control
the mouse or read the screen (that stays with Claude), and its Tamil is weaker than Claude's.

### Safety

- **Asks first:** terminal commands that change things (installs, deletes, `git push`, redirects,
  chained commands), file writes and JavaScript show an *Allow this action?* dialog. Read-only
  commands (`git status`, `ls`, `git diff`, …) run directly.
- **Stop button** while it works, or **slam the mouse into any screen corner** to abort mouse
  control instantly.
- In always-listening mode only sentences that start with the wake word reach the AI, so
  background conversation is never sent anywhere. Simple built-in commands still work without it.
- Text read from web pages, files and command output is treated as data. The agent is told not to
  follow instructions found there.
- Every API call costs money (screenshots are the expensive part). Reading tabs as text is much
  cheaper than screenshots, and the agent prefers it.

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

## Online vs offline

| Feature | Offline? |
|---|---|
| Listening + speech recognition (Whisper, English + Tamil) | ✅ after the first model download |
| Built-in commands: time, date, open apps/sites, web search | ✅ |
| Spoken replies | ✅ falls back to the voices built into Windows when Edge's online voices can't be reached. Tamil offline needs the Windows Tamil voice pack (*Settings → Time & language → Speech → Add voices*); without it Tamil replies are shown as text. |
| AI agent (mouse, terminal, Chrome, files) | ❌ needs internet and Anthropic API credit |

**Cost & limits:** the AI agent uses the pay-as-you-go Anthropic API (separate from a Claude.ai
subscription). If the credit runs out or a spend limit is hit, the assistant says so and keeps
working for built-in commands. Set a monthly spend limit at console.anthropic.com.

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
├── voice_loop.py       # always-listening loop: mic → VAD → STT → brain/agent → TTS
├── agent/
│   ├── agent.py        # Claude tool-use loop, approvals, cancel, spoken replies
│   ├── tools.py        # tool schemas + which actions need approval
│   ├── computer.py     # computer-use toolset → pyautogui/mss (screen scaling, keys)
│   ├── chrome.py       # Chrome DevTools protocol: tabs, page text, JavaScript
│   └── system.py       # terminal, clipboard, files, open apps
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
pip install -e ".[gui,voice,agent,dev]"
personal-assistant              # desktop app, always listening
personal-assistant --text       # desktop app, typing only
personal-assistant-cli --cli    # terminal, always listening
```

Settings live in `.env` (see `.env.example`). Use `PA_WHISPER_MODEL=medium` for better Tamil
accuracy if your PC can handle it. Voices use Edge neural TTS and need internet.

## Build the .exe yourself

On Windows:

```bash
pip install -e ".[gui,voice,agent,build]"
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
- [x] AI agent: mouse/keyboard, terminal, Chrome tabs, clipboard, files
- [ ] Neural wake word ("Hey Assistant") with openWakeWord
- [ ] VS Code integration (open files at a line, run tasks) and GitHub API tools
- [x] Offline voice fallback
- [ ] More languages

## Development

```bash
pytest
ruff check .
```
