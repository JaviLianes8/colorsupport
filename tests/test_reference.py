"""Compare with the fetched supports-color implementation running in Node.js."""

from __future__ import annotations

import json
import random
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest
from conftest import PIPE, TTY

from colorsupport import detect

HARNESS = """
import fs from 'node:fs';
Object.defineProperty(process, 'platform', {value: 'linux'});
for (const key of Object.keys(process.env)) delete process.env[key];
const reference = await import('./reference.mjs');
const cases = JSON.parse(fs.readFileSync(0, 'utf8'));
const results = cases.map(([env, tty]) => {
    for (const key of Object.keys(process.env)) delete process.env[key];
    Object.assign(process.env, env);
    const found = reference.createSupportsColor({isTTY: tty}, {sniffFlags: false});
    return found ? found.level : 0;
});
console.log(JSON.stringify(results));
"""


def test_live_reference_on_shared_conventions(
    upstream: Callable[[str], str], tmp_path: Path
) -> None:
    source = upstream("supports-color.js")
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is not installed")
    # URL, revision and hash are in tests/upstream/MANIFEST.json. The implementation is
    # unmodified; only its host platform and environment are injected by the harness.
    (tmp_path / "reference.mjs").write_text(source, encoding="utf-8", newline="\n")
    script = tmp_path / "compare.mjs"
    script.write_text(HARNESS, encoding="utf-8")
    rng = random.Random(20261101)
    choices = {
        "TERM": ["", "dumb", "xterm", "xterm-256color", "xterm-kitty", "wezterm", "unknown"],
        "COLORTERM": ["", "truecolor", "yes"],
        "TERM_PROGRAM": ["iTerm.app", "Apple_Terminal", "other"],
        "TERM_PROGRAM_VERSION": ["", "2.5", "3.1", "10.0"],
        "CI": ["", "1"],
        "GITHUB_ACTIONS": ["", "true"],
        "TRAVIS": ["1"],
        "TEAMCITY_VERSION": ["9.0.1", "9.1.2", "10.0", "v10.0"],
        "FORCE_COLOR": ["0", "1", "2", "3", "99", "false"],
        "TF_BUILD": [""],
        "AGENT_NAME": [""],
    }
    cases: list[tuple[dict[str, str], bool]] = []
    for _ in range(3000):
        env = {key: rng.choice(values) for key, values in choices.items() if rng.randrange(4) == 0}
        cases.append((env, bool(rng.randrange(2))))
    done = subprocess.run(
        [node, str(script)],
        input=json.dumps(cases),
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert done.returncode == 0, done.stderr
    expected = json.loads(done.stdout)
    assert len(expected) == len(cases)
    for (env, tty), wanted in zip(cases, expected, strict=True):
        found = detect(TTY if tty else PIPE, env=env, platform="linux", terminfo=lambda t: None)
        assert found.level == wanted, (env, tty, found, wanted)
