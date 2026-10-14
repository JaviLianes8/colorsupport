"""The rules in the code match the pinned sources they come from.

The sources are not committed (see tests/upstream/MANIFEST.json); each test skips until
`python scripts/fetch_upstream.py` has fetched them, and fails if a rule drifts.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from colorsupport import _terminal, _terminfo, _windows

Read = Callable[[str], str]


def flat(text: str) -> str:
    return " ".join(text.split())


def test_no_color_and_force_color_ignore_empty_values(upstream: Read) -> None:
    assert "when present and not an empty string" in flat(upstream("no-color.md"))
    assert "present and not an empty string" in flat(upstream("force-color.md"))
    clicolors = flat(upstream("clicolors.md"))
    assert "Empty variables are treated as though they were unset." in clicolors
    assert "`FORCE_COLOR` as an alias for `CLICOLOR_FORCE`" in clicolors


def test_cpython_reads_no_color_before_force_color_before_term(upstream: Read) -> None:
    source = upstream("cpython-colorize.py.txt")
    body = source.split("def can_colorize", 1)[1]
    order = [body.index(key) for key in ('"NO_COLOR"', '"FORCE_COLOR"', '"TERM") == "dumb"')]
    assert order == sorted(order)


def test_supports_color_lists_match(upstream: Read) -> None:
    source = upstream("supports-color.js")
    lists = re.findall(r"if \(\[([^\]]+)\]\.some", source)
    assert [re.findall(r"'([A-Z_]+)'", item) for item in lists] == [
        list(_terminal._CI_TRUECOLOR),
        list(_terminal._CI_BASIC),
    ]
    assert "env.CI_NAME === 'codeship'" in source
    terms = re.findall(r"if \(env\.TERM === '([^']+)'\) \{\s*return 3;", source)
    assert terms == list(_terminal._TRUECOLOR_TERMS)


def test_supports_color_patterns_match(upstream: Read) -> None:
    source = upstream("supports-color.js")
    assert f"/{_terminal._TERM_256.pattern.removesuffix(chr(92) + 'Z')}$/iv" in source
    assert f"/{_terminal._TERM_BASIC.pattern}/iv" in source
    assert f"/^(?:{_terminal._TEAMCITY.pattern})/v" in source
    assert "'TF_BUILD' in env && 'AGENT_NAME' in env" in source


def test_supports_color_windows_builds_match(upstream: Read) -> None:
    source = upstream("supports-color.js")
    builds = [int(n.replace("_", "")) for n in re.findall(r">= (\d+_\d+)", source)]
    assert builds == [_windows.BUILD_256, _windows.BUILD_TRUECOLOR]


def test_truecolor_colorterm_values_match(upstream: Read) -> None:
    assert '"truecolor" or "24bit"' in flat(upstream("termstandard-colors.md"))
    assert 'value == "truecolor" || value == "24bit"' in upstream("anstyle-query-lib.rs")
    assert 'Some(value != "0")' in upstream("anstyle-query-lib.rs")
    assert _terminal._COLORTERM_TRUECOLOR == ("truecolor", "24bit")


def test_the_vt_flag_matches_the_console_docs(upstream: Read) -> None:
    flags = upstream("console-mode-flags.md")
    assert re.search(r"\*\*ENABLE_VIRTUAL_TERMINAL_PROCESSING\*\* 0x0004 ", flags)
    assert _windows.VT_PROCESSING == 0x0004


def test_terminfo_layout_matches_ncurses(upstream: Read) -> None:
    numbers = [
        line.split()[0]
        for line in upstream("ncurses-Caps.txt").splitlines()
        if not line.startswith("#") and len(line.split()) > 2 and line.split()[2] == "num"
    ]
    assert numbers.index("max_colors") == _terminfo._MAX_COLORS
    manual = flat(upstream("ncurses-term.5.txt"))
    assert "(octal 0432)" in manual and "(octal 01036)" in manual
    assert (_terminfo._LEGACY_MAGIC, _terminfo._EXTENDED_MAGIC) == (0o432, 0o1036)
