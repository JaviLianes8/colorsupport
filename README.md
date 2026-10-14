# colorsupport

Detect how much color a terminal stream can show (none, 16, 256 or truecolor) and say
why. It follows the `NO_COLOR`, `FORCE_COLOR`, `CLICOLOR` and `CLICOLOR_FORCE`
conventions, reads `TERM`, `COLORTERM`, terminfo, CI services and Windows consoles, and
takes every input as an argument so tests are deterministic. No dependencies, fully typed.

## Install

```
pip install colorsupport
```

## Usage

```python
import sys

from colorsupport import ColorLevel, level

match level(sys.stdout):
    case ColorLevel.TRUECOLOR:
        line = "\x1b[38;2;255;120;0mhello\x1b[0m"
    case ColorLevel.ANSI256:
        line = "\x1b[38;5;208mhello\x1b[0m"
    case ColorLevel.BASIC:
        line = "\x1b[33mhello\x1b[0m"
    case ColorLevel.NONE:
        line = "hello"
```

`detect` returns the level together with the reason, which is what a user asking "why no
colors?" needs to see. Every input can be passed in; anything left out is read from the
running process when the function is called.

```python
from colorsupport import ColorLevel, detect


class Terminal:
    def isatty(self) -> bool:
        return True


found = detect(Terminal(), env={"TERM": "xterm-256color"}, platform="linux")
print(found)
# 256: TERM=xterm-256color
print(found.level >= ColorLevel.BASIC, found.level.colors)
# True 256
print(detect(Terminal(), env={"NO_COLOR": "1", "COLORTERM": "truecolor"}))
# none: NO_COLOR is set
print(detect(Terminal(), env={"FORCE_COLOR": "true", "COLORTERM": "truecolor"}))
# truecolor: FORCE_COLOR='true' turns color on; COLORTERM=truecolor
print(detect(Terminal(), env={}, platform="win32", vt=True, windows_build=19045))
# truecolor: Windows console with VT processing, build 19045
```

A program with its own `--color=auto|always|never` flag passes it as `when`. The
NO_COLOR page asks for exactly this: a flag given for one run beats the variable.

```python
import io

from colorsupport import detect, supports_color

piped = io.StringIO()
print(supports_color(piped, env={}))
# False
print(detect(piped, env={"NO_COLOR": "1"}, when="always", platform="linux"))
# 16: the caller turned color on (when='always'); the terminal does not say how many colors
print(detect(piped, env={"FORCE_COLOR": "3"}, when="never"))
# none: the caller turned color off (when='never')
```

## How the level is decided

Highest priority first. A variable set to an empty string counts as unset.

1. `when="never"` gives none; `when="always"` turns color on and skips steps 2 to 5.
2. `NO_COLOR` gives none.
3. `FORCE_COLOR`: `0` or `false` gives none; `1`, `2` and `3` give exactly 16, 256 and
   truecolor (larger numbers mean truecolor), even on a pipe; any other value turns color
   on and lets the terminal decide the depth.
4. `CLICOLOR_FORCE` turns color on and lets the terminal decide the depth.
5. `CLICOLOR=0` gives none.
6. Azure Pipelines (`TF_BUILD` and `AGENT_NAME`) gives 16, even on a pipe.
7. A stream that is not a terminal gives none, unless color was turned on above.
8. `TERM=dumb` gives none.
9. On Windows, a console stream decides: ConEmu with `ConEmuANSI=ON` gives 256, `ANSICON`
   gives 16, a console without virtual terminal processing gives none, Windows Terminal
   (`WT_SESSION`) gives truecolor, otherwise build 14931 and later give truecolor and
   10586 and later 256. A terminal that is not a console (mintty, a pty) goes on to step 10.
10. CI: GitHub Actions, Gitea Actions and CircleCI give truecolor; Travis, AppVeyor,
    GitLab, Buildkite, Drone and Codeship give 16; any other `CI` gives none. TeamCity 9.1
    and later gives 16.
11. `COLORTERM=truecolor` or `24bit`, `TERM` of kitty, Ghostty or WezTerm give truecolor;
    iTerm2 3+ gives truecolor and older iTerm2 and Apple Terminal give 256.
