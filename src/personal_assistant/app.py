"""Entry point. Desktop UI by default; ``--cli`` for a terminal, ``--text`` to type."""

from __future__ import annotations

import argparse
import logging
import sys

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


def run_cli(settings: Settings, voice: bool) -> None:
    import threading

    from personal_assistant.voice_loop import VoiceLoop

    loop = VoiceLoop(settings, _ConsoleEvents(), voice=voice, exit_quits=True)
    worker = threading.Thread(target=loop.run, daemon=True)
    worker.start()
    try:
        if voice:
            worker.join()
        else:
            while worker.is_alive():
                line = input()
                if line.strip():
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
        import ctranslate2  # noqa: F401  (loads the native library)
        import edge_tts  # noqa: F401
        import faster_whisper  # noqa: F401
        import numpy  # noqa: F401
        import soundfile  # noqa: F401

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
