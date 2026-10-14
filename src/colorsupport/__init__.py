"""Detect how much color a terminal stream can show (none, 16, 256, truecolor) and why."""

from __future__ import annotations

from ._detect import detect, level, supports_color
from ._level import ColorLevel, Detection
from ._terminfo import terminfo_colors
from ._windows import enable_vt

__version__ = "0.1.0"

__all__ = [
    "ColorLevel",
    "Detection",
    "detect",
    "enable_vt",
    "level",
    "supports_color",
    "terminfo_colors",
]
