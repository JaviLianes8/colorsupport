# colorsupport improvement round

Progress:
- [x] Brainstorm ranked improvements (this file)
- [x] Pin the ground truth: manifest, fetch script, tests that read the pinned sources
- [x] Conventions: NO_COLOR, FORCE_COLOR, CLICOLOR, CLICOLOR_FORCE with documented precedence
- [x] Terminal rules: COLORTERM, TERM, TERM_PROGRAM, CI providers, terminfo fallback
- [x] Windows: console VT mode, Windows Terminal, ConEmu, ANSICON, build number levels
- [x] Explained result: `Detection(level, reason)`, `when=` override for `--color=WHEN`
- [x] Typed API and contracts: contract test, typing test, README examples executed
- [x] Command line: `colorsupport` and `python -m colorsupport`
- [x] Docs and packaging: README, CHANGELOG, metadata, sdist contents, installed-wheel e2e
- [x] Gates: ruff format, ruff check, mypy --strict, pytest
- [x] Mutation run: removing guarded logic makes the suite fail
- [x] Independent review findings fixed with regression tests
- [ ] Pull request opened, guard clean

## Starting point

The unreleased `0.1.0` branch gives `ColorLevel`, `level(stream, env)` and
`supports_color(stream, env)`. Compared with the sources below:

- `NO_COLOR=""` turns color off. The NO_COLOR page says the variable counts only when it is
  present and not empty, and the CLICOLOR page says empty variables are treated as unset.
- `FORCE_COLOR=""` forces basic color; the FORCE_COLOR page also asks for a non-empty value.
  `FORCE_COLOR=yes` forces basic, `FORCE_COLOR=7` forces basic instead of the capped
  truecolor `supports-color` gives, and `FORCE_COLOR=true` pins basic instead of only
  enabling color and letting the terminal decide the depth.
- `CLICOLOR` and `CLICOLOR_FORCE` are ignored.
- `TERM` containing `256` anywhere means 256 colors; `TERM=xterm-kitty`, `wezterm`,
  `xterm-ghostty`, iTerm2 and Apple Terminal are not recognised; an unknown or missing
  `TERM` on a terminal still gives basic color.
- No CI provider is recognised. (Piped CI output still needs forcing, as in supports-color;
  the provider rules apply when the CI runner gives the program a terminal.)
- Windows is not handled: a legacy console without virtual terminal processing is reported
  as able to show color, and Windows Terminal and ConEmu are not recognised.
- The result is a bare level. There is no way to learn why, which is what a user filing
  "why no colors?" needs, and no hook for a program's own `--color=always|never|auto`.
- Defaults are bound at import (`stream=sys.stdout`), so a redirected `sys.stdout` is missed.

## Sources (fetched 2026-10-14)

Copies are kept in the ignored `tests/upstream/` folder, recorded in
`tests/upstream/MANIFEST.json` (URL, revision, size, sha256, licence) and fetched by
`scripts/fetch_upstream.py`. None of them is committed or shipped.

- NO_COLOR, jcs/no_color `index.md` at cd23335831f927018abdbba8ea5eb0d3e54f9210.
- FORCE_COLOR, donatj/force-color.org `index.md` at 08df127f8d94e6e699915d5f96d7332ab4feb8be.
- CLICOLOR and CLICOLOR_FORCE, jhasse/clicolors `index.md` at
  f717f230ba595c2310683c59c8eaf0d71438c2b1 (the page now marks itself deprecated in favour
  of the two above and asks for FORCE_COLOR to be read as an alias of CLICOLOR_FORCE).
- chalk/supports-color `index.js` at 4963567f020de0f4cb15ebdfd3c6f5b7d13d54bf: the
  reference for TERM, COLORTERM, TERM_PROGRAM, CI and Windows build rules.
- CPython `Lib/_colorize.py` at fe7735f03ecd720e717daf221511f74c23cd90dc: `can_colorize`
  (NO_COLOR before FORCE_COLOR, `TERM=dumb`, the Windows VT check, then isatty).
