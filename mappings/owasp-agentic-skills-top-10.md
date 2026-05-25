# Mapping: DVAAC v0.1.4 → OWASP Agentic Skills Top 10

OWASP's Agentic Skills Top 10 is the most relevant external taxonomy for skill-surface threats.

This mapping is informative; it is not authoritative for the OWASP project. DVAAC fixtures are intentionally narrower and more concrete than the OWASP categories.

| DVAAC fixture | OWASP Agentic Skills Top 10 | Coverage |
|---|---|---|
| 01-clean-declared-skill | (none — baseline) | n/a |
| 02-skill-md-prompt-injection | **AST01 — Malicious Skills** (instruction-layer variant) | direct match |
| 03-hidden-test-payload | **AST01 — Malicious Skills** (developer-execution-surface variant) | direct match for whole-bundle scanner claims |
| 04-aac-core-clean-skill | (none — portable AAC baseline) | n/a |
| 05-shadow-skill-from-trace | **AST03 — Shadow Skills** / runtime skill drift candidate | trace-aware adjacent |
| 06-medium-overbroad-tool-scope | **AST04 — Excessive Permissions** | direct match |
| 07-low-missing-owner-metadata | (none — metadata quality) | n/a |
| 08-info-local-only-skill | (none — informational note) | n/a |
| 09-cross-file-logic-split | **AST01 — Malicious Skills** (evasion variant) | direct match for whole-bundle scanner claims |
| 10-skill-drift | **AST02 — Skill Drift / Supply Chain Drift** | adjacent |
| 11-dynamic-remote-fetch | **AST02 — Mutable Remote Skill Content** | adjacent |
| 12-mcp-tool-scope-escalation | OWASP MCP cross-reference | n/a |
| 13-secret-exfiltration-via-allowed-tool | **AST01 — Malicious Skills** (allowed-tool exfiltration variant) | direct match |
| 14-memory-poisoning | **AST05 — Memory Poisoning** | adjacent |
| 15-a2a-delegation-misuse | Cross-agent delegation category | adjacent |
| 16-accepted-critical-risk | **AST01 — Malicious Skills** with accepted risk | verdict-semantics fixture |

## What this mapping is for

A scanner author claiming OWASP Agentic Skills Top 10 coverage can use DVAAC fixtures to demonstrate which specific sub-classes of AST01 (and adjacent categories) their scanner handles. *"We catch AST01"* is much weaker than *"we catch AST01 instruction-layer (DVAAC 02) but not AST01 developer-execution-surface (DVAAC 03)."*

DVAAC's value is making OWASP categories runnable.
