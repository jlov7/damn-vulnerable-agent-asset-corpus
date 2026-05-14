# Fixture 01 — `clean-declared-skill`

**Threat class:** Baseline (none).
**Expected verdict:** `pass`.
**Static-declared scanner:** correctly emits no findings.
**Static-extended scanner:** correctly emits no findings.
**Trace-aware scanner:** correctly emits no findings.

This fixture is the baseline. It is an ordinary, well-formed Anthropic-style skill that does what it says: format text. No prompt injection, no hidden execution surface, no tool scope creep, no remote fetch. A conformant scanner should emit zero findings against this fixture and produce an AAC with `verdict: pass`.

The purpose of including a clean baseline in DVAAC is to detect false positives: a scanner that flags this fixture is over-eager and would generate alert fatigue in production.

## What the scanner inspects

- `skill/SKILL.md`: declared skill manifest. Plain, no instruction-layer attacks.

## Expected outputs

- `expected-findings.json`: empty array.
- `expected-aac.json`: `verdict: pass`, complete coverage, all four `runwright.skills.release` required detector categories run successfully and return clean.

## Mapping

- OWASP Agentic Skills Top 10: none.
- OWASP MCP Top 10: none.
- AAC v0.2 finding categories: none.
