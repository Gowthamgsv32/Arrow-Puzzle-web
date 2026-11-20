"""Executes Claude's computer-use toolset actions (computer_toolset_20260801) on the
real desktop with pyautogui + mss.

Coordinates from Claude are in the pixel space of the screenshots we send. Screens are
downscaled to fit the model's image limits, so every coordinate is scaled back here.
"""

from __future__ import annotations

import base64
import io
import math
import sys
import time
from collections.abc import Callable

# Conservative limits that every computer-use model accepts.
MAX_LONG_EDGE = 1568
MAX_PIXELS = 1_150_000

TOOLSET_NAME = "computer"

# xdotool-style key names Claude uses -> pyautogui names
_KEY_ALIASES = {
    "return": "enter",
    "kp_enter": "enter",
    "escape": "esc",
    "backspace": "backspace",
    "page_up": "pageup",
    "page_down": "pagedown",
    "prior": "pageup",
    "next": "pagedown",
    "control": "ctrl",
    "control_l": "ctrl",
    "control_r": "ctrlright",
    "ctrl_l": "ctrl",
    "alt_l": "alt",
    "alt_r": "altright",
    "shift_l": "shift",
    "shift_r": "shiftright",
    "super": "win",
    "super_l": "win",
    "super_r": "win",
    "meta": "win",
    "cmd": "command",
    "print": "printscreen",
    "minus": "-",
    "plus": "+",
    "equal": "=",
    "comma": ",",
    "period": ".",
    "slash": "/",
    "backslash": "\\",
    "semicolon": ";",
    "apostrophe": "'",
    "grave": "`",
    "bracketleft": "[",
    "bracketright": "]",
}


def scale_factor(width: int, height: int) -> float:
    long_edge = MAX_LONG_EDGE / max(width, height)
    pixels = math.sqrt(MAX_PIXELS / (width * height))
    return min(1.0, long_edge, pixels)


def parse_keys(combo: str) -> list[str]:
    """'ctrl+shift+Tab' -> ['ctrl', 'shift', 'tab'] in pyautogui names."""
    combo = combo.replace(" ", "")
    plus = combo.endswith("++") or combo == "+"  # "ctrl++" = ctrl and the plus key
    parts = [p for p in combo.split("+") if p] + (["+"] if plus else [])
    keys = []
    for raw in parts:
        key = _KEY_ALIASES.get(raw.lower(), raw.lower() if len(raw) > 1 else raw)
        if key == "win" and sys.platform == "darwin":
            key = "command"
        keys.append(key)
    return keys


class ActionError(Exception):
    pass


