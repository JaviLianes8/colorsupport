# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-11-01

- Stabilize the seven public names, detection precedence, level labels and CLI options
  from 0.1.0. Python 3.10 through 3.14; no runtime dependencies.
- Type stream arguments as `object` instead of `Any`, retaining arbitrary stream support.
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
