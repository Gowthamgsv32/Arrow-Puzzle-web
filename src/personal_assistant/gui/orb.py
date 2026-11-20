"""Animated, glowing orb that reacts to the assistant's state and the mic level."""

from __future__ import annotations

import math
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QBrush, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QSizePolicy, QWidget

from personal_assistant.gui.theme import STATE_COLORS, qcolor


class Orb(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setMinimumSize(220, 220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._state = "loading"
        self._level = 0.0  # smoothed 0..1
        self._target = 0.0
        self._t0 = time.monotonic()
        self._timer = QTimer(self, interval=16, timeout=self._tick)  # ~60 fps
        self._timer.start()

    def set_state(self, state: str) -> None:
        self._state = state if state in STATE_COLORS else "listening"

    def set_level(self, rms: float) -> None:
        # Speech RMS is roughly 0.01..0.2; map to 0..1 on a log-ish curve.
        self._target = max(0.0, min(1.0, math.sqrt(rms * 12)))

    def _tick(self) -> None:
        t = time.monotonic() - self._t0
        if self._state == "speaking":
            self._target = 0.35 + 0.3 * abs(math.sin(t * 7)) * abs(math.sin(t * 2.3))
        elif self._state not in ("listening", "hearing"):
            self._target = 0.0
        self._level += (self._target - self._level) * 0.18
        self._target *= 0.92
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = time.monotonic() - self._t0
        core_hex, glow_hex = STATE_COLORS[self._state]
        c = QPointF(self.width() / 2, self.height() / 2)
        base = min(self.width(), self.height()) * 0.22
        breathe = 0.04 * math.sin(t * 1.6)
        r = base * (1 + breathe + 0.35 * self._level)

        # Outer glow
        glow = QRadialGradient(c, r * 2.4)
        glow.setColorAt(0.0, qcolor(glow_hex, 140))
        glow.setColorAt(0.45, qcolor(glow_hex, 45))
        glow.setColorAt(1.0, qcolor(glow_hex, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(c, r * 2.4, r * 2.4)

        # Ripples while hearing / speaking
        if self._state in ("hearing", "speaking", "listening"):
            for i in range(3):
                phase = (t * 0.6 + i / 3) % 1.0
                rr = r * (1.05 + phase * (0.9 + self._level))
                pen = QPen(qcolor(core_hex, int(120 * (1 - phase) * (0.35 + self._level))))
                pen.setWidthF(2.0)
                p.setPen(pen)
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(c, rr, rr)

        # Rotating arcs while thinking / loading
        if self._state in ("thinking", "loading", "working"):
            pen = QPen(qcolor(core_hex, 220))
            pen.setWidthF(3.0)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            box = QRectF(c.x() - r * 1.35, c.y() - r * 1.35, r * 2.7, r * 2.7)
            start = int(-t * 360 * 16) % (360 * 16)
            p.drawArc(box, start, 90 * 16)
            p.drawArc(box, start + 180 * 16, 90 * 16)

        # Core sphere with a soft highlight
        core = QRadialGradient(QPointF(c.x() - r * 0.35, c.y() - r * 0.4), r * 1.4)
        core.setColorAt(0.0, qcolor("#ffffff", 235))
        core.setColorAt(0.25, qcolor(core_hex, 255))
        core.setColorAt(1.0, qcolor(glow_hex, 255))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(core))
        p.drawEllipse(c, r, r)
        p.end()
