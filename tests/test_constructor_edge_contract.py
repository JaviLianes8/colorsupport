"""Constructor contracts for exact values and hostile equality results."""

from __future__ import annotations

import traceback
from decimal import Decimal
from fractions import Fraction

import pytest

from colorsupport import ColorLevel


class NonUnitEquality(int):
    def __eq__(self, other: object) -> int:  # type: ignore[override]
        return 2 if int.__eq__(self, other) else 0


class ComparisonError(Exception):
    pass


@pytest.mark.parametrize(
    ("value", "rounded"),
    [(Decimal("1e-400"), 0), (Fraction(1, 10**400), 0)]
    + [(Decimal(f"{level}.00000000000000000001"), level) for level in (1, 2, 3)]
    + [(Fraction(level * 10**20 + 1, 10**20), level) for level in (1, 2, 3)],
)
def test_constructor_rejects_exact_fractions_that_round_to_levels(
    value: Decimal | Fraction, rounded: int
) -> None:
    assert value != rounded
    assert float(value) == rounded
    with pytest.raises(ValueError, match=r"^unknown color level; expected 0, 1, 2 or 3$"):
        ColorLevel(value)  # type: ignore[arg-type]


@pytest.mark.parametrize("expected", list(ColorLevel))
def test_constructor_accepts_nonunit_truthy_equality(expected: ColorLevel) -> None:
    value = NonUnitEquality(expected.value)
    assert (value == expected.value) == 2
    assert ColorLevel(value) is expected


@pytest.mark.parametrize("expected", list(ColorLevel))
def test_constructor_rejects_numeric_text_accepted_by_parse(expected: ColorLevel) -> None:
    text = str(expected.value)
    with pytest.raises(ValueError, match=r"^unknown color level; expected 0, 1, 2 or 3$"):
        ColorLevel(text)  # type: ignore[arg-type]
    assert ColorLevel.parse(text) is expected


@pytest.mark.parametrize("exception_type", [RuntimeError, LookupError, ComparisonError])
@pytest.mark.parametrize("chained", [False, True])
@pytest.mark.parametrize("during_truth_conversion", [False, True])
def test_constructor_redacts_equality_and_truth_conversion_errors(
    exception_type: type[Exception], chained: bool, during_truth_conversion: bool
) -> None:
    class FailingTruth:
        def __bool__(self) -> bool:
            if chained:
                try:
                    raise LookupError("PRIVATE_CAUSE")
                except LookupError as cause:
                    raise exception_type("PRIVATE_COMPARISON") from cause
            raise exception_type("PRIVATE_COMPARISON")

    class FailingComparison:
        def __eq__(self, other: object) -> object:  # type: ignore[override]
            result = FailingTruth()
            return result if during_truth_conversion else bool(result)

    with pytest.raises(ValueError) as raised:
        ColorLevel(FailingComparison())  # type: ignore[arg-type]
    assert type(raised.value) is ValueError
    assert str(raised.value) == "unknown color level; expected 0, 1, 2 or 3"
    assert raised.value.__cause__ is None
    assert raised.value.__context__ is None
    rendered = "".join(traceback.format_exception(raised.type, raised.value, raised.tb))
    assert "PRIVATE_COMPARISON" not in rendered
    assert "PRIVATE_CAUSE" not in rendered
    assert len(rendered) < 10_000
