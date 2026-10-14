"""NO_COLOR, FORCE_COLOR, CLICOLOR, CLICOLOR_FORCE and the caller's `when`.

Expected values are written by hand from no-color.org, force-color.org, the CLICOLOR page
and supports-color (see tests/upstream/MANIFEST.json for the pinned revisions).
"""

from __future__ import annotations

import pytest
from conftest import PIPE, TTY, on_linux

from colorsupport import ColorLevel, detect


def test_no_color_turns_color_off_on_a_truecolor_terminal() -> None:
    found = on_linux(TTY, NO_COLOR="1", COLORTERM="truecolor")
    assert (found.level, found.reason) == (ColorLevel.NONE, "NO_COLOR is set")


def test_an_empty_no_color_counts_as_unset() -> None:
    assert on_linux(TTY, NO_COLOR="", COLORTERM="truecolor").level is ColorLevel.TRUECOLOR


def test_no_color_wins_over_every_force() -> None:
    env = {"NO_COLOR": "x", "FORCE_COLOR": "3", "CLICOLOR_FORCE": "1"}
    assert on_linux(PIPE, **env).level is ColorLevel.NONE


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1", ColorLevel.BASIC),
        ("2", ColorLevel.ANSI256),
        ("3", ColorLevel.TRUECOLOR),
        ("03", ColorLevel.TRUECOLOR),
        ("4", ColorLevel.TRUECOLOR),
        ("10", ColorLevel.TRUECOLOR),
        ("9" * 5000, ColorLevel.TRUECOLOR),
        (" 2 ", ColorLevel.ANSI256),
    ],
)
def test_a_numeric_force_color_is_an_exact_level_even_on_a_pipe(
    value: str, expected: ColorLevel
) -> None:
    assert on_linux(PIPE, FORCE_COLOR=value, COLORTERM="truecolor").level is expected


def test_a_numeric_force_color_beats_the_terminal() -> None:
    found = on_linux(TTY, FORCE_COLOR="1", COLORTERM="truecolor", TERM="dumb")
    assert (found.level, found.reason) == (ColorLevel.BASIC, "FORCE_COLOR=1 asks for 16 colors")
    assert on_linux(TTY, FORCE_COLOR="2").reason == "FORCE_COLOR=2 asks for 256 colors"
    assert on_linux(TTY, FORCE_COLOR="3").reason == "FORCE_COLOR=3 asks for truecolor"


@pytest.mark.parametrize("value", ["0", "000", "false", "FALSE", " false "])
def test_force_color_zero_or_false_turns_color_off(value: str) -> None:
    found = on_linux(TTY, FORCE_COLOR=value, COLORTERM="truecolor")
    assert found.level is ColorLevel.NONE
    assert found.reason.endswith("turns color off")


@pytest.mark.parametrize("value", ["true", "yes", "always", "-1", "1.5"])
def test_other_force_color_values_turn_color_on_and_keep_the_depth(value: str) -> None:
    assert on_linux(PIPE, FORCE_COLOR=value).level is ColorLevel.BASIC
    deep = on_linux(TTY, FORCE_COLOR=value, COLORTERM="truecolor")
    assert deep.level is ColorLevel.TRUECOLOR
    assert deep.reason == f"FORCE_COLOR={value!r} turns color on; COLORTERM=truecolor"


def test_force_color_shows_a_long_value_cut_short() -> None:
    found = on_linux(PIPE, FORCE_COLOR="x" * 100)
    assert found.reason == f"FORCE_COLOR={'x' * 32!r} turns color on; " + (
        "the terminal does not say how many colors"
    )


def test_an_empty_force_color_counts_as_unset() -> None:
    assert on_linux(PIPE, FORCE_COLOR="").level is ColorLevel.NONE


def test_clicolor_force_turns_color_on_even_on_a_pipe() -> None:
    found = on_linux(PIPE, CLICOLOR_FORCE="1", TERM="xterm-256color")
    assert (found.level, found.reason) == (
        ColorLevel.ANSI256,
        "CLICOLOR_FORCE is set; TERM=xterm-256color",
    )
    assert on_linux(PIPE, CLICOLOR_FORCE="0").level is ColorLevel.BASIC
    assert on_linux(PIPE, CLICOLOR_FORCE="").level is ColorLevel.NONE


def test_force_color_is_read_before_clicolor_force() -> None:
    assert on_linux(PIPE, FORCE_COLOR="0", CLICOLOR_FORCE="1").level is ColorLevel.NONE


def test_clicolor_zero_turns_color_off_unless_forced() -> None:
    found = on_linux(TTY, CLICOLOR="0", COLORTERM="truecolor")
    assert (found.level, found.reason) == (ColorLevel.NONE, "CLICOLOR=0 turns color off")
    assert on_linux(TTY, CLICOLOR="0", CLICOLOR_FORCE="1").level is ColorLevel.BASIC
    assert on_linux(TTY, CLICOLOR="1", TERM="xterm").level is ColorLevel.BASIC
    assert on_linux(PIPE, CLICOLOR="1").level is ColorLevel.NONE


def test_when_never_turns_color_off_whatever_the_environment() -> None:
    found = detect(TTY, env={"FORCE_COLOR": "3"}, when="never", platform="linux")
    assert (found.level, found.reason) == (
        ColorLevel.NONE,
        "the caller turned color off (when='never')",
    )


def test_when_always_overrides_no_color_and_keeps_the_depth() -> None:
    env = {"NO_COLOR": "1", "FORCE_COLOR": "0", "COLORTERM": "truecolor"}
    found = detect(PIPE, env=env, when="always", platform="linux", terminfo=lambda t: None)
    assert found.level is ColorLevel.TRUECOLOR
    assert found.reason == "the caller turned color on (when='always'); COLORTERM=truecolor"
    bare = detect(PIPE, env={}, when="always", platform="linux", terminfo=lambda t: None)
    assert bare.level is ColorLevel.BASIC


@pytest.mark.parametrize("when", ["", "AUTO", "on", "yes"])
def test_an_unknown_when_raises(when: str) -> None:
    with pytest.raises(ValueError, match="when must be one of auto, always, never"):
        detect(TTY, env={}, when=when)  # type: ignore[arg-type]


def test_the_reason_shows_what_the_user_set() -> None:
    assert on_linux(PIPE, FORCE_COLOR="   ").reason.startswith("FORCE_COLOR='   ' turns color on")
    assert on_linux(PIPE, FORCE_COLOR=" 2 ").reason == "FORCE_COLOR= 2  asks for 256 colors"
    digits = "7" * 100_000
    reason = on_linux(PIPE, FORCE_COLOR=digits).reason
    assert reason == f"FORCE_COLOR={digits[:40]!r} asks for truecolor"


def test_reasons_stay_ascii() -> None:
    value = "j" + chr(0xE9) + "s"
    assert on_linux(PIPE, FORCE_COLOR=value).reason.startswith(f"FORCE_COLOR={value!a} turns")
    term = chr(0x65E5) + "-256color"
    found = on_linux(TTY, TERM=term)
    assert (found.level, found.reason) == (ColorLevel.ANSI256, f"TERM={term!a}")
    assert found.reason.isascii()
