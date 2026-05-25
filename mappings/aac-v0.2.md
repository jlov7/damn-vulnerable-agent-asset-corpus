# Mapping: DVAAC v0.1.3 → AAC v0.2

This document maps DVAAC v0.1.3 fixtures and finding categories to the Agent Assurance Case (AAC) v0.2 specification.

DVAAC is the input/output benchmark; AAC is the assurance evidence object DVAAC's expected outputs conform to.

## Fixture → Profile

| DVAAC fixture | AAC profile declared | AAC assurance level |
|---|---|---|
| 01-clean-declared-skill | `runwright.skills.release` | `basic` |
| 02-skill-md-prompt-injection | `runwright.skills.release` | `basic` |
| 03-hidden-test-payload | `runwright.skills.release` | `basic` |
| 04-aac-core-clean-skill | `aac.core` | `structural` |
| 05-shadow-skill-from-trace | `aac.core` | `structural` |
| 06-medium-overbroad-tool-scope | `aac.core` | `structural` |
| 07-low-missing-owner-metadata | `aac.core` | `structural` |
| 08-info-local-only-skill | `aac.core` | `structural` |
| 09-cross-file-logic-split | `aac.core` | `structural` |
| 10-skill-drift | `aac.core` | `structural` |
| 11-dynamic-remote-fetch | `aac.core` | `structural` |
| 12-mcp-tool-scope-escalation | `aac.core` | `structural` |
| 13-secret-exfiltration-via-allowed-tool | `aac.core` | `structural` |
| 14-memory-poisoning | `aac.core` | `structural` |
| 15-a2a-delegation-misuse | `aac.core` | `structural` |
| 16-accepted-critical-risk | `aac.core` | `strict` |

Fixtures 01-03 declare a concrete Runwright release profile. Fixtures 04-16 declare `aac.core` only, so scanner authors can exercise DVAAC without adopting a vendor-specific profile.

## DVAAC finding categories → AAC verdict semantics

DVAAC uses kebab-case finding categories that map to AAC v0.2 verdict semantics as follows.

| DVAAC category | Typical severity | AAC v0.2 verdict effect |
|---|---|---|
| `skill-prompt-injection` | high | HOLD (unresolved HIGH finding) |
| `skill-developer-execution-surface` | critical | FAIL (unresolved CRITICAL finding) |
| `runtime-shadow-skill` | high | HOLD |
| `skill-tool-scope` | medium | PASS |
| `asset-metadata-quality` | low | PASS |
| `detector-informational-note` | info | PASS |
| `cross-file-logic-split` | high | HOLD |
| `skill-drift` | high | HOLD |
| `dynamic-remote-fetch` | high | HOLD |
| `mcp-tool-scope-escalation` | high | HOLD |
| `secret-exfiltration-via-allowed-tool` | high | HOLD |
| `memory-poisoning` | high | HOLD |
| `a2a-delegation-misuse` | high | HOLD |
| `accepted-critical-risk` | critical accepted by exception | HOLD |

The severity and verdict relationship is governed by AAC v0.2 SPEC §5. DVAAC does not redefine it.

## DVAAC fixture → AAC required detector categories

Because fixtures 01-03 declare `runwright.skills.release`, the AAC v0.2 reference verifier requires those cases to include detector runs for the four required categories of that profile:

- `skill-manifest-integrity`
- `skill-secret-exposure`
- `skill-executable-surface`
- `skill-tool-scope`

Fixtures 01-03 include a single bundled detector run covering all four categories. A scanner author may emit multiple detector runs instead, provided each required category is covered by at least one run with `status` not in `{skipped, error}`. Fixtures 04-16 use `aac.core` and do not require Runwright detector categories.

## DVAAC evidence artifacts → AAC `evidence_artifacts`

Every external URI referenced from an AAC (in `findings.evidence_refs`, `coverage.detector_runs[*].evidence_ref`, `aibom_ref`, `graph_snapshot_ref`, `eval_results[*].evidence_ref`, `runtime_events[*].trace_ref`, `release_conditions[*].evidence_ref`, `compliance_mappings[*].evidence_refs`) must appear in `evidence_artifacts` with a SHA-256 digest. This is enforced by the AAC reference verifier for vendor profiles.

DVAAC fixtures use synthetic `evidence://` URIs, but v0.1.3 digests are real local bindings checked by `runner/verify_fixtures.py`. Detector and AIBOM evidence URIs resolve to files under `fixtures/NN-name/evidence/`; file excerpt URIs resolve to exact checked-in source lines.

## Signature

DVAAC fixtures are signed at runner-run time with the AAC reference *demo* key. This is a conformance-time plumbing check, not an issuer-trust claim. The load-bearing checks are AAC schema/profile/verdict validation plus DVAAC's local digest bindings. Production AACs sign with issuer-controlled keys.

## Version pinning

DVAAC v0.1.3 is pinned to AAC v0.2-candidate.6 at commit `a51c7bd4a2de326333b149ad321785a276376cfa`. The `signed_by` URN and `key_id` values in DVAAC fixtures match the demo key constants in that reference verifier. If AAC re-numbers, deprecates, or breaks compatibility, DVAAC fixtures will need a new corpus patch or minor version.
