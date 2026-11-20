from __future__ import annotations

from PySide6.QtGui import QColor, QFont

BG_TOP = "#0b1020"
BG_BOTTOM = "#141b34"
SURFACE = "rgba(255, 255, 255, 0.06)"
BORDER = "rgba(255, 255, 255, 0.10)"
TEXT = "#e8ecff"
MUTED_TEXT = "#8b93b8"
ACCENT_1 = "#7c5cff"
ACCENT_2 = "#22d3ee"

# Orb colours per assistant state: (core, glow)
STATE_COLORS = {
    "loading": ("#94a3b8", "#475569"),
    "listening": ("#22d3ee", "#7c5cff"),
    "hearing": ("#67e8f9", "#22d3ee"),
    "thinking": ("#fbbf24", "#f97316"),
    "working": ("#c4b5fd", "#7c5cff"),
    "speaking": ("#34d399", "#22d3ee"),
    "muted": ("#64748b", "#334155"),
    "error": ("#f87171", "#b91c1c"),
}

STATE_LABELS = {
    "en": {
        "loading": "Getting ready…",
        "listening": "Listening — just speak",
        "hearing": "Hearing you…",
        "thinking": "Thinking…",
        "working": "Working on it…",
        "speaking": "Speaking…",
        "muted": "Paused — click the mic to resume",
        "error": "Something went wrong",
    },
}


def qcolor(hex_: str, alpha: int = 255) -> QColor:
    c = QColor(hex_)
    c.setAlpha(alpha)
    return c


def ui_font(size: int = 11, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    font = QFont()
    # Segoe UI / Nirmala UI ship with Windows and render Tamil well.
    font.setFamilies(["Segoe UI", "Nirmala UI", "Noto Sans Tamil", "Noto Sans", "Inter"])
    font.setPointSize(size)
    font.setWeight(weight)
    return font


STYLESHEET = f"""
QWidget#root {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {BG_TOP}, stop:1 {BG_BOTTOM});
}}
QLabel {{ color: {TEXT}; }}
QLabel#title {{ font-weight: 600; letter-spacing: 0.5px; }}
QLabel#status {{ color: {MUTED_TEXT}; }}
QLabel#chip {{
    color: {MUTED_TEXT}; background: {SURFACE}; border: 1px solid {BORDER};
    border-radius: 11px; padding: 3px 10px;
}}
QLabel#chip[active="true"] {{
    color: white; border: 1px solid {ACCENT_2};
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT_1}, stop:1 {ACCENT_2});
}}
QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; border: none; }}
QScrollBar:vertical {{ background: transparent; width: 8px; margin: 4px 0; }}
QScrollBar::handle:vertical {{ background: rgba(255,255,255,0.15); border-radius: 4px; min-height: 24px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ height: 0; background: none; }}
QLabel#userBubble {{
    color: white; border-radius: 16px; padding: 10px 14px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {ACCENT_1}, stop:1 #5b8cff);
}}
QLabel#assistantBubble {{
    color: {TEXT}; background: {SURFACE}; border: 1px solid {BORDER};
    border-radius: 16px; padding: 10px 14px;
}}
QLabel#ignored {{ color: #5d6587; font-style: italic; }}
QLabel#step {{
    color: #a5b4fc; background: rgba(124, 92, 255, 0.10); border-left: 2px solid {ACCENT_1};
    border-radius: 6px; padding: 4px 8px;
}}
QPushButton#stop {{
    color: white; border: none; border-radius: 13px; padding: 4px 14px; min-height: 26px;
    background: #ef4444;
}}
QPushButton#stop:hover {{ background: #dc2626; }}
QLabel#meta {{ color: #6b739a; }}
QFrame#inputBar {{
    background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 22px;
}}
QLineEdit {{
    background: transparent; border: none; color: {TEXT}; padding: 8px 4px;
    selection-background-color: {ACCENT_1};
}}
QPushButton#send {{
    color: white; border: none; border-radius: 17px; padding: 0 16px; min-height: 34px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT_1}, stop:1 {ACCENT_2});
}}
QPushButton#send:hover {{ background: {ACCENT_1}; }}
QPushButton#mic {{
    border: 1px solid {BORDER}; border-radius: 22px; background: {SURFACE};
    min-width: 44px; max-width: 44px; min-height: 44px; max-height: 44px; font-size: 18px;
}}
QPushButton#mic:checked {{ background: rgba(248, 113, 113, 0.25); border-color: #f87171; }}
QPushButton#mic:hover {{ border-color: {ACCENT_2}; }}
"""
