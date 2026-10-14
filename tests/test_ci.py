"""CI services: which logs show color, and Azure Pipelines when piped.

Expected values are written by hand from supports-color's index.js (pinned in
tests/upstream/MANIFEST.json); tests/test_upstream.py checks the lists against that file.
"""

from __future__ import annotations

import pytest
from conftest import PIPE, TTY, on_linux

from colorsupport import ColorLevel


@pytest.mark.parametrize("name", ["GITHUB_ACTIONS", "GITEA_ACTIONS", "CIRCLECI"])
def test_ci_services_with_truecolor_logs(name: str) -> None:
    found = on_linux(TTY, **{"CI": "true", name: "true", "TERM": "dumb-ish"})
    assert found.level is ColorLevel.TRUECOLOR
    assert found.reason == f"CI service with color logs ({name} is set)"


@pytest.mark.parametrize("name", ["TRAVIS", "APPVEYOR", "GITLAB_CI", "BUILDKITE", "DRONE"])
def test_ci_services_with_basic_color_logs(name: str) -> None:
    assert on_linux(TTY, **{"CI": "1", name: "", "COLORTERM": "truecolor"}).level == 1


def test_codeship_and_unknown_ci() -> None:
    assert on_linux(TTY, CI="1", CI_NAME="codeship").level is ColorLevel.BASIC
    unknown = on_linux(TTY, CI="woodpecker", COLORTERM="truecolor")
    assert unknown.level is ColorLevel.NONE
    assert unknown.reason == "CI is set and the service is not known to show color"
    assert on_linux(TTY, GITHUB_ACTIONS="true").level is ColorLevel.NONE


def test_ci_is_still_piped_unless_forced() -> None:
    assert on_linux(PIPE, CI="1", GITHUB_ACTIONS="1").level is ColorLevel.NONE
    assert on_linux(PIPE, CI="1", GITHUB_ACTIONS="1", FORCE_COLOR="true").level == 3


def test_azure_pipelines_has_color_even_when_piped() -> None:
    found = on_linux(PIPE, TF_BUILD="True", AGENT_NAME="Hosted")
    assert (found.level, found.reason) == (
        ColorLevel.BASIC,
        "Azure Pipelines (TF_BUILD, AGENT_NAME)",
    )
    assert on_linux(PIPE, TF_BUILD="True").level is ColorLevel.NONE
    assert on_linux(PIPE, TF_BUILD="1", AGENT_NAME="a", FORCE_COLOR="0").level == 0


@pytest.mark.parametrize(
    ("version", "expected"),
    [("9.1.2", 1), ("9.01.0", 1), ("10.0", 1), ("2023.05", 1), ("9.0.1", 0), ("8.1", 0)],
)
def test_teamcity_has_color_from_9_1(version: str, expected: int) -> None:
    assert on_linux(TTY, TEAMCITY_VERSION=version, TERM="xterm").level == expected


def test_ci_counts_by_presence_even_when_empty() -> None:
    assert on_linux(TTY, CI="", GITHUB_ACTIONS="").level is ColorLevel.TRUECOLOR
    assert on_linux(TTY, CI="1", CI_NAME="jenkins").level is ColorLevel.NONE


@pytest.mark.parametrize("version", ["v10.0", "x9.1.0", " 9.1.0"])
def test_teamcity_version_must_start_with_the_number(version: str) -> None:
    assert on_linux(TTY, TEAMCITY_VERSION=version, TERM="xterm").level is ColorLevel.NONE
