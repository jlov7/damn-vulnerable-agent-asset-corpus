# DVAAC Release Fingerprints

This file records public, reproducible fingerprints for the current DVAAC release. It is release provenance, not third-party scanner validation.

Machine-readable companion: [`release-evidence.v0.1.5.json`](release-evidence.v0.1.5.json), validated by [`release-evidence.schema.json`](release-evidence.schema.json).
The executable fingerprint verifier reads that evidence file as its release source of truth.

## Current Release

- Repository: <https://github.com/jlov7/damn-vulnerable-agent-asset-corpus>
- Release: `v0.1.5`
- Release URL: <https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/releases/tag/v0.1.5>
- Release commit: `749511a94acc705123a9a5db82f71bbf7b12a64d`
- DOI: <https://doi.org/10.5281/zenodo.20448675>
- Release published: `2026-05-28T22:44:12Z`
- Pinned AAC verifier: `v0.2-candidate.8`
- Pinned AAC verifier commit: `936885583a49dfd06fd11ce45c8ee82330f1007d`
- Current public validation issue: <https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/issues/1>

## Signed Tag Check

```bash
git fetch --tags origin
git rev-list -n 1 v0.1.5
git tag -v v0.1.5
```

Expected release commit:

```text
749511a94acc705123a9a5db82f71bbf7b12a64d
```

Observed tag verification:

```text
Good "git" signature for jase.lovell@me.com with ED25519 key SHA256:WGevS9odnPKBtzTZjoVXSj2aexpZo4k6VL/dHaVaJdY
object 749511a94acc705123a9a5db82f71bbf7b12a64d
type commit
tag v0.1.5
```

## Release Assets

Release assets attached to `v0.1.5`:

| Asset | GitHub asset digest |
|---|---|
| `RELEASE-MANIFEST.json` | `sha256:cf63460fcef5d8f30ee282d264587db2858e471a58c79fb8f279c02e02147682` |
| `SHA256SUMS` | `sha256:62bb77446ae211062605682bb5b002bd508b72b8250d53c8e4065f1245d6aded` |
| `signed-aac-v0.1.5.tar.gz` | `sha256:e0278106d00fdb8756672a155134604a78011882c594ac5a362cb910aee55df0` |
| `signed-aac-v0.1.5.tar.gz.sha256` | `sha256:d32f6dc4c6240f5ed35caed79ab6c5d5c7eef8420273fd55eb6d008dffa64c51` |

`v0.1.5` predates the `release-assets` workflow and does not claim GitHub
artifact-attestation provenance. Future releases should be generated through
that workflow so the release assets are bound to a GitHub-hosted provenance
attestation in addition to the signed tag, manifest signature, and checksums
documented here.

Verify the archive sidecar:

```bash
curl -L -O https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/releases/download/v0.1.5/signed-aac-v0.1.5.tar.gz
curl -L -O https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/releases/download/v0.1.5/signed-aac-v0.1.5.tar.gz.sha256
shasum -a 256 -c signed-aac-v0.1.5.tar.gz.sha256
```

## Release Verification Commands

From immutable release checkouts:

```bash
mkdir dvaac-review
cd dvaac-review
git clone --branch v0.2-candidate.8 --depth 1 https://github.com/jlov7/agent-assurance-case
test "$(git -C agent-assurance-case rev-parse HEAD)" = "936885583a49dfd06fd11ce45c8ee82330f1007d"

git clone --branch v0.1.5 --depth 1 https://github.com/jlov7/damn-vulnerable-agent-asset-corpus
cd damn-vulnerable-agent-asset-corpus
test "$(git rev-parse HEAD)" = "749511a94acc705123a9a5db82f71bbf7b12a64d"
uv venv
source .venv/bin/activate
uv pip install -r runner/requirements.txt
AAC_VERIFIER_PATH=../agent-assurance-case/verifier/verify.py python3 runner/verify_fixtures.py
```

Expected final line:

```text
DVAAC: all fixtures conform.
```

Validate a third-party scorecard against the release validator:

```bash
python3 runner/validate_scorecard.py path/to/scorecard.json
```

Expected output for a structurally valid scorecard:

```text
DVAAC scorecard: valid submission.
```

From current `main`, reviewers can run the executable release-fingerprint verifier. It clones the immutable DVAAC and AAC release tags into a temporary directory, checks the exact commits, verifies both signed tags with the public release-signing key, runs corpus conformance, runs scorecard-validator tests when present, checks pytest collection safety, downloads the published release assets, verifies their GitHub asset digests, checks the archive sidecar, extracts the signed-AAC archive safely, verifies the inner `SHA256SUMS` file, and confirms that GitHub artifact attestations are absent for `v0.1.5` as documented above:

```bash
python3 scripts/verify_release_fingerprints.py
```

GitHub also runs the same check through the `release-fingerprints` workflow on every pull request, on every push to `main`, on a weekly schedule, and on manual dispatch. The `Verify DVAAC release fingerprint` job is a required protected-branch check. Those workflow runs are self-verification evidence; they are not third-party scanner validation or independent corpus review.

## Protected Main Gate

As of `2026-05-25`, the protected `main` branch requires strict status checks for:

- `conformance`
- `Analyze Python`
- `Verify DVAAC release fingerprint`
- `Quality checks`
- `OpenSSF Scorecard`

The initial protected-gate evidence after enabling the release-fingerprint requirement is listed below. `Quality checks` and `OpenSSF Scorecard` were added as required protected checks after this initial evidence point. For the latest `main` status, use the workflow badges or GitHub Actions run history.

- Main commit: `70662ba39170356d74ffe8eb807bbd508486d486`
- Release-fingerprints workflow: <https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/actions/runs/26409761070>
- DVAAC conformance workflow: <https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/actions/runs/26409761092>
- CodeQL workflow: <https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/actions/runs/26409761129>
- Open code-scanning alerts at last check: `0`

## Baseline Post-Release Evidence

The release tag is immutable review evidence. `main` may contain later documentation clarifications. This baseline evidence records a green post-release `main` state after the DOI, validation-entry, and release-fingerprint workflow updates, without implying it will remain the latest `main` commit:

- Evidence checked: `2026-05-25`
- Workflow commit: `c6c3a9caec88cc728dc312f1dd66cf90518a4bc8`
- Release-fingerprints workflow: <https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/actions/runs/26409297378>
- DVAAC conformance workflow: <https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/actions/runs/26409297376>
- CodeQL workflow: <https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/actions/runs/26409297373>
- Open code-scanning alerts at last check: `0`
- Historical fixed CodeQL alert: `py/empty-except` note, state `fixed`

## Claim Boundary

These fingerprints make the release easier to verify and cite. They do not claim scanner quality, product safety, statistical vulnerability coverage, legal certification, employer endorsement, standards-body endorsement, or accepted third-party validation. Accepted scanner results and corpus critiques are tracked separately in [VALIDATION_LEDGER.md](VALIDATION_LEDGER.md).
