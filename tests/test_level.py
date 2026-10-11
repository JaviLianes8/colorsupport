from __future__ import annotations

from colorsupport import ColorLevel, level, supports_color


class FakeStream:
    """A stream stand-in whose TTY status the test controls."""

    def __init__(self, tty: bool) -> None:
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty


TTY = FakeStream(tty=True)
PIPE = FakeStream(tty=False)


def test_no_color_disables_even_on_a_truecolor_tty() -> None:
    env = {"NO_COLOR": "1", "COLORTERM": "truecolor"}
    assert level(TTY, env) is ColorLevel.NONE


def test_no_color_disables_with_an_empty_value() -> None:
    assert level(TTY, {"NO_COLOR": ""}) is ColorLevel.NONE


def test_no_color_wins_over_force_color() -> None:
    env = {"NO_COLOR": "1", "FORCE_COLOR": "3"}
    assert level(TTY, env) is ColorLevel.NONE


def test_force_color_truecolor_on_a_pipe() -> None:
    assert level(PIPE, {"FORCE_COLOR": "3"}) is ColorLevel.TRUECOLOR


def test_force_color_numeric_levels() -> None:
    assert level(PIPE, {"FORCE_COLOR": "1"}) is ColorLevel.BASIC
    assert level(PIPE, {"FORCE_COLOR": "2"}) is ColorLevel.ANSI256


def test_force_color_true_forces_basic() -> None:
    assert level(PIPE, {"FORCE_COLOR": "true"}) is ColorLevel.BASIC


def test_force_color_zero_disables() -> None:
    env = {"FORCE_COLOR": "0", "COLORTERM": "truecolor"}
    assert level(TTY, env) is ColorLevel.NONE


def test_colorterm_truecolor_gives_three() -> None:
    assert level(TTY, {"COLORTERM": "truecolor"}) is ColorLevel.TRUECOLOR


def test_colorterm_24bit_gives_three() -> None:
    assert level(TTY, {"COLORTERM": "24bit"}) is ColorLevel.TRUECOLOR


def test_term_256color_gives_two() -> None:
    assert level(TTY, {"TERM": "xterm-256color"}) is ColorLevel.ANSI256


def test_dumb_term_disables() -> None:
    assert level(TTY, {"TERM": "dumb"}) is ColorLevel.NONE


def test_plain_tty_falls_back_to_basic() -> None:
    assert level(TTY, {"TERM": "xterm"}) is ColorLevel.BASIC


def test_non_tty_is_none_without_a_force() -> None:
    assert level(PIPE, {"COLORTERM": "truecolor"}) is ColorLevel.NONE


def test_supports_color_is_false_on_a_pipe() -> None:
    assert supports_color(PIPE, {}) is False


def test_supports_color_is_true_when_forced() -> None:
    assert supports_color(PIPE, {"FORCE_COLOR": "1"}) is True


def test_a_broken_isatty_counts_as_no_tty() -> None:
    class Broken:
        def isatty(self) -> bool:
            raise ValueError("stream is closed")

    assert level(Broken(), {}) is ColorLevel.NONE
