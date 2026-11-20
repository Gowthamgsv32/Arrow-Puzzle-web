"""Scrolling conversation with chat bubbles."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from personal_assistant.gui.theme import ui_font

LANG_NAMES = {"en": "English", "ta": "தமிழ்"}


class ChatView(QScrollArea):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        inner = QWidget()
        self._layout = QVBoxLayout(inner)
        self._layout.setContentsMargins(4, 4, 8, 4)
        self._layout.setSpacing(10)
        self._layout.addStretch(1)
        self.setWidget(inner)

    def add_user(self, text: str, language: str | None) -> None:
        self._add_bubble(text, "userBubble", Qt.AlignmentFlag.AlignRight, language)

    def add_assistant(self, text: str, language: str | None) -> None:
        self._add_bubble(text, "assistantBubble", Qt.AlignmentFlag.AlignLeft, language)

    def add_ignored(self, text: str) -> None:
        label = QLabel(f"“{text}”  · not a command")
        label.setObjectName("ignored")
        label.setFont(ui_font(9))
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._insert(label)

    def add_step(self, text: str) -> None:
        label = QLabel(f"›  {text}")
        label.setObjectName("step")
        font = ui_font(9)
        font.setFamilies(["Cascadia Mono", "Consolas", "JetBrains Mono", "DejaVu Sans Mono",
                          "monospace", *font.families()])
        label.setFont(font)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._insert(label)

    def add_notice(self, text: str) -> None:
        label = QLabel(text)
        label.setObjectName("meta")
        label.setFont(ui_font(9))
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._insert(label)

    def _add_bubble(self, text, name, align, language) -> None:
        bubble = QLabel(text)
        bubble.setObjectName(name)
        bubble.setFont(ui_font(11))
        bubble.setWordWrap(True)
        bubble.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        # Word-wrapped QLabels otherwise shrink to their minimum; size to the text.
        natural = bubble.fontMetrics().horizontalAdvance(text) + 48
        bubble.setMinimumWidth(min(natural, 320))
        bubble.setMaximumWidth(380)

        meta = QLabel(f"{LANG_NAMES.get(language or '', '')}  {datetime.now():%H:%M}".strip())
        meta.setObjectName("meta")
        meta.setFont(ui_font(8))

        col = QVBoxLayout()
        col.setSpacing(3)
        col.addWidget(bubble, 0, align)
        col.addWidget(meta, 0, align)
        row = QHBoxLayout()
        if align == Qt.AlignmentFlag.AlignRight:
            row.addStretch(1)
        row.addLayout(col)
        if align == Qt.AlignmentFlag.AlignLeft:
            row.addStretch(1)
        holder = QWidget()
        holder.setLayout(row)
        row.setContentsMargins(0, 0, 0, 0)
        self._insert(holder)

    def _insert(self, widget: QWidget) -> None:
        self._layout.insertWidget(self._layout.count() - 1, widget)
        QTimer.singleShot(30, self._scroll_to_bottom)

    def _scroll_to_bottom(self) -> None:
        bar = self.verticalScrollBar()
        bar.setValue(bar.maximum())
