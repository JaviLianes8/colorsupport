"""Console mode contracts, including real escape rendering in a private buffer."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from colorsupport import enable_vt

SRC = Path(__file__).resolve().parents[1] / "src"


def test_enable_vt_defaults_to_current_stdout(monkeypatch: pytest.MonkeyPatch) -> None:
    stdout, stderr = object(), object()
    seen: list[object] = []

    def mode(stream: object) -> int | None:
        seen.append(stream)
        return 5 if stream is stdout else None

    with monkeypatch.context() as patch:
        patch.setattr(sys, "stdout", stdout)
        patch.setattr(sys, "stderr", stderr)
        patch.setattr("colorsupport._windows.console_mode", mode)
        default = enable_vt()
        explicit = enable_vt(stderr)
    assert default is True and explicit is False
    assert seen == [stdout, stderr]


CHILD = r"""
import ctypes, json, msvcrt, os, sys
from ctypes import wintypes as w
sys.path.insert(0, sys.argv[1])
from colorsupport import detect, enable_vt
from colorsupport._windows import console_mode
k = ctypes.WinDLL("kernel32", use_last_error=True)
k.CreateConsoleScreenBuffer.argtypes = [w.DWORD, w.DWORD, w.LPVOID, w.DWORD, w.LPVOID]
k.CreateConsoleScreenBuffer.restype = w.HANDLE
k.SetConsoleMode.argtypes = [w.HANDLE, w.DWORD]
k.SetConsoleCursorPosition.argtypes = [w.HANDLE, w.DWORD]
k.WriteConsoleW.argtypes = [w.HANDLE, w.LPCWSTR, w.DWORD, ctypes.POINTER(w.DWORD), w.LPVOID]
k.ReadConsoleOutputCharacterW.argtypes = [w.HANDLE, w.LPWSTR, w.DWORD, w.DWORD,
                                        ctypes.POINTER(w.DWORD)]
h = k.CreateConsoleScreenBuffer(0xC0000000, 3, None, 1, None)
assert h != ctypes.c_void_p(-1).value, ctypes.get_last_error()
rows = []
with os.fdopen(msvcrt.open_osfhandle(h, os.O_TEXT), "w") as console:
    for initial in (0, 1, 3, 4, 5, 7):
        assert k.SetConsoleMode(h, initial)
        before = int(detect(console, env={}, windows_build=14931).level)
        enabled = enable_vt(console)
        after = console_mode(console)
        again = enable_vt(console)
        repeated = console_mode(console)
        count = w.DWORD()
        assert k.SetConsoleCursorPosition(h, 0)
        assert k.WriteConsoleW(h, " " * 20, 20, ctypes.byref(count), None)
        assert k.SetConsoleCursorPosition(h, 0)
        seq = "\x1b[31mX\x1b[0m"
        assert k.WriteConsoleW(h, seq, len(seq), ctypes.byref(count), None)
        buf = ctypes.create_unicode_buffer(20)
        assert k.ReadConsoleOutputCharacterW(h, buf, 19, 0, ctypes.byref(count))
        rows.append([initial, before, enabled, after, again, repeated, buf.value])
with open(sys.argv[2], "w", encoding="utf-8") as output:
    json.dump(rows, output)
"""


@pytest.mark.skipif(sys.platform != "win32", reason="needs a Windows console")
def test_real_console_requires_both_flags_and_preserves_modes(tmp_path: Path) -> None:
    script, output = tmp_path / "console.py", tmp_path / "console.json"
    script.write_text(CHILD, encoding="utf-8")
    done = subprocess.run(
        [sys.executable, "-I", "-B", str(script), str(SRC), str(output)],
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        timeout=60,
        check=False,
    )
    assert done.returncode == 0
    for initial, before, enabled, after, again, repeated, screen in json.loads(output.read_text()):
        assert before == (3 if initial & 5 == 5 else 0), initial
        assert enabled is True and again is True
        assert after == repeated == initial | 5, initial
        assert screen == "X" + " " * 18, (initial, screen)
