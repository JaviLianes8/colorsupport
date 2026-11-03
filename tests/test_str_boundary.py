"""Every text and integer input is read once through its base type, never through its methods.

Each value below is a generated subclass whose every method and dunder either raises or
lies while armed. Each public API is called with plain values and with poisoned copies;
the results must be identical and no poisoned code may run.
"""

from __future__ import annotations

import random
from pathlib import Path

import pytest
from _poison import CALLS, armed, poison
from conftest import PIPE, TTY
from test_terminfo import entry

from colorsupport import ColorLevel, detect, level, supports_color, terminfo_colors
from colorsupport._detect import ENV_NAMES

PStr, PInt = poison(str), poison(int)
VALUES = ["", "0", "1", "2", "3", "99", "false", "FALSE ", "ON", "dumb", "truecolor", "24bit"]
VALUES += ["xterm", "xterm-256color", "xterm-kitty", "screen", "linux", "iTerm.app", "codeship"]
VALUES += ["Apple_Terminal", "3.4", "9.1.2", "x-256", "\x1b[31m", "a" * 50, "custom"]


def environments(seed: int, count: int) -> list[dict[str, str]]:
    rng = random.Random(seed)
    return [
        {name: rng.choice(VALUES) for name in rng.sample(ENV_NAMES, rng.randrange(8))}
        for _ in range(count)
    ]


def poisoned(env: dict[str, str]) -> dict[str, str]:
    return {name: PStr(value) for name, value in env.items()}


def call_all(env: dict[str, str], stream: object, **options: object) -> tuple[object, ...]:
    kwargs: dict[str, object] = {"env": env, "terminfo": lambda term: None, **options}
    found = detect(stream, **kwargs)  # type: ignore[arg-type]
    return found, level(stream, **kwargs), supports_color(stream, **kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize("mode", ["raise", "lie"])
@pytest.mark.parametrize("platform", ["linux", "win32"])
@pytest.mark.parametrize("seed", [3, 20261103])
def test_detection_reads_poisoned_text_as_its_exact_value(
    seed: int, platform: str, mode: str
) -> None:
    for env in environments(seed, 300):
        for when in ("auto", "always", "never"):
            for stream in (TTY, PIPE):
                options = {"platform": platform, "vt": True, "windows_build": 19045}
                expected = call_all(env, stream, when=when, **options)
                hostile = {"platform": PStr(platform), "vt": True, "windows_build": PInt(19045)}
                with armed(mode):
                    got = call_all(poisoned(env), stream, when=PStr(when), **hostile)
                assert got == expected
                assert CALLS == []


@pytest.mark.parametrize("mode", ["raise", "lie"])
@pytest.mark.parametrize("count", [0, 7, 8, 255, 256, 16_777_215, 16_777_216, 2**70])
def test_callback_and_flag_integers_are_read_exactly(count: int, mode: str) -> None:
    env = {"TERM": "custom"}
    for vt in (True, False, 1, 0):
        for build in (0, 10585, 10586, 14930, 14931, 2**70):
            options = {"platform": "win32", "windows_build": build}
            expected = call_all(env, TTY, vt=vt, terminfo=lambda term: count, **options)
            hostile = {"platform": "win32", "windows_build": PInt(build)}
            with armed(mode):
                got = call_all(env, TTY, vt=PInt(vt), terminfo=lambda term: PInt(count), **hostile)
            assert got == expected
            assert CALLS == []


@pytest.mark.parametrize(
    ("argument", "value", "message"),
    [
        ("vt", "yes", "vt must be a bool or None"),
        ("vt", 1.0, "vt must be a bool or None"),
        ("windows_build", "19045", "windows_build must be an int or None"),
        ("windows_build", 19045.0, "windows_build must be an int or None"),
        ("terminfo", lambda term: 256.0, "terminfo must return an int or None"),
        ("terminfo", lambda term: "256", "terminfo must return an int or None"),
    ],
)
def test_wrongly_typed_numbers_raise_type_error(argument: str, value: object, message: str) -> None:
    # On Windows the console decides before terminfo is asked, so terminfo runs on Linux.
    system = "linux" if argument == "terminfo" else "win32"
    options: dict[str, object] = {"platform": system, "vt": True, "windows_build": 19045}
    options["terminfo"] = lambda term: 256
    options[argument] = value
    with pytest.raises(TypeError, match=f"^{message}$"):
        detect(TTY, env={"TERM": "custom"}, **options)  # type: ignore[arg-type]


@pytest.mark.parametrize("mode", ["raise", "lie"])
@pytest.mark.parametrize("text", [*VALUES, " TrueColor ", "BASIC", "ansi256", "none", "4"])
def test_parse_reads_poisoned_text_as_its_exact_value(text: str, mode: str) -> None:
    try:
        expected: object = ColorLevel.parse(text)
    except ValueError as error:
        expected = str(error)
    with armed(mode):
        try:
            got: object = ColorLevel.parse(PStr(text))
        except ValueError as error:
            got = str(error)
    assert got == expected
    assert CALLS == []


@pytest.mark.parametrize("mode", ["raise", "lie"])
@pytest.mark.parametrize("term", ["t", "xterm", ".t", "a/t", "a\\t", "a:t", "t\0", "", "é"])
def test_terminfo_reads_poisoned_names_and_variables_exactly(
    tmp_path: Path, term: str, mode: str
) -> None:
    for name in ("t", "xterm", "é"):
        folder = tmp_path / "db" / name[0]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / name).write_bytes(entry(256))
    (tmp_path / "home" / ".terminfo").mkdir(parents=True)
    for env in (
        {"TERMINFO": str(tmp_path / "db")},
        {"HOME": str(tmp_path / "home"), "TERMINFO_DIRS": f"x;{tmp_path / 'db'}"},
        {"TERMINFO_DIRS": str(tmp_path / "db")},
    ):
        expected = terminfo_colors(term, env)
        hostile = poisoned(env)
        with armed(mode):
            got = terminfo_colors(PStr(term), hostile)
        assert got == expected
        assert CALLS == []
