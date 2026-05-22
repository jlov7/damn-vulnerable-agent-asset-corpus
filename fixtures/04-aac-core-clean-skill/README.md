# Fixture 04 — `aac-core-clean-skill`

**Threat class:** Baseline (none).
**Expected verdict:** `pass`.
**Static-declared scanner:** correctly emits no findings.
**Static-extended scanner:** correctly emits no findings.
**Trace-aware scanner:** no trace artifact is supplied in this fixture.

This fixture is the portable AAC baseline. It is intentionally similar to fixture 01, but its expected AAC declares the profile-agnostic `aac.core` profile instead of `runwright.skills.release`.

The purpose of including this fixture is adoption: a scanner author can run DVAAC without adopting a Runwright-specific release profile.

## What the scanner inspects

- `skill/SKILL.md`: declared skill manifest. Plain, no instruction-layer attacks.

## Expected outputs

- `expected-findings.json`: empty array.
- `expected-aac.json`: `verdict: pass`, `profile_id: aac.core`, no unresolved findings.

## Mapping

- OWASP Agentic Skills Top 10: none.
- OWASP MCP Top 10: none.
- AAC v0.2 finding categories: none.
