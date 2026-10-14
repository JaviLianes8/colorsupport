"""Detect the color level of a stream, explained, with every input injectable."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable, Mapping
from typing import Any, Literal

from ._conventions import read_override
from ._level import ColorLevel, Detection
from ._terminal import ci_level, term_level
from ._terminfo import terminfo_colors
from ._windows import windows_level

When = Literal["auto", "always", "never"]
Terminfo = Callable[[str], int | None]


def detect(
    stream: Any = None,
    *,
    env: Mapping[str, str] | None = None,
    when: When = "auto",
    platform: str | None = None,
    windows_build: int | None = None,
    vt: bool | None = None,
    terminfo: Terminfo | None = None,
) -> Detection:
    """Report the color level of stream and why it was chosen.

    stream is any object with `isatty()` and defaults to sys.stdout at call time. Every
    other input defaults to the real one: env to os.environ, platform to sys.platform,
    windows_build to the running build, vt to the console mode of stream on Windows, and
    terminfo to `terminfo_colors` reading the terminfo database named by env.

    when is the program's own `--color` choice: "always" turns color on past NO_COLOR and
    the other switches, "never" turns it off, "auto" (the default) reads the environment.
    Detection never raises for a broken or closed stream; an unknown `when` raises
    ValueError.
    """
    env = os.environ if env is None else env
    override = read_override(env, when)
    if override is not None and override.exact:
        return Detection(override.level, override.reason)
    floor = ColorLevel.NONE if override is None else override.level
    prefix = "" if override is None else f"{override.reason}; "
    # Azure Pipelines shows color although its output is piped (supports-color).
    if "TF_BUILD" in env and "AGENT_NAME" in env:
        return Detection(ColorLevel.BASIC, f"{prefix}Azure Pipelines (TF_BUILD, AGENT_NAME)")
    stream = sys.stdout if stream is None else stream
    if override is None and not _isatty(stream):
        return Detection(ColorLevel.NONE, "the stream is not a terminal")
    found = _terminal(stream, env, platform, windows_build, vt, terminfo)
    if found is None:
        if override is not None:
            return Detection(floor, f"{prefix}the terminal does not say how many colors")
        return Detection(ColorLevel.NONE, "the terminal does not say it shows color")
    level, reason = found
    return Detection(max(level, floor), prefix + reason)


def level(
    stream: Any = None,
    *,
    env: Mapping[str, str] | None = None,
    when: When = "auto",
    platform: str | None = None,
    windows_build: int | None = None,
    vt: bool | None = None,
    terminfo: Terminfo | None = None,
) -> ColorLevel:
    """Return the color level of stream; the arguments are those of `detect`."""
    found = detect(
        stream,
        env=env,
        when=when,
        platform=platform,
        windows_build=windows_build,
        vt=vt,
        terminfo=terminfo,
    )
    return found.level


def supports_color(
    stream: Any = None,
    *,
    env: Mapping[str, str] | None = None,
    when: When = "auto",
    platform: str | None = None,
    windows_build: int | None = None,
    vt: bool | None = None,
    terminfo: Terminfo | None = None,
) -> bool:
    """Return whether stream can show any color; the arguments are those of `detect`."""
    found = detect(
        stream,
        env=env,
        when=when,
        platform=platform,
        windows_build=windows_build,
        vt=vt,
        terminfo=terminfo,
    )
    return found.level > ColorLevel.NONE


def _terminal(
    stream: Any,
    env: Mapping[str, str],
    platform: str | None,
    windows_build: int | None,
    vt: bool | None,
    terminfo: Terminfo | None,
) -> tuple[ColorLevel, str] | None:
    if env.get("TERM") == "dumb":
        return ColorLevel.NONE, "TERM=dumb"
    if (sys.platform if platform is None else platform) == "win32":
        found = windows_level(stream, env, vt, windows_build)
        if found is not None:
            return found
    found = ci_level(env)
    if found is not None:
        return found

    def lookup(term: str) -> int | None:
        return terminfo_colors(term, env)

    return term_level(env, lookup if terminfo is None else terminfo)


def _isatty(stream: Any) -> bool:
    try:
        return stream is not None and bool(stream.isatty())
    except (AttributeError, ValueError, OSError):
        return False
