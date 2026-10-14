"""Windows console checks: virtual terminal processing, known hosts and the OS build."""

from __future__ import annotations

import functools
import sys
from collections.abc import Mapping
from typing import Any

from ._level import ColorLevel

# ENABLE_VIRTUAL_TERMINAL_PROCESSING, from the console mode flags in Microsoft's console docs.
VT_PROCESSING = 0x0004
# supports-color: build 10586 is the first with 256 colors, 14931 the first with truecolor.
BUILD_256 = 10586
BUILD_TRUECOLOR = 14931


@functools.cache
def _kernel32() -> Any:
    # A private handle with its own prototypes, so other libraries' settings on the shared
    # ctypes.windll instance cannot change how these calls behave.
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined,unused-ignore]
    kernel32.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel32.GetConsoleMode.restype = wintypes.BOOL
    kernel32.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.SetConsoleMode.restype = wintypes.BOOL
    return kernel32


def _handle(stream: Any) -> int | None:
    # Any failure of a foreign stream object means "not a console": detection never raises.
    try:
        fd = stream.fileno()
    except Exception:
        return None
    if sys.platform != "win32" or not isinstance(fd, int):
        return None
    import msvcrt

    try:
        return msvcrt.get_osfhandle(fd)
    except (OSError, OverflowError):
        return None


def console_mode(stream: Any) -> int | None:
    """The console output mode of stream, or None when it is not a Windows console."""
    handle = _handle(stream)
    if handle is None:
        return None
    import ctypes
    from ctypes import wintypes

    mode = wintypes.DWORD()
    if not _kernel32().GetConsoleMode(handle, ctypes.byref(mode)):
        return None
    return int(mode.value)


def vt_enabled(stream: Any) -> bool | None:
    """Whether a Windows console processes escape sequences; None if not a console."""
    mode = console_mode(stream)
    return None if mode is None else bool(mode & VT_PROCESSING)


def enable_vt(stream: Any = None) -> bool:
    """Turn on escape sequence processing for a Windows console stream.

    stream defaults to sys.stdout. Returns True when the stream is a Windows console that
    now processes escape sequences, False otherwise: the stream is not a console (a pipe, a
    file, a pty), the console is too old to accept the mode, or this is not Windows, where
    terminals need no switch. Detection never calls this; it only reads the mode.
    """
    stream = sys.stdout if stream is None else stream
    mode = console_mode(stream)
    if mode is None:
        return False
    if mode & VT_PROCESSING:
        return True
    # Consoles older than Windows 10 refuse the flag, so success means it is on.
    return bool(_kernel32().SetConsoleMode(_handle(stream), mode | VT_PROCESSING))


def windows_build() -> int:
    """The Windows build number, or 0 when it cannot be read."""
    if sys.platform != "win32":
        return 0
    return int(sys.getwindowsversion().build)


def windows_level(
    stream: Any, env: Mapping[str, str], vt: bool | None, build: int | None
) -> tuple[ColorLevel, str] | None:
    """Decide for a Windows console, or None to let the TERM rules decide (not a console)."""
    state = vt_enabled(stream) if vt is None else vt
    if state is None:
        return None
    # ConEmu and ANSICON hook the console writes themselves, whatever the console mode.
    if env.get("ConEmuANSI") == "ON":
        return ColorLevel.ANSI256, "ConEmu processes ANSI sequences (ConEmuANSI=ON)"
    if env.get("ANSICON"):
        return ColorLevel.BASIC, "ANSICON is set"
    if not state:
        return ColorLevel.NONE, "the Windows console has virtual terminal processing off"
    if "WT_SESSION" in env:
        return ColorLevel.TRUECOLOR, "Windows Terminal (WT_SESSION is set)"
    number = windows_build() if build is None else build
    if number >= BUILD_TRUECOLOR:
        return ColorLevel.TRUECOLOR, f"Windows console with VT processing, build {number}"
    if number >= BUILD_256:
        return ColorLevel.ANSI256, f"Windows console with VT processing, build {number}"
    return ColorLevel.BASIC, f"Windows console with VT processing, build {number}"
