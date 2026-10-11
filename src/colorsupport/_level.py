"""Color level detection from a stream and its environment."""

from __future__ import annotations

import enum
import os
import sys
from collections.abc import Mapping
from typing import Protocol


class ColorLevel(enum.IntEnum):
    """How much color a stream can render, from none up to 24-bit truecolor."""

    NONE = 0
    BASIC = 1
    ANSI256 = 2
    TRUECOLOR = 3


class SupportsIsatty(Protocol):
    def isatty(self) -> bool: ...


_FORCE_VALUES: dict[str, ColorLevel] = {
    "0": ColorLevel.NONE,
    "false": ColorLevel.NONE,
    "": ColorLevel.BASIC,
    "1": ColorLevel.BASIC,
    "true": ColorLevel.BASIC,
    "2": ColorLevel.ANSI256,
    "3": ColorLevel.TRUECOLOR,
}


def level(
    stream: SupportsIsatty = sys.stdout,
    env: Mapping[str, str] = os.environ,
) -> ColorLevel:
    """Report the color level of ``stream`` given ``env``.

    Precedence: ``NO_COLOR`` disables everything, then ``FORCE_COLOR`` forces a
    level, then ``COLORTERM``/``TERM`` decide, and a plain TTY falls back to basic.
    """
    if "NO_COLOR" in env:
        return ColorLevel.NONE

    forced = _forced_level(env)
    if forced is not None:
        return forced

    if not _is_a_tty(stream):
        return ColorLevel.NONE

    colorterm = env.get("COLORTERM", "").strip().lower()
    if colorterm in ("truecolor", "24bit"):
        return ColorLevel.TRUECOLOR

    term = env.get("TERM", "").strip().lower()
    if term == "dumb":
        return ColorLevel.NONE
    if "256" in term:
        return ColorLevel.ANSI256
    return ColorLevel.BASIC


def supports_color(
    stream: SupportsIsatty = sys.stdout,
    env: Mapping[str, str] = os.environ,
) -> bool:
    """Return whether ``stream`` can render any color at all."""
    return level(stream, env) > ColorLevel.NONE


def _forced_level(env: Mapping[str, str]) -> ColorLevel | None:
    if "FORCE_COLOR" not in env:
        return None
    value = env["FORCE_COLOR"].strip().lower()
    return _FORCE_VALUES.get(value, ColorLevel.BASIC)


def _is_a_tty(stream: SupportsIsatty) -> bool:
    try:
        return bool(stream.isatty())
    except (ValueError, OSError):
        return False
