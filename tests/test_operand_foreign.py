"""ColorLevel rejects every value that is not an accepted number, whatever it pretends.

The values below claim to be a level through every protocol a careless reader might
consult (equality, hashing, __index__, __class__, ABC registration) or raise each
builtin exception class from those hooks. None of that code may run.
"""

from __future__ import annotations

import enum
import numbers
from decimal import Decimal
from fractions import Fraction

import pytest
from _poison import CALLS, armed, exception_classes, make_error, poison
from test_operand_domain import MEMBERS, assert_rejected, build

from colorsupport import ColorLevel


class OtherLevel(enum.IntEnum):
    LOW = 0
    HIGH = 3
    OUT = 4


@pytest.mark.parametrize(
    ("value", "expected"),
    [(member, member) for member in MEMBERS]
    + [(OtherLevel.LOW, ColorLevel.NONE), (OtherLevel.HIGH, ColorLevel.TRUECOLOR)],
)
def test_enum_members_are_read_as_their_numbers(value: int, expected: ColorLevel) -> None:
    assert ColorLevel(value) is expected


class _Duck:
    """Pretends to be the number 2 through every protocol a reader might consult."""

    def __eq__(self, other: object) -> bool:
        return other == 2

    def __hash__(self) -> int:
        return 2

    def __index__(self) -> int:
        return 2

    def __int__(self) -> int:
        return 2

    def __float__(self) -> float:
        return 2.0

    def __complex__(self) -> complex:
        return 2 + 0j

    def __bool__(self) -> bool:
        return True

    @property  # type: ignore[misc]
    def __class__(self) -> type:
        return int


numbers.Integral.register(_Duck)
NON_NUMBERS: list[object] = [
    None,
    OtherLevel.OUT,
    _Duck(),
    *[str(n) for n in range(4)],
    *[b(str(n).encode()) for n in range(4) for b in (bytes, bytearray)],
    memoryview(b"2"),
    [2],
    (2,),
    {2},
    {2: 2},
    range(2, 3),
    object(),
    poison(str)("2"),
    poison(bytes)(b"2"),
    poison(tuple)((2,)),
]


@pytest.mark.parametrize("mode", ["raise", "lie"])
@pytest.mark.parametrize("value", NON_NUMBERS, ids=lambda v: type(v).__name__)
def test_every_other_type_is_rejected_even_when_it_claims_to_be_a_level(
    value: object, mode: str
) -> None:
    with armed(mode):
        assert_rejected(value)
    assert CALLS == []


@pytest.mark.parametrize("failure", exception_classes(), ids=lambda cls: cls.__name__)
def test_no_exception_class_raised_by_the_value_can_escape(
    failure: type[BaseException],
) -> None:
    def fail(*args: object) -> object:
        raise make_error(failure)

    class Raising:
        __eq__ = __ne__ = __bool__ = __index__ = __int__ = __float__ = fail  # type: ignore[assignment]
        __complex__ = __hash__ = __repr__ = __str__ = __getattr__ = fail  # type: ignore[assignment]
        __class__ = property(fail)

    with armed("raise", failure):
        for base in (int, float, complex, Decimal, Fraction):
            assert ColorLevel(build(base, 1, True)) is ColorLevel.BASIC  # type: ignore[arg-type]
            assert_rejected(build(base, 7, True))
        assert_rejected(build(str, "1", True))
        assert_rejected(Raising())
    assert CALLS == []
