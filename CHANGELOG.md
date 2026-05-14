# DVAAC Changelog

## v0.1.1 — 2026-05-14 — Publication hardening

### Fixed

- Replaced placeholder asset and evidence digests with runner-verified local SHA-256 bindings.
- Added local detector-output and AIBOM evidence files for every fixture.
- Hardened `runner/verify_fixtures.py` to reject duplicate JSON object members, validate `expected-findings.json`, refuse verifier imports from `fixtures/`, check AAC verifier API shape, verify evidence line ranges, verify policy input hashes, and keep AAC verifier output quiet unless a fixture fails.
- Fixed fixture 03's declared `scripts/apply.py` so config filenames cannot escape the target directory.
- Updated fixture 03 prose to describe the safe `/tmp` marker payload without claiming credential exfiltration by the demo.
- Moved CI from an inert template path to an active GitHub Actions workflow.
- Aligned citation, manifest, schema URI, licensing, and version metadata for v0.1.1.
- Added top-level pytest collection guards and renamed fixture 03's payload demonstration so default pytest discovery and common IDE test discovery do not execute it.
- Added fixture 04, a portable clean `aac.core` baseline.
- Added `scorecard-template.json` for scanner result publication.
- Added `scorecard-template.schema.json` and made the runner validate the scorecard template.
- Added `--write-signed DIR` to emit demo-signed AACs for auditor inspection without mutating checked-in templates.
- Expanded the initial corpus to 16 fixtures, covering trace-aware shadow skills, medium/low/info severity calibration, cross-file bundle logic, skill drift, dynamic remote fetch, MCP scope escalation, allowed-tool exfiltration, memory poisoning, A2A delegation misuse, and accepted critical risk.
- Changed DVAAC schema `$id` values to raw GitHub content URLs.
- Clarified that demo-key signing is a conformance plumbing check, not an issuer-trust claim.
- Pinned CI to AAC `v0.2-candidate.5` and added CI checks for committed JSON syntax and citation metadata.
- Aligned runner policy input hash checks with the AAC/JCS canonicalizer.
- Retargeted weak evidence line references in fixtures 06, 07, 08, and 13 to the exact source lines supporting each finding.

### Known limitations

- Fixtures 01-03 use `runwright.skills.release`; fixtures 04-16 use `aac.core`.
- AAC content hashes are signed at runtime by the runner using the AAC reference demo key. This binds DVAAC to AAC's tested verification path without requiring corpus consumers to manage a key, but it means the checked-in `expected-aac.json` files have placeholder hash/signature fields. Use `runner/verify_fixtures.py --write-signed DIR` to emit signed AACs for static audit artifacts.

## v0.1.0 — 2026-05-11 — Initial draft

### Added

- Three reference fixtures: `01-clean-declared-skill`, `02-skill-md-prompt-injection`, `03-hidden-test-payload`.
- Conformance runner that verifies every expected AAC end-to-end against the AAC v0.2 reference verifier (schema, content hash, signature, profile, recomputed verdict).
- `TAXONOMY.md` distinguishing static-declared, static-extended, and trace-aware detector classes.
- Mappings to AAC v0.2, OWASP Agentic Skills Top 10, and OWASP MCP Top 10.
- `CITATION.cff` for Zenodo archival.
- Dual licensing: CC BY 4.0 for fixtures/docs, Apache 2.0 for runner code.

### Known limitations

- Only three fixtures. The corpus is intentionally minimal in v0.1 to make the conformance bar testable.
- All fixtures use `runwright.skills.release` as the declared profile. Future versions will include `aac.core`-only fixtures.
- No MCP, A2A, memory, or runtime-trace fixtures. Superseded by v0.1.1.
- AAC content hashes are signed at runtime by the runner using the AAC reference demo key. This binds DVAAC to AAC's tested verification path without requiring corpus consumers to manage a key, but it means the checked-in `expected-aac.json` files have placeholder hash/signature fields. Superseded by the v0.1.1 `--write-signed` mode for auditors who require static signed evidence.
