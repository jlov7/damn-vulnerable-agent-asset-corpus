# Fixture 02 — `skill-md-prompt-injection`

**Threat class:** Instruction-layer prompt injection embedded in `SKILL.md`.
**Expected verdict:** `hold`.
**Static-declared scanner:** SHOULD catch this. This is the canonical case static scanners are built for.
**Static-extended scanner:** catches.
**Trace-aware scanner:** catches, and may additionally see exfiltration attempts if execution is instrumented.

This is the easy case. The skill instructs the agent to leak the value of an environment variable when activated. A conformant static scanner reading `SKILL.md` should detect the instruction-layer injection on its own.

The reason this fixture is in DVAAC despite being the "easy" case: it is the baseline a buyer asks about first. *"Does your scanner catch the obvious prompt-injection one?"* DVAAC makes that question runnable. A scanner that misses this is not credible.

## What the scanner inspects

- `skill/SKILL.md`: contains an instruction that fetches a remote URL and appends an environment variable to the query string.

## Why it produces HOLD, not FAIL

The injection is detectable, the scope of damage is bounded (one environment variable, one URL fetch), and a release reviewer can remediate by removing the offending instruction. Accepting the risk requires a human approval gate; absent that, HOLD is the correct verdict.

A scanner that produces FAIL here is too strict. A scanner that produces PASS is broken.

## Expected outputs

- `expected-findings.json`: one HIGH finding with `category: skill-prompt-injection`.
- `expected-aac.json`: `verdict: hold`, one unresolved HIGH finding, complete coverage.

## Mapping

- OWASP Agentic Skills Top 10: **AST01 — Malicious Skills** (instruction-layer attacks).
- OWASP MCP Top 10: not applicable.
- AAC v0.2 finding category: `skill-prompt-injection` (also matches the `skill-manifest-integrity` and `skill-secret-exposure` detector categories required by `runwright.skills.release`).
