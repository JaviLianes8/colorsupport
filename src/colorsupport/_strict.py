"""Read caller-supplied values through their base types, never through methods they override."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from decimal import Decimal
from fractions import Fraction
from typing import Any

# Slot and member descriptors of the base types. Calling them reads the stored value
# directly, so a subclass that overrides a dunder, a method or a property cannot change it.
_COMPLEX_REAL: Any = vars(complex)["real"]
_COMPLEX_IMAG: Any = vars(complex)["imag"]
_FRACTION_NUMERATOR: Any = vars(Fraction)["_numerator"]
_FRACTION_DENOMINATOR: Any = vars(Fraction)["_denominator"]
_TYPE_NAME: Any = vars(type)["__name__"]


def is_instance(value: object, base: type) -> bool:
    """Whether the real type of value derives from base.

    Unlike isinstance, this never reads a `__class__` the value defines and ignores
    virtual subclasses registered with an abstract base class.
    """
    return type.__subclasscheck__(base, type(value))


def type_name(value: object) -> str:
    """The name of the real type of value, at most 40 characters, without calling its code."""
    name: str = _TYPE_NAME.__get__(type(value), type)
    return str.__str__(name)[:40]


def exact_str(value: object) -> str | None:
    """The exact str stored in a str or str subclass, or None for any other type."""
    if not is_instance(value, str):
        return None
    return str.__str__(value)


def exact_int(value: object) -> int | None:
    """The exact int stored in an int, a bool or an int subclass, or None for other types."""
    return int.__index__(value) if is_instance(value, int) else None  # type: ignore[arg-type]


def read_env(env: Mapping[str, str], names: Iterable[str]) -> dict[str, str]:
    """The named variables present in env, each read as its exact str.

    Only the mapping's own lookups run; a value that is not a str counts as empty.
    """
    return {name: exact_str(env[name]) or "" for name in names if name in env}


def small_integer(value: object, limit: int) -> int | None:
    """The integer 0..limit that value represents exactly, or None.

    Accepted carriers are int (and bool), float, complex with a zero imaginary part,
    Decimal and Fraction, including their subclasses. Each is read through its base type,
    so no method of the value runs and nothing it could raise escapes. Every other type,
    text and bytes included, is None, as are NaN, infinities and non-integral values.
    """
    number = _exact_number(value)
    if number is None:
        return None
    numerator, denominator = number
    if denominator == 0 or numerator % denominator != 0:
        return None
    whole = numerator // denominator
    return whole if 0 <= whole <= limit else None


def _exact_number(value: object) -> tuple[int, int] | None:
    # The value as a numerator and a denominator; None when it is not a finite
    # real number of an accepted type. The integer pair is only built for values whose
    # magnitude is already known to be small, so huge exponents cost nothing.
    whole = exact_int(value)
    if whole is not None:
        return whole, 1
    if is_instance(value, float):
        return _from_float(float.__float__(value))  # type: ignore[arg-type]
    if is_instance(value, complex):
        imag: float = _COMPLEX_IMAG.__get__(value, complex)
        if imag != 0.0:
            return None
        return _from_float(_COMPLEX_REAL.__get__(value, complex))
    if is_instance(value, Decimal):
        return _from_decimal(value)  # type: ignore[arg-type]
    if is_instance(value, Fraction):
        return _from_fraction(value)  # type: ignore[arg-type]
    return None


def _from_float(number: float) -> tuple[int, int] | None:
    # NaN and the infinities are not integers either.
    return (int(number), 1) if float.is_integer(number) else None


def _from_decimal(value: Decimal) -> tuple[int, int] | None:
    if not Decimal.is_finite(value):
        return None
    if Decimal.is_zero(value):
        return 0, 1
    # A nonzero value below one has a negative adjusted exponent, one from ten upwards a
    # positive one; only the adjusted exponent zero (1 to 9.99...) needs exact digits.
    if Decimal.adjusted(value) != 0:
        return None
    return Decimal.as_integer_ratio(value)


def _from_fraction(value: Fraction) -> tuple[int, int] | None:
    try:
        numerator: object = _FRACTION_NUMERATOR.__get__(value, Fraction)
        denominator: object = _FRACTION_DENOMINATOR.__get__(value, Fraction)
    except AttributeError:
        return None
    if not (is_instance(numerator, int) and is_instance(denominator, int)):
        return None
    return int.__index__(numerator), int.__index__(denominator)  # type: ignore[arg-type]
