# colorsupport 1.0.0 certification report

Progress (2026-11-01):
- [x] Review baseline and live PyPI 0.1.0; create release/1.0.0 from d2b2ca6
- [x] Review stable API, bound errors, add runnable docstrings and strict typing
- [x] Fetch all eleven pinned sources and compare 3,000 cases with Node.js reference
- [x] Add seeded properties, adversarial inputs, README badge, GUIDE and CHANGELOG
- [x] Initial gates: format, lint, strict types, 261 tests pass (two optional skips)
- [ ] Build and inspect distributions; installed-wheel e2e and PyPI upgrade
- [ ] Run every available supported interpreter
- [ ] Complete mutation round and final gates
- [ ] Independent reviewer (item 16) and five QA lenses (item 19)
- [ ] Merge and publish (item 17)

## Scope and API

The seven 0.1.0 public names, parameter names, defaults, return types, enum values,
override precedence and CLI options remain stable. Streams are typed as object,
retaining runtime duck typing. Invalid value messages no longer repeat the value;
non-string terminfo names consistently raise TypeError; huge integers have bounded
diagnostics. All behavior changes are listed in CHANGELOG 1.0.0, dated 2026-11-01.
Detection is a heuristic, and its reason is diagnostic text, not a parsing contract.

## Ground truth

On 2026-11-01 all eleven URLs in tests/upstream/MANIFEST.json were fetched again.
Every recorded size and SHA-256 matched. Copies are kept outside the repository via
COLORSUPPORT_UPSTREAM; no third-party source is distributed. The manifest records
exact URLs, revisions, retrieval date, licences, sizes and hashes. Tests read the
fetched material and fail on a hash mismatch, or skip when it is absent.

Sources: NO_COLOR, FORCE_COLOR and CLICOLOR convention pages; supports-color;
CPython _colorize; anstyle-query; termstandard/colors; Microsoft console mode flags;
ncurses Caps, term(5) and terminfo(5). These pin switch semantics, precedence,
terminal and CI names, Windows thresholds, VT flag, numeric formats and search order.

tests/test_reference.py executes the fetched, unmodified supports-color source in
Node.js with injected Linux platform and environments. All 3,000 seeded cases in
the shared contract agree. Intentional differences (NO_COLOR, empty and forgiving
FORCE_COLOR, Windows console mode, terminfo and 24bit) are outside that comparison
and documented in README. Synthetic terminfo entries and random inputs are labelled
as such; they are not claimed as externally supplied vectors.

## Robustness and contracts

The suite pins public signatures, defaults, all seven exports, error families,
type information, frozen/hashable/picklable results, examples and CLI behavior.
tests/test_fuzz.py runs 6,000 environment cases, 10,000 binary fuzz cases and 4,000
generated 32-bit terminfo entries with fixed seeds. Adversarial shapes grow from
100,000 to 1,600,000 characters under a broad 30-second bound. Huge integer inputs
and million-character invalid values retain bounded errors and reasons.

The Windows integration test creates a hidden console screen buffer through the
Windows API and verifies real mode changes without opening named device files.

## Pending independent stages

No certification-stage independent reviewer or QA lens has run yet. Earlier
improvement-round reviews do not constitute 1.0.0 verdicts. Items 16 and 19 remain
pending. Merge and publication remain pending with the maintainer.
