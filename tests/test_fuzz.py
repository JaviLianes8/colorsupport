"""Seeded synthetic inputs and invariants, not external golden vectors."""

from __future__ import annotations

import random
import struct
import time

import pytest
from conftest import PIPE, TTY

from colorsupport import ColorLevel, detect, level, supports_color
from colorsupport._terminfo import parse_colors


@pytest.mark.parametrize("seed", [17, 20261101, 7391])
def test_seeded_environment_and_level_properties(seed: int) -> None:
    rng = random.Random(seed)
    alphabet = "abcXYZ0123456789-_; \n\x1b\0\ud800\u00e9"
    keys = ["NO_COLOR", "FORCE_COLOR", "TERM", "COLORTERM", "CI", "CLICOLOR", "CLICOLOR_FORCE"]
    for _ in range(2000):
        text = "".join(rng.choices(alphabet, k=rng.randrange(120)))
        env = {rng.choice(keys): text for _ in range(4)}
        stream = rng.choice([TTY, PIPE])
        found = detect(stream, env=env, platform="linux", terminfo=lambda t: None)
        assert isinstance(found.level, ColorLevel)
        assert found.reason.isascii() and len(found.reason) < 1000
        assert level(stream, env=env, platform="linux", terminfo=lambda t: None) is found.level
        assert supports_color(stream, env=env, platform="linux", terminfo=lambda t: None) == (
            found.level > ColorLevel.NONE
        )
        assert detect(stream, env=env, when="never").level is ColorLevel.NONE
        assert (
            detect(stream, env=env, when="always", platform="linux", terminfo=lambda t: None).level
            >= 1
        )
        try:
            parsed = ColorLevel.parse(text)
        except ValueError as error:
            assert len(str(error)) < 100
        else:
            assert ColorLevel.parse(parsed.label) is parsed


@pytest.mark.parametrize("seed", [41, 20261101])
def test_seeded_binary_terminfo_inputs(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(5000):
        data = bytes(rng.randrange(256) for _ in range(rng.randrange(150)))
        if rng.randrange(2) and len(data) >= 12:
            data = struct.pack("<h", rng.choice([0o432, 0o1036])) + data[2:]
        found = parse_colors(data)
        assert found is None or (isinstance(found, int) and found >= 0)
    for _ in range(2000):
        count = rng.randrange(2**31)
        names = b"x" * rng.randrange(1, 40)
        flags = bytes(rng.randrange(256) for _ in range(rng.randrange(30)))
        header = struct.pack("<6h", 0o1036, len(names), len(flags), 14, 0, 0)
        prefix = header + names + flags
        prefix += b"\0" * (len(prefix) % 2)
        assert parse_colors(prefix + b"\xff" * 52 + struct.pack("<i", count)) == count


def test_long_adversarial_shapes_finish_with_bounded_diagnostics() -> None:
    # A broad bound detects pathological growth without relying on small timing ratios.
    start = time.monotonic()
    for size in (100_000, 400_000, 1_600_000):
        for key, value in (
            ("FORCE_COLOR", "9" * size),
            ("FORCE_COLOR", "0" * size + "2"),
            ("TERM", "x" * size + "-256color"),
            ("TERM", "\ud800" * size),
            ("TEAMCITY_VERSION", "9." + "0" * size),
            ("TERM_PROGRAM_VERSION", "9" * size),
        ):
            env = {key: value}
            if key == "TERM_PROGRAM_VERSION":
                env["TERM_PROGRAM"] = "iTerm.app"
            result = detect(TTY, env=env, platform="linux", terminfo=lambda t: None)
            assert len(result.reason) < 1000 and result.reason.isascii()
    assert time.monotonic() - start < 30
