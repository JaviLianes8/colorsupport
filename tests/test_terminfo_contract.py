"""Public terminfo boundary contracts using hand-built compiled entries."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from test_terminfo import entry, install

from colorsupport import terminfo_colors


@pytest.mark.parametrize("count", [0, -1, -2])
def test_zero_colors_is_distinct_from_missing(tmp_path: Path, count: int) -> None:
    install(tmp_path, "custom", entry(count))
    assert terminfo_colors("custom", {"TERMINFO": str(tmp_path)}) == (0 if count == 0 else None)


@pytest.mark.parametrize("size", [32767, 32768, 32769])
def test_entry_size_limit_is_inclusive(tmp_path: Path, size: int) -> None:
    install(tmp_path, "custom", entry(256).ljust(size, b"\0"))
    assert terminfo_colors("custom", {"TERMINFO": str(tmp_path)}) == (
        256 if size <= 32768 else None
    )


def test_colon_name_cannot_read_a_readable_target(tmp_path: Path) -> None:
    # On Windows this is an alternate stream on a regular file; elsewhere a normal name.
    install(tmp_path, "audit", entry(8))
    install(tmp_path, "audit:colors", entry(256))
    assert (tmp_path / "a" / "audit:colors").read_bytes() == entry(256)
    assert terminfo_colors("audit:colors", {"TERMINFO": str(tmp_path)}) is None


@pytest.mark.parametrize("term", ["", ".hidden", "a/b", "a\\b", "audit:colors", "a\0b"])
def test_unsafe_names_never_open_files(monkeypatch: pytest.MonkeyPatch, term: str) -> None:
    calls: list[str] = []

    def opened(path: str, flags: int) -> int:
        calls.append(path)
        raise OSError("unexpected open")

    with monkeypatch.context() as patch:
        patch.setattr(os, "open", opened)
        result = terminfo_colors(term, {"TERMINFO": "unused"})
    assert result is None
    assert calls == []
