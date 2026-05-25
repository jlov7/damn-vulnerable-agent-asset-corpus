# DVAAC Validation Ledger

This ledger records third-party scanner results and corpus critiques for DVAAC. It is intentionally separate from local conformance checks.

## Current Target

- DVAAC release: `v0.1.3`
- DVAAC release commit: `80d9f3ae8f80af273ce311a0b5071cc42d55c8c4`
- DOI: <https://doi.org/10.5281/zenodo.20345025>
- Pinned AAC verifier: `v0.2-candidate.6`
- AAC verifier commit: `a51c7bd4a2de326333b149ad321785a276376cfa`
- Public validation issue: <https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/issues/1>

## Current External Validation Status

No third-party scanner result or independent corpus critique has been accepted into this repository yet.

| Date | Source | Result type | Detector class | Target | Status | Evidence |
|---|---|---|---|---|---|---|
| none yet | none yet | none yet | n/a | none yet | no accepted external result | n/a |

This is the current claim boundary: DVAAC is signed, DOI-backed, CI-green, and ready to receive scanner results; it is not yet externally validated.

## What Counts As Accepted External Validation

An entry can be added here when it has:

- scanner name, version, and commit or release URL when available;
- exact DVAAC release tag or commit tested;
- exact AAC verifier tag or commit used, when applicable;
- claimed detector class;
- command line, environment, and relevant configuration;
- complete scorecard or per-fixture result;
- handling of misses and false positives;
- maintainer disposition in a linked issue or pull request.

Private comments, social-media reactions, stars, and vendor claims without reproducible fixture-level evidence do not count as accepted external validation.

## Local Evidence That Does Not Count As External Validation

The following are useful release evidence, but they are self-validation:

- GitHub Actions on `main`;
- `runner/verify_fixtures.py`;
- `make verify`, `make pytest-safety`, and `make write-signed`;
- release assets, checksums, and manifests;
- the Zenodo DOI.

These artifacts make DVAAC reviewable. They do not replace third-party scanner results or independent corpus critique.
