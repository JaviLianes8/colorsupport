"""The whole ColorLevel constructor domain, checked against an oracle written from the docs.

Documented contract: `ColorLevel(value)` returns the member whose number equals the exact
value of an int, bool, float, complex with zero imaginary part, Decimal or Fraction (or a
subclass of one), read through the base type; everything else raises a bare ValueError
with a fixed message, no chained exception, no notes and no trace of the input.
"""

from __future__ import annotations

import traceback
from collections.abc import Iterator
from decimal import Decimal
from fractions import Fraction

import pytest
from _poison import CALLS, SECRET, armed, poison

from colorsupport import ColorLevel

MESSAGE = "unknown color level; expected 0, 1, 2 or 3"
MEMBERS = (ColorLevel.NONE, ColorLevel.BASIC, ColorLevel.ANSI256, ColorLevel.TRUECOLOR)
INF, NAN = float("inf"), float("nan")
TINY = Fraction(1, 10**20)
RATIONALS = (
    [Fraction(n) for n in range(-3, 7)]
    + [Fraction(k, 4) for k in range(-4, 17)]
    + [Fraction(1, 3), Fraction(-1, 3), 3 + TINY, 3 - TINY, 1 + TINY, TINY, -TINY]
    + [Fraction(1, 10**400), Fraction(10**20), Fraction(-(10**20)), Fraction(2**64)]
)
FLOATS = [INF, -INF, NAN, -0.0, 5e-324, 1e308, 3.0000000000000004, 2.9999999999999996]
DECIMALS = [
    "0",
    "-0",
    "0E+999999999",
    "0E-999999999",
    "2E0",
    "20E-1",
    "2.000",
    "3.00000000000000000001",
    "0.99999999999999999999",
    "1e999999999",
    "1e-999999999",
    "-1",
    "NaN",
    "-NaN",
    "sNaN",
    "Infinity",
    "-Infinity",
]


def oracle(exact: Fraction | None) -> ColorLevel | None:
    if exact is None or exact.denominator != 1 or not 0 <= exact.numerator <= 3:
        return None
    return MEMBERS[exact.numerator]


def exact_float(value: float) -> Fraction | None:
    return None if value != value or value in (INF, -INF) else Fraction(*value.as_integer_ratio())


def exact_decimal(text: str) -> Fraction | None:
    # Read from the digits and the exponent; Fraction(Decimal) would expand 1e999999999.
    sign, digits, exponent = Decimal(text).as_tuple()
    if not isinstance(exponent, int):
        return None
    coefficient = int("".join(map(str, digits)) or "0")
    if coefficient == 0:
        return Fraction(0)
    if exponent > 10:
        return Fraction(10**11)
    if exponent + len(digits) < 0:
        # Nonzero and below one in magnitude: a stand-in with the same sign is enough.
        return Fraction(-1 if sign else 1, 2)
    magnitude = coefficient * Fraction(10) ** exponent
    return -magnitude if sign else magnitude


def domain() -> Iterator[tuple[str, type, object, Fraction | None]]:
    """(id, base type, constructor argument, exact value) for every accepted carrier."""
    for q in RATIONALS:
        if q.denominator == 1:
            yield f"int:{q}", int, int(q), q
        yield f"fraction:{q}", Fraction, q, q
        yield f"float:{q}", float, float(q), exact_float(float(q))
        for imag in (0.0, -0.0, 5e-324, 1.0):
            value = complex(float(q), imag)
            exact = exact_float(float(q)) if imag == 0 else None
            yield f"complex:{q}{imag:+}j", complex, value, exact
    for f in FLOATS:
        yield f"float:{f!r}", float, f, exact_float(f)
        yield f"complex:{f!r}", complex, complex(f, 0.0), exact_float(f)
    for text in DECIMALS:
        yield f"decimal:{text}", Decimal, text, exact_decimal(text)
    yield "bool:False", bool, False, Fraction(0)
    yield "bool:True", bool, True, Fraction(1)


CASES = list(domain())


POISONED: dict[type, type] = {
    base: poison(base) for base in (int, float, complex, Decimal, Fraction, str)
}


def build(base: type, raw: object, hostile: bool) -> object:
    if base is bool:
        return raw
    if hostile:
        return POISONED[base](raw)
    return Decimal(str(raw)) if base is Decimal else raw


def assert_rejected(value: object) -> None:
    with pytest.raises(ValueError) as raised:
        ColorLevel(value)  # type: ignore[arg-type]
    error = raised.value
    assert type(error) is ValueError
    assert error.args == (MESSAGE,)
    assert error.__cause__ is None and error.__context__ is None
    assert getattr(error, "__notes__", None) is None
    assert SECRET not in "".join(traceback.format_exception(error))


@pytest.mark.parametrize("hostile", [False, True], ids=["plain", "poisoned"])
@pytest.mark.parametrize("mode", ["raise", "lie"])
@pytest.mark.parametrize(("case", "base", "raw", "exact"), CASES, ids=[c[0] for c in CASES])
def test_constructor_matches_the_exact_value_oracle(
    case: str, base: type, raw: object, exact: Fraction | None, hostile: bool, mode: str
) -> None:
    value = build(base, raw, hostile)
    expected = oracle(exact)
    with armed(mode):
        if expected is None:
            assert_rejected(value)
        else:
            assert ColorLevel(value) is expected  # type: ignore[arg-type]
    assert CALLS == []
