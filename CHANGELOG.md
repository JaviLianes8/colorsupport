# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0]

- First release.
- `level(stream, env)` returns a `ColorLevel` of none, basic, 256 or truecolor.
- `supports_color(stream, env)` returns whether any color is available.
- Honors the `NO_COLOR` and `FORCE_COLOR` conventions and reads `COLORTERM` and
  `TERM`, with the stream and environment injectable for deterministic detection.
