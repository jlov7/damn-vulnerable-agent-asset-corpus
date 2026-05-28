# What This Is / What This Is Not

A one-page statement of scope and claims for the Damn Vulnerable Agent Asset
Corpus (DVAAC). If you are quoting this project in a post, article, review, or
product comparison, quote from here.

## What DVAAC is

- A **compact conformance corpus**: 16 deliberately vulnerable or deliberately
  clean agentic-AI release fixtures, each with expected findings and an Agent
  Assurance Case (AAC v0.2) template.
- A **runner** (`runner/verify_fixtures.py`) that checks the corpus's own
  ground truth is internally consistent — digests bind, finding IDs/severities
  match, schemas validate, and the AAC templates verify against the AAC v0.2
  reference verifier. It never imports or executes fixture payloads.
- **Personal, independent research and development**, published openly and
  invited for adversarial critique.

## What DVAAC is not

- **Not a statistical benchmark.** 16 hand-authored fixtures are a
  non-representative sample. There is no measured detection rate to cite.
- **Not a scanner and not a vulnerability database.** DVAAC ships ground truth,
  not detection logic.
- **Not a validator of scanner accuracy.** A passing run certifies *corpus
  consistency*, not that any scanner is correct, complete, or safe.
- **Not a safety guarantee.** A scanner that covers these fixture classes has
  not been shown to ensure universal agent safety.
- **Not independently validated yet.** No third-party scanner result or corpus
  critique has been accepted; see
  [docs/VALIDATION_LEDGER.md](docs/VALIDATION_LEDGER.md).
- **Not an employer or institutional work product.** See the Independence
  Notice in [README.md](README.md#independence-notice).

## The verification boundary

| Property | Status | Evidence |
| --- | --- | --- |
| Corpus ground truth is self-consistent (digests, IDs, schemas) | Self-verified | `make verify`, `runner/verify_fixtures.py` |
| AAC templates verify against the reference verifier | Self-verified | pinned AAC `v0.2-candidate.7` |
| Runner refuses to execute/import fixture payloads | Self-verified | `make pytest-safety`, CI guards |
| Release tag is signed and DOI-archived | Self-verified | `docs/RELEASE_FINGERPRINTS.md`, Zenodo |
| Independent scanner result / corpus critique | **Not yet accepted** | `docs/VALIDATION_LEDGER.md` |
| Scanner accuracy / real-world detection rate | **Out of scope** | `LIMITATIONS.md` |

## How to help

The most useful contributions are adversarial: a scanner result that disputes a
fixture's expected findings, a corpus critique that finds an inconsistency, or a
new fixture class that preserves the safety envelope. Start from the
[review recipes](docs/EXTERNAL_VALIDATION.md#review-recipes) and the
[validation thread](https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/issues/1).
