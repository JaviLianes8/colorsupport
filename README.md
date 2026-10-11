# colorsupport

Detect a terminal stream color level (none, 16, 256, truecolor) honoring NO_COLOR and FORCE_COLOR

## Install

```
pip install colorsupport
```

## Usage

```python
import sys

from colorsupport import ColorLevel, level, supports_color

match level(sys.stdout):
    case ColorLevel.TRUECOLOR:
        print("\x1b[38;2;255;120;0mhello\x1b[0m")
    case ColorLevel.ANSI256:
        print("\x1b[38;5;208mhello\x1b[0m")
    case ColorLevel.BASIC:
        print("\x1b[33mhello\x1b[0m")
    case ColorLevel.NONE:
        print("hello")

if supports_color(sys.stderr):
    ...
```

Both functions take the stream and the environment as arguments, so detection is
pure and testable: pass any mapping and any object with an `isatty()` method.

```python
level(stream, env={"COLORTERM": "truecolor"})  # ColorLevel.TRUECOLOR
```

`ColorLevel` is an `IntEnum`, so the levels compare as `0 < 1 < 2 < 3`.

### Conventions

- `NO_COLOR`: present with any value, color is off. This wins over everything.
- `FORCE_COLOR`: `0`/`false` off, `1`/`true` basic, `2` for 256, `3` for truecolor.
  It forces a level even when the stream is not a terminal.
- `COLORTERM`: `truecolor` or `24bit` means truecolor.
- `TERM`: a `256` in the name means 256 colors, `dumb` means none, anything else on
  a terminal means basic.
- When none of those apply, a terminal gets basic color and a pipe gets none.

Precedence, highest first: `NO_COLOR`, then `FORCE_COLOR`, then `COLORTERM`/`TERM`,
then whether the stream is a terminal.

## Why

Terminal programs keep rewriting the same color-capability check, and getting the
`NO_COLOR` and `FORCE_COLOR` conventions subtly wrong. JavaScript has
`supports-color`; Python does not have a clean, standalone, typed equivalent that
returns a level. `termcolor` and `rich` decide on or off only internally, and
`colorama` translates ANSI on Windows rather than detecting a level. This library
is a single zero-dependency function that answers the one question: how much color
can this stream show.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
