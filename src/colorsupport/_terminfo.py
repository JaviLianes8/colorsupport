"""Read the `colors` capability from a compiled terminfo entry, without curses."""

from __future__ import annotations

import os
import struct
from collections.abc import Mapping

# The layout is described in ncurses term(5): six little-endian shorts (magic, then the
# sizes of the names, booleans, numbers, strings and string table), the names, one byte per
# boolean, a pad byte to an even offset, then the numbers. `max_colors` is the 14th number
# in ncurses include/Caps. The legacy format stores numbers as 16-bit, the extended one
# (ncurses 6.1+) as 32-bit.
_LEGACY_MAGIC = 0o432
_EXTENDED_MAGIC = 0o1036
_MAX_COLORS = 13
_HEADER = struct.Struct("<6h")
# The extended format limits an entry to 32768 bytes; nothing larger is read.
_MAX_SIZE = 32768

# Locations ncurses builds commonly compile in, searched after the environment ones.
SYSTEM_DIRS = (
    "/etc/terminfo",
    "/lib/terminfo",
    "/usr/share/terminfo",
    "/usr/lib/terminfo",
    "/usr/share/lib/terminfo",
)


def parse_colors(data: bytes) -> int | None:
    """Return the `colors` number of a compiled entry, or None if absent or unreadable."""
    value = _raw_colors(data)
    # -1 marks an absent capability and -2 a cancelled one.
    return value if value is not None and value >= 0 else None


def _raw_colors(data: bytes) -> int | None:
    """The stored number, negative when absent, or None when the entry is not readable."""
    if len(data) < _HEADER.size:
        return None
    magic, names, booleans, numbers, _, _ = _HEADER.unpack_from(data)
    if magic == _LEGACY_MAGIC:
        number = struct.Struct("<h")
    elif magic == _EXTENDED_MAGIC:
        number = struct.Struct("<i")
    else:
        return None
    if names < 0 or booleans < 0 or numbers < 0:
        return None
    if numbers <= _MAX_COLORS:
        return -1
    start = _HEADER.size + names + booleans
    start += start % 2
    position = start + _MAX_COLORS * number.size
    if position + number.size > len(data):
        return None
    (value,) = number.unpack_from(data, position)
    return int(value)


def search_dirs(env: Mapping[str, str]) -> list[str]:
    """The terminfo directories in the order ncurses searches them."""
    dirs: list[str] = []
    if env.get("TERMINFO"):
        dirs.append(env["TERMINFO"])
    if env.get("HOME"):
        dirs.append(os.path.join(env["HOME"], ".terminfo"))
    if "TERMINFO_DIRS" in env:
        for part in env["TERMINFO_DIRS"].split(":"):
            # An empty entry stands for the system location.
            dirs.extend([part] if part else SYSTEM_DIRS)
    dirs.extend(SYSTEM_DIRS)
    return list(dict.fromkeys(dirs))


def terminfo_colors(term: str, env: Mapping[str, str] | None = None) -> int | None:
    """Return how many colors the terminfo entry for `term` declares, or None.

    The entry is looked up like ncurses does: `TERMINFO`, `~/.terminfo` (from `HOME`),
    `TERMINFO_DIRS`, then the usual system folders, under both the letter and the hex
    subfolder layouts. env defaults to os.environ. Names that could leave the folder
    (holding a slash, a backslash or a NUL, or starting with a dot) are refused.
    """
    env = os.environ if env is None else env
    if not term or term.startswith(".") or any(c in term for c in "/\\\0"):
        return None
    first = term[0]
    for folder in search_dirs(env):
        for sub in (first, f"{ord(first):02x}"):
            value = _read(os.path.join(folder, sub, term))
            # Like ncurses, the first readable entry wins, even when it has no colors.
            if value is not None:
                return value if value >= 0 else None
    return None


def _read(path: str) -> int | None:
    try:
        with open(path, "rb") as entry:
            data = entry.read(_MAX_SIZE + 1)
    except (OSError, ValueError):
        return None
    if len(data) > _MAX_SIZE:
        return None
    return _raw_colors(data)
