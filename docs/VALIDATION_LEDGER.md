# DVAAC Validation Ledger

This ledger records third-party scanner results and corpus critiques for DVAAC. It is intentionally separate from local conformance checks.

## Current Target

- DVAAC release: `v0.1.5`
- DVAAC release commit: `e90a76daf9107871d1ff6a2d7c438d2b92709e53`
- DOI: <https://doi.org/10.5281/zenodo.20379817>
- Pinned AAC verifier: `v0.2-candidate.8`
- AAC verifier commit: `936885583a49dfd06fd11ce45c8ee82330f1007d`
- Public validation issue: <https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/issues/1>

## Current External Validation Status

No third-party scanner result or independent corpus critique has been accepted into this repository yet.

| Date | Source | Result type | Detector class | Target | Status | Evidence |
|---|---|---|---|---|---|---|
| none yet | none yet | none yet | n/a | none yet | no accepted external result | n/a |

This is the current claim boundary: DVAAC is signed, CI-green, DOI-archived, and ready to receive scanner results; it is not yet externally validated.

This boundary is machine-checked against release evidence and reviewer-facing docs by [`scripts/validate_external_validation_status.py`](../scripts/validate_external_validation_status.py).

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

Scanner-result ledger candidates should include a complete scorecard based on
[`scorecard-template.json`](../scorecard-template.json), validated from current
`main` where possible. Current `main` may include stricter intake checks than
the immutable release checkout, including scanner source provenance and runnable
context:

```bash
python3 runner/validate_scorecard.py path/to/scorecard.json
make validate-scorecard SCORECARD=path/to/scorecard.json
```

The validator checks scorecard schema conformance, fixture coverage, summary
counts, claimed detector-class coverage, populated scanner metadata, scanner
source provenance, runnable context, public reproducibility declaration, and
exact finding identity for fixtures marked as passed. Passing validation does
not prove that scanner evidence is semantically correct; it only makes the
submission reproducible enough for maintainer review.

Corpus-critique ledger candidates should include a filled
[`corpus-critique-template.json`](../corpus-critique-template.json), validated
from current `main` with:

```bash
python3 runner/validate_corpus_critique.py path/to/corpus-critique.json
```

The corpus-critique validator checks report shape, target identity, fixture
references, at least one public reproduction step, duplicate finding IDs, public
reproducibility fields, and claim-boundary fields. Passing validation does not
prove that the critique is correct or accepted; it only makes the report
reproducible enough for maintainer review.

Private comments, social-media reactions, stars, and vendor claims without reproducible fixture-level evidence do not count as accepted external validation.

## Local Evidence That Does Not Count As External Validation

The following are useful release evidence, but they are self-validation:

- GitHub Actions on `main`;
- `runner/verify_fixtures.py`;
- `make verify`, `make pytest-safety`, and `make write-signed`;
- release assets, checksums, and manifests;
- the Zenodo DOI.

These artifacts make DVAAC reviewable. They do not replace third-party scanner results or independent corpus critique.
