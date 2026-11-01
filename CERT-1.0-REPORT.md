# colorsupport 1.0.0 certification report

Progress (2026-11-01):
- [x] Review baseline and live PyPI 0.1.0; create release/1.0.0 from d2b2ca6
- [x] Review stable API, bound errors, add runnable docstrings and strict typing
- [x] Fetch all eleven pinned sources and compare 3,000 cases with Node.js reference
- [x] Add seeded properties, adversarial inputs, README badge, GUIDE and CHANGELOG
- [x] Initial gates: format, lint, strict types, 261 tests pass (two optional skips)
- [x] Build and inspect distributions; installed-wheel e2e and PyPI upgrade
- [x] Run the installed-wheel suite on all twelve available supported Python builds
- [x] Complete 19-mutation round; gates and installed-wheel e2e pass
- [x] Address all 13 QA round 1 findings; six additional mutations killed
- [x] Address all five QA round 2 findings; three reported mutations and a context variant killed
- [x] Address all four QA round 3 findings; all four reported constructor mutations killed
- [x] Address all five QA round 4 findings; all five reported constructor mutations killed
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

## QA round 1 (2026-11-01)

Reviewed baseline: `463831bcf4c05d55c07d548c43c64ef77aacb985`.
Fix commit: `fix certification QA round one findings`, the commit containing this
section, directly following that baseline. All 13 supplied findings are addressed.
Independent re-verification and the final item 16/19 verdicts remain pending.
Merge and publication remain pending with the maintainer.

| Finding | Change and verification |
| --- | --- |
| A-001 | GUIDE explains that terminfo also establishes unknown names' levels; custom-terminal with 256 colors executed successfully. |
| A-002 | README distinguishes the eleven pinned files from unpinned ConEmu background documentation; all eleven fetched and verified. |
| A-003, B-02 | README explicitly records both CLICOLOR deviations; existing 0.1.0 behavior is retained. Executed reference gives True for 0 and 1 on a terminal, library gives False. |
| B-01 | Detection requires both output-processing flags; enable_vt sets both. Private-console rendering covers modes 0, 1, 3, 4, 5 and 7 and consumes escape sequences. |
| B-03 | README distinguishes v10.2.2's parseInt behavior from pinned revision 4963567. Executing both gives level 2 and none respectively for spaced FORCE_COLOR. |
| C-001 | ColorLevel constructor errors omit invalid values. Secret-like text, million-character text and a 4001-digit integer have bounded ValueError messages; valid members remain unchanged. |
| E01 / M27 | Full console modes and repeated calls are asserted by test_real_console_requires_both_flags_and_preserves_modes; flag-dropping mutation killed. |
| E02 / M32 | test_enable_vt_defaults_to_current_stdout checks distinct current stdout, stderr and explicit streams; wrong-default mutation killed. |
| E03 / M37 | test_zero_colors_is_distinct_from_missing checks 0, absent and cancelled public lookup results; zero-dropping mutation killed. |
| E04 / M38 | test_entry_size_limit_is_inclusive checks 32767, 32768 and 32769 bytes; boundary mutation killed. |
| E05 / M41 | A readable colon target and an open spy prove unsafe names are rejected before opening; colon-removal mutation killed. |
| E06 / M46 | test_module_check_preserves_exit_status exercises both module subprocess exit statuses with empty output; exit-dropping mutation killed. |

Behavior tests were added before production edits: the focused baseline run had
4 failures (three constructor diagnostics and Windows processing), then 58 passed
after the fixes. Both behavior changes are recorded in CHANGELOG. Coverage findings
needed no production changes; all six injected defects fail the new contracts in
isolated copies. M27 uses the updated two-flag mask for the same flag-dropping defect.

Validation: ruff format --check ., ruff check ., mypy --strict src and additionally
mypy --strict src tests all exit 0. Full pytest with freshly fetched references and
COLORSUPPORT_E2E=1: **287 passed, 1 skipped** (POSIX FIFO on Windows), including fresh
wheel installation, actual PyPI 0.1.0 upgrade, examples and Node.js comparisons.
Per-test timeout: 300 seconds. Evidence is retained under
`C:/lianes8-build/codex-pylib/scratch/colorsupport-cert/fix-r1/`: red.log, full.log,
full.xml, mutations.json, M27/M32/M37/M38/M41/M46.log and executable doc_checks.py.

### Disputed findings

None.

## QA round 2 (2026-11-01)

Reviewed baseline: `166ea8defed6a0a126af41709865b1c3c8a26064`.
Fix commit: `fix certification QA round two findings`, the commit containing this
section, directly following that baseline. All five supplied findings are addressed.
Independent re-verification and the final item 16/19 verdicts remain pending.

