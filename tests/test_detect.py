"""Defaults resolved at call time, broken streams, and the two shortcut functions."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from conftest import PIPE, TTY
from test_terminfo import entry, install

from colorsupport import ColorLevel, detect, level, supports_color


class Raising:
    def __init__(self, error: Exception) -> None:
        self.error = error

    def isatty(self) -> bool:
        raise self.error


@pytest.mark.parametrize("error", [ValueError("closed"), OSError("gone"), AttributeError("x")])
def test_a_stream_that_fails_isatty_is_not_a_terminal(error: Exception) -> None:
    found = detect(Raising(error), env={"COLORTERM": "truecolor"}, platform="linux")
    assert found.level is ColorLevel.NONE


def test_a_stream_without_isatty_or_none_is_not_a_terminal() -> None:
    assert detect(object(), env={"COLORTERM": "truecolor"}).level is ColorLevel.NONE
    closed = io.StringIO()
    closed.close()
    assert detect(closed, env={"COLORTERM": "truecolor"}).level is ColorLevel.NONE


def test_stream_defaults_to_sys_stdout_at_call_time(monkeypatch: pytest.MonkeyPatch) -> None:
    env = {"COLORTERM": "truecolor"}
    monkeypatch.setattr("sys.stdout", TTY)
    assert detect(env=env, platform="linux").level is ColorLevel.TRUECOLOR
    monkeypatch.setattr("sys.stdout", PIPE)
    assert detect(env=env, platform="linux").level is ColorLevel.NONE
    monkeypatch.setattr("sys.stdout", None)
    assert detect(env=env, platform="linux").level is ColorLevel.NONE


def test_env_and_platform_default_to_the_process(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("NO_COLOR", "FORCE_COLOR", "CLICOLOR_FORCE", "CLICOLOR", "TF_BUILD", "CI"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("FORCE_COLOR", "2")
    assert detect(PIPE).level is ColorLevel.ANSI256
    monkeypatch.setenv("FORCE_COLOR", "true")
    monkeypatch.setenv("TERM", "dumb")
    monkeypatch.setattr("sys.platform", "win32")
    assert detect(TTY, vt=False).reason == "FORCE_COLOR='true' turns color on; TERM=dumb"
    monkeypatch.delenv("TERM")
    assert detect(TTY, vt=False).reason.endswith("virtual terminal processing off")


def test_terminfo_defaults_to_the_database_named_by_env(tmp_path: Path) -> None:
    install(tmp_path, "foot", entry(16_777_216, magic=0o1036))
    env = {"TERM": "foot", "TERMINFO": str(tmp_path)}
    assert detect(TTY, env=env, platform="linux").level is ColorLevel.TRUECOLOR
    assert detect(TTY, env={"TERM": "foot"}, platform="linux", terminfo=lambda t: 256).level == 2


def test_level_and_supports_color_pass_every_argument() -> None:
    def lookup(term: str) -> int:
        return 256

    assert level(TTY, env={"TERM": "foot"}, platform="linux", terminfo=lookup) == 2
    assert level(TTY, env={}, platform="win32", vt=True, windows_build=10586) == 2
    assert level(PIPE, env={}, when="always", platform="linux", terminfo=lookup) == 1
    assert supports_color(TTY, env={}, platform="win32", vt=True, windows_build=1)
    assert not supports_color(TTY, env={"COLORTERM": "x"}, when="never")
    assert supports_color(PIPE, env={}, when="always", terminfo=lookup)
    assert not supports_color(TTY, env={"TERM": "foot"}, platform="linux", terminfo=lambda t: 0)
    assert not supports_color(TTY, env={}, platform="win32", vt=False, windows_build=99999)
    assert supports_color(TTY, env={"TERM": "foot"}, platform="linux", terminfo=lookup)


class Odd:
    isatty = True


@pytest.mark.parametrize("error", [RuntimeError("boom"), TypeError("no"), KeyError("k")])
def test_any_isatty_failure_means_not_a_terminal(error: Exception) -> None:
    found = detect(Raising(error), env={"COLORTERM": "truecolor"}, platform="linux")
    assert found.level is ColorLevel.NONE
    assert detect(Odd(), env={"COLORTERM": "truecolor"}).level is ColorLevel.NONE
