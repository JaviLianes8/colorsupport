# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
