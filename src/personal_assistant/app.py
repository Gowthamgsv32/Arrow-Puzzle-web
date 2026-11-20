"""Entry point. Desktop UI by default; ``--cli`` for a terminal, ``--text`` to type."""

from __future__ import annotations

import argparse
import logging
import sys
import threading

from personal_assistant.config import Settings
from personal_assistant.paths import user_data_dir


def _setup_logging(verbose: bool) -> None:
    handlers: list[logging.Handler] = [
        logging.FileHandler(user_data_dir() / "assistant.log", encoding="utf-8")
    ]
    if sys.stderr is not None:  # None inside a windowed .exe
        handlers.append(logging.StreamHandler())
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
    )


class _ConsoleEvents:
    def on_status(self, state: str, detail: str = "") -> None:
        print(f"[{state}] {detail}".rstrip())

    def on_level(self, level: float) -> None:
        pass

    def on_heard(self, text: str, language: str | None, accepted: bool) -> None:
        print(f"you ({language or '?'}){'' if accepted else ' [ignored]'}> {text}")

    def on_reply(self, text: str, language: str) -> None:
        print(f"assistant> {text}")

    def on_quit(self) -> None:
        pass

    def on_step(self, text: str) -> None:
        print(f"  › {text}")

    def on_confirm(self, question: str) -> bool:
        print(f"\n{question}\nAllow? [y/N] ", end="", flush=True)
        self.pending_answer = threading.Event()
        self.answer = False
        self.pending_answer.wait(timeout=180)
        self.pending_answer = None
        return self.answer

    pending_answer: threading.Event | None = None
    answer: bool = False


def run_cli(settings: Settings, voice: bool) -> None:
    from personal_assistant.voice_loop import VoiceLoop

    events = _ConsoleEvents()
    loop = VoiceLoop(settings, events, voice=voice, exit_quits=True)
    worker = threading.Thread(target=loop.run, daemon=True)
    worker.start()
    try:
        # stdin carries commands, and y/n answers while an approval is pending
        while worker.is_alive():
            line = input() if not voice or events.pending_answer else None
            if line is None:
                worker.join(timeout=0.3)
                continue
            if events.pending_answer:
                events.answer = line.strip().lower() in ("y", "yes", "ஆம்")
                events.pending_answer.set()
            elif line.strip():
                loop.submit_text(line)
                worker.join(timeout=0.3)
    except (EOFError, KeyboardInterrupt):
        loop.stop()
        worker.join(timeout=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Personal desktop assistant (English + Tamil).")
    parser.add_argument("--cli", action="store_true", help="run in the terminal instead of the UI")
    parser.add_argument("--text", action="store_true", help="type commands; no microphone")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--selftest", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    _setup_logging(args.verbose)
    if args.selftest:
        sys.exit(selftest())
    settings = Settings.from_env()

    if args.cli or (args.text and not _has_gui()):
        run_cli(settings, voice=not args.text)
        return
    from personal_assistant.gui.window import run_gui

    sys.exit(run_gui(settings, voice=not args.text))


def selftest() -> int:
    """Used by CI on the packaged .exe: every bundled dependency must import and the
    window must build. Result is written to the log (a windowed exe has no console)."""
    import os

    log = logging.getLogger("selftest")
    try:
        # AI agent stack
        import anthropic  # noqa: F401
        import ctranslate2  # noqa: F401  (loads the native library)
        import edge_tts  # noqa: F401
        import faster_whisper  # noqa: F401
        import mss  # noqa: F401
        import numpy  # noqa: F401
        import pyperclip  # noqa: F401
        import soundfile  # noqa: F401
        import websocket  # noqa: F401

        from personal_assistant.agent.agent import DeveloperAgent, build_system_prompt

        if sys.platform == "win32" or os.getenv("DISPLAY"):
            import pyautogui  # noqa: F401  (needs a display on Linux)

        if sys.platform == "win32":  # offline voice: SAPI must load inside the .exe
            from personal_assistant.audio.tts import _default_engine

            voices = _default_engine().getProperty("voices")
            log.info("Offline voices: %s", [v.name for v in voices])
            assert voices, "no SAPI voices"

        DeveloperAgent(Settings(), client=object())  # tools + prompt build without network
        assert "desktop assistant" in build_system_prompt()

        try:
            import sounddevice  # noqa: F401
        except OSError as exc:  # no PortAudio on some Linux CI images
            log.warning("sounddevice unavailable: %s", exc)

        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication

        from personal_assistant.gui.window import MainWindow

        app = QApplication.instance() or QApplication([])
        window = MainWindow(Settings.from_env(), voice=False)
        window.show()
        app.processEvents()
        window.quit_app()
    except Exception:
        log.exception("SELFTEST FAILED")
        return 1
    log.info("SELFTEST OK")
    return 0


def _has_gui() -> bool:
    try:
        import PySide6  # noqa: F401
    except ImportError:
        return False
    return True


if __name__ == "__main__":
    main()
