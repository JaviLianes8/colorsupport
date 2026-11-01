"""Stable signatures, safe errors, value objects and runnable public examples."""

from __future__ import annotations

import doctest
import importlib
import inspect
import pickle
import re
from pathlib import Path
from typing import get_type_hints

import pytest
from conftest import TTY

import colorsupport as cs


def test_detection_signatures_and_defaults_are_stable() -> None:
    for function in (cs.detect, cs.level, cs.supports_color):
        params = list(inspect.signature(function).parameters.values())
        assert [p.name for p in params] == [
            "stream",
            "env",
            "when",
            "platform",
            "windows_build",
            "vt",
            "terminfo",
        ]
        assert params[0].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
        assert all(p.kind is inspect.Parameter.KEYWORD_ONLY for p in params[1:])
        assert [p.default for p in params] == [None, None, "auto", None, None, None, None]
        assert get_type_hints(function)["stream"] is object
    for other, names, defaults in (
        (cs.enable_vt, ["stream"], [None]),
        (cs.terminfo_colors, ["term", "env"], [inspect.Parameter.empty, None]),
        (cs.Detection, ["level", "reason"], [inspect.Parameter.empty] * 2),
    ):
        params = list(inspect.signature(other).parameters.values())
        assert [p.name for p in params] == names
        assert [p.default for p in params] == defaults
        assert all(p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD for p in params)


def test_every_public_docstring_has_a_passing_example() -> None:
    for name in cs.__all__:
        assert ">>>" in (getattr(cs, name).__doc__ or ""), name
    for name in ("_level", "_detect", "_terminfo", "_windows"):
        result = doctest.testmod(importlib.import_module(f"colorsupport.{name}"))
        assert result.failed == 0
        assert result.attempted > 0


def test_guide_examples_execute() -> None:
    guide = Path(__file__).resolve().parents[1] / "GUIDE.md"
    blocks = re.findall(r"```python\n(.*?)```", guide.read_text(encoding="utf-8"), re.S)
    assert blocks
    for block in blocks:
        exec(compile(block, str(guide), "exec"), {})


def test_values_are_hashable_and_pickle_round_trip() -> None:
    for member in cs.ColorLevel:
        value = cs.Detection(member, "a reason")
        assert pickle.loads(pickle.dumps(value)) == value
        assert {value: member}[cs.Detection(member, "a reason")] is member
        assert pickle.loads(pickle.dumps(member)) is member


@pytest.mark.parametrize(
    "text",
    ["secret-token", "x" * 1_000_000, "\ud800" * 100_000],
    ids=["secret", "million", "surrogates"],
)
def test_errors_do_not_echo_invalid_values(text: str) -> None:
    with pytest.raises(ValueError) as parsed:
        cs.ColorLevel.parse(text)
    assert str(parsed.value) == "unknown color level; expected one of none, 16, 256, truecolor"
    for function in (cs.detect, cs.level, cs.supports_color):
        with pytest.raises(ValueError) as detected:
            function(env={}, when=text)  # type: ignore[arg-type]
        assert str(detected.value) == "when must be one of auto, always, never"


@pytest.mark.parametrize("value", [None, False, 0, 4, b"x", [], object()])
def test_non_string_terminfo_names_raise_type_error(value: object) -> None:
    with pytest.raises(TypeError, match=r"^term must be a str$"):
        cs.terminfo_colors(value, {})  # type: ignore[arg-type]


def test_huge_integers_keep_exact_comparisons_and_bounded_reasons() -> None:
    huge = 10**5000
    for number, expected in ((huge, cs.ColorLevel.TRUECOLOR), (-huge, cs.ColorLevel.BASIC)):
        result = cs.detect(TTY, env={}, platform="win32", vt=True, windows_build=number)
        assert result.level is expected
        assert result.reason == "Windows console with VT processing, build a large integer"
    for number, expected in ((huge, cs.ColorLevel.TRUECOLOR), (-huge, cs.ColorLevel.NONE)):
        result = cs.detect(TTY, env={"TERM": "custom"}, platform="linux", terminfo=lambda t: number)  # noqa: B023
        assert result.level is expected
        assert result.reason == "terminfo for TERM=custom declares a large integer colors"


def test_injected_callback_errors_propagate_unchanged() -> None:
    error = LookupError("callback failure")

    def lookup(term: str) -> int:
        raise error

    with pytest.raises(LookupError) as raised:
        cs.detect(TTY, env={"TERM": "custom"}, platform="linux", terminfo=lookup)
    assert raised.value is error
