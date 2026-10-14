"""Windows consoles: the VT mode, known hosts, the build number and `enable_vt`."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import PIPE, TTY

from colorsupport import ColorLevel, detect, enable_vt
from colorsupport._windows import console_mode, vt_enabled, windows_build

SRC = Path(__file__).resolve().parents[1] / "src"


def on_windows(
    vt: bool | None, build: int = 19045, stream: object = TTY, **env: str
) -> tuple[ColorLevel, str]:
    found = detect(
        stream, env=env, platform="win32", vt=vt, windows_build=build, terminfo=lambda t: None
    )
    return (found.level, found.reason)


def test_a_console_without_vt_processing_has_no_color() -> None:
    assert on_windows(False, WT_SESSION="x", COLORTERM="truecolor") == (
        ColorLevel.NONE,
        "the Windows console has virtual terminal processing off",
    )


def test_windows_terminal_is_truecolor() -> None:
    assert on_windows(True, build=10586, WT_SESSION="") == (
        ColorLevel.TRUECOLOR,
        "Windows Terminal (WT_SESSION is set)",
    )


@pytest.mark.parametrize(
    ("build", "expected"),
    [
        (22631, ColorLevel.TRUECOLOR),
        (14931, ColorLevel.TRUECOLOR),
        (14930, ColorLevel.ANSI256),
        (10586, ColorLevel.ANSI256),
        (10585, ColorLevel.BASIC),
        (0, ColorLevel.BASIC),
    ],
)
def test_the_build_decides_a_vt_console(build: int, expected: ColorLevel) -> None:
    assert on_windows(True, build=build) == (
        expected,
        f"Windows console with VT processing, build {build}",
    )


def test_conemu_and_ansicon_color_any_console() -> None:
    assert on_windows(False, ConEmuANSI="ON") == (
        ColorLevel.ANSI256,
        "ConEmu processes ANSI sequences (ConEmuANSI=ON)",
    )
    assert on_windows(False, ConEmuANSI="OFF")[0] is ColorLevel.NONE
    assert on_windows(False, ANSICON="80x25 (80x300)") == (ColorLevel.BASIC, "ANSICON is set")
    assert on_windows(False, ANSICON="")[0] is ColorLevel.NONE


def test_a_terminal_that_is_not_a_console_falls_back_to_term() -> None:
    assert on_windows(None, TERM="xterm-256color") == (ColorLevel.ANSI256, "TERM=xterm-256color")
    assert on_windows(None, WT_SESSION="x")[0] is ColorLevel.NONE


def test_windows_rules_apply_only_on_windows() -> None:
    found = detect(TTY, env={"WT_SESSION": "x"}, platform="linux", vt=True, windows_build=99999)
    assert found.level is ColorLevel.NONE


def test_term_dumb_and_forcing_still_apply_on_windows() -> None:
    assert on_windows(True, TERM="dumb")[0] is ColorLevel.NONE
    assert on_windows(False, stream=PIPE, FORCE_COLOR="true")[0] is ColorLevel.BASIC
    assert on_windows(True, stream=PIPE)[0] is ColorLevel.NONE


@pytest.mark.parametrize("stream", [io.StringIO(), PIPE, None, object()])
def test_non_console_streams_have_no_console_mode(stream: object) -> None:
    assert console_mode(stream) is None
    assert vt_enabled(stream) is None
    assert enable_vt(stream if stream is not None else io.StringIO()) is False


def test_a_closed_or_pipe_file_has_no_console_mode(tmp_path: Path) -> None:
    closed = open(tmp_path / "f", "w")  # noqa: SIM115
    closed.close()
    assert console_mode(closed) is None
    read_end, write_end = os.pipe()
    try:
        with os.fdopen(write_end, "w", closefd=False) as pipe:
            assert console_mode(pipe) is None
    finally:
        os.close(read_end)
        os.close(write_end)


def test_a_bad_file_descriptor_has_no_console_mode() -> None:
    class Broken:
        def fileno(self) -> int:
            return 987654

    assert console_mode(Broken()) is None


def test_windows_build_reads_the_running_system() -> None:
    if sys.platform == "win32":
        assert windows_build() == sys.getwindowsversion().build > 0
    else:
        assert windows_build() == 0


CHILD = """
import json, sys
sys.path.insert(0, sys.argv[1])
from colorsupport import detect, enable_vt
from colorsupport._windows import vt_enabled
import ctypes, msvcrt
console = open("CONOUT$", "w")
# Start from a console with processed output and wrapping but no VT processing.
ctypes.windll.kernel32.SetConsoleMode(msvcrt.get_osfhandle(console.fileno()), 0x0003)
before = vt_enabled(console)
off = detect(console, env={}).level
turned = enable_vt(console)
again = enable_vt(console)
after = vt_enabled(console)
on = detect(console, env={}).level
json.dump([before, int(off), turned, again, after, int(on)], open(sys.argv[2], "w"))
"""


@pytest.mark.skipif(sys.platform != "win32", reason="needs a Windows console")
def test_a_real_console_is_read_and_switched(tmp_path: Path) -> None:
    script, out = tmp_path / "child.py", tmp_path / "out.json"
    script.write_text(CHILD, encoding="utf-8")
    # CREATE_NO_WINDOW gives the child a console of its own that is never shown.
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    command = [sys.executable, "-I", "-B", str(script), str(SRC), str(out)]
    done = subprocess.run(command, creationflags=flags, timeout=60, check=False)
    assert done.returncode == 0
    before, off, turned, again, after, on = json.loads(out.read_text(encoding="utf-8"))
    assert (before, off) == (False, 0)
    assert (turned, again, after) == (True, True, True)
    assert on == (3 if windows_build() >= 14931 else 2)
