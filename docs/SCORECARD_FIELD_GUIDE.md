# Scorecard Field Guide

This guide defines how to fill `scorecard-template.json` for a scanner result submission. It is intentionally strict because accepted scorecards become public evidence in `docs/VALIDATION_LEDGER.md`.

Validation proves structure and internal consistency. It does not prove that a scanner's evidence is semantically correct; maintainers and reviewers still inspect the submitted evidence.

For an end-to-end scanner-author workflow, see [Scanner Integration Guide](SCANNER_INTEGRATION_GUIDE.md).

## Validate Before Submitting

From a current `main` checkout of this repository, after installing the runner dependencies:

```bash
uv venv
source .venv/bin/activate
uv pip install -r runner/requirements.txt
```

Then run:

```bash
make validate-scorecard SCORECARD=path/to/scorecard.json
```

Equivalent direct command, including from an immutable `v0.1.4` release checkout:

```bash
python runner/validate_scorecard.py path/to/scorecard.json
```

Expected output for a structurally valid submission:

```text
DVAAC scorecard: valid submission.
```

## Top-Level Fields

| Field | Required value | Notes |
|---|---|---|
| `corpus_id` | `dvaac` | Must not be changed. |
| `corpus_version` | `0.1.4` | Must match the release under review. |
| `scanner.name` | scanner or tool name | Use a real public name for public submissions. |
| `scanner.version` | release version or commit | Prefer a release tag plus commit if available. |
| `scanner.vendor_or_project` | vendor, project, or individual | Use the entity responsible for the scanner result. |
| `scanner.source_url_or_commit` | public source URL, release URL, or commit | Identifies the scanner build reviewers should inspect or rerun. |
| `scanner.run_at` | UTC timestamp, second precision | Format: `YYYY-MM-DDTHH:MM:SSZ`. |
| `run_context.command` | exact scanner command | Include arguments needed to reproduce the run. |
| `run_context.environment` | operating system and runtime | Include language/runtime versions when they affect scanner behavior. |
| `run_context.configuration` | ruleset or config summary | Use `default configuration` only when that is literally what was run. |
| `run_context.public_artifact_url` | public artifact URL, or empty if pasted inline | Link logs, scorecard artifacts, or CI output when available. |
| `run_context.evidence_publicly_reproducible` | `true` for ledger candidates | Set `false` only for informal/private dry runs that should not enter the validation ledger. |
| `detector_class_claimed` | `static-declared`, `static-extended`, or `trace-aware` | Claim only the strongest detector class the scorecard fully covers. |

## Detector Class Rule

If a scorecard claims a detector class, every fixture at that class or weaker must pass. The validator enforces this against `corpus.manifest.json` and requires the claimed class to be the strongest detector class fully covered by the submitted per-fixture results.

Use the strongest fully covered claim:

- `static-declared`: scanner uses declared fixture metadata and source artifacts.
- `static-extended`: scanner reasons across files or non-declared local artifacts.
- `trace-aware`: scanner uses runtime trace evidence.

If your scanner is partial, do not inflate the detector class. If no detector class fits, open a corpus critique issue instead of submitting a validation-ledger scorecard.

## Summary Fields

`summary.fixtures_total` must equal the number of fixtures in `corpus.manifest.json`.

`summary.fixtures_passed` must equal the number of `per_fixture_results[*].passed` values set to `true`.

`summary.coverage_at_claimed_class` must be `true` only when every required fixture for `detector_class_claimed` passed. If a stronger detector class is also fully covered, update `detector_class_claimed` to that stronger class.

## Per-Fixture Results

Each fixture in `corpus.manifest.json` must have exactly one `per_fixture_results` entry.

For a passed fixture:

- `passed` must be `true`;
- `emitted_findings` must contain the exact expected `(finding_id, category, severity)` set from that fixture's `expected-findings.json`;
- each emitted finding must include non-empty `evidence`;
- `notes` should describe scanner behavior, unsupported edge cases, or reviewer caveats.

For a missed or unsupported fixture:

- `passed` must be `false`;
- `emitted_findings` should include what the scanner actually emitted, or an empty list if it emitted nothing;
- `notes` should explain whether the miss is unsupported scope, false negative, false positive handling, or a scanner limitation.

## Evidence Field

Use concrete evidence, not broad prose. Good evidence points to one or more of:

- fixture file path and line number;
- emitted rule ID and finding payload;
- trace ID or event ID;
- detector log line;
- scanner command output;
- score or confidence field if the scanner emits one.

Do not include secrets, private customer data, internal hostnames, or non-public evidence. Redact sensitive values and describe the redaction.

## What Not To Submit

Do not submit:

- a scorecard with placeholder scanner metadata;
- a scorecard without scanner source provenance or runnable context;
- a scorecard generated by hand without running a scanner, except as an explicitly labeled private dry run;
- a scorecard that marks a fixture passed while omitting finding evidence;
- a scorecard that claims `trace-aware` coverage when trace fixtures were not inspected;
- private feedback that cannot be reproduced or summarized publicly.

## Acceptance Boundary

An accepted scorecard supports only this narrow claim:

> This scanner covers the DVAAC v0.1.4 fixture classes for the detector class it claims.

It does not imply product safety, universal agent safety, legal compliance, endorsement, or external validation beyond the submitted scorecard.
