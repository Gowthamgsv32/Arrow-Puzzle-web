"""Main window: header, orb, conversation, input bar; tray icon keeps it listening."""

from __future__ import annotations

import threading
from importlib import resources

from PySide6.QtCore import QObject, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QAction, QCloseEvent, QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from personal_assistant.config import Settings
from personal_assistant.gui.chat import ChatView
from personal_assistant.gui.orb import Orb
from personal_assistant.gui.theme import STATE_LABELS, STYLESHEET, ui_font
from personal_assistant.i18n import load_locales
from personal_assistant.voice_loop import ERROR, MUTED, VoiceLoop


class Bridge(QObject):
    """Turns VoiceLoop callbacks (worker thread) into Qt signals (UI thread)."""

    status = Signal(str, str)
    level = Signal(float)
    heard = Signal(str, object, bool)
    reply = Signal(str, str)
    quit = Signal()

    def on_status(self, state: str, detail: str = "") -> None:
        self.status.emit(state, detail)

    def on_level(self, level: float) -> None:
        self.level.emit(level)

    def on_heard(self, text: str, language: str | None, accepted: bool) -> None:
        self.heard.emit(text, language, accepted)

    def on_reply(self, text: str, language: str) -> None:
        self.reply.emit(text, language)

    def on_quit(self) -> None:
        self.quit.emit()


def app_icon() -> QIcon:
    path = resources.files("personal_assistant") / "assets" / "icon.png"
    return QIcon(str(path))


