"""The command line, table driven: odd spellings of every option and the exact bytes printed.

Model, from the GUIDE and `ColorLevel.parse`: a LEVEL is a label, member name or number,
case ignored, with surrounding whitespace (any str.isspace character, CR and LF included)
stripped; nothing inside the word is unescaped or trimmed. `--when` takes one of its three
exact choices. A repeated option keeps its last value, unique prefixes of long options are
accepted, and every usage error exits 2 with one fixed message that never echoes input.
Output is exactly one line: `str(detect(...))` or the JSON object below, key order fixed.
"""

from __future__ import annotations

import io
import os

import pytest

from colorsupport._cli import main

# The terminal on stdout declares 256 colors; stderr is a pipe.
ENV = {"TERM": "xterm-256color", "TERMINFO": "", "COLUMNS": "400"}
USAGE = (
    "usage: colorsupport [-h] [--stderr] [--when {auto,always,never}] [--json | --check LEVEL]\n"
    "colorsupport: error: invalid arguments; --when expects auto, always, never; "
    "--check expected one of none, 16, 256, truecolor; see --help\n"
)
PLAIN = "256: TERM=xterm-256color\n"
JSON = '{"level": "256", "colors": 256, "reason": "TERM=xterm-256color"}\n'

CHECKS = [
    ("", 2),
    (" ", 2),
    ("\r\n", 2),
    ("256\r\n", 0),
    ("\t16\t", 0),
    ("\u00a0256\u2003", 0),
    ("256\x0b\x0c", 0),
    ("truecolor", 1),
    ("TrueColor", 1),
    (" TRUECOLOR\n", 1),
    ("ANSI256", 0),
    ("basic", 0),
    ("none", 0),
    ("0", 0),
    ("3", 1),
    ("tru\\x65color", 2),
    ("true\ncolor", 2),
    ("1 6", 2),
    ("+3", 2),
    ("03", 2),
    ("3.0", 2),
    ("-1", 2),
    ("\x00", 2),
    ("16\x00", 2),
    ("'256'", 2),
]

LINES = [
    ([], 0, PLAIN),
    (["--json"], 0, JSON),
    (["--json", "--json"], 0, JSON),
    (["--js"], 0, JSON),
    (["--check=256"], 0, ""),
    (["--ch", "16"], 0, ""),
    (["--check", "256", "--check", "truecolor"], 1, ""),
    (["--check", "truecolor", "--check", "16"], 0, ""),
    (["--when", "never", "--when", "always", "--check", "16"], 0, ""),
    (["--when", "always", "--when", "never", "--check", "16"], 1, ""),
    (["--w", "never", "--check", "16"], 1, ""),
    (["--when=never"], 0, "none: the caller turned color off (when='never')\n"),
    (["--stderr", "--check", "none"], 0, ""),
    (["--stderr", "--stderr", "--check", "16"], 1, ""),
    (["--std"], 0, "none: the stream is not a terminal\n"),
    (["--when", " never"], 2, USAGE),
    (["--when", "never\r\n"], 2, USAGE),
    (["--when", "NEVER"], 2, USAGE),
    (["--when", "nev"], 2, USAGE),
    (["--when="], 2, USAGE),
    ([""], 2, USAGE),
    (["extra"], 2, USAGE),
    (["--check"], 2, USAGE),
    (["--check", "--json"], 2, USAGE),
    (["--json", "--check", "16"], 2, USAGE),
    (["--JSON"], 2, USAGE),
    (["-json"], 2, USAGE),
]


class Terminal(io.StringIO):
    def isatty(self) -> bool:
        return True


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(os.environ):
        monkeypatch.delenv(name)
    for name, value in ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr("sys.platform", "linux")


