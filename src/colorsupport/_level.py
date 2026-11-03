"""The color levels a stream can show and the explained result of a detection."""

from __future__ import annotations

import enum
from dataclasses import dataclass

from ._strict import exact_str, small_integer, type_name

_COLORS = (0, 16, 256, 16_777_216)
_LABELS = ("none", "16", "256", "truecolor")


class _ColorLevelType(enum.EnumMeta):
    # This populated enum supports value lookup, not EnumMeta's enum-creation overload.
    def __call__(cls, value: object) -> ColorLevel:  # type: ignore[override]
        # The value is read through its base numeric type, so no method of the caller's
        # object runs: nothing can lie about equality, raise, or reach the error message.
        number = small_integer(value, len(_COLORS) - 1)
        if number is None:
            raise ValueError("unknown color level; expected 0, 1, 2 or 3")
        # Members are declared in value order, 0 to 3.
        members: tuple[ColorLevel, ...] = tuple(cls)
        return members[number]


class ColorLevel(enum.IntEnum, metaclass=_ColorLevelType):
    """How much color a stream can show, from none up to 24-bit truecolor.

    The levels compare as numbers, so `level >= ColorLevel.ANSI256` reads naturally.
    `ColorLevel(value)` accepts a number whose exact value is 0, 1, 2 or 3: an int or
    bool, a float, a complex with a zero imaginary part, a Decimal or a Fraction, or a
    subclass of one of them, read through the base type without calling the subclass's
    methods. Anything else (text, bytes, None, other objects, NaN, fractional values)
    raises ValueError without including the input.

    >>> ColorLevel.TRUECOLOR > ColorLevel.ANSI256
    True
    """

    NONE = 0
    BASIC = 1
    ANSI256 = 2
    TRUECOLOR = 3

    @property
    def colors(self) -> int:
        """The number of colors: 0, 16, 256 or 16777216.

        >>> ColorLevel.ANSI256.colors
        256
        """
        return _COLORS[self]

    @property
    def label(self) -> str:
        """A short name: "none", "16", "256" or "truecolor".

        >>> ColorLevel.BASIC.label
        '16'
        """
        return _LABELS[self]

    @classmethod
    def parse(cls, text: str) -> ColorLevel:
        """Read a level from its label, its name or its number, ignoring case.

        `"truecolor"`, `"TRUECOLOR"` and `"3"` all give `ColorLevel.TRUECOLOR`; `"16"`,
        `"basic"` and `"1"` give `ColorLevel.BASIC`. Unknown strings raise ValueError;
        non-strings raise TypeError. A str subclass is read as its exact str value, without
        calling its methods. Error messages do not include the supplied value.

        >>> ColorLevel.parse(" TrueColor ") is ColorLevel.TRUECOLOR
        True
        """
        exact = exact_str(text)
        if exact is None:
            raise TypeError(f"expected a str, got {type_name(text)}")
        key = exact.strip().lower()
        for member in cls:
            if key in (member.label, member.name.lower(), str(member.value)):
                return member
        choices = ", ".join(member.label for member in cls)
        raise ValueError(f"unknown color level; expected one of {choices}")


@dataclass(frozen=True)
class Detection:
    """An immutable color level and its explanation; constructor arguments are typed.

    >>> print(Detection(ColorLevel.BASIC, "TERM=xterm"))
    16: TERM=xterm
    """

    level: ColorLevel
    reason: str

    def __str__(self) -> str:
        return f"{self.level.label}: {self.reason}"
