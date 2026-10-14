"""The color levels a stream can show and the explained result of a detection."""

from __future__ import annotations

import enum
from dataclasses import dataclass

_COLORS = (0, 16, 256, 16_777_216)
_LABELS = ("none", "16", "256", "truecolor")


class ColorLevel(enum.IntEnum):
    """How much color a stream can show, from none up to 24-bit truecolor.

    The levels compare as numbers, so `level >= ColorLevel.ANSI256` reads naturally.
    """

    NONE = 0
    BASIC = 1
    ANSI256 = 2
    TRUECOLOR = 3

    @property
    def colors(self) -> int:
        """The number of colors: 0, 16, 256 or 16777216."""
        return _COLORS[self]

    @property
    def label(self) -> str:
        """A short name: "none", "16", "256" or "truecolor"."""
        return _LABELS[self]

    @classmethod
    def parse(cls, text: str) -> ColorLevel:
        """Read a level from its label, its name or its number, ignoring case.

        `"truecolor"`, `"TRUECOLOR"` and `"3"` all give `ColorLevel.TRUECOLOR`; `"16"`,
        `"basic"` and `"1"` give `ColorLevel.BASIC`. Anything else raises ValueError.
        """
        if not isinstance(text, str):
            raise TypeError(f"expected a str, got {type(text).__name__}")
        key = text.strip().lower()
        for member in cls:
            if key in (member.label, member.name.lower(), str(member.value)):
                return member
        choices = ", ".join(member.label for member in cls)
        raise ValueError(f"unknown color level {text!r}; expected one of {choices}")


@dataclass(frozen=True)
class Detection:
    """A color level and the reason it was chosen, in one short sentence."""

    level: ColorLevel
    reason: str

    def __str__(self) -> str:
        return f"{self.level.label}: {self.reason}"
