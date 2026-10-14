"""Read the color depth of a terminal from TERM, COLORTERM, its program and CI markers."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping

from ._level import ColorLevel

Found = tuple[ColorLevel, str]

# The rules and names below follow the supports-color package (chalk), see the README.
_CI_TRUECOLOR = ("GITHUB_ACTIONS", "GITEA_ACTIONS", "CIRCLECI")
_CI_BASIC = ("TRAVIS", "APPVEYOR", "GITLAB_CI", "BUILDKITE", "DRONE")
_TRUECOLOR_TERMS = ("xterm-kitty", "xterm-ghostty", "wezterm")
_TEAMCITY = re.compile(r"9\.0*[1-9]\d*\.|\d{2,}\.", re.ASCII)
_TERM_256 = re.compile(r"-256(?:color)?\Z", re.IGNORECASE)
_TERM_BASIC = re.compile(r"^screen|^xterm|^vt100|^vt220|^rxvt|color|ansi|cygwin|linux", re.I)
# COLORTERM values that announce 24-bit color, from termstandard/colors and anstyle-query.
_COLORTERM_TRUECOLOR = ("truecolor", "24bit")


def ci_level(env: Mapping[str, str]) -> Found | None:
    """Decide for a CI service, or None when this is not CI."""
    if "CI" in env:
        for name in _CI_TRUECOLOR:
            if name in env:
                return ColorLevel.TRUECOLOR, f"CI service with color logs ({name} is set)"
        for name in _CI_BASIC:
            if name in env:
                return ColorLevel.BASIC, f"CI service with color logs ({name} is set)"
        if env.get("CI_NAME") == "codeship":
            return ColorLevel.BASIC, "CI service with color logs (CI_NAME=codeship)"
        return ColorLevel.NONE, "CI is set and the service is not known to show color"
    if "TEAMCITY_VERSION" in env:
        if _TEAMCITY.match(env["TEAMCITY_VERSION"]):
            return ColorLevel.BASIC, "TeamCity 9.1 or later"
        return ColorLevel.NONE, "TeamCity before 9.1 shows no color"
    return None


def term_level(env: Mapping[str, str], terminfo: Callable[[str], int | None]) -> Found | None:
    """Decide from COLORTERM, TERM, TERM_PROGRAM and terminfo, or None when nothing says."""
    term = env.get("TERM", "")
    colorterm = env.get("COLORTERM", "")
    if colorterm in _COLORTERM_TRUECOLOR:
        return ColorLevel.TRUECOLOR, f"COLORTERM={colorterm}"
    if term in _TRUECOLOR_TERMS:
        return ColorLevel.TRUECOLOR, f"TERM={term}"
    program = env.get("TERM_PROGRAM", "")
    if program == "iTerm.app":
        if _major(env.get("TERM_PROGRAM_VERSION", "")) >= 3:
            return ColorLevel.TRUECOLOR, "iTerm2 3 or later (TERM_PROGRAM=iTerm.app)"
        return ColorLevel.ANSI256, "iTerm2 before 3 (TERM_PROGRAM=iTerm.app)"
    if program == "Apple_Terminal":
        return ColorLevel.ANSI256, "Apple Terminal (TERM_PROGRAM=Apple_Terminal)"
    found = _by_name(term)
    by_info = _by_terminfo(term, terminfo)
    if by_info is not None and (found is None or by_info[0] > found[0]):
        found = by_info
    if found is not None:
        return found
    if "COLORTERM" in env:
        return ColorLevel.BASIC, "COLORTERM is set"
    return None


def shown(value: str) -> str:
    """An environment value as it can safely appear in a reason."""
    if value.isprintable() and len(value) <= 40:
        return value
    return repr(value[:40])


def _major(version: str) -> int:
    # The leading ASCII digits; supports-color reads the part before the first dot.
    match = re.match(r"[0-9]+", version)
    digits = match.group().lstrip("0") if match else ""
    return int(digits) if 0 < len(digits) <= 6 else (10**6 if digits else 0)


def _by_name(term: str) -> Found | None:
    if _TERM_256.search(term):
        return ColorLevel.ANSI256, f"TERM={shown(term)}"
    if _TERM_BASIC.search(term):
        return ColorLevel.BASIC, f"TERM={shown(term)}"
    return None


def _by_terminfo(term: str, terminfo: Callable[[str], int | None]) -> Found | None:
    if not term:
        return None
    colors = terminfo(term)
    if colors is None:
        return None
    reason = f"terminfo for TERM={shown(term)} declares {colors} colors"
    if colors >= 16_777_216:
        return ColorLevel.TRUECOLOR, reason
    if colors >= 256:
        return ColorLevel.ANSI256, reason
    if colors >= 8:
        return ColorLevel.BASIC, reason
    return ColorLevel.NONE, reason