12. `TERM` ending in `-256` or `-256color` gives 256; the `screen`, `xterm`, `vt100`,
    `vt220`, `rxvt`, `ansi`, `cygwin` and `linux` families or a name with `color` give 16.
    The terminfo entry for `TERM` (its `colors` number) can raise this level.
13. Any other `COLORTERM` gives 16. Otherwise none.

When color was turned on in steps 1, 3 or 4, the result is never below 16.

### Where the sources disagree

- The FORCE_COLOR page lets `FORCE_COLOR` win over `NO_COLOR`; CPython and the CLICOLOR
  page let `NO_COLOR` win. `NO_COLOR` wins here, and `when="always"` is the way past it.
- CPython reads any non-empty `FORCE_COLOR`, `0` included, as "on". `supports-color` reads
  `0` and `false` as "off", and so does this library.
- `supports-color` ignores a `FORCE_COLOR` that is neither a number nor `true`/`false`;
  the FORCE_COLOR page asks for any non-empty value to turn color on, which is followed.
- `supports-color` reads the Windows build without looking at the console mode, and does
  not know ConEmu or Windows Terminal. Here the console mode is read (never changed); call
  `enable_vt` to turn virtual terminal processing on first.
- `supports-color` reads `--color` flags from the command line. A library should not parse
  its host's arguments, so that is left to `when`.

## Windows

```python
import sys

from colorsupport import enable_vt, level

enable_vt(sys.stdout)  # True when stdout is a console that now reads escape sequences
```

`enable_vt` sets `ENABLE_VIRTUAL_TERMINAL_PROCESSING` on the console behind the stream.
It returns False and does nothing for pipes, files, other terminals and other systems.

## terminfo

`terminfo_colors(term, env)` reads the `colors` number of a compiled terminfo entry
straight from the database, in the order ncurses searches it (`TERMINFO`, `~/.terminfo`,
`TERMINFO_DIRS`, then the usual system folders), in both the legacy and the 32-bit
format. It does not use `curses`, whose `setupterm` can only run once per process.

## Command line

```
$ colorsupport
truecolor: COLORTERM=truecolor
$ colorsupport --json
{"level": "truecolor", "colors": 16777216, "reason": "COLORTERM=truecolor"}
$ colorsupport --check 256 && echo "256 colors or more"
$ NO_COLOR=1 python -m colorsupport --stderr
none: NO_COLOR is set
```

`--stderr` looks at stderr instead of stdout, `--when` passes a `--color` choice, and
`--check LEVEL` prints nothing and exits 0 when the level is at least `LEVEL` (`none`,
`16`, `256` or `truecolor`), 1 otherwise.

## API

| Name | What it does |
| --- | --- |
| `detect(stream=None, *, env, when, platform, windows_build, vt, terminfo)` | The `Detection` for stream |
| `level(...)` | The `ColorLevel` only, same arguments |
| `supports_color(...)` | Whether any color can be shown, same arguments |
| `ColorLevel` | `NONE`, `BASIC`, `ANSI256`, `TRUECOLOR`; `.colors`, `.label`, `ColorLevel.parse` |
| `Detection` | Frozen `level` and `reason`; `str()` gives `"256: TERM=xterm-256color"` |
| `enable_vt(stream=None)` | Turn on escape sequence processing for a Windows console |
| `terminfo_colors(term, env=None)` | The `colors` number of a terminfo entry, or None |

## Why

Terminal programs keep rewriting the same check and getting the conventions subtly
wrong: an empty `NO_COLOR` turning color off, `FORCE_COLOR=0` turning it on, a legacy
Windows console printing raw escape codes. JavaScript has `supports-color`; Python's own
check (`_colorize`, 3.13+) is private and answers only yes or no. This library gives the
depth and the reason, follows the published conventions and writes down where they differ.

## Sources

The rules come from no-color.org, force-color.org, the CLICOLOR page, the
`supports-color` package, CPython's `_colorize`, `anstyle-query`, termstandard/colors,
the Microsoft console documentation, ConEmu's documentation and ncurses `term(5)`.
`tests/upstream/MANIFEST.json` pins each one; `python scripts/fetch_upstream.py` fetches
them so the tests can check the rules against them.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