| Finding | Change and verification |
| --- | --- |
| A-004 | README distinguishes upstream's forced minimum from this library's exact level. Freshly fetched supports-color v10.2.2 returns 3 on native Windows with spaced FORCE_COLOR=2 and a pipe; colorsupport returns 2. |
| C-002 | Constructor value lookup bypasses Enum's fallback formatting. Hostile string/integer representations are never called; a 10001-digit integer receives the bounded ValueError. Member identity, bool, float, complex, Decimal and Fraction construction remain valid. |
| E07 / N14 | test_failed_mode_update_returns_false asserts False after a zero SetConsoleMode result and checks the requested mode; the reported mutation fails. |
| E08 / N15 | Stub and private-console contracts preserve output flags 0x0008 and 0x0010 separately and combined. The reported truncation mutation fails both contracts. |
| E09 / N20 | test_constructor_exception_chain_is_redacted checks formatted tracebacks and cause/context messages. The reported cause mutation and an unsuppressed-context variant both fail. |

Constructor contracts preceded the production fix: the focused baseline had three
failures and 15 passes. The final constructor tests against an isolated baseline copy
have four failures and nine passes, including the added hostile-comparison case.
Rejected values now raise a constant ValueError before enum fallback formatting;
comparison failures cannot expose their messages through an exception chain.
CHANGELOG records these behavior changes. Windows production behavior is unchanged;
E07, E08 and E09 close test gaps in already-correct behavior.

| Mutation | Catching contract |
| --- | --- |
| N14: ignore failed console write | test_failed_mode_update_returns_false |
| N15: truncate existing mode to three bits | test_enabling_preserves_extended_output_flags; test_real_console_requires_both_flags_and_preserves_modes |
| N20: expose rejected value through cause | test_constructor_exception_chain_is_redacted |
| N20 context variant: expose value through context | test_constructor_exception_chain_is_redacted |

Validation: ruff format --check ., ruff check ., mypy --strict src and additionally
mypy --strict src tests exit 0.
Full pytest with all eleven freshly fetched references and COLORSUPPORT_E2E=1:
**304 passed, 1 skipped** (POSIX FIFO on Windows), including fresh installation,
PyPI 0.1.0 upgrade, real Windows console checks and Node.js comparisons.
Per-test timeout: 300 seconds. Evidence is retained under
`C:/lianes8-build/codex-pylib/scratch/colorsupport-cert/fix-r2/`: red-clean.log,
baseline-final.log, full.log, full.xml, mutations.json, N14/N15/N20/N20-context.log,
doc_check.py and reference-manifest.json.

### Disputed findings

None.

## QA round 3 (2026-11-01)

Reviewed baseline: `e54a6bc6c394e735e671a0acf8cbb509aeff8a8c`.
Fix commit: `close constructor contract gaps for certification round three`, the
commit containing this section, directly following that baseline. All four supplied
findings are addressed. Independent re-verification and final verdicts remain pending.

| Finding | Change and verification |
| --- | --- |
| E10 / R09 | Reject negative integers, negative floats and non-real complex values with magnitudes matching valid levels. test_constructor_rejects_negative_and_nonreal_numbers catches all nine cases. |
| E11 / R10 | Reject fractional floats that round to each of the four valid levels. test_constructor_rejects_fractional_numbers catches all four cases. |
| E12 / R12 | Accept integer subclasses whose equality returns integer 0 or 1. test_constructor_accepts_truthy_integer_equality checks all four enum singletons and catches all four cases. |
| E13 / R13 | Require a constant ValueError with no cause or context for RuntimeError, ValueError, TypeError, AssertionError and OverflowError comparisons, both direct and chained. test_constructor_redacts_comparison_errors catches eight cases under the reported mutation. |

These are missing-contract findings: production code already satisfies the promises.
No production behavior or public API changes were necessary. CHANGELOG records the
expanded coverage. The constructor suite passes all 40 cases on unchanged production
code. Each exact reported mutation passes all 13 original constructor cases in an
isolated scratch copy, then fails with the new tests: R09 has 9 failures, R10 has 4,
R12 has 4 and R13 has 8. No production file was mutated in the working repository.

Validation: ruff format --check ., ruff check ., mypy --strict src and additionally
mypy --strict src tests exit 0. Full pytest with all eleven freshly fetched references
and COLORSUPPORT_E2E=1: **331 passed, 1 skipped** (POSIX FIFO on Windows), including
fresh installation, PyPI 0.1.0 upgrade, real Windows console checks and Node.js
comparisons. Per-test timeout: 300 seconds. Evidence is retained under
`C:/lianes8-build/codex-pylib/scratch/colorsupport-cert/fix-r3/`: check_mutations.py,
mutations.json, R09/R10/R12/R13-before/after.log and .xml, full.log and full.xml.

