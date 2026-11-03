"""The terminfo reader and lookup, checked against oracles written here from ncurses term(5).

Entry oracle: a 12-byte header of six little-endian shorts (magic, name, boolean, number,
string and table sizes); magic 0o432 stores numbers as 16-bit, 0o1036 as 32-bit; the
numbers start after the names and booleans, aligned to an even offset; `colors` is number
13. Fewer than 14 numbers or a negative value means absent. Lookup oracle: GUIDE order.
Inputs are seeded synthetic entries and names, not external vectors.
"""

from __future__ import annotations

import os
import random
import struct
from pathlib import Path

import pytest

from colorsupport import terminfo_colors
from colorsupport._terminfo import parse_colors

UNREADABLE, ABSENT = "unreadable", "absent"


def oracle(data: bytes) -> int | str:
    if len(data) < 12:
        return UNREADABLE
    magic, names, booleans, numbers = struct.unpack("<4h", data[:8])
    width = {0o432: 2, 0o1036: 4}.get(magic)
    if width is None or min(names, booleans, numbers) < 0:
        return UNREADABLE
    if numbers < 14:
        return ABSENT
    offset = 12 + names + booleans
    offset += offset % 2
    at = offset + 13 * width
    if at + width > len(data):
        return UNREADABLE
    value = int.from_bytes(data[at : at + width], "little", signed=True)
    return value if value >= 0 else ABSENT


def random_entry(rng: random.Random) -> bytes:
    magic = rng.choice([0o432, 0o1036, 0o432, 0o1036, 0o433, 0, -0o432])
    width = 4 if magic == 0o1036 else 2
    sizes = [rng.choice([0, 1, 2, 3, 7, 40, -1, rng.randrange(-5, 60)]) for _ in range(2)]
    count = rng.choice([0, 13, 14, 15, 40, -1, rng.randrange(0, 50)])
    names = bytes(rng.randrange(256) for _ in range(max(sizes[0], 0)))
    flags = bytes(rng.randrange(256) for _ in range(max(sizes[1], 0)))
    pad = b"\0" * ((12 + len(names) + len(flags)) % 2 if rng.randrange(4) else 1)
    limit = 2 ** (8 * width - 1)
    pool = [-2, -1, 0, 1, 7, 8, 255, 256, limit - 1, -limit, rng.randrange(-limit, limit)]
    numbers = [rng.choice(pool) for _ in range(max(count, 0))]
    body = struct.pack(f"<{len(numbers)}{'h' if width == 2 else 'i'}", *numbers)
    header = struct.pack("<6h", magic, sizes[0], sizes[1], count, 0, 0)
    data = header + names + flags + pad + body
    return data[: rng.randrange(len(data) + 1)] if rng.randrange(5) == 0 else data


ENTRIES = [random_entry(random.Random(seed)) for seed in range(4000)]


def test_parse_colors_matches_the_entry_oracle() -> None:
    for data in ENTRIES:
        expected = oracle(data)
        assert parse_colors(data) == (expected if isinstance(expected, int) else None), data


def test_lookup_takes_the_first_readable_entry(tmp_path: Path) -> None:
    rng = random.Random(7)
    for n in range(150):
        first, second = rng.choice(ENTRIES), rng.choice(ENTRIES)
        base = tmp_path / str(n)
        for folder, data in (("one", first), ("two", second)):
            (base / folder / "t").mkdir(parents=True)
            (base / folder / "t" / "term").write_bytes(data)
        env = {"TERMINFO": str(base / "one"), "TERMINFO_DIRS": str(base / "two")}
        a, b = oracle(first), oracle(second)
        chosen = a if a != UNREADABLE else b
        assert terminfo_colors("term", env) == (chosen if isinstance(chosen, int) else None)


SYSTEM: tuple[str, ...] = (
    () if os.name == "nt" else ("/etc/terminfo", "/lib/terminfo", "/usr/share/terminfo")
)
SYSTEM += () if os.name == "nt" else ("/usr/lib/terminfo", "/usr/share/lib/terminfo")


def expected_paths(term: str, env: dict[str, str]) -> list[str]:
    if not term or term[0] == "." or set(term) & set("/\\:\0"):
        return []
    dirs = [env["TERMINFO"]] if env.get("TERMINFO", "") else []
    dirs += [os.path.join(env["HOME"], ".terminfo")] if env.get("HOME", "") else []
    for part in env["TERMINFO_DIRS"].split(os.pathsep) if "TERMINFO_DIRS" in env else []:
        dirs += [part] if part else list(SYSTEM)
    unique = list(dict.fromkeys([*dirs, *SYSTEM]))
    return [os.path.join(d, s, term) for d in unique for s in (term[0], f"{ord(term[0]):02x}")]


def random_case(rng: random.Random) -> tuple[str, dict[str, str]]:
    letters = "ab.:/\\\0xX-9é "
    term = "".join(rng.choices(letters, k=rng.randrange(5)))
    env: dict[str, str] = {}
    for name in ("TERMINFO", "HOME", "TERMINFO_DIRS"):
        if rng.randrange(3):
            parts = [rng.choice(["", "d1", "d2", "/x", "d1"]) for _ in range(rng.randrange(4))]
            env[name] = os.pathsep.join(parts)
    return term, env


@pytest.mark.parametrize("hit", [None, 0, 1, 2, 5])
def test_lookup_order_and_name_checks_match_the_oracle(
    monkeypatch: pytest.MonkeyPatch, hit: int | None
) -> None:
    rng = random.Random(2026 + (hit or 0))
    for _ in range(1500):
        term, env = random_case(rng)
        tried: list[str] = []

        def read(path: str, tried: list[str] = tried) -> int | None:
            tried.append(path)
            return 256 if len(tried) - 1 == hit else None

        monkeypatch.setattr("colorsupport._terminfo._read", read)
        expected = expected_paths(term, env)
        found = terminfo_colors(term, env)
        if hit is not None and hit < len(expected):
            assert (found, tried) == (256, expected[: hit + 1]), (term, env)
        else:
            assert (found, tried) == (None, expected), (term, env)