- rust-cli/anstyle `crates/anstyle-query/src/lib.rs` at
  d891cdae9f5d9e923232bb42cecc597be09afe7a: `CLICOLOR=0` is off, COLORTERM `truecolor` or
  `24bit`, `CI` by presence.
- termstandard/colors `README.md` at caf0bb949ad64307d938a055f7fbec76ce65d91e: COLORTERM
  `truecolor` or `24bit` as the truecolor signal.
- MicrosoftDocs/Console-Docs `docs/includes/console-mode-flags.md` at
  50eb4826f13887a146bb0f947cf46b39b5344f77: `ENABLE_VIRTUAL_TERMINAL_PROCESSING` is `0x0004`.
- ncurses `man/term.5`, `man/terminfo.tail` and `include/Caps` at
  6c26c1f46499e2fbedfb2c69c9463eceeab62ca5 (ThomasDickey/ncurses-snapshots): the compiled
  entry layout, the two magic numbers, `max_colors` as the 14th number, the search order.
- ConEmu, https://conemu.github.io/en/AnsiEscapeCodes.html (read, not pinned): `ConEmuANSI`
  is `ON` or `OFF`; 256 colors with ANSI processing, 24-bit only with an extra setting.

The sources disagree in places, and each choice is written down in the README:

- NO_COLOR against FORCE_COLOR: the FORCE_COLOR example lets FORCE_COLOR win, CPython and
  the CLICOLOR page let NO_COLOR win. NO_COLOR wins here; a program's own `--color=always`
  (`when="always"`) is the documented way past it, as the NO_COLOR page asks.
- `FORCE_COLOR=0`: CPython treats any non-empty value as "on", `supports-color` reads `0`
  and `false` as "off". The latter is followed, since Node and most tools agree with it.

## Ranked improvements

1. **Conventions done right.** Empty means unset for every variable. NO_COLOR first, then
   FORCE_COLOR (`0`/`false` off, `1` to `3` exact, larger numbers capped at truecolor, other
   values on with the depth detected), then CLICOLOR_FORCE (on, depth detected), then
   `CLICOLOR=0` (off). Forced color never drops below basic, even on a pipe.
2. **Terminal rules from supports-color.** `TERM=dumb`, CI providers (GitHub Actions,
   Gitea, CircleCI truecolor; Travis, AppVeyor, GitLab, Buildkite, Drone, Codeship basic;
   Azure Pipelines even when piped; TeamCity 9.1+), COLORTERM `truecolor`/`24bit`, kitty,
   Ghostty, WezTerm, iTerm2, Apple Terminal, `-256color` and the basic TERM families.
3. **Windows.** On `win32` a console handle must have `ENABLE_VIRTUAL_TERMINAL_PROCESSING`
   (read with `GetConsoleMode`, never changed by detection); then Windows Terminal is
   truecolor, ConEmu with ANSI on is 256, ANSICON is basic, and otherwise the build number
   decides (10586 for 256, 14931 for truecolor). `enable_vt(stream)` turns the mode on
   explicitly. A TTY that is not a console (mintty, a pty) falls through to the TERM rules.
4. **Explained result.** `detect()` returns `Detection(level, reason)`, the reason a short
   sentence naming the deciding variable. `ColorLevel` gains `colors` (0, 16, 256,
   16777216) and a label. `when="always"|"never"|"auto"` maps a program's own flag.
5. **Injectable everything.** `stream`, `env`, `platform`, `windows_build`, `vt` and
   `terminfo` are keyword arguments, resolved at call time, so tests are deterministic and
   `sys.stdout` replacements are honoured. Detection never raises on a broken stream.
6. **terminfo fallback.** An unknown TERM asks terminfo for `colors` (curses, POSIX only,
   injectable), so a `TERM=foot` or a custom entry gets its real depth.
