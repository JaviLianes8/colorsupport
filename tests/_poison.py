"""Generated subclasses of builtin types whose every method and dunder lies or raises.

While `armed`, each overridden attribute records its name in `CALLS` and then either
raises `failure` (a secret-bearing exception) or returns a plausible lie. Disarmed, it
delegates to the base type, so instances can still be built and compared by the test.
A public API that reads such a value only through its base type sees the plain value
and leaves `CALLS` empty.
"""

from __future__ import annotations

import builtins
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

SECRET = "POISON_SECRET_MARKER"
CALLS: list[str] = []
_STATE: dict[str, Any] = {"armed": False, "mode": "raise", "failure": RuntimeError}

# Attributes that build or describe the class itself; overriding them breaks construction.
_KEEP = {
    "__new__",
    "__init__",
    "__init_subclass__",
    "__subclasshook__",
    "__class_getitem__",
    "__getattribute__",
    "__setattr__",
    "__delattr__",
    "__dict__",
    "__doc__",
    "__module__",
    "__slots__",
    "__weakref__",
    "__abstractmethods__",
    "_abc_impl",
}

# Lies that would steer a careless reader towards a valid level or a safe name.
_LIES: dict[str, object] = {
    "__eq__": True,
    "__ne__": False,
    "__bool__": True,
    "__index__": 2,
    "__int__": 2,
    "__trunc__": 2,
    "__floor__": 2,
    "__ceil__": 2,
    "__round__": 2,
    "__float__": 2.0,
    "__complex__": 2 + 0j,
    "__hash__": 2,
    "__len__": 1,
    "__contains__": False,
    "real": 2,
    "imag": 0,
    "numerator": 2,
    "denominator": 1,
    "as_integer_ratio": (2, 1),
    "is_integer": True,
    "is_finite": True,
    "startswith": False,
}


def exception_classes() -> list[type[BaseException]]:
    """Every builtin exception class, BaseException ones included."""
    found = [
        value
        for value in vars(builtins).values()
        if isinstance(value, type) and issubclass(value, BaseException)
    ]

    class CustomError(Exception):
        pass

    return [*sorted(found, key=lambda cls: cls.__name__), CustomError]


def make_error(cls: type[BaseException]) -> BaseException:
    try:
        return cls(SECRET)
    except TypeError:
        error = cls.__new__(cls)
        error.args = (SECRET,)
        return error


def _hit(name: str, lie: object) -> object:
    CALLS.append(name)
    if _STATE["mode"] == "lie":
        return lie
    raise make_error(_STATE["failure"])


def _method(base: type, name: str, original: Any) -> Callable[..., object]:
    lie = _LIES.get(name, "truecolor" if issubclass(base, str) else 2)

    def poisoned(self: object, *args: object, **kwargs: object) -> object:
        if _STATE["armed"]:
            return _hit(name, lie)
        return original(self, *args, **kwargs)

    return poisoned


def _descriptor(name: str, original: Any) -> property:
    lie = _LIES.get(name, 2)

    def get(self: object) -> object:
        if _STATE["armed"]:
            return _hit(name, lie)
        return original.__get__(self, type(self))

    if not hasattr(original, "__set__"):
        return property(get)

    def put(self: object, value: object) -> None:
        # Construction of slot-based types such as Fraction stores through here.
        original.__set__(self, value)

    return property(get, put)


def poison(base: type) -> type:
    """A subclass of base overriding every inherited attribute that the reader could call."""
    body: dict[str, object] = {}
    for klass in reversed(base.__mro__):
        for name, original in vars(klass).items():
            if name in _KEEP or isinstance(original, (classmethod, staticmethod, str)):
                continue
            if callable(original):
                body[name] = _method(base, name, original)
            elif hasattr(original, "__get__"):
                body[name] = _descriptor(name, original)
    body["__class__"] = _descriptor("__class__", vars(object)["__class__"])

    def getattribute(self: object, name: str) -> object:
        if _STATE["armed"]:
            return _hit("__getattribute__", 2)
        reader: Any = base.__getattribute__
        return reader(self, name)

    body["__getattribute__"] = getattribute
    return type(f"Poison{base.__name__.title()}", (base,), body)


@contextmanager
def armed(mode: str = "raise", failure: type[BaseException] = RuntimeError) -> Iterator[None]:
    """Arm every poisoned value for the duration of the block."""
    CALLS.clear()
    _STATE.update(armed=True, mode=mode, failure=failure)
    try:
        yield
    finally:
        _STATE["armed"] = False
