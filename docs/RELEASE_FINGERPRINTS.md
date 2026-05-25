# DVAAC Release Fingerprints

This file records public, reproducible fingerprints for the current DVAAC release. It is release provenance, not third-party scanner validation.

Machine-readable companion: [`release-evidence.v0.1.4.json`](release-evidence.v0.1.4.json), validated by [`release-evidence.schema.json`](release-evidence.schema.json).
The executable fingerprint verifier reads that evidence file as its release source of truth.

## Current Release

- Repository: <https://github.com/jlov7/damn-vulnerable-agent-asset-corpus>
- Release: `v0.1.4`
- Release URL: <https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/releases/tag/v0.1.4>
- Release commit: `e90a76daf9107871d1ff6a2d7c438d2b92709e53`
- DOI: <https://doi.org/10.5281/zenodo.20379817>
- Release published: `2026-05-25T13:16:03Z`
- Pinned AAC verifier: `v0.2-candidate.7`
- Pinned AAC verifier commit: `689198d9c249a966a0abab6415ae8668efb512d9`
- Current public validation issue: <https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/issues/1>

## Signed Tag Check

```bash
git fetch --tags origin
git rev-list -n 1 v0.1.4
git tag -v v0.1.4
```

Expected release commit:

```text
e90a76daf9107871d1ff6a2d7c438d2b92709e53
```

Observed tag verification:

```text
Good "git" signature for jase.lovell@me.com with ED25519 key SHA256:WGevS9odnPKBtzTZjoVXSj2aexpZo4k6VL/dHaVaJdY
object e90a76daf9107871d1ff6a2d7c438d2b92709e53
type commit
tag v0.1.4
```

## Release Assets

Release assets attached to `v0.1.4`:

| Asset | GitHub asset digest |
|---|---|
| `RELEASE-MANIFEST.json` | `sha256:91ca62843fd1576ae90c2a7ebcd506a499621d108f4b876f5a11008555299170` |
| `SHA256SUMS` | `sha256:5bbd4df2ac987315fd1460fa48646672a804316e0e481b35180fc73fa732a513` |
| `signed-aac-v0.1.4.tar.gz` | `sha256:ba73b6b3b75c8043feb2cc9e039c0bd5ee3d40b7e1b7aa99e65ad55ef516a43b` |
| `signed-aac-v0.1.4.tar.gz.sha256` | `sha256:a7878cb84bbddf708c3852889a700d027967033169533e804de37340b2ccfa35` |

`v0.1.4` predates the `release-assets` workflow and does not claim GitHub
artifact-attestation provenance. Future releases should be generated through
that workflow so the release assets are bound to a GitHub-hosted provenance
attestation in addition to the signed tag, manifest signature, and checksums
documented here.

Verify the archive sidecar:

```bash
curl -L -O https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/releases/download/v0.1.4/signed-aac-v0.1.4.tar.gz
curl -L -O https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/releases/download/v0.1.4/signed-aac-v0.1.4.tar.gz.sha256
shasum -a 256 -c signed-aac-v0.1.4.tar.gz.sha256
```

## Release Verification Commands

From immutable release checkouts:

```bash
mkdir dvaac-review
cd dvaac-review
git clone --branch v0.2-candidate.7 --depth 1 https://github.com/jlov7/agent-assurance-case
test "$(git -C agent-assurance-case rev-parse HEAD)" = "689198d9c249a966a0abab6415ae8668efb512d9"

git clone --branch v0.1.4 --depth 1 https://github.com/jlov7/damn-vulnerable-agent-asset-corpus
cd damn-vulnerable-agent-asset-corpus
test "$(git rev-parse HEAD)" = "e90a76daf9107871d1ff6a2d7c438d2b92709e53"
uv venv
source .venv/bin/activate
uv pip install -r runner/requirements.txt
AAC_VERIFIER_PATH=../agent-assurance-case/verifier/verify.py python runner/verify_fixtures.py
```

Expected final line:

```text
DVAAC: all fixtures conform.
```

Validate a third-party scorecard against the release validator:

```bash
python runner/validate_scorecard.py path/to/scorecard.json
```

Expected output for a structurally valid scorecard:

```text
DVAAC scorecard: valid submission.
```

From current `main`, reviewers can run the executable release-fingerprint verifier. It clones the immutable DVAAC and AAC release tags into a temporary directory, checks the exact commits, verifies both signed tags with the public release-signing key, runs corpus conformance, runs scorecard-validator tests when present, checks pytest collection safety, downloads the published release assets, verifies their GitHub asset digests, checks the archive sidecar, extracts the signed-AAC archive safely, and verifies the inner `SHA256SUMS` file:

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
