"""Build the wheel, install it in a throwaway venv and drive the installed package.

Slow and needs the build backend, so it runs only with COLORSUPPORT_E2E=1.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import venv
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    os.environ.get("COLORSUPPORT_E2E") != "1", reason="set COLORSUPPORT_E2E=1 to build and install"
)

PROGRAM = """
import importlib.metadata, importlib.resources, io
import colorsupport
from colorsupport import ColorLevel, Detection, detect, enable_vt, level, supports_color

assert "site-packages" in colorsupport.__file__, colorsupport.__file__
assert importlib.metadata.version("colorsupport") == colorsupport.__version__
assert importlib.resources.files("colorsupport").joinpath("py.typed").is_file()

class Tty:
    def isatty(self):
        return True

found = detect(Tty(), env={"TERM": "xterm-256color"}, platform="linux", terminfo=lambda t: None)
assert found == Detection(ColorLevel.ANSI256, "TERM=xterm-256color"), found
assert level(io.StringIO(), env={"FORCE_COLOR": "3"}) is ColorLevel.TRUECOLOR
assert not supports_color(Tty(), env={"NO_COLOR": "1"})
assert level(Tty(), env={}, platform="win32", vt=False) is ColorLevel.NONE
assert enable_vt(io.StringIO()) is False
assert ColorLevel.parse("truecolor").colors == 16777216
try:
    detect(env={}, when="sometimes")
except ValueError:
    pass
else:
    raise AssertionError("when was not checked")
print("e2e ok")
"""


def _run(*cmd: str | Path, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(c) for c in cmd], cwd=cwd, env=env, capture_output=True, text=True, check=False
    )


def test_installed_wheel_end_to_end(tmp_path: Path) -> None:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("NO_COLOR", "CLICOLOR"))}
    env.pop("FORCE_COLOR", None)
    dist = tmp_path / "dist"
    built = _run(sys.executable, "-m", "build", "--outdir", dist, ROOT, cwd=tmp_path, env=env)
    assert built.returncode == 0, built.stderr
    (wheel,) = dist.glob("colorsupport-*.whl")
    (sdist,) = dist.glob("colorsupport-*.tar.gz")
    names = zipfile.ZipFile(wheel).namelist()
    assert "colorsupport/py.typed" in names
    assert "colorsupport/__main__.py" in names
    assert not any(name.startswith("tests/") for name in names)
    listing = _run(sys.executable, "-m", "tarfile", "-l", sdist, cwd=tmp_path, env=env).stdout
    assert "IMPROVEMENTS-round" not in listing
    assert "tests/upstream/MANIFEST.json" in listing
    assert "supports-color.js" not in listing
    assert "no-color.md" not in listing
    assert "tests/test_upstream.py" in listing
    assert "scripts/fetch_upstream.py" in listing

    env_dir = tmp_path / "venv"
    venv.create(env_dir, with_pip=True)
    bindir = env_dir / ("Scripts" if sys.platform == "win32" else "bin")
    python = bindir / "python"
    installed = _run(python, "-m", "pip", "install", "-q", wheel, cwd=tmp_path, env=env)
    assert installed.returncode == 0, installed.stderr

    # Run from an empty folder so the source tree cannot shadow the install.
    work = tmp_path / "work"
    work.mkdir()
    result = _run(python, "-I", "-c", PROGRAM, cwd=work, env=env)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "e2e ok"

    script = bindir / ("colorsupport.exe" if sys.platform == "win32" else "colorsupport")
    piped = _run(script, "--json", cwd=work, env=env)
    assert json.loads(piped.stdout) == {
        "level": "none",
        "colors": 0,
        "reason": "the stream is not a terminal",
    }
    forced = _run(python, "-m", "colorsupport", cwd=work, env={**env, "FORCE_COLOR": "2"})
    assert forced.stdout == "256: FORCE_COLOR=2 asks for 256 colors\n"
    assert _run(script, "--check", "16", cwd=work, env=env).returncode == 1
    assert _run(script, "--check", "8", cwd=work, env=env).returncode == 2
