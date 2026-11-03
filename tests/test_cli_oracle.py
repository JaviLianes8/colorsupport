"""Every combination of command-line options, checked against the documented behaviour.

GUIDE: the command looks at stdout, or stderr with --stderr; --when is passed through;
plain output is `str(detect(...))`; --json prints level label, colors and reason;
--check LEVEL prints nothing and exits 0 when the level is at least LEVEL, else 1.
"""

from __future__ import annotations

import io
import json
import os

import pytest

from colorsupport import ColorLevel, detect
from colorsupport._cli import main

SPELLINGS = {
    level: [level.label, level.name, level.name.lower(), str(level.value), f" {level.label} "]
    for level in ColorLevel
}
ENVS: list[dict[str, str]] = [{}, *({"FORCE_COLOR": f} for f in ("0", "1", "2", "3", "x"))]
ENVS += [{"NO_COLOR": "1"}, {"TERM": "xterm-256color"}, {"COLORTERM": "truecolor"}]


class Terminal(io.StringIO):
    def isatty(self) -> bool:
        return True


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(os.environ):
        monkeypatch.delenv(name)
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.setenv("TERMINFO", "")


def run(monkeypatch: pytest.MonkeyPatch, argv: list[str], stderr_tty: bool) -> tuple[int, str]:
    out: io.StringIO = Terminal() if not stderr_tty else io.StringIO()
    err: io.StringIO = Terminal() if stderr_tty else io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    monkeypatch.setattr("sys.stderr", err)
    code = main(argv)
    return code, out.getvalue() + err.getvalue()


@pytest.mark.parametrize("stderr_tty", [False, True])
@pytest.mark.parametrize("use_stderr", [False, True])
@pytest.mark.parametrize("when", [None, "auto", "always", "never"])
def test_output_and_exit_codes_match_detect(
    monkeypatch: pytest.MonkeyPatch, when: str | None, use_stderr: bool, stderr_tty: bool
) -> None:
    head = (["--stderr"] if use_stderr else []) + ([] if when is None else ["--when", when])
    for env in ENVS:
        for name in ("FORCE_COLOR", "NO_COLOR", "TERM", "COLORTERM"):
            monkeypatch.delenv(name, raising=False)
        for name, value in env.items():
            monkeypatch.setenv(name, value)
        stream = Terminal() if use_stderr == stderr_tty else io.StringIO()
        found = detect(stream, when=when or "auto")  # type: ignore[arg-type]
        assert run(monkeypatch, head, stderr_tty) == (0, f"{found}\n"), (env, head)
        record: dict[str, object] = {"level": found.level.label, "colors": found.level.colors}
        record["reason"] = found.reason
        code, text = run(monkeypatch, [*head, "--json"], stderr_tty)
        assert (code, json.loads(text)) == (0, record), (env, head)
        for minimum, spellings in SPELLINGS.items():
            for spelling in spellings:
                expected = 0 if found.level >= minimum else 1
                result = run(monkeypatch, [*head, "--check", spelling], stderr_tty)
                assert result == (expected, ""), (env, head, spelling)
