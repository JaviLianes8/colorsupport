from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path

import pytest

from colorsupport import Detection, detect

UPSTREAM = Path(__file__).resolve().parent / "upstream"


class FakeStream:
    """A stream stand-in whose TTY status the test controls."""

    def __init__(self, tty: bool) -> None:
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty


TTY = FakeStream(tty=True)
PIPE = FakeStream(tty=False)


def on_linux(stream: object = TTY, **env: str) -> Detection:
    """Detect on a Linux-like host with no terminfo database, so only env decides."""
    return detect(stream, env=env, platform="linux", terminfo=lambda term: None)


def read_upstream(name: str) -> str:
    """Return a third-party reference file as text.

    The files are not committed: `python scripts/fetch_upstream.py` fetches them. Their
    tests skip while a file is absent and fail if it differs from the manifest.
    """
    path = UPSTREAM / name
    if not path.is_file():
        pytest.skip(f"{name} is not fetched; run python scripts/fetch_upstream.py")
    entry = json.loads((UPSTREAM / "MANIFEST.json").read_text(encoding="utf-8"))[name]
    body = path.read_bytes()
    assert hashlib.sha256(body).hexdigest() == entry["sha256"], f"{name} differs from MANIFEST"
    return body.decode("utf-8")


@pytest.fixture
def upstream() -> Callable[[str], str]:
    return read_upstream
