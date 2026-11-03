# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-11-01

- Stabilize the seven public names, detection precedence, level labels and CLI options
  from 0.1.0. Python 3.10 through 3.14; no runtime dependencies.
- Type stream arguments as `object` instead of `Any`, retaining arbitrary stream support.
- Windows native console detection now requires both processed output and virtual
  terminal processing. `enable_vt` enables both while preserving all existing mode flags,
  so consoles with processed output disabled no longer report success with literal escapes.
- Invalid `ColorLevel(value)` construction raises `ValueError` with a bounded, redacted
  message, including secret-like text and huge integers; valid enum construction is unchanged.
- Reject unknown constructor values before enum fallback formatting, without calling their
  `repr` or `str`, including hostile subclasses and integers beyond the text conversion limit.
  Failed value comparisons also produce a redacted `ValueError` without exposing the
  comparison error in exception chains.
- Invalid `when` and unknown color-level messages no longer repeat the supplied value;
  non-string level type names are limited to 40 characters.
- Invalid command-line usage prints bounded option guidance without repeating arguments;
  its exit code remains 2.
- `terminfo_colors` now consistently raises `TypeError` for non-string names, including
  falsey objects that previously returned None and integers that raised AttributeError.
- Build numbers and injected terminfo counts wider than 64 bits are described as
  `a large integer` in reasons, avoiding huge messages and integer conversion failures.
- Add runnable public docstrings, the API guide, seeded robustness tests, reference
  implementation comparisons, installed-wheel upgrade tests and release contracts.
- Extend constructor contracts for negative and fractional numbers, non-real complex
  values, truthy integer-subclass equality and comparison exception redaction.
  Constructor behavior and the public API are unchanged.
- Extend constructor contracts for exact Decimal/Fraction precision, non-unit truthy
  equality results, numeric text rejection, custom comparison errors and failures
  during equality-result truth conversion. Production behavior remains unchanged.
- Cover negative truthy equality results, binary numeric text rejection and None
  rejection in constructor contracts. Production behavior and the public API are unchanged.
- The command prints plain usage, help and error text on every Python version; on 3.14
  argparse would otherwise color them by the state of stdout, even when stderr is piped.
- Pin the caller-value boundary of every public parameter with one poisoned-subclass
  table, the command line with table-driven spellings (whitespace, CRLF, repeats,
  prefixes, escapes) and the exact plain and JSON output.
- Read every caller-supplied value once, through its base type, before any rule looks at
  it, so no method of the caller's object runs and nothing it could raise or claim escapes:
  - `ColorLevel(value)` accepts an int, bool, float, complex with a zero imaginary part,
    Decimal or Fraction (or a subclass of one) whose exact value is 0 to 3. Other objects
    that merely compare equal to a level (custom `__eq__`, `__index__` or numeric types
    outside the standard library) now raise the same redacted `ValueError`.
  - A str subclass passed as `when`, `platform`, an environment value, a terminfo name or
    `ColorLevel.parse` text is read as its exact str value. Detection copies the variables
    it reads once at the start; a value that is not a str counts as empty.
  - `vt`, `windows_build` and the count returned by a `terminfo` callback are read as
    exact integers (bool and int subclasses included); other types raise `TypeError`
    instead of failing later with an unrelated error.

## [0.1.0]

First release.

- `detect(stream, ...)` returns a `Detection`: a `ColorLevel` (none, 16, 256, truecolor)
  and a one-sentence reason naming the variable or check that decided it.
- `level(...)` and `supports_color(...)` return the level or whether any color is shown.
- Follows `NO_COLOR`, `FORCE_COLOR` (`0`/`false` off, `1` to `3` exact, other values on),
  `CLICOLOR_FORCE` and `CLICOLOR=0`, treating empty values as unset; `when="always"`,
  `"never"` or `"auto"` carries a program's own `--color` flag.
- Reads `TERM`, `COLORTERM`, `TERM_PROGRAM` (iTerm2, Apple Terminal), kitty, Ghostty,
  WezTerm, CI services (GitHub Actions, Gitea, CircleCI, Travis, AppVeyor, GitLab,
  Buildkite, Drone, Codeship, Azure Pipelines, TeamCity) and the terminfo `colors` number.
- On Windows, reads the console's virtual terminal processing mode, Windows Terminal,
  ConEmu, ANSICON and the build number; `enable_vt(stream)` turns the mode on.
- `terminfo_colors(term, env)` reads compiled terminfo entries (legacy and 32-bit) without
  curses.
- Every input (stream, environment, platform, Windows build, console mode, terminfo) can
  be injected; defaults are read when the function is called.
- `colorsupport` and `python -m colorsupport` print the level and reason, `--json`, or
  check a minimum level with `--check`.