class ComputerController:
    def __init__(self, is_cancelled: Callable[[], bool] = lambda: False):
        _stub_mouseinfo_without_tk()
        import pyautogui

        _enable_dpi_awareness()
        pyautogui.FAILSAFE = True  # slam the mouse into a screen corner to abort
        pyautogui.PAUSE = 0.05
        self.gui = pyautogui
        self.is_cancelled = is_cancelled
        self.scale = 1.0
        self.origin = (0, 0)
        self._have_geometry = False

    # ---- screenshots -------------------------------------------------------------------
    def _grab(self, region: tuple[int, int, int, int] | None = None):
        import mss
        from PIL import Image

        with mss.mss() as sct:
            mon = sct.monitors[1]  # primary display
            if region is None:
                box = mon
            else:
                left, top, right, bottom = region
                box = {"left": left, "top": top, "width": right - left, "height": bottom - top}
            shot = sct.grab(box)
            return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX"), mon

    def screenshot_b64(self) -> str:
        img, mon = self._grab()
        self.origin = (mon["left"], mon["top"])
        self.scale = scale_factor(*img.size)
        self._have_geometry = True
        if self.scale < 1.0:
            img = img.resize(
                (round(img.width * self.scale), round(img.height * self.scale)), _lanczos()
            )
        return _png_b64(img)

    def zoom_b64(self, region: list[int]) -> str:
        x0, y0 = self.to_screen(region[0], region[1])
        x1, y1 = self.to_screen(region[2], region[3])
        if x1 <= x0 or y1 <= y0:
            raise ActionError("zoom region must have x1 > x0 and y1 > y0")
        img, _ = self._grab((x0, y0, x1, y1))
        s = scale_factor(*img.size)
        if s < 1.0:
            img = img.resize((round(img.width * s), round(img.height * s)), _lanczos())
        return _png_b64(img)

    # ---- coordinates ---------------------------------------------------------------------
    def to_screen(self, x: float, y: float) -> tuple[int, int]:
        if not self._have_geometry:
            self.screenshot_b64()  # establishes scale for the first action
        return (
            round(x / self.scale) + self.origin[0],
            round(y / self.scale) + self.origin[1],
        )

    def to_model(self, x: int, y: int) -> tuple[int, int]:
        if not self._have_geometry:
            self.screenshot_b64()
        return round((x - self.origin[0]) * self.scale), round((y - self.origin[1]) * self.scale)

    # ---- actions -------------------------------------------------------------------------
    def execute(self, name: str, args: dict) -> list[dict] | str:
        """Run one toolset member. Returns tool_result content."""
        g = self.gui
        if name == "screenshot":
            return [_image_block(self.screenshot_b64())]
        if name == "zoom":
            return [_image_block(self.zoom_b64(args["region"]))]
        if name == "cursor_position":
            x, y = self.to_model(*g.position())
            return f"X={x}, Y={y}"
        if name in ("left_click", "right_click", "middle_click", "double_click", "triple_click"):
            button = {"right_click": "right", "middle_click": "middle"}.get(name, "left")
            clicks = {"double_click": 2, "triple_click": 3}.get(name, 1)
            with self._modifiers(args.get("text")):
                if args.get("coordinate"):
                    g.click(*self.to_screen(*args["coordinate"]), clicks=clicks, button=button,
                            interval=0.08)
                else:
                    g.click(clicks=clicks, button=button, interval=0.08)
            return "OK"
        if name == "left_click_drag":
            sx, sy = self.to_screen(*args["start_coordinate"])
            ex, ey = self.to_screen(*args["coordinate"])
            with self._modifiers(args.get("text")):
                g.moveTo(sx, sy)
                g.dragTo(ex, ey, duration=0.4, button="left")
            return "OK"
        if name == "mouse_move":
            g.moveTo(*self.to_screen(*args["coordinate"]), duration=0.15)
            return "OK"
        if name == "left_mouse_down":
            g.mouseDown()
            return "OK"
        if name == "left_mouse_up":
            g.mouseUp()
            return "OK"
        if name == "scroll":
            self._scroll(args)
            return "OK"
        if name == "type":
            self.type_text(args["text"])
            return "OK"
        if name == "key":
            keys = parse_keys(args["text"])
            for _ in range(int(args.get("repeat") or 1)):
                if self.is_cancelled():
                    raise ActionError("Cancelled by user")
                g.hotkey(*keys)
            return "OK"
        if name == "hold_key":
            keys = parse_keys(args["text"])
            for k in keys:
                g.keyDown(k)
            try:
                self._sleep(float(args.get("duration", 1)))
            finally:
                for k in reversed(keys):
                    g.keyUp(k)
            return "OK"
        if name == "wait":
            self._sleep(float(args.get("duration", 1)))
            return "OK"
        raise ActionError(f"Unsupported computer action: {name}")

    def type_text(self, text: str) -> None:
        if text.isascii():
            self.gui.write(text, interval=0.008)
        else:
            # pyautogui can only type ASCII; paste Tamil/emoji/etc. via the clipboard.
            import pyperclip

            previous = _safe_paste(pyperclip)
            pyperclip.copy(text)
            self.gui.hotkey("command" if sys.platform == "darwin" else "ctrl", "v")
            time.sleep(0.15)
            if previous is not None:
                pyperclip.copy(previous)

    def _scroll(self, args: dict) -> None:
        g = self.gui
        if args.get("coordinate"):
            g.moveTo(*self.to_screen(*args["coordinate"]))
        amount = int(args.get("scroll_amount") or 3)
        direction = args.get("scroll_direction", "down")
        # Windows wheel events are in 1/120ths of a notch.
        unit = 120 if sys.platform == "win32" else 1
        with self._modifiers(args.get("text")):
            if direction in ("up", "down"):
                g.scroll(amount * unit * (1 if direction == "up" else -1))
            elif sys.platform == "win32":
                with self._modifiers("shift"):
                    g.scroll(amount * unit * (1 if direction == "left" else -1))
            else:
                g.hscroll(amount * (-1 if direction == "left" else 1))

    def _sleep(self, seconds: float) -> None:
        end = time.monotonic() + min(seconds, 300)
        while time.monotonic() < end:
            if self.is_cancelled():
                raise ActionError("Cancelled by user")
            time.sleep(0.1)

    def _modifiers(self, combo: str | None):
        gui = self.gui

        class _Hold:
            def __enter__(self_inner):
                self_inner.keys = parse_keys(combo) if combo else []
                for k in self_inner.keys:
                    gui.keyDown(k)

            def __exit__(self_inner, *exc):
                for k in reversed(self_inner.keys):
                    gui.keyUp(k)

        return _Hold()


def _image_block(b64: str) -> dict:
    return {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64}}


def _png_b64(img) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return base64.standard_b64encode(buf.getvalue()).decode("ascii")


def _lanczos():
    from PIL import Image

    return Image.Resampling.LANCZOS


def _safe_paste(pyperclip):
    try:
        return pyperclip.paste()
    except Exception:  # noqa: BLE001 - clipboard may hold non-text data
        return None


def _stub_mouseinfo_without_tk() -> None:
    """pyautogui imports `mouseinfo`, a debug tool that exits the process when tkinter is
    missing (some Linux Pythons). We never use it, so stand in an empty module."""
    try:
        import tkinter  # noqa: F401
    except ImportError:
        import types

        sys.modules.setdefault("mouseinfo", types.ModuleType("mouseinfo"))


def _enable_dpi_awareness() -> None:
    """Make Windows report physical pixels so screenshots and clicks line up on scaled displays."""
    if sys.platform != "win32":
        return
    import ctypes

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass
