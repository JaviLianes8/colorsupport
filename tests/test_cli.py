"""The `colorsupport` command line, driven in process."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import PIPE, TTY

from colorsupport._cli import main

SRC = Path(__file__).resolve().parents[1] / "src"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("NO_COLOR", "FORCE_COLOR", "CLICOLOR_FORCE", "CLICOLOR", "TF_BUILD", "CI"):
        monkeypatch.delenv(name, raising=False)


def test_prints_level_and_reason(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    assert capsys.readouterr().out == "none: the stream is not a terminal\n"


def test_json_output(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FORCE_COLOR", "3")
    assert main(["--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "level": "truecolor",
        "colors": 16777216,
        "reason": "FORCE_COLOR=3 asks for truecolor",
    }


def test_stderr_is_looked_at_on_request(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COLORTERM", "truecolor")
    monkeypatch.setenv("TERM", "xterm")
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.setattr("sys.stderr", TTY)
    assert main(["--stderr"]) == 0
    assert capsys.readouterr().out == "truecolor: COLORTERM=truecolor\n"
    monkeypatch.setattr("sys.stderr", PIPE)
    assert main(["--stderr", "--check", "16"]) == 1


def test_check_is_an_exit_code(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FORCE_COLOR", "2")
    assert main(["--check", "256"]) == 0
    assert main(["--check", "none"]) == 0
    assert main(["--check", "truecolor"]) == 1
    assert capsys.readouterr().out == ""


def test_when_is_passed_through(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--when", "always", "--check", "16"]) == 0
    assert main(["--when", "never"]) == 0
    assert capsys.readouterr().out == "none: the caller turned color off (when='never')\n"


@pytest.mark.parametrize(
    "argv", [["--check", "8"], ["--when", "on"], ["--json", "--check", "16"], ["extra"]]
)
def test_bad_usage_exits_2(argv: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as raised:
        main(argv)
    assert raised.value.code == 2
    assert "usage: colorsupport" in capsys.readouterr().err


def test_bad_level_names_the_choices(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["--check", "8"])
    assert "expected one of none, 16, 256, truecolor" in capsys.readouterr().err


def test_runs_as_a_module() -> None:
    command = [sys.executable, "-B", "-m", "colorsupport", "--json"]
    env = {k: v for k, v in os.environ.items() if k not in ("NO_COLOR", "CLICOLOR")}
    env.update(PYTHONPATH=str(SRC), FORCE_COLOR="1")
    done = subprocess.run(command, capture_output=True, text=True, env=env, check=False)
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout)["level"] == "16"


def test_importing_main_module_does_not_run_it() -> None:
    import colorsupport.__main__ as entry

    assert entry.__name__ == "colorsupport.__main__"
    assert vars(entry)["main"] is main