7. **Typed API, runnable docs.** `py.typed`, `mypy --strict` over a usage snippet, README
   examples executed by the tests, API table checked against `__all__`.
8. **Command line.** `colorsupport` prints the level and reason for stdout (or `--stderr`),
   `--json` for tools, `--check LEVEL` as an exit code for shell scripts.
9. **Packaging.** Classifiers, keywords, console script, sdist without planning notes or
   third-party files, installed-wheel end-to-end test.

## Out of scope

- Reading `sys.argv` for `--color` flags as `supports-color` does: a library should not
  parse its host's command line; `when=` takes the program's own decision.
- `PYTHON_COLORS`: it controls the interpreter's own output only.
- Querying the terminal with escape sequences (needs raw mode and a reply, not deterministic).
- Translating ANSI into Win32 console calls for consoles older than Windows 10 (colorama's
  job); such consoles are reported as having no color.

## Verification

- Gates on a fresh clone on a second Windows machine (CPython 3.14.2): `ruff format --check .`,
  `ruff check .`, `mypy --strict src` and `pytest`, first without the pinned sources (their
  tests skip) and again after `scripts/fetch_upstream.py`. Locally (CPython 3.13.2) the same
  gates plus `mypy --strict src tests` and `mypy --strict --platform linux src`.
- With `COLORSUPPORT_E2E=1` the installed-wheel test builds the wheel and sdist, checks their
  contents (no plan, no third-party files, manifest and fetch script kept), installs the wheel
  in a fresh venv and drives the API, the `colorsupport` script and `python -m colorsupport`.
- A real Windows console is created hidden for one test: its mode is read, `enable_vt` turns
  processing on and the level follows.
- terminfo against a real database (WSL Ubuntu): `xterm-256color` reads 256, `xterm` 8, and a
  FIFO in the database returns at once.
- Mutation runs (one change at a time, no bytecode, `__pycache__` purged, 240 s per mutant,
  suite green before and after). First run, 88 mutants: 12 alive, killed by tests for `CI` by
  presence, `CI_NAME`, TeamCity anchoring, TERM case, the reason length cap, negative and
  short terminfo sections, the dot and separator name guards; the `enable_vt` re-read was
  dropped as redundant. After the review, 96 mutants: 4 alive. Equivalent: the forced floor
  (always 16 when not exact), the regular-file check and the empty `TERMINFO_DIRS` entry on
  Windows (no FIFOs, no system folders; both are covered on POSIX). The fd leak survivor is now
  killed by a test that deletes the entry after reading it.
- The review regression tests were run against the code before the fixes: 12 fail there (the
  FIFO test skips on Windows and was checked in WSL).

## Review fixes

An independent review attacked the branch; every finding below is fixed with a test that
fails without the fix:

- A FIFO (or a device) in the terminfo database blocked the lookup forever. Entries are now
  opened non-blocking and read only when they are regular files; handles are always closed.
- On Windows a drive-relative TERM (`C:x`) could leave the database folder, `TERMINFO_DIRS`
  was split on colons and the POSIX system folders were searched. Colons are refused,
  `os.pathsep` splits, and Windows searches only the folders the environment names.
- Reasons could hold characters the console cannot encode, crashing the command line; they
  are now ASCII. `FORCE_COLOR` reasons show the value the user set, cut to 40 characters.
- Streams whose `isatty` or `fileno` misbehave in other ways (any exception, a non-callable,
  an out-of-range descriptor) no longer raise.
- ConEmu and ANSICON were trusted for streams that are not consoles (the NUL device answers
  `isatty` with True). The console check now comes first.
- Docs: which variables treat an empty value as unset, the FORCE_COLOR page's own "any
  value" rule, `FORCE_COLOR` read before `CLICOLOR_FORCE`, the forgiving spaces and case,
  mintty under native Windows Python, and the terminfo(5) search order (now pinned and tested).
- Also adopted: a private `kernel32` handle with explicit prototypes.
