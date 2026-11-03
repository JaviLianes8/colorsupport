"""One table of every public parameter that takes text or a number, each fed a poisoned subclass.

A poisoned value overrides every method and dunder of its base type to raise or lie while
armed. Every entry below calls a public API once with plain values and once with poisoned
copies: the results must be identical and no poisoned code may run. A drift guard checks
that the table names every parameter of every public callable, so a new parameter cannot
skip the boundary unnoticed.
"""

from __future__ import annotations

import inspect
import os
from collections.abc import Callable
from functools import partial
from pathlib import Path

import pytest
from _poison import CALLS, armed, poison
from conftest import PIPE, TTY
from test_terminfo import entry

import colorsupport as cs

PStr, PInt = poison(str), poison(int)
DETECTORS = (cs.detect, cs.level, cs.supports_color)

# Parameters that are not caller text or numbers, with the reason they stay outside the table.
EXEMPT = {
    ("detect", "stream"): "any object; its own isatty() is the documented probe",
    ("enable_vt", "stream"): "any object; only its file descriptor is asked for",
    ("Detection", "level"): "documented as typed, with no runtime coercion",
    ("Detection", "reason"): "documented as typed, with no runtime coercion",
}


def outcome(call: Callable[[], object]) -> object:
    try:
        return call()
    except (TypeError, ValueError) as error:
        return type(error), str(error)


def detect_with(**overrides: object) -> Callable[[Callable[..., object]], object]:
    options: dict[str, object] = {"env": {"TERM": "custom"}, "platform": "linux"}
    options.update(terminfo=lambda term: 256, vt=True, windows_build=19045, when="auto")
    options.update(overrides)
    return lambda api: api(TTY, **options)


Thunk = Callable[[], object]
# (api, parameter) -> list of (plain call, poisoned call). Each call takes the api.
Pair = tuple[Callable[[Callable[..., object]], object], Callable[[Callable[..., object]], object]]


def detector_pairs(parameter: str) -> list[Pair]:
    if parameter == "when":
        texts = ["auto", "always", "never", "", "AUTO", " never", "on"]
        return [(detect_with(when=t), detect_with(when=PStr(t))) for t in texts]
    if parameter == "platform":
        texts = ["linux", "win32", "", "WIN32", "win32 ", "darwin"]
        return [(detect_with(platform=t), detect_with(platform=PStr(t))) for t in texts]
    if parameter == "env":
        values = ["", "0", "1", "2", "3", "false", "dumb", "xterm-256color", "truecolor"]
        names = ["NO_COLOR", "FORCE_COLOR", "CLICOLOR_FORCE", "CLICOLOR", "TERM", "COLORTERM"]
        return [
            (detect_with(env={n: v}), detect_with(env={n: PStr(v)})) for n in names for v in values
        ]
    if parameter == "vt":
        flags = [True, False, 1, 0]
        return [
            (detect_with(platform="win32", vt=f), detect_with(platform="win32", vt=PInt(f)))
            for f in flags
        ]
    if parameter == "windows_build":
        builds = [0, 10585, 10586, 14930, 14931, 2**70]
        return [
            (
                detect_with(platform="win32", windows_build=b),
                detect_with(platform="win32", windows_build=PInt(b)),
            )
            for b in builds
        ]
    if parameter == "terminfo":
        counts = [0, 8, 16, 255, 256, 16_777_216, 2**70]
        return [
            (
                detect_with(terminfo=lambda term, c=c: c),
                detect_with(terminfo=lambda term, c=c: PInt(c)),
            )
            for c in counts
        ]
    raise AssertionError(parameter)


def other_pairs(api: str, parameter: str, db: Path) -> list[tuple[Thunk, Thunk]]:
    if (api, parameter) == ("ColorLevel", "value"):
        numbers = range(-1, 5)
        return [(partial(cs.ColorLevel, n), partial(cs.ColorLevel, PInt(n))) for n in numbers]
    parse = cs.ColorLevel.parse
    if (api, parameter) == ("parse", "text"):
        texts = ["none", "16", "256", "truecolor", " 3 ", "BASIC", "ansi256", "", "8", "\t1\r\n"]
        return [(partial(parse, t), partial(parse, PStr(t))) for t in texts]
    lookup = cs.terminfo_colors
    if (api, parameter) == ("terminfo_colors", "term"):
        names = ["t", "xterm", "", ".t", "a/t", "a\\t", "a:t", "t\0", "\xe9"]
        env = {"TERMINFO": str(db)}
        return [(partial(lookup, t, env), partial(lookup, PStr(t), env)) for t in names]
    if (api, parameter) == ("terminfo_colors", "env"):
        dirs = os.pathsep.join(["x", str(db)])
        envs = [{"TERMINFO": str(db)}, {"HOME": str(db)}, {"TERMINFO_DIRS": dirs}]
        return [
            (partial(lookup, "t", e), partial(lookup, "t", {k: PStr(v) for k, v in e.items()}))
            for e in envs
        ]
    raise AssertionError((api, parameter))


TABLE = [(api.__name__, p) for api in DETECTORS for p in ("when", "platform", "env")]
TABLE += [(api.__name__, p) for api in DETECTORS for p in ("vt", "windows_build", "terminfo")]
OTHERS = [("ColorLevel", "value"), ("parse", "text"), ("terminfo_colors", "term")]
OTHERS += [("terminfo_colors", "env")]


def public_parameters() -> set[tuple[str, str]]:
    found: set[tuple[str, str]] = set()
    for name in cs.__all__:
        target = getattr(cs, name)
        callables = [("ColorLevel", lambda value: None), ("parse", cs.ColorLevel.parse)]
        if name != "ColorLevel":
            callables = [(name, target)]
        for label, function in callables:
            for parameter in inspect.signature(function).parameters:
                found.add((label, parameter))
    return found


def test_table_names_every_public_parameter() -> None:
    covered = {*TABLE, *OTHERS, *EXEMPT}
    for api in ("level", "supports_color"):
        covered.add((api, "stream"))
    assert covered == public_parameters()


@pytest.mark.parametrize("mode", ["raise", "lie"])
@pytest.mark.parametrize(("api", "parameter"), TABLE)
def test_detection_parameters_read_poisoned_values_exactly(
    api: str, parameter: str, mode: str
) -> None:
    target = getattr(cs, api)
    for plain, hostile in detector_pairs(parameter):
        expected = outcome(partial(plain, target))
        with armed(mode):
            got = outcome(partial(hostile, target))
        assert got == expected, (api, parameter)
        assert CALLS == []
    assert outcome(lambda: target(PIPE, env={}, platform="linux")) == outcome(
        lambda: target(PIPE, env={}, platform=PStr("linux"))
    )


@pytest.mark.parametrize("mode", ["raise", "lie"])
@pytest.mark.parametrize(("api", "parameter"), OTHERS)
def test_other_parameters_read_poisoned_values_exactly(
    tmp_path: Path, api: str, parameter: str, mode: str
) -> None:
    for root in (tmp_path, tmp_path / ".terminfo"):
        (root / "t").mkdir(parents=True)
        (root / "t" / "t").write_bytes(entry(256))
    for plain, hostile in other_pairs(api, parameter, tmp_path):
        expected = outcome(plain)
        with armed(mode):
            got = outcome(hostile)
        assert got == expected, (api, parameter)
        assert CALLS == []
