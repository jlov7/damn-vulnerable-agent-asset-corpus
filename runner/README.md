# DVAAC runner

A small script that walks every fixture under `fixtures/`, checks local corpus bindings, mints a demo-key AAC signature as a plumbing check, and verifies the signed template against the AAC v0.2 reference verifier.

## What this is

This runner is *fixture conformance*, not detection. DVAAC ships ground truth (vulnerable inputs and expected outputs). The runner makes sure the ground truth itself is well-formed and verifiable.

A scanner author should:

1. Run their own detector against each fixture's input artifacts.
2. Build their own AAC.
3. Compare their AAC's findings against the fixture's `expected-findings.json`.
4. Preserve the local digest-binding rules if they reuse DVAAC evidence artifacts.
5. Publish scanner results using `scorecard-template.json`.

## Locating the AAC verifier

The runner needs to import the AAC reference verifier (`verify.py`). It looks for it in this order:

1. The `--aac-verifier` CLI argument.
2. The `AAC_VERIFIER_PATH` environment variable.
3. A sibling directory: `../agent-assurance-case/verifier/verify.py`.
4. A local-development sibling directory: `../agent-assurance-case-spec/verifier/verify.py`.

To use a checked-out copy of the public AAC repository:

```bash
git clone --branch v0.2-candidate.5 --depth 1 https://github.com/jlov7/agent-assurance-case ../agent-assurance-case
AAC_VERIFIER_PATH=../agent-assurance-case/verifier/verify.py python verify_fixtures.py
```

The runner refuses to import a verifier from inside `fixtures/`, because fixture payloads are untrusted by design.

## Running

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python verify_fixtures.py
```

Expected last line:

```text
DVAAC: all fixtures conform.
```

Exit code 0 = all conform. Non-zero = at least one fixture or one expected AAC is broken.

To emit demo-signed AACs for auditor inspection without mutating the checked-in templates:

```bash
python verify_fixtures.py --write-signed dist/signed-aac
```

## What the runner checks per fixture

- `README.md`, `expected-findings.json`, `expected-aac.json` all exist.
- JSON parsing rejects duplicate object members and non-standard numeric constants.
- `corpus.manifest.json` validates against `corpus.manifest.schema.json` and matches fixture verdicts, finding counts, profiles, assurance levels, and detector-class coverage claims.
- `scorecard-template.json` validates against `scorecard-template.schema.json` and covers every fixture directory.
- `expected-findings.json` validates against `runner/expected-findings.schema.json`.
- The finding IDs in `expected-aac.json` are exactly the IDs listed in `expected-findings.json`, with matching `severity`, `category`, `title`, `subject_asset_id`, and `description` for each.
- Asset digests match the local `source_uri` files or directories.
- Every local `evidence://dvaac/NN/...` artifact digest matches the corresponding file or line excerpt.
- Symlinks anywhere under a fixture tree are rejected, and all asset/evidence paths must resolve inside the owning fixture directory.
- `policy_decisions[*].inputs_hash` matches the canonical policy decision object with `inputs_hash` removed.
- The expected AAC signs with the AAC reference demo key for conformance-time plumbing, hashes correctly, and passes the AAC v0.2 verifier.

The runner cannot prove that prose is semantically true. Threat descriptions, evidence line choices, and fixture realism are manually reviewed and should be challenged in PR review.

## Digest rules

- Asset digests are SHA-256 hashes over canonical JSON entries of each file under the asset's `source_uri` directory: `{"path": "...", "sha256": "..."}`. Generated local cache files (`__pycache__/`, `.coverage`, `.mypy_cache/`, `.pyre/`, `.pytest_cache/`, `.pytype/`, `.ruff_cache/`, `.tox/`, `.venv/`, `*.pyc`, `*.pyo`, `.DS_Store`) are ignored.
- Detector and AIBOM evidence digests are SHA-256 hashes of the local files under `fixtures/NN-name/evidence/`.
- File-excerpt evidence digests are SHA-256 hashes over the exact referenced lines joined with `\n` plus one trailing `\n`.
- Policy input hashes are SHA-256 hashes over canonical JSON for the policy decision object after removing `inputs_hash`.

## Pinning to an AAC version

DVAAC v0.1.1 expects AAC v0.2-candidate.5 (schema `$id` `https://raw.githubusercontent.com/jlov7/agent-assurance-case/v0.2-candidate.5/schemas/agent-assurance-case-v0.2.schema.json`).

When AAC issues a new minor or major version, DVAAC will publish a corresponding corpus version with re-signed fixtures. Until then, use the AAC v0.2 reference verifier.
