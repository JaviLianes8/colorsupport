"""The public API is typed: mypy infers the documented types and rejects wrong ones."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"

SNIPPET = """
from colorsupport import ColorLevel, detect, enable_vt, level, supports_color, terminfo_colors
reveal_type(detect())
reveal_type(detect().level)
reveal_type(detect().reason)
reveal_type(level(env={}))
reveal_type(supports_color(when="always"))
reveal_type(enable_vt())
reveal_type(terminfo_colors("xterm"))
reveal_type(ColorLevel.parse("256").colors)
detect(when="sometimes")
detect(None, {})
level(env={"A": 1})
supports_color(terminfo=lambda term: "256")
"""


@pytest.fixture(scope="module")
def mypy_output(tmp_path_factory: pytest.TempPathFactory) -> str:
    folder = tmp_path_factory.mktemp("typing")
    target = folder / "snippet.py"
    target.write_text(SNIPPET, encoding="utf-8")
    config = folder / "mypy.ini"
    config.write_text(f"[mypy]\nmypy_path = {SRC.as_posix()}\n", encoding="utf-8")
    cache = str(folder / "cache")
    args = ["--strict", "--config-file", str(config), "--cache-dir", cache, str(target)]
    try:
        from mypy import api
    except ImportError:
        # The interpreter running pytest may lack mypy while the one on PATH has it.
        program = shutil.which("mypy")
        if program is None:
            pytest.skip("mypy is not installed")
        result = subprocess.run([program, *args], capture_output=True, text=True, check=False)
        return result.stdout + result.stderr
    out, err, _ = api.run(args)
    return str(out) + str(err)


def test_functions_return_the_documented_types(mypy_output: str) -> None:
    assert [_revealed(mypy_output, line) for line in range(3, 11)] == [
        "colorsupport._level.Detection",
        "colorsupport._level.ColorLevel",
        "str",
        "colorsupport._level.ColorLevel",
        "bool",
        "bool",
        "int | None",
        "int",
    ]


def test_misuse_is_rejected(mypy_output: str) -> None:
    for line, code in ((11, "arg-type"), (12, "call-arg"), (13, "dict-item"), (14, "arg-type")):
        assert re.search(rf"snippet\.py:{line}: error: .*\[{code}\]", mypy_output), mypy_output


def _revealed(output: str, line: int) -> str:
    match = re.search(rf"snippet\.py:{line}: note: Revealed type is \"(.+)\"", output)
    assert match, output
    # Older mypy releases spell builtins with their module prefix.
    return match.group(1).replace("builtins.", "")
