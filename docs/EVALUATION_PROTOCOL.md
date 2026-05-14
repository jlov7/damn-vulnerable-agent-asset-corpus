# Evaluation Protocol

This protocol defines how scanner authors should use DVAAC results without overstating them.

## Detector Classes

DVAAC uses three detector classes:

- `static-declared`: inspects declared instruction/tool surfaces.
- `static-extended`: inspects the full checked-in asset bundle.
- `trace-aware`: inspects runtime traces, tool-call sequences, memory mutations, and side effects.

A scanner claiming a detector class must cover every fixture whose `minimum_detector_class` is that class or weaker.

## Passing A Fixture

A scanner passes a fixture when it emits the expected finding set with matching:

- finding category;
- severity;
- subject asset;
- enough evidence for a reviewer to identify the same vulnerable artifact;
- verdict semantics if the scanner emits AAC.

For clean fixtures, a scanner should not emit a vulnerability finding. Informational notes are acceptable only when they do not change the expected verdict.

## No Partial Credit

DVAAC is intentionally binary at the fixture level. Partial recognition is useful for debugging scanner behavior, but it should not be reported as fixture coverage.

## Reporting Results

Use `scorecard-template.json` and include:

- scanner name and version;
- detector class claimed;
- per-fixture pass/fail;
- emitted finding IDs/categories/severities;
- evidence references or line numbers;
- notes for misses.

## What Results Mean

DVAAC coverage means a scanner handles these concrete fixture classes. It does not prove statistical vulnerability coverage, product safety, or compliance with any law or standard.

Vendors should report DVAAC as a reproducible benchmark result, not as a certification.
