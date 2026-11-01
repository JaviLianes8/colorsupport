"""Constructor contracts for redacted diagnostics and numeric compatibility."""

from __future__ import annotations

import traceback
from decimal import Decimal
from fractions import Fraction

import pytest

from colorsupport import ColorLevel

_RENDER_CALLS: list[str] = []


class SecretText(str):
    def __repr__(self) -> str:
        _RENDER_CALLS.append("repr")
        raise RuntimeError("SENSITIVE_MARKER")

    def __str__(self) -> str:
        _RENDER_CALLS.append("str")
        raise AssertionError("SENSITIVE_MARKER")


class SecretInteger(int):
    def __repr__(self) -> str:
        _RENDER_CALLS.append("repr")
        raise AssertionError("SENSITIVE_MARKER")

    def __str__(self) -> str:
        _RENDER_CALLS.append("str")
        raise RuntimeError("SENSITIVE_MARKER")


class SecretComparison:
    def __eq__(self, other: object) -> bool:
        raise RuntimeError("SENSITIVE_MARKER")


@pytest.mark.parametrize(
    "value",
    [SecretText("invalid"), SecretInteger(4), 10**10000],
    ids=["hostile-text", "hostile-integer", "beyond-integer-text-limit"],
)
def test_constructor_rejects_values_without_rendering_them(value: object) -> None:
    _RENDER_CALLS.clear()
    with pytest.raises(ValueError, match=r"^unknown color level; expected 0, 1, 2 or 3$"):
        ColorLevel(value)  # type: ignore[arg-type]
    assert _RENDER_CALLS == []


@pytest.mark.parametrize(
    "value",
    ["SENSITIVE_MARKER", "SENSITIVE_MARKER" + "x" * 1_000_000, SecretComparison()],
    ids=["secret", "long-text", "hostile-comparison"],
)
def test_constructor_exception_chain_is_redacted(value: object) -> None:
    with pytest.raises(ValueError) as raised:
        ColorLevel(value)  # type: ignore[arg-type]
    rendered = "".join(traceback.format_exception(raised.type, raised.value, raised.tb))
    assert "SENSITIVE_MARKER" not in rendered
    assert len(rendered) < 10_000
    error: BaseException | None = raised.value
    while error is not None:
        assert "SENSITIVE_MARKER" not in str(error)
        error = error.__cause__ or error.__context__


@pytest.mark.parametrize(
    ("value", "expected"),
    [(False, 0), (True, 1), (2.0, 2), (3 + 0j, 3), (Decimal(2), 2), (Fraction(1), 1)],
)
def test_constructor_preserves_numeric_equivalence(value: object, expected: int) -> None:
    assert ColorLevel(value) is ColorLevel(expected)  # type: ignore[arg-type]


def test_constructor_preserves_valid_hostile_integer() -> None:
    assert ColorLevel(SecretInteger(2)) is ColorLevel.ANSI256
