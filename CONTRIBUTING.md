# Contributing

DVAAC accepts contributions that improve the corpus as a benchmark: clearer fixture truth, safer payload demonstrations, stronger runner checks, better schemas, and sharper documentation.

## Ground Rules

- Do not add executable payloads that touch the network, read real secrets, spawn subprocesses, persist, delete, overwrite, or change permissions.
- Do not add symlinks under `fixtures/**`.
- Do not add `test_*.py` or `*_test.py` files under `fixtures/**`.
- Keep each fixture focused on one threat class.
- Prefer small, inspectable artifacts over realism that makes review harder.
- Every evidence reference must point to exact local bytes and have a real SHA-256 digest.

## Fixture Checklist

A new fixture must include:

- `fixtures/NN-name/README.md`
- source artifacts under `skill/`, `mcp/`, `a2a/`, `memory/`, or `evidence/traces/`
- `expected-findings.json`
- `expected-aac.json`
- a `corpus.manifest.json` entry
- a `scorecard-template.json` entry
- mapping updates when relevant

Before opening a PR, run:

```bash
make verify
make pytest-safety
make write-signed
```

Include the runner output in the PR description.

## Review And Merge Policy

The `main` branch is protected. Changes should land through pull requests after the required GitHub Actions checks pass: `conformance`, CodeQL `Analyze Python`, and `Verify DVAAC release fingerprint`.

Release tags are signed, treated as immutable, and superseded by new tags rather than rewritten.

## Expected-Findings Rules

`expected-findings.json` is the source of scanner truth. Its finding IDs, categories, severities, titles, descriptions, and subject asset IDs must match `expected-aac.json` exactly.

Use `critical` only when AAC verdict semantics should produce `fail`, unless the fixture is explicitly about accepted risk. Use `high` for unresolved findings that should produce `hold`. Use `medium`, `low`, and `info` for nonblocking calibration.

## Review Standard

DVAAC is intentionally small enough for a reviewer to read end-to-end. A fixture that requires extensive setup, hidden state, network access, or complex execution is not a good fit.

Review comments should be specific and evidence-backed: file path, line number, observation, impact, and suggested fix.
