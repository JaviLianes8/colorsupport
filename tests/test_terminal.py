"""TERM, COLORTERM, TERM_PROGRAM, CI and terminfo on a terminal.

Expected values are written by hand from supports-color's index.js (pinned in
tests/upstream/MANIFEST.json); tests/test_upstream.py checks the lists against that file.
"""

from __future__ import annotations

import pytest
from conftest import PIPE, TTY, on_linux

from colorsupport import ColorLevel, detect


def test_a_pipe_has_no_color() -> None:
    found = on_linux(PIPE, COLORTERM="truecolor")
    assert (found.level, found.reason) == (ColorLevel.NONE, "the stream is not a terminal")


@pytest.mark.parametrize("value", ["truecolor", "24bit"])
def test_colorterm_announces_truecolor(value: str) -> None:
    found = on_linux(TTY, COLORTERM=value, TERM="xterm")
    assert (found.level, found.reason) == (ColorLevel.TRUECOLOR, f"COLORTERM={value}")


def test_any_other_colorterm_means_basic_color() -> None:
    assert on_linux(TTY, COLORTERM="yes").reason == "COLORTERM is set"
    assert on_linux(TTY, COLORTERM="").level is ColorLevel.BASIC
    assert on_linux(TTY, COLORTERM="TrueColor", TERM="xterm-256color").level is ColorLevel.ANSI256


@pytest.mark.parametrize("term", ["xterm-kitty", "xterm-ghostty", "wezterm"])
def test_truecolor_terminals_are_known_by_term(term: str) -> None:
    assert on_linux(TTY, TERM=term).level is ColorLevel.TRUECOLOR


@pytest.mark.parametrize("term", ["xterm-256color", "screen-256", "XTERM-256COLOR", "a-256"])
def test_a_256_suffix_means_256_colors(term: str) -> None:
    found = on_linux(TTY, TERM=term)
    assert (found.level, found.reason) == (ColorLevel.ANSI256, f"TERM={term}")


@pytest.mark.parametrize("term", ["xterm-256colors", "256color", "x-256color-y", "xterm-2560"])
def test_256_elsewhere_in_term_is_not_256_colors(term: str) -> None:
    assert on_linux(TTY, TERM=term).level < ColorLevel.ANSI256


@pytest.mark.parametrize(
    "term",
    ["screen", "xterm", "vt100", "vt220", "rxvt-unicode", "mycolor", "ansi", "cygwin", "linux"],
)
def test_known_term_families_get_basic_color(term: str) -> None:
    assert on_linux(TTY, TERM=term).level is ColorLevel.BASIC


@pytest.mark.parametrize("term", ["", "foo", "my-vt100", "a-screen", "unknown"])
def test_an_unknown_term_on_a_terminal_has_no_color(term: str) -> None:
    found = on_linux(TTY, TERM=term)
    assert (found.level, found.reason) == (
        ColorLevel.NONE,
        "the terminal does not say it shows color",
    )


def test_term_dumb_has_no_color_and_wins_over_colorterm() -> None:
    found = on_linux(TTY, TERM="dumb", COLORTERM="truecolor")
    assert (found.level, found.reason) == (ColorLevel.NONE, "TERM=dumb")


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("3.4.19", ColorLevel.TRUECOLOR),
        ("3", ColorLevel.TRUECOLOR),
        ("10.0", ColorLevel.TRUECOLOR),
        ("9" * 50, ColorLevel.TRUECOLOR),
        ("2.9.2", ColorLevel.ANSI256),
        ("03", ColorLevel.TRUECOLOR),
        ("", ColorLevel.ANSI256),
        ("beta", ColorLevel.ANSI256),
    ],
)
def test_iterm_version_decides_its_depth(version: str, expected: ColorLevel) -> None:
    found = on_linux(TTY, TERM_PROGRAM="iTerm.app", TERM_PROGRAM_VERSION=version, TERM="x")
    assert found.level is expected


def test_apple_terminal_has_256_colors() -> None:
    found = on_linux(TTY, TERM_PROGRAM="Apple_Terminal", TERM="xterm")
    assert found.reason == "Apple Terminal (TERM_PROGRAM=Apple_Terminal)"
    assert found.level is ColorLevel.ANSI256