### Disputed findings

None.

## QA round 4 (2026-11-01)

Reviewed baseline: `d236633c7d46356e6df3805f183c4bda7e4243ca`.
Fix commit: `close constructor contract gaps for certification round four`, the
commit containing this section, directly following that baseline. All five supplied
findings are addressed. Independent re-verification and final verdicts remain pending.

| Finding | Change and verification |
| --- | --- |
| E14 / S01 | test_constructor_rejects_exact_fractions_that_round_to_levels rejects nonintegral Decimal and Fraction values whose float conversion equals each valid level, including underflow to zero. The exact mutation fails eight cases. |
| E15 / S04 | test_constructor_accepts_nonunit_truthy_equality checks an unhashable integer subclass returning 2 for equality and 0 otherwise; all four enum singleton identities are preserved. The exact mutation fails four cases. |
| E16 / S05 | test_constructor_rejects_numeric_text_accepted_by_parse rejects strings 0 through 3 in the constructor and confirms that parse accepts them. The exact mutation fails four cases. |
| E17 / S06 | test_constructor_redacts_equality_and_truth_conversion_errors adds LookupError and a custom Exception subclass, directly raised and chained. It asserts the exact constant ValueError, absent cause/context and bounded, redacted traceback. The exact mutation fails eight cases. |
| E18 / S10 | The same contract exercises equality results whose __bool__ raises RuntimeError, LookupError or a custom exception, directly or with a cause. The exact mutation fails six cases. |

These are missing-contract findings: unchanged production code passes all 68
constructor cases, including 28 new cases. No production behavior or public API
change was necessary. CHANGELOG records the expanded coverage. Each exact reported
mutation passes all 40 earlier constructor cases in an isolated scratch copy, then
fails with the new contracts. Failures are behavioral assertions with no collection
errors. No production file was mutated in the working repository.

Validation: ruff format --check ., ruff check ., mypy --strict src and additionally
mypy --strict src tests exit 0. Full pytest with all eleven freshly fetched references
and COLORSUPPORT_E2E=1: **359 passed, 1 skipped** (POSIX FIFO on Windows), including
fresh installation, PyPI 0.1.0 upgrade, real Windows console checks and Node.js
comparisons. Per-test timeout: 300 seconds. Evidence is retained under
`C:/lianes8-build/codex-pylib/scratch/colorsupport-cert/fix-r4/`: check_mutations.py,
mutations.json, S01/S04/S05/S06/S10-before/after.log and .xml, full.log and full.xml.

### Disputed findings

None.

## Packaging and upgrade (items 8, 11 to 14)

The live endpoint https://pypi.org/pypi/colorsupport/json reported 0.1.0 on
2026-11-01. Two isolated e2e runs build wheel and sdist: a fresh installation and
an in-place upgrade of the actual PyPI 0.1.0. Consumers run from an empty folder
with isolated imports, exercise all public names and both CLI entry points, and
check JSON, stderr selection, forced color, threshold exits and invalid usage.
Across 2,000 seeded environments, normal detection results, reasons and wrappers
match the installed 0.1.0 exactly. Its pickled Detection loads after upgrading.
Each changed error behavior and huge-number diagnostic is checked before and after;
pip check passes after the upgrade. Public stream annotation changes are checked too.

The wheel contains only the package, py.typed and distribution metadata with LICENSE.
The sdist contains source, tests, docs, scripts and the reference manifest, without
fetched source copies, caches, scratch files or certification/improvement reports.
Both distributions pass twine check --strict. Metadata is 1.0.0, Production/Stable,
Python >=3.10, classifiers through 3.14, MIT, project URLs and no runtime dependencies.
README uses absolute links, has the certification badge, install and usage examples,
the problem and a comparison with supports-color and CPython's private check.

## Mutation round (item 18)

Each mutation was applied alone in a separate scratch copy. The contract suite ran
with -x and a 300-second per-test timeout. All 19 were killed by assertions; setup
errors during the first attempts at 11 to 15 were not counted, and those cases were
rerun after creating the test scratch parent. No survivor remains.