def mic_icon(muted: bool) -> QIcon:
    """Microphone glyph drawn with QPainter (emoji fonts vary between machines)."""
    size = 64
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    color = QColor("#f87171" if muted else "#e8ecff")
    pen = QPen(color, 4.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    p.setBrush(color)
    p.drawRoundedRect(QRectF(24, 10, 16, 28), 8, 8)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawArc(QRectF(16, 18, 32, 30), 180 * 16, 180 * 16)
    p.drawLine(32, 48, 32, 55)
    p.drawLine(24, 55, 40, 55)
    if muted:
        p.setPen(QPen(QColor("#f87171"), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(14, 12, 50, 54)
    p.end()
    return QIcon(pix)


class MainWindow(QWidget):
    def __init__(self, settings: Settings, voice: bool = True):
        super().__init__()
        self.settings = settings
        self.setObjectName("root")
        self.setWindowTitle("Personal Assistant")
        self.setWindowIcon(app_icon())
        self.resize(460, 760)
        self.setMinimumSize(380, 560)
        self.setStyleSheet(STYLESHEET)
        self._really_quit = False
        self._tray_hint_shown = False

        locales = load_locales(settings.languages)
        self._build_ui({code: loc.name for code, loc in locales.items()})
        self._build_tray()

        self.bridge = Bridge()
        self.bridge.status.connect(self._on_status)
        self.bridge.level.connect(self.orb.set_level)
        self.bridge.heard.connect(self._on_heard)
        self.bridge.reply.connect(self._on_reply)
        self.bridge.quit.connect(self.quit_app)

        self.loop = VoiceLoop(settings, self.bridge, voice=voice)
        self._thread = threading.Thread(target=self.loop.run, name="voice-loop", daemon=True)
        self._thread.start()

        hint = "Say “open YouTube” or “யூடியூப் திற”" if voice else "Voice is off — type a command"
        self.chat.add_notice(hint)

    # ---- layout ----------------------------------------------------------------------
    def _build_ui(self, languages: dict[str, str]) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Personal Assistant")
        title.setObjectName("title")
        title.setFont(ui_font(14, QFont.Weight.DemiBold))
        header.addWidget(title)
        header.addStretch(1)
        self.chips: dict[str, QLabel] = {}
        for code, name in languages.items():
            chip = QLabel(name)
            chip.setObjectName("chip")
            chip.setFont(ui_font(9))
            chip.setProperty("active", code == self.settings.default_language)
            header.addWidget(chip)
            self.chips[code] = chip
        root.addLayout(header)

        self.orb = Orb()
        root.addWidget(self.orb, 3)

        self.status = QLabel(STATE_LABELS["en"]["loading"])
        self.status.setObjectName("status")
        self.status.setFont(ui_font(10))
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setWordWrap(True)
        root.addWidget(self.status)

        self.chat = ChatView()
        root.addWidget(self.chat, 4)

        bar = QFrame()
        bar.setObjectName("inputBar")
        row = QHBoxLayout(bar)
        row.setContentsMargins(16, 4, 5, 4)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Type a command…  /  கட்டளையை தட்டச்சு செய்யவும்…")
        self.input.setFont(ui_font(11))
        self.input.returnPressed.connect(self._send)
        send = QPushButton("Send")
        send.setObjectName("send")
        send.setFont(ui_font(10, QFont.Weight.DemiBold))
        send.setCursor(Qt.CursorShape.PointingHandCursor)
        send.clicked.connect(self._send)
        row.addWidget(self.input, 1)
        row.addWidget(send)

        self.mic = QPushButton()
        self.mic.setIcon(mic_icon(False))
        self.mic.setIconSize(QSize(24, 24))
        self.mic.setObjectName("mic")
        self.mic.setCheckable(True)
        self.mic.setToolTip("Pause / resume listening")
        self.mic.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mic.toggled.connect(self._toggle_mute)

        bottom = QHBoxLayout()
        bottom.setSpacing(10)
        bottom.addWidget(bar, 1)
        bottom.addWidget(self.mic)
        root.addLayout(bottom)

    def _build_tray(self) -> None:
        self.tray = QSystemTrayIcon(app_icon(), self)
        self.tray.setToolTip("Personal Assistant — listening")
        menu = QMenu()
        show = QAction("Show", self, triggered=self._show_window)
        self.tray_mute = QAction("Pause listening", self, checkable=True)
        self.tray_mute.toggled.connect(lambda on: self.mic.setChecked(on))
        quit_ = QAction("Quit", self, triggered=self.quit_app)
        menu.addActions([show, self.tray_mute])
        menu.addSeparator()
        menu.addAction(quit_)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda reason: self._show_window()
            if reason == QSystemTrayIcon.ActivationReason.Trigger
            else None
        )
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()

    # ---- slots -----------------------------------------------------------------------
    def _send(self) -> None:
        text = self.input.text().strip()
        if text:
            self.input.clear()
            self.loop.submit_text(text)

    def _toggle_mute(self, muted: bool) -> None:
        self.mic.setIcon(mic_icon(muted))
        if self.tray_mute.isChecked() != muted:
            self.tray_mute.setChecked(muted)
        self.loop.set_muted(muted)

    def _on_status(self, state: str, detail: str) -> None:
        self.orb.set_state(state)
        self.status.setText(detail or STATE_LABELS["en"].get(state, state))
        self.tray.setToolTip(f"Personal Assistant — {STATE_LABELS['en'].get(state, state)}")
        if state == MUTED and not self.mic.isChecked():
            self.mic.blockSignals(True)
            self.mic.setChecked(True)
            self.mic.setIcon(mic_icon(True))
            self.mic.blockSignals(False)
        if state == ERROR:
            self.chat.add_notice(f"⚠ {detail}")

    def _on_heard(self, text: str, language: str | None, accepted: bool) -> None:
        if accepted:
            self.chat.add_user(text, language)
        else:
            self.chat.add_ignored(text)
        if language in self.chips:
            for code, chip in self.chips.items():
                chip.setProperty("active", code == language)
                chip.style().unpolish(chip)
                chip.style().polish(chip)

    def _on_reply(self, text: str, language: str) -> None:
        self.chat.add_assistant(text, language)

    def _show_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def quit_app(self) -> None:
        self._really_quit = True
        self.loop.stop()
        self.tray.hide()
        QApplication.quit()

    def closeEvent(self, event: QCloseEvent) -> None:
        # Closing the window keeps the assistant listening in the system tray.
        if not self._really_quit and self.tray.isVisible():
            event.ignore()
            self.hide()
            if not self._tray_hint_shown:
                self.tray.showMessage(
                    "Still listening",
                    "Personal Assistant is running in the tray. Right-click the icon to quit.",
                    app_icon(),
                    4000,
                )
                self._tray_hint_shown = True
            return
        self.loop.stop()
        event.accept()


def run_gui(settings: Settings, voice: bool = True) -> int:
    app = QApplication.instance() or QApplication([])
    app.setApplicationName("Personal Assistant")
    app.setFont(ui_font(10))
    app.setQuitOnLastWindowClosed(False)
    window = MainWindow(settings, voice=voice)
    window.show()
    return app.exec()
