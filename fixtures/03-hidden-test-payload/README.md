# Fixture 03 — `hidden-test-payload`

**Threat class:** Developer-execution-surface attack. Malicious code lives in a bundled payload-demo file, not in the declared instruction surface.
**Expected verdict:** `fail`.
**Static-declared scanner:** likely MISSES this. `SKILL.md` and the declared script (`scripts/apply.py`) look clean.
**Static-extended scanner:** catches.
**Trace-aware scanner:** catches if developer test execution or bundle validation is instrumented; no trace artifact is supplied in v0.1.1.

This is the differentiating case. Every part of the declared agent surface looks fine. The malicious behaviour lives in `tests/apply_payload_demo.py`, which represents code a developer might run as part of ordinary skill validation. The demo file reads `SKILL.md`, extracts an inline code block, and `exec()`s it. The file is deliberately not named `test_*.py`, so default pytest discovery does not execute it, but the primitive is the same one a malicious bundle can hide in test or validation code. The agent itself never sees the malicious instruction — the developer's machine does, with the developer's permissions.

**Demonstration payload safety.** DVAAC's payload in `SKILL.md` writes a marker file to `/tmp/dvaac_hidden_test_payload.txt` containing the literal string `DVAAC_FAKE_SECRET=demo-only-do-not-use`. There is no network egress, no real secret access, and no persistence beyond `/tmp`. The threat class — arbitrary local code execution from a file outside the declared execution surface — is real and CRITICAL; the specific demonstration is deliberately safe so the fixture can be inspected and forked without harm.

This is why DVAAC v0.1.1 includes it: it is the cleanest demonstration of *what static-declared scanning misses*.

## What the scanner inspects

- `skill/SKILL.md`: declared manifest. Looks clean.
- `skill/scripts/apply.py`: declared script. Looks clean.
- `skill/tests/apply_payload_demo.py`: **not declared as an executable surface, but is one.** This is the payload demonstration. It is deliberately not named `test_*.py`, and the repository also ships pytest collection guards, so default test discovery does not execute it.

## Why it produces FAIL, not HOLD

Because the test suite executes attacker-controlled code from `SKILL.md` with developer-local permissions before an agentic release decision is ever made. The demonstration payload writes only a safe `/tmp` marker, but the primitive is arbitrary local code execution from a file outside the declared execution surface. There is no remediation path that lets this bundle proceed; the skill must be rejected and treated as malicious.

## Expected outputs

- `expected-findings.json`: one CRITICAL finding with `category: skill-developer-execution-surface`.
- `expected-aac.json`: `verdict: fail`, one unresolved CRITICAL finding, complete coverage.

## Mapping

- OWASP Agentic Skills Top 10: **AST01 — Malicious Skills**, but specifically the under-served execution-surface variant.
- OWASP MCP Top 10: not applicable.
- AAC v0.2 finding category: `skill-developer-execution-surface` (matches the `skill-executable-surface` required detector category in `runwright.skills.release`).

## How to claim coverage of this fixture

If your scanner claims to catch fixture 03, it MUST:

1. Inspect bundled test files in skill packages, not only files referenced as executable in the manifest.
2. Identify constructs that read `SKILL.md` and pass extracted content to `exec()`, `eval()`, `subprocess`, or equivalent dynamic execution paths.
3. Treat module-import dynamic execution in bundled validation code as CRITICAL. If this file were named as a default test module, ordinary test discovery would import it before any release decision; DVAAC deliberately uses a non-test filename plus repository-level pytest guards so the benchmark remains safe to inspect.

Half-credit is not awarded: a scanner that catches the dynamic `exec()` but misses that the source is `SKILL.md` is not solving this threat class.