@pytest.mark.parametrize("name", ["GITHUB_ACTIONS", "GITEA_ACTIONS", "CIRCLECI"])
def test_ci_services_with_truecolor_logs(name: str) -> None:
    found = on_linux(TTY, **{"CI": "true", name: "true", "TERM": "dumb-ish"})
    assert found.level is ColorLevel.TRUECOLOR
    assert found.reason == f"CI service with color logs ({name} is set)"


@pytest.mark.parametrize("name", ["TRAVIS", "APPVEYOR", "GITLAB_CI", "BUILDKITE", "DRONE"])
def test_ci_services_with_basic_color_logs(name: str) -> None:
    assert on_linux(TTY, **{"CI": "1", name: "", "COLORTERM": "truecolor"}).level == 1


def test_codeship_and_unknown_ci() -> None:
    assert on_linux(TTY, CI="1", CI_NAME="codeship").level is ColorLevel.BASIC
    unknown = on_linux(TTY, CI="woodpecker", COLORTERM="truecolor")
    assert unknown.level is ColorLevel.NONE
    assert unknown.reason == "CI is set and the service is not known to show color"
    assert on_linux(TTY, GITHUB_ACTIONS="true").level is ColorLevel.NONE


def test_ci_is_still_piped_unless_forced() -> None:
    assert on_linux(PIPE, CI="1", GITHUB_ACTIONS="1").level is ColorLevel.NONE
    assert on_linux(PIPE, CI="1", GITHUB_ACTIONS="1", FORCE_COLOR="true").level == 3


def test_azure_pipelines_has_color_even_when_piped() -> None:
    found = on_linux(PIPE, TF_BUILD="True", AGENT_NAME="Hosted")
    assert (found.level, found.reason) == (
        ColorLevel.BASIC,
        "Azure Pipelines (TF_BUILD, AGENT_NAME)",
    )
    assert on_linux(PIPE, TF_BUILD="True").level is ColorLevel.NONE
    assert on_linux(PIPE, TF_BUILD="1", AGENT_NAME="a", FORCE_COLOR="0").level == 0


@pytest.mark.parametrize(
    ("version", "expected"),
    [("9.1.2", 1), ("9.01.0", 1), ("10.0", 1), ("2023.05", 1), ("9.0.1", 0), ("8.1", 0)],
)
def test_teamcity_has_color_from_9_1(version: str, expected: int) -> None:
    assert on_linux(TTY, TEAMCITY_VERSION=version, TERM="xterm").level == expected


@pytest.mark.parametrize(
    ("colors", "expected"),
    [
        (16_777_216, ColorLevel.TRUECOLOR),
        (16_777_215, ColorLevel.ANSI256),
        (256, ColorLevel.ANSI256),
        (255, ColorLevel.BASIC),
        (8, ColorLevel.BASIC),
        (7, ColorLevel.NONE),
        (0, ColorLevel.NONE),
    ],
)
def test_terminfo_decides_an_unknown_term(colors: int, expected: ColorLevel) -> None:
    asked: list[str] = []

    def lookup(term: str) -> int:
        asked.append(term)
        return colors

    found = detect(TTY, env={"TERM": "foot"}, platform="linux", terminfo=lookup)
    assert asked == ["foot"]
    assert found.level is expected
    assert found.reason == f"terminfo for TERM=foot declares {colors} colors"


def test_terminfo_only_raises_the_level_from_the_name() -> None:
    def detect_with(colors: int | None) -> ColorLevel:
        env = {"TERM": "xterm-direct"}
        return detect(TTY, env=env, platform="linux", terminfo=lambda t: colors).level

    assert detect_with(16_777_216) is ColorLevel.TRUECOLOR
    assert detect_with(0) is ColorLevel.BASIC
    assert detect_with(None) is ColorLevel.BASIC
    same = detect(TTY, env={"TERM": "xterm"}, platform="linux", terminfo=lambda t: 8)
    assert same.reason == "TERM=xterm"


def test_terminfo_is_not_asked_without_a_term() -> None:
    def lookup(term: str) -> int:
        raise AssertionError(term)

    assert detect(TTY, env={}, platform="linux", terminfo=lookup).level is ColorLevel.NONE


def test_a_term_with_control_characters_is_shown_escaped() -> None:
    term = "xterm" + chr(27) + "[31m"
    found = on_linux(TTY, TERM=term)
    assert found.reason == f"TERM={term!r}"
    assert chr(27) not in found.reason
