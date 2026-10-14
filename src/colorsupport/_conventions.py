"""The environment switches users set to turn color on or off, and the caller's own choice."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

from ._level import ColorLevel
from ._terminal import shown

WHEN_CHOICES = ("auto", "always", "never")


@dataclass(frozen=True)
class Override:
    """A decision taken before the terminal is looked at.

    With `exact` the level is final; otherwise it is a floor and the terminal still decides
    how much color above it can be shown.
    """

    level: ColorLevel
    exact: bool
    reason: str


def read_override(env: Mapping[str, str], when: str) -> Override | None:
    """Apply `when`, then NO_COLOR, FORCE_COLOR, CLICOLOR_FORCE and CLICOLOR, in that order.

    Every variable set to an empty string counts as unset, as the NO_COLOR, FORCE_COLOR and
    CLICOLOR pages all ask.
    """
    if when == "never":
        return Override(ColorLevel.NONE, True, "the caller turned color off (when='never')")
    if when == "always":
        return Override(ColorLevel.BASIC, False, "the caller turned color on (when='always')")
    if when != "auto":
        raise ValueError(f"when must be one of {', '.join(WHEN_CHOICES)}, got {when!r}")
    if env.get("NO_COLOR"):
        return Override(ColorLevel.NONE, True, "NO_COLOR is set")
    force = env.get("FORCE_COLOR", "")
    if force:
        return _force_color(force)
    if env.get("CLICOLOR_FORCE"):
        return Override(ColorLevel.BASIC, False, "CLICOLOR_FORCE is set")
    if env.get("CLICOLOR") == "0":
        return Override(ColorLevel.NONE, True, "CLICOLOR=0 turns color off")
    return None


def _force_color(raw: str) -> Override:
    # A number asks for an exact level, as in supports-color; any other value only turns
    # color on and lets the terminal decide the depth. Unlike supports-color, surrounding
    # spaces and the case of "false" are ignored.
    text = raw.strip()
    if re.fullmatch(r"[0-9]+", text):
        digits = text.lstrip("0")
        number = 3 if len(digits) > 1 else int(digits or "0")
        level = ColorLevel(min(number, 3))
        if level is ColorLevel.NONE:
            return Override(level, True, f"FORCE_COLOR={shown(raw)} turns color off")
        wanted = "truecolor" if level is ColorLevel.TRUECOLOR else f"{level.colors} colors"
        return Override(level, True, f"FORCE_COLOR={shown(raw)} asks for {wanted}")
    quoted = ascii(raw[:32])
    if text.lower() == "false":
        return Override(ColorLevel.NONE, True, f"FORCE_COLOR={quoted} turns color off")
    return Override(ColorLevel.BASIC, False, f"FORCE_COLOR={quoted} turns color on")
