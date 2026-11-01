# colorsupport guide

## Stable surface

Import from `colorsupport`. Its seven public names are `ColorLevel`, `Detection`,
`detect`, `level`, `supports_color`, `enable_vt` and `terminfo_colors`.
`__version__` is the release string. Private modules are implementation details.

`detect(stream=None, *, env=None, when="auto", platform=None, windows_build=None,
vt=None, terminfo=None)` returns `Detection`. `level` and `supports_color` have the
same arguments and return `ColorLevel` and `bool`, respectively. Parameter names,
defaults and keyword-only boundaries are part of the 1.x contract.

Any object is accepted as a stream. Missing, closed, non-callable or failing `isatty`
means no terminal; missing or failing `fileno` means no Windows console. `None` reads
`sys.stdout` at call time. `env` is a mapping of strings to strings and defaults to
`os.environ`. `platform` defaults to `sys.platform`. `windows_build` is an integer,
`vt` a boolean; omitted values are queried only when needed on Windows.
`terminfo` is a callback taking a terminal name and returning an integer or None.
Its exceptions propagate unchanged; it is a caller-supplied dependency, not a stream.

`ColorLevel` is an ordered `IntEnum`: NONE=0, BASIC=1, ANSI256=2, TRUECOLOR=3.
Their `.colors` values are 0, 16, 256 and 16777216; `.label` values are `none`, `16`,
`256` and `truecolor`. `ColorLevel.parse` accepts a label, member name or integer
level as text, stripping surrounding whitespace and ignoring case.
`Detection(level, reason)` is a frozen, comparable, hashable dataclass. Its typed
constructor expects a `ColorLevel` and a string, with no runtime coercion or validation.
`str(result)` joins the label and reason with `: `. Detection reasons are diagnostic
text, not a machine-readable protocol; use `.level` for decisions.

```python
from colorsupport import ColorLevel, Detection, detect

result = detect(env={"FORCE_COLOR": "2"})
assert result.level is ColorLevel.ANSI256
assert result == Detection(ColorLevel.ANSI256, "FORCE_COLOR=2 asks for 256 colors")
```

## Decisions and limits

The [README precedence list](https://github.com/JaviLianes8/colorsupport#how-the-level-is-decided)
describes the complete order. The caller's `when="never"` or `when="always"` wins
over environment switches. `NO_COLOR` wins over `FORCE_COLOR`. Numeric force values
are exact levels capped at 3; other force values enable at least basic color, except
`false` (case and surrounding whitespace ignored), which disables it.
Empty override variables count as unset; CI markers and `COLORTERM` use presence.

Detection is a heuristic: it does not send terminal queries, render colors, translate
escape sequences or inspect the host's command-line arguments. `BASIC` is the ANSI
color tier even when a terminfo entry reports eight colors. Terminfo only raises a
known name's level. The README records disagreements among the reference sources.

`enable_vt(stream=None)` returns True only when Windows console processing is enabled
already or successfully enabled by this call. Detection never changes console mode.
Non-console objects return False. This function does not restore the old mode.

`terminfo_colors(term, env=None)` returns the first readable entry's nonnegative
color count, or None for absent, cancelled, missing, unsafe or unreadable entries.
It reads at most 32769 bytes and rejects entries larger than 32768. This is a color
capability reader, not a validator for the rest of a compiled terminfo entry.
Both 16-bit and 32-bit numeric layouts are supported. Search paths follow TERMINFO,
HOME/.terminfo, TERMINFO_DIRS and system locations; Windows has no system locations
and separates TERMINFO_DIRS with semicolons. Names starting with a dot or containing
a slash, backslash, colon or NUL are refused. The database folders are trusted input.

## Errors and diagnostics

| Call | Error |
| --- | --- |
| `ColorLevel.parse` with unknown text | `ValueError`, choices listed without input |
| `ColorLevel.parse` with non-text | `TypeError`, no value echoed |
| `detect`, `level`, `supports_color` with unknown `when` | `ValueError`, choices listed |
| `terminfo_colors` with non-text name | `TypeError` |
| Caller-supplied `terminfo` callback fails | Original exception propagates |

Other argument types must match the annotations. Environment values in reasons are
ASCII escaped and truncated to 32 or 40 characters; reasons can therefore include a
prefix of TERM or FORCE_COLOR. Do not use those variables for secrets. Exception
messages from this library do not echo invalid values. Integers wider than 64 bits
are represented as `a large integer` in reasons while comparisons remain exact.

## Command line

`colorsupport` and `python -m colorsupport` share the same options. `--json` prints
`level` (label), `colors` (count), and `reason`. `--stderr` selects the inspected
stream; output still goes to stdout. `--when` accepts auto, always or never.
`--check LEVEL` prints nothing, exits 0 for a sufficient level and 1 otherwise.
Invalid usage exits 2. `--json` and `--check` are mutually exclusive.

## Upgrade from 0.1.0

Install 1.0.0 with `python -m pip install --upgrade colorsupport`. Normal detection,
constructor behavior, enum values and command-line output are unchanged. Invalid
value messages omit the input, non-string terminfo names consistently raise TypeError,
and huge numeric diagnostics are bounded. Stream annotations now use `object`.
See the [CHANGELOG](https://github.com/JaviLianes8/colorsupport/blob/main/CHANGELOG.md).

## Verification

Install `.[dev]`, then run `scripts/check.ps1`. Fetch the pinned references with
`python scripts/fetch_upstream.py`; `COLORSUPPORT_UPSTREAM` optionally selects their
local folder. The manifest records source URLs, revisions, hashes and retrieval date.
Reference tests skip if files are absent; the Node.js comparison also needs Node.js.
Set `COLORSUPPORT_E2E=1` to build and install the wheel and test the PyPI upgrade.
Use `pytest --basetemp PATH` to select a disposable test directory. Every test has a
300-second timeout. External source copies are never committed or distributed.
