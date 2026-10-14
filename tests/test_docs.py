"""The README examples run and print what their comments say; docs and versions agree."""

from __future__ import annotations

import contextlib
import io
import itertools
import re
from pathlib import Path

import colorsupport

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")


def _python_blocks() -> list[str]:
    return re.findall(r"```python\n(.*?)```", README, flags=re.DOTALL)


def _expected_output(block: str) -> list[str]:
    """Each print line is followed by a comment line that holds what it prints."""
    lines = block.splitlines()
    return [
        following.strip()[2:]
        for line, following in itertools.pairwise(lines)
        if line.strip().startswith("print(") and following.strip().startswith("# ")
    ]


def test_every_readme_example_runs_and_prints_its_comment() -> None:
    checked = 0
    for block in _python_blocks():
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exec(compile(block, "README.md", "exec"), {"__name__": "readme"})
        assert out.getvalue().splitlines() == _expected_output(block)
        checked += len(_expected_output(block))
    assert len(_python_blocks()) == 4
    assert checked == 8


def test_every_print_in_the_readme_shows_its_output() -> None:
    for block in _python_blocks():
        prints = [line for line in block.splitlines() if line.strip().startswith("print(")]
        assert len(prints) == len(_expected_output(block))


def test_the_api_table_lists_every_public_name() -> None:
    table = README.split("## API", 1)[1].split("\n## ", 1)[0]
    for name in colorsupport.__all__:
        assert f"`{name}" in table, name


def test_version_matches_pyproject() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', text, flags=re.MULTILINE)
    assert match is not None
    assert match.group(1) == colorsupport.__version__


def test_changelog_has_an_entry_for_this_version() -> None:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## [{colorsupport.__version__}]" in text


def _tracked_text_files() -> list[Path]:
    suffixes = {".py", ".md", ".toml", ".ps1", ".txt", ".yml", ".json"}
    found = []
    for path in ROOT.rglob("*"):
        parts = path.relative_to(ROOT).parts
        if not path.is_file() or path.suffix not in suffixes:
            continue
        if parts[:2] == ("tests", "upstream") and path.name != "MANIFEST.json":
            continue
        if any((p.startswith(".") and p != ".github") or p == "__pycache__" for p in parts):
            continue
        found.append(path)
    return found


def test_no_em_dash_or_raw_control_character_in_the_tree() -> None:
    controls = {chr(c) for c in range(32) if chr(c) not in "\t\n\r"}
    for path in _tracked_text_files():
        text = path.read_text(encoding="utf-8")
        assert chr(0x2014) not in text, path
        assert not controls & set(text), path


def test_source_files_stay_under_two_hundred_lines() -> None:
    for path in [*ROOT.joinpath("src").rglob("*.py"), *ROOT.joinpath("tests").rglob("*.py")]:
        assert len(path.read_text(encoding="utf-8").splitlines()) <= 200, path