def run(monkeypatch: pytest.MonkeyPatch, argv: list[str] | None) -> tuple[int, str]:
    out, err = Terminal(), io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    monkeypatch.setattr("sys.stderr", err)
    try:
        code = main(argv)
    except SystemExit as done:
        assert isinstance(done.code, int)
        code = done.code
    assert not (out.getvalue() and err.getvalue())
    return code, out.getvalue() + err.getvalue()


@pytest.mark.parametrize(("text", "status"), CHECKS, ids=[ascii(c[0]) for c in CHECKS])
def test_check_level_spellings(monkeypatch: pytest.MonkeyPatch, text: str, status: int) -> None:
    expected = USAGE if status == 2 else ""
    assert run(monkeypatch, ["--check", text]) == (status, expected)
    assert run(monkeypatch, [f"--check={text}"]) == (status, expected)


@pytest.mark.parametrize(("argv", "status", "output"), LINES, ids=[" ".join(c[0]) for c in LINES])
def test_command_lines_print_exact_output(
    monkeypatch: pytest.MonkeyPatch, argv: list[str], status: int, output: str
) -> None:
    assert run(monkeypatch, argv) == (status, output)


@pytest.mark.parametrize("argv", [["--help"], ["-h", "--json"], ["--when", "x"], ["--bad"]])
@pytest.mark.parametrize("force", ["", "1", "3"])
def test_help_and_usage_are_plain_text(
    monkeypatch: pytest.MonkeyPatch, argv: list[str], force: str
) -> None:
    # Python 3.14 argparse would color them, judged by stdout, even on a piped stderr.
    monkeypatch.setenv("FORCE_COLOR", force)
    code, output = run(monkeypatch, argv)
    assert code in (0, 2) and output.startswith("usage: colorsupport [-h]")
    assert "\x1b" not in output


@pytest.mark.parametrize("argv", [[], ["--json"], ["--check", " 256\r\n"], ["--when", "x"]])
def test_default_argv_is_the_process_command_line(
    monkeypatch: pytest.MonkeyPatch, argv: list[str]
) -> None:
    expected = run(monkeypatch, argv)
    monkeypatch.setattr("sys.argv", ["colorsupport", *argv])
    assert run(monkeypatch, None) == expected


SERIALISED = [
    ({"FORCE_COLOR": "007"}, "truecolor", 16777216, "FORCE_COLOR=007 asks for truecolor"),
    ({"FORCE_COLOR": " 1 "}, "16", 16, "FORCE_COLOR= 1  asks for 16 colors"),
    ({"FORCE_COLOR": "false"}, "none", 0, "FORCE_COLOR='false' turns color off"),
    ({"NO_COLOR": "1"}, "none", 0, "NO_COLOR is set"),
    ({"FORCE_COLOR": "1", "TERM": "x-256color"}, "16", 16, "FORCE_COLOR=1 asks for 16 colors"),
    (
        {"FORCE_COLOR": 'a"b\\\u00e9\n'},
        "256",
        256,
        "FORCE_COLOR='a\"b\\\\\\xe9\\n' turns color on; TERM=xterm-256color",
    ),
    (
        {"FORCE_COLOR": "\u00e9" * 40},
        "256",
        256,
        "FORCE_COLOR='" + "\\xe9" * 32 + "' turns color on; TERM=xterm-256color",
    ),
]


def json_text(label: str, colors: int, reason: str) -> str:
    # Written out by hand: no indent, ", " and ": " separators, ASCII only, one newline.
    escaped = reason.replace("\\", "\\\\").replace('"', '\\"')
    return f'{{"level": "{label}", "colors": {colors}, "reason": "{escaped}"}}\n'


@pytest.mark.parametrize(("env", "label", "colors", "reason"), SERIALISED)
def test_output_is_serialised_exactly(
    monkeypatch: pytest.MonkeyPatch, env: dict[str, str], label: str, colors: int, reason: str
) -> None:
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    assert run(monkeypatch, ["--json"]) == (0, json_text(label, colors, reason))
    assert run(monkeypatch, []) == (0, f"{label}: {reason}\n")
