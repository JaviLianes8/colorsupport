"""Compiled terminfo entries, built by hand from the layout in ncurses term(5)."""

from __future__ import annotations

import os
import struct
from pathlib import Path

import pytest

from colorsupport import terminfo_colors
from colorsupport._terminfo import SYSTEM_DIRS, parse_colors, search_dirs

LEGACY = 0o432
EXTENDED = 0o1036


def entry(colors: int | None, *, magic: int = LEGACY, names: bytes = b"t|test\0") -> bytes:
    """A minimal compiled entry: header, names, one boolean, pad, then 15 numbers."""
    width = "h" if magic == LEGACY else "i"
    numbers = [-1] * 15
    if colors is not None:
        numbers[13] = colors
    header = struct.pack("<6h", magic, len(names), 1, len(numbers), 0, 0)
    body = header + names + b"\x01"
    if len(body) % 2:
        body += b"\0"
    return body + struct.pack(f"<{len(numbers)}{width}", *numbers)


def test_reads_colors_from_the_legacy_format() -> None:
    assert parse_colors(entry(256)) == 256
    assert parse_colors(entry(8, names=b"ab\0")) == 8


def test_reads_32_bit_colors_from_the_extended_format() -> None:
    assert parse_colors(entry(16_777_216, magic=EXTENDED)) == 16_777_216


def test_the_pad_byte_is_skipped_only_when_needed() -> None:
    odd = entry(88, names=b"x\0")
    even = entry(88, names=b"xy\0")
    # 12 header bytes + 2 names + 1 boolean is odd and needs the pad; 3 names do not.
    assert len(odd) == len(even)
    assert parse_colors(odd) == parse_colors(even) == 88


@pytest.mark.parametrize("stored", [-1, -2])
def test_absent_or_cancelled_colors_read_as_none(stored: int) -> None:
    assert parse_colors(entry(stored)) is None


def test_unreadable_entries_give_none() -> None:
    good = entry(256)
    assert parse_colors(b"") is None
    assert parse_colors(good[:11]) is None
    assert parse_colors(good[:-4]) is None
    assert parse_colors(struct.pack("<h", 0o433) + good[2:]) is None
    short = struct.pack("<6h", LEGACY, 2, 0, 13, 0, 0) + b"a\0" + b"\0" * 26
    assert parse_colors(short) is None
    negative = struct.pack("<6h", LEGACY, -2, 0, 15, 0, 0) + good[12:]
    assert parse_colors(negative) is None


def test_negative_section_sizes_are_unreadable() -> None:
    # Without the sign checks these offsets would land on the 256 stored below.
    numbers = struct.pack("<15h", *([-1] * 13 + [256, -1]))
    for names, booleans in ((-2, 4), (4, -2)):
        header = struct.pack("<6h", LEGACY, names, booleans, 15, 0, 0)
        assert parse_colors(header + b"\0" * 2 + numbers) is None


def test_thirteen_numbers_have_no_colors_even_with_more_data() -> None:
    header = struct.pack("<6h", LEGACY, 2, 0, 13, 0, 0)
    data = header + b"a\0" + struct.pack("<13h", *([-1] * 13)) + struct.pack("<h", 256) * 4
    assert parse_colors(data) is None


def install(folder: Path, term: str, data: bytes, *, hexed: bool = False) -> None:
    sub = folder / (f"{ord(term[0]):02x}" if hexed else term[0])
    sub.mkdir(parents=True, exist_ok=True)
    (sub / term).write_bytes(data)


def test_finds_an_entry_under_terminfo(tmp_path: Path) -> None:
    install(tmp_path, "foot", entry(256))
    assert terminfo_colors("foot", {"TERMINFO": str(tmp_path)}) == 256


def test_finds_an_entry_in_the_hex_layout(tmp_path: Path) -> None:
    install(tmp_path, "foot", entry(16_777_216, magic=EXTENDED), hexed=True)
    assert terminfo_colors("foot", {"TERMINFO": str(tmp_path)}) == 16_777_216


def test_searches_terminfo_then_home_then_terminfo_dirs(tmp_path: Path) -> None:
    first, home, listed = tmp_path / "first", tmp_path / "home", tmp_path / "listed"
    install(listed, "foot", entry(8))
    env = {"TERMINFO": str(first), "HOME": str(home), "TERMINFO_DIRS": str(listed)}
    assert terminfo_colors("foot", env) == 8
    install(home / ".terminfo", "foot", entry(88))
    assert terminfo_colors("foot", env) == 88
    install(first, "foot", entry(256))
    assert terminfo_colors("foot", env) == 256


def test_the_first_readable_entry_wins_even_without_colors(tmp_path: Path) -> None:
    first, second = tmp_path / "a", tmp_path / "b"
    install(first, "vt", entry(None))
    install(second, "vt", entry(256))
    env = {"TERMINFO_DIRS": f"{first}:{second}"}
    assert terminfo_colors("vt", env) is None
    install(first, "vt", b"not an entry")
    assert terminfo_colors("vt", env) == 256


def test_search_dirs_follow_the_ncurses_order() -> None:
    env = {"TERMINFO": "/t", "HOME": "/h", "TERMINFO_DIRS": "/a::/b:/t"}
    dirs = search_dirs(env)
    assert dirs[:3] == ["/t", os.path.join("/h", ".terminfo"), "/a"]
    assert dirs[3:] == [*SYSTEM_DIRS, "/b"]
    assert search_dirs({}) == list(SYSTEM_DIRS)
    assert search_dirs({"TERMINFO": "", "HOME": ""}) == list(SYSTEM_DIRS)
    assert search_dirs({"TERMINFO_DIRS": ""}) == list(SYSTEM_DIRS)


@pytest.mark.parametrize("term", ["", ".", "..", "../x", "a/b", "a\b", "a\0b", ".hidden"])
def test_names_that_could_leave_the_folder_are_refused(tmp_path: Path, term: str) -> None:
    (tmp_path / "secret").write_bytes(entry(256))
    (tmp_path / "a").mkdir()
    env = {"TERMINFO": str(tmp_path / "a")}
    assert terminfo_colors(term, env) is None


def test_a_dot_name_cannot_reach_a_hidden_file(tmp_path: Path) -> None:
    (tmp_path / ".x").write_bytes(entry(256))
    assert terminfo_colors(".x", {"TERMINFO": str(tmp_path)}) is None


@pytest.mark.parametrize("sep", ["/", "\\"])
def test_a_separator_cannot_climb_out_of_the_folder(tmp_path: Path, sep: str) -> None:
    folder = tmp_path / "db"
    (folder / "x" / "x").mkdir(parents=True)
    (tmp_path / "secret").write_bytes(entry(256))
    term = sep.join(["x", "..", "..", "..", "secret"])
    assert terminfo_colors(term, {"TERMINFO": str(folder)}) is None


def test_an_oversized_file_is_not_read(tmp_path: Path) -> None:
    install(tmp_path, "big", entry(256) + b"\0" * 40000)
    install(tmp_path, "ok", entry(256) + b"\0" * 1000)
    env = {"TERMINFO": str(tmp_path)}
    assert terminfo_colors("big", env) is None
    assert terminfo_colors("ok", env) == 256


def test_a_folder_in_place_of_an_entry_is_skipped(tmp_path: Path) -> None:
    (tmp_path / "f" / "foot").mkdir(parents=True)
    assert terminfo_colors("foot", {"TERMINFO": str(tmp_path)}) is None


def test_env_defaults_to_the_process_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    install(tmp_path, "foot", entry(256))
    monkeypatch.setenv("TERMINFO", str(tmp_path))
    assert terminfo_colors("foot") == 256
