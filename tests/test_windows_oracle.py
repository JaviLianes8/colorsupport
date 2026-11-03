"""Console mode arithmetic and the Windows decision table, checked against oracles.

The oracles are written here from GUIDE and README, independently of the library: a
console processes escapes when processed output (0x0001) and virtual terminal processing
(0x0004) are both set; enable_vt sets exactly those two bits, keeps every other bit, and
reports what SetConsoleMode said. Modes cover every combination of the low ten bits and
seeded random 32-bit values.
"""

from __future__ import annotations

import random
import sys
from collections.abc import Iterator

import pytest
from conftest import TTY

from colorsupport import ColorLevel, detect, enable_vt
from colorsupport._windows import vt_enabled

REQUIRED = 0x0001 | 0x0004
MODES = [*range(1024), *random.Random(20261103).sample(range(2**32), 600), 2**32 - 1]


class Kernel:
    """A SetConsoleMode stand-in that records its calls and answers a fixed value."""

    def __init__(self, answer: int) -> None:
        self.answer = answer
        self.calls: list[tuple[object, int]] = []

    def SetConsoleMode(self, handle: object, mode: int) -> int:
        self.calls.append((handle, mode))
        return self.answer


@pytest.fixture
def console(monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[str, object]]:
    state: dict[str, object] = {"mode": 0, "kernel": Kernel(1)}
    monkeypatch.setattr("colorsupport._windows.console_mode", lambda stream: state["mode"])
    monkeypatch.setattr("colorsupport._windows._handle", lambda stream: ("handle", stream))
    monkeypatch.setattr("colorsupport._windows._kernel32", lambda: state["kernel"])
    yield state


@pytest.mark.parametrize("answer", [0, 1, 7, -1])
def test_enable_vt_matches_the_mode_oracle(console: dict[str, object], answer: int) -> None:
    stream = object()
    for mode in MODES:
        kernel = Kernel(answer)
        console.update(mode=mode, kernel=kernel)
        already = mode & REQUIRED == REQUIRED
        expected = True if already else answer != 0
        assert enable_vt(stream) is expected, hex(mode)
        assert kernel.calls == ([] if already else [(("handle", stream), mode | REQUIRED)])


def test_enable_vt_without_a_console_never_sets_a_mode(console: dict[str, object]) -> None:
    kernel = Kernel(1)
    console.update(mode=None, kernel=kernel)
    assert enable_vt(object()) is False
    assert kernel.calls == []


def test_vt_enabled_matches_the_mode_oracle(console: dict[str, object]) -> None:
    for mode in MODES:
        console["mode"] = mode
        assert vt_enabled(object()) is (mode & REQUIRED == REQUIRED), hex(mode)
    console["mode"] = None
    assert vt_enabled(object()) is None


def test_enable_vt_reads_stdout_when_it_is_called(
    console: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    for stdout in (object(), object()):
        kernel = Kernel(1)
        console.update(mode=0, kernel=kernel)
        monkeypatch.setattr(sys, "stdout", stdout)
        assert enable_vt() is True
        assert kernel.calls == [(("handle", stdout), REQUIRED)]


BUILDS = [0, 1, 10585, 10586, 10587, 14930, 14931, 14932, 22631, 2**64, 2**64 + 1]
HOSTS = [{}, {"ConEmuANSI": "ON"}, {"ConEmuANSI": "on"}, {"ConEmuANSI": ""}, {"ANSICON": "1"}]
HOSTS += [{"ANSICON": ""}, {"WT_SESSION": ""}, {"WT_SESSION": "x", "ANSICON": "1"}]


def oracle(vt: bool, env: dict[str, str], build: int) -> tuple[ColorLevel, str]:
    if env.get("ConEmuANSI") == "ON":
        return ColorLevel.ANSI256, "ConEmu processes ANSI sequences (ConEmuANSI=ON)"
    if env.get("ANSICON", "") != "":
        return ColorLevel.BASIC, "ANSICON is set"
    if not vt:
        return ColorLevel.NONE, "the Windows console has virtual terminal processing off"
    if "WT_SESSION" in env:
        return ColorLevel.TRUECOLOR, "Windows Terminal (WT_SESSION is set)"
    shown = str(build) if build < 2**64 else "a large integer"
    reason = f"Windows console with VT processing, build {shown}"
    if build >= 14931:
        return ColorLevel.TRUECOLOR, reason
    return (ColorLevel.ANSI256 if build >= 10586 else ColorLevel.BASIC), reason


def test_windows_decisions_match_the_table_oracle() -> None:
    for vt in (True, False):
        for env in HOSTS:
            for build in BUILDS:
                found = detect(
                    TTY, env=env, platform="win32", vt=vt, windows_build=build, terminfo=None
                )
                assert (found.level, found.reason) == oracle(vt, env, build), (vt, env, build)
