from __future__ import annotations

import pytest

from colorsupport import ColorLevel, Detection


def test_levels_are_ordered_numbers() -> None:
    assert [int(member) for member in ColorLevel] == [0, 1, 2, 3]
    assert ColorLevel.NONE < ColorLevel.BASIC < ColorLevel.ANSI256 < ColorLevel.TRUECOLOR


def test_colors_counts_each_level() -> None:
    assert [member.colors for member in ColorLevel] == [0, 16, 256, 16_777_216]


def test_labels_name_each_level() -> None:
    assert [member.label for member in ColorLevel] == ["none", "16", "256", "truecolor"]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("none", ColorLevel.NONE),
        ("0", ColorLevel.NONE),
        ("16", ColorLevel.BASIC),
        ("basic", ColorLevel.BASIC),
        ("1", ColorLevel.BASIC),
        ("256", ColorLevel.ANSI256),
        ("ANSI256", ColorLevel.ANSI256),
        ("2", ColorLevel.ANSI256),
        (" TrueColor ", ColorLevel.TRUECOLOR),
        ("3", ColorLevel.TRUECOLOR),
    ],
)
def test_parse_reads_labels_names_and_numbers(text: str, expected: ColorLevel) -> None:
    assert ColorLevel.parse(text) is expected


@pytest.mark.parametrize("text", ["", "4", "8", "24bit", "true", "-1"])
def test_parse_rejects_anything_else(text: str) -> None:
    with pytest.raises(ValueError, match="unknown color level"):
        ColorLevel.parse(text)


def test_parse_rejects_a_non_string() -> None:
    with pytest.raises(TypeError, match="expected a str, got int"):
        ColorLevel.parse(3)  # type: ignore[arg-type]


def test_detection_prints_label_and_reason() -> None:
    assert str(Detection(ColorLevel.ANSI256, "TERM=xterm-256color")) == "256: TERM=xterm-256color"


def test_detection_is_immutable_and_comparable() -> None:
    found = Detection(ColorLevel.NONE, "x")
    assert found == Detection(ColorLevel.NONE, "x")
    with pytest.raises(AttributeError):
        found.level = ColorLevel.BASIC  # type: ignore[misc]
