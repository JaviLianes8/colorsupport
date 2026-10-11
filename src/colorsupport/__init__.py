"""Detect a terminal stream color level honoring NO_COLOR and FORCE_COLOR."""

from __future__ import annotations

from ._level import ColorLevel, level, supports_color

__version__ = "0.1.0"

__all__ = ["ColorLevel", "level", "supports_color"]
