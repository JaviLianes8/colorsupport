"""The `colorsupport` command: print the detected level and reason, or check it."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from ._detect import detect
from ._level import ColorLevel


def _level(text: str) -> ColorLevel:
    try:
        return ColorLevel.parse(text)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from None


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="colorsupport",
        description="Report how much color the terminal on stdout (or stderr) can show.",
    )
    parser.add_argument("--stderr", action="store_true", help="look at stderr, not stdout")
    parser.add_argument(
        "--when",
        choices=("auto", "always", "never"),
        default="auto",
        help="the --color choice of the calling program (default: auto)",
    )
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="print level, colors and reason")
    output.add_argument(
        "--check",
        metavar="LEVEL",
        type=_level,
        help="print nothing; exit 0 if at least LEVEL (none, 16, 256, truecolor), else 1",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return its exit code."""
    args = _parser().parse_args(argv)
    stream = sys.stderr if args.stderr else sys.stdout
    found = detect(stream, when=args.when)
    if args.check is not None:
        return 0 if found.level >= args.check else 1
    if args.json:
        record = {"level": found.level.label, "colors": found.level.colors, "reason": found.reason}
        print(json.dumps(record))
    else:
        print(found)
    return 0
