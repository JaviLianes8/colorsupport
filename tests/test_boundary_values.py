"""Exact readings at the boundary: what counts as a level name and what counts as a set flag."""

from __future__ import annotations

import pytest
from conftest import TTY

from colorsupport import ColorLevel, Detection, detect

# Lookalikes that a looser case folding (casefold, NFKC) would turn into a valid name.
LOOKALIKES = [
    "ba\u017fic",
    "BA\u017fIC",
    "n\u043ene",
    "\uff22\uff21\uff33\uff29\uff23",
    "\uff11\uff16",
]
LOOKALIKES += ["truecolo\u0280", "\u2160", "\u00b2", "\u0663"]


@pytest.mark.parametrize("text", LOOKALIKES, ids=ascii)
def test_parse_compares_with_lower_only(text: str) -> None:
    with pytest.raises(ValueError, match=r"^unknown color level; expected one of "):
        ColorLevel.parse(text)


@pytest.mark.parametrize("flag", [-1, 2, 2**70, -(2**70)])
def test_any_nonzero_integer_vt_means_on(flag: int) -> None:
    options: dict[str, object] = {"env": {}, "platform": "win32", "windows_build": 19045}
    on = detect(TTY, vt=True, **options)  # type: ignore[arg-type]
    assert detect(TTY, vt=flag, **options) == on  # type: ignore[arg-type]
    assert detect(TTY, vt=0, **options) == detect(TTY, vt=False, **options)  # type: ignore[arg-type]
    assert on.level is ColorLevel.TRUECOLOR


class ClaimsStr:
    # An object that claims to be a str through __class__; isinstance would believe it.
    @property  # type: ignore[misc]
    def __class__(self) -> type:
        return str


@pytest.mark.parametrize("when", [None, 0, b"auto", ClaimsStr()], ids=repr)
def test_when_of_another_type_is_unknown(when: object) -> None:
    assert isinstance(ClaimsStr(), str)
    with pytest.raises(ValueError, match=r"^when must be one of auto, always, never$"):
        detect(TTY, env={}, platform="linux", when=when)  # type: ignore[arg-type]


def test_parse_type_error_names_at_most_40_characters_of_the_type() -> None:
    long_type = type("L" * 60, (), {})
    with pytest.raises(TypeError) as raised:
        ColorLevel.parse(long_type())
    assert str(raised.value) == "expected a str, got " + "L" * 40


@pytest.mark.parametrize("reason", ["x ", " x", "x\n", "", "\t"], ids=repr)
def test_detection_text_keeps_the_reason_verbatim(reason: str) -> None:
    assert str(Detection(ColorLevel.BASIC, reason)) == "16: " + reason