| # | Deliberate bug | Test that caught it |
| --- | --- | --- |
| 1 | ANSI256 reports 255 colors | test_every_public_docstring_has_a_passing_example |
| 2 | parse stops stripping whitespace | test_every_public_docstring_has_a_passing_example |
| 3 | Detection becomes mutable | test_values_are_hashable_and_pickle_round_trip |
| 4 | Ignore NO_COLOR | test_no_color_turns_color_off_on_a_truecolor_terminal |
| 5 | Cap FORCE_COLOR at 2 | test_json_output |
| 6 | CLICOLOR=1 disables instead of 0 | test_clicolor_zero_turns_color_off_unless_forced |
| 7 | Invert the pipe check | test_huge_integers_keep_exact_comparisons_and_bounded_reasons |
| 8 | supports_color accepts NONE | test_every_public_docstring_has_a_passing_example |
| 9 | level always returns BASIC | test_every_public_docstring_has_a_passing_example |
| 10 | Lower the forced minimum with min | test_huge_integers_keep_exact_comparisons_and_bounded_reasons |
| 11 | Read legacy numbers big-endian | test_reads_colors_from_the_legacy_format |
| 12 | Read capability 12 instead of 13 | test_terminfo_defaults_to_the_database_named_by_env |
| 13 | Accept a 40 KB terminfo file | test_an_oversized_file_is_not_read |
| 14 | Raise Windows truecolor threshold to 14932 | test_supports_color_windows_builds_match |
| 15 | Test VT mode with OR instead of AND | test_a_real_console_is_read_and_switched |
| 16 | Wrong error type for a non-text terminal name | test_non_string_terminfo_names_raise_type_error |
| 17 | Echo invalid parse input | test_errors_do_not_echo_invalid_values |
| 18 | Remove the integer diagnostic bound | test_huge_integers_keep_exact_comparisons_and_bounded_reasons |
| 19 | Restore argument-echoing CLI diagnostics | test_invalid_arguments_are_not_echoed |

## Gates (item 15)

Each command exits zero independently: ruff format --check ., ruff check .,
mypy --strict src, mypy --strict src tests and pytest. The latest QA round 4 run with
COLORSUPPORT_E2E=1 and fetched sources has 359 passed, one skipped (POSIX FIFO on
Windows). The initial default suite had 264 passed, three skipped (the two opt-in e2e cases
and POSIX FIFO). Every public docstring example and every README/GUIDE Python
example executes in the suite. All tests use a 300-second timeout.

## Interpreter matrix (item 10)

During initial preparation, every distinct working CPython build found on this machine ran the sdist's tests
against the installed wheel, with the source package excluded from the extracted
sdist so it could not shadow the install. Each result is 264 passed, three skipped
(the two opt-in wheel-building cases and POSIX FIFO). The wheel's CLI and real
Windows console test run in this suite, as does the Node.js reference comparison.

| Python | Build | Result |
| --- | --- | --- |
| 3.10.11 | Embedded | PASS |
| 3.10.22 | Standalone | PASS |
| 3.11.9 | Embedded | PASS |
| 3.11.11 | Blender-bundled CPython | PASS |
| 3.11.18 | Standalone | PASS |
| 3.12.10 | Embedded | PASS |
| 3.12.16 | Standalone | PASS |
| 3.13.2 | Embedded | PASS |
| 3.13.18 | Standalone | PASS |
| 3.14.6 | System installation | PASS |
| 3.14.10 | Standalone | PASS |
| 3.14.10t | Free-threaded | PASS |

Embedded builds were copied into scratch and configured to find their local standard
library and installed test dependencies. Existing interpreters were not modified.
The 3.10 embedded path order was adjusted for mypy's discovery subprocess. Tests now
use inspect.get_annotations to avoid Python 3.10's implicit Optional conversion,
discover the installed wheel through mypy's --python-executable option, and import
venv only inside the opt-in e2e test. All supported minor versions were exercised.
Stale launcher entries pointing at removed interpreter folders were not runnable.

## Preparation scorecard

| Items | Result | Evidence |
| --- | --- | --- |
| 1, 2 | PASS | Seven stable exports, signatures/defaults pinned in contract tests |
| 3 | PASS | Runnable public docstrings and README/GUIDE examples |
| 4 | PASS | Strict typing for src and tests, installed consumers, py.typed |
| 5 | PASS | Documented builtin error types, bounded API and CLI diagnostics |
| 6 | PASS | Contract, boundary, callback, Windows, terminfo and CLI tests |
| 7 | PASS | Eleven live-fetched sources and 3,000 live reference comparisons |
| 8 | PASS | Fresh wheel installation and actual PyPI 0.1.0 upgrade |
| 9 | PASS | Fixed seeds, malformed binaries, huge inputs and diagnostic bounds |
| 10 | PASS | Twelve working Python builds, all supported minor versions |
| 11, 12 | PASS | README badge/links, GUIDE, dated CHANGELOG and twine checks |
| 13, 14 | PASS | Stable metadata, no runtime dependencies, archives inspected |
| 15 | PASS | Four gates exit zero independently; 359 tests with e2e enabled in QA round 4 |
| 16 | Pending | Independent reviewer |
| 17 | Pending | Merge and publication |
| 18 | PASS | All 19 deliberate mutations killed |
| 19 | Pending | Five independent QA lenses |
