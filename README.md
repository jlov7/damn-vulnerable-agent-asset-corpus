<div align="center">

<img src="assets/dvaac-logo.svg" width="620" alt="Damn Vulnerable Agent Asset Corpus">

# Damn Vulnerable Agent Asset Corpus

**A compact, runnable conformance corpus for agent-asset assurance tools — it checks corpus consistency, not scanner accuracy.**

[![CI](https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/actions/workflows/ci.yml/badge.svg)](https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/actions/workflows/ci.yml)
[![Release fingerprints](https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/actions/workflows/release-fingerprints.yml/badge.svg)](https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/actions/workflows/release-fingerprints.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/jlov7/damn-vulnerable-agent-asset-corpus/badge)](https://scorecard.dev/viewer/?uri=github.com/jlov7/damn-vulnerable-agent-asset-corpus)
![Status](https://img.shields.io/badge/status-v0.1.5-2f6f9f)
![Fixtures](https://img.shields.io/badge/fixtures-16-0f766e)
![AAC](https://img.shields.io/badge/AAC-v0.2--candidate.7-111827)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20379817.svg)](https://doi.org/10.5281/zenodo.20379817)
![License](https://img.shields.io/badge/license-CC--BY--4.0%20%2B%20Apache--2.0-blue)

[Companion AAC verifier](https://github.com/jlov7/agent-assurance-case) · [Evaluation protocol](docs/EVALUATION_PROTOCOL.md) · [Scanner integration](docs/SCANNER_INTEGRATION_GUIDE.md) · [External validation](docs/EXTERNAL_VALIDATION.md) · [Release fingerprints](docs/RELEASE_FINGERPRINTS.md) · [Security posture](SECURITY_POSTURE.md) · [Security insights](security-insights.yml) · [Repository posture](repository-posture.json) · [Runtime dependency SBOM](sbom/runtime-requirements.cdx.json) · [Runtime dependency lock](runner/requirements.lock.txt) · [Security policy](SECURITY.md)

</div>

DVAAC ships deliberately vulnerable and deliberately clean agentic AI release fixtures, expected findings, and Agent Assurance Case (AAC) templates that are verified against the AAC v0.2 reference verifier. The runner validates corpus truth; it is not a scanner and it does not import or execute fixture payloads.

This release is pinned to AAC `v0.2-candidate.8` at commit `936885583a49dfd06fd11ce45c8ee82330f1007d`.

The citable artifact is the signed, DOI-archived release tag
[`v0.1.5`](https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/releases/tag/v0.1.5),
not the tip of `main`. `main` may contain unreleased changes that are not part
of the archived release; cite or audit the tagged commit unless you are
deliberately reviewing in-progress work.

## What This Is / What This Is Not

For a one-page statement of scope and the boundary between what is self-verified
and what has been independently reviewed, read
[VALIDATION_BOUNDARY.md](VALIDATION_BOUNDARY.md). In short: DVAAC is a small,
self-consistent conformance corpus and a runner that checks the corpus ground
truth; it is **not** a statistical benchmark, **not** a scanner, and a passing
result certifies corpus consistency, not scanner accuracy or agent safety. It is
self-verified and not yet independently validated; see
[docs/EXTERNAL_VALIDATION.md](docs/EXTERNAL_VALIDATION.md).

## Why This Exists

Agent-asset scanners make different claims about what they detect: skill poisoning, MCP scope escalation, memory poisoning, trace-only shadow behavior, and more. Without a shared fixture corpus, those claims are hard to compare.

DVAAC is a small, reproducible conformance corpus for those claims. Each fixture has vulnerable or clean input artifacts, expected scanner findings, and an expected AAC template. The runner verifies that the ground truth is internally consistent before anyone uses it to score a scanner.

DVAAC is **not** a statistical benchmark, a scanner, a vulnerability database, or an assurance guarantee. With 16 hand-authored fixtures it is a deliberately small, non-representative sample. A scanner that passes DVAAC has demonstrated coverage of these specific fixture classes, not universal agent safety.

## What Ships In Each Fixture

Each `fixtures/NN-name/` directory contains:

- source artifacts such as `SKILL.md`, MCP descriptors, A2A cards, memory seeds, scripts, or trace evidence;
- `README.md` describing the threat and detector expectations;
- `expected-findings.json` listing findings a conformant scanner should emit;
- `expected-aac.json`, an AAC template with placeholder `content_hash` and `signature`;
- local evidence files when the AAC references detector output, AIBOMs, or trace artifacts.

The runner signs AAC templates at conformance time with the AAC demo key. That signature is a plumbing check, not an issuer-trust claim. Production scanners should sign AACs with their own issuer keys.

## Trust Model

DVAAC's release claim is deliberately narrow:

- every fixture's expected outputs validate against the DVAAC schemas;
- local source, evidence, excerpt, and policy-input digests are recomputed;
- expected findings and AAC findings are checked for exact ID, category, severity, title, description, and subject consistency;
- the AAC template is demo-signed at conformance time and verified by the pinned AAC reference verifier;
- release artifacts generated by `make write-signed` include a demo-signed `RELEASE-MANIFEST.json` that binds signed AACs to the corpus manifest, scorecard template, and schemas.

The demo key is not a trust anchor. It proves verifier plumbing and reproducibility, not author identity.

## Fixture Matrix

| ID | Fixture | Threat class | Minimum detector class | Expected verdict |
|---:|---|---|---|---:|
| 01 | `clean-declared-skill` | Baseline clean skill | static-declared | PASS |
| 02 | `skill-md-prompt-injection` | Skill prompt injection | static-declared | HOLD |
| 03 | `hidden-test-payload` | Developer execution surface | static-extended | FAIL |
| 04 | `aac-core-clean-skill` | Portable AAC baseline | static-declared | PASS |
| 05 | `shadow-skill-from-trace` | Runtime shadow skill | trace-aware | HOLD |
| 06 | `medium-overbroad-tool-scope` | Overbroad tool scope | static-declared | PASS |
| 07 | `low-missing-owner-metadata` | Metadata quality | static-declared | PASS |
| 08 | `info-local-only-skill` | Informational detector note | static-declared | PASS |
| 09 | `cross-file-logic-split` | Cross-file behavior split | static-extended | HOLD |
| 10 | `skill-drift` | Runtime instruction drift | static-extended | HOLD |
| 11 | `dynamic-remote-fetch` | Remote instruction fetch | static-declared | HOLD |
| 12 | `mcp-tool-scope-escalation` | MCP tool scope escalation | static-declared | HOLD |
| 13 | `secret-exfiltration-via-allowed-tool` | Allowed-tool exfiltration | static-declared | HOLD |
| 14 | `memory-poisoning` | Poisoned memory seed | static-extended | HOLD |
| 15 | `a2a-delegation-misuse` | Cross-agent authority misuse | static-declared | HOLD |
| 16 | `accepted-critical-risk` | Accepted critical risk semantics | static-declared | HOLD |

Detector classes are defined in [TAXONOMY.md](TAXONOMY.md). Machine-readable fixture metadata lives in [corpus.manifest.json](corpus.manifest.json).

## Quick Start

From a checkout of this repository:

```bash
git clone --branch v0.2-candidate.8 --depth 1 https://github.com/jlov7/agent-assurance-case ../agent-assurance-case
test "$(git -C ../agent-assurance-case rev-parse HEAD)" = "936885583a49dfd06fd11ce45c8ee82330f1007d"
uv venv
source .venv/bin/activate
uv pip install -r runner/requirements.txt
AAC_VERIFIER_PATH=../agent-assurance-case/verifier/verify.py python3 runner/verify_fixtures.py
```

This command path validates the corpus and does not execute fixture payload code. Install `uv` first if it is not already available: <https://docs.astral.sh/uv/>.

Expected final line:

```text
DVAAC: all fixtures conform.
```

To run the pytest collection-safety gate or the test suite, also install the
development dependencies (they add `pytest` and `hypothesis`):

```bash
uv pip install -r runner/requirements-dev.txt
```

If you have `make` (and the sibling AAC verifier checked out as shown in the
clone step above, or `AAC_VERIFIER_PATH` set):

```bash
make install          # installs both runtime and dev dependencies
make verify           # resolves the AAC verifier from ../agent-assurance-case[-spec]
make pytest-safety
```

Run the full publication-readiness gate:

```bash
./VERIFY-PUBLICATION-READY.sh
```

Verify the published release fingerprint from current `main`:

```bash
python3 scripts/verify_release_fingerprints.py
```

That command checks the immutable DVAAC and AAC release tags and commits, both
signed tags, corpus conformance, scorecard-validator tests, pytest collection
safety, public release asset digests, checksum files, and the documented absence
of GitHub artifact attestations for the already-published `v0.1.5` assets.

## What The Runner Checks

`runner/verify_fixtures.py` verifies the corpus itself. It does not detect vulnerabilities.

The runner checks:

- fixture layout;
- duplicate-key and nonstandard-number rejection for JSON files;
- `expected-findings.json`, manifest, and scorecard schema conformance;
- exact finding ID/category/severity/title/description/subject consistency between expected findings and AAC templates;
- local asset digests;
- local evidence-file and line-excerpt digests;
- policy input hashes;
- symlink rejection and fixture-local path containment;
- AAC verifier API compatibility and demo-key constants;
- AAC schema/profile/verdict/signature verification through the AAC reference verifier.

To generate demo-signed AACs for release/auditor review:

```bash
make write-signed
```

This writes `dist/signed-aac/*.json`, `dist/signed-aac/RELEASE-MANIFEST.json`, and `dist/signed-aac/SHA256SUMS`. The release manifest is demo-signed and binds the signed AACs to the corpus manifest, scorecard template, and runner schemas that define the release; the checksum file covers those artifacts. `dist/` is intentionally ignored by Git; attach those generated artifacts to a release or archival deposit when needed.

## Scanner Author Workflow

1. Run your scanner against each fixture’s source artifacts.
2. Compare emitted findings against `expected-findings.json`.
3. If your scanner emits AAC, compare its case against `expected-aac.json`.
4. Publish results using [scorecard-template.json](scorecard-template.json).
5. Validate the filled scorecard with the current-`main` validator for ledger consideration: `make validate-scorecard SCORECARD=path/to/scorecard.json`. The `v0.1.5` release checkout validator remains available with `python3 runner/validate_scorecard.py path/to/scorecard.json`, but current `main` may include stricter intake checks.
6. State the detector class you claim: `static-declared`, `static-extended`, or `trace-aware`.

DVAAC does not award partial credit. A fixture is covered only when the expected category, severity, and evidence are represented accurately enough for a reviewer to recognize the same finding.

For third-party scanner submissions and critique boundaries, see [Scanner Integration](docs/SCANNER_INTEGRATION_GUIDE.md), [External Validation](docs/EXTERNAL_VALIDATION.md), the [review recipes](docs/EXTERNAL_VALIDATION.md#review-recipes), the [Scorecard Field Guide](docs/SCORECARD_FIELD_GUIDE.md), the [corpus critique template](corpus-critique-template.json), the [Validation Ledger](docs/VALIDATION_LEDGER.md), the [Release Fingerprints](docs/RELEASE_FINGERPRINTS.md), and the current [DVAAC v0.1.5 scanner/corpus critique thread](https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/issues/1).

## Safety

DVAAC fixtures are intentionally vulnerable. Do not execute fixture payloads. The conformance runner does not import or execute fixture code. Read [SECURITY.md](SECURITY.md) before running anything beyond the documented verification commands.

The repository includes pytest collection guards and CI checks that block pytest-discoverable fixture payload filenames, but those controls are not a sandbox.

## Mappings

- [OWASP Agentic Skills Top 10 mapping](mappings/owasp-agentic-skills-top-10.md)
- [OWASP MCP Top 10 mapping](mappings/owasp-mcp-top-10.md)
- [AAC v0.2 mapping](mappings/aac-v0.2.md)

These mappings are informative. They are not endorsements by OWASP, CSA, NIST, or any other standards body.

## Repository Structure

```text
fixtures/                  vulnerable and clean corpus fixtures
mappings/                  informative mappings to external taxonomies
docs/                      evaluation, validation, and release-process notes
docs/SCANNER_INTEGRATION_GUIDE.md scanner-author integration path
runner/                    conformance runner and runner schemas
scripts/                   executable release-fingerprint checks
sbom/                      CycloneDX runtime dependency SBOM
runner/requirements.lock.txt hash-pinned resolved runtime dependency closure
VERIFY-PUBLICATION-READY.sh one-command publication-readiness gate
.github/workflows/ci.yml   corpus conformance CI
corpus.manifest.json       machine-readable corpus index
scorecard-template.json    scanner result publication template
TAXONOMY.md                detector-class and threat-surface definitions
SECURITY_POSTURE.md        repository-level security posture and supply-chain signals
SECURITY.md                safe inspection rules
```

## Contributing

Fixture contributions are welcome after publication, but they must preserve DVAAC’s safety envelope: no network activity, no real secret access, no destructive behavior, no persistence, no subprocess spawning, and no symlinks under `fixtures/**`.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full fixture acceptance checklist.

Scanner results and corpus-level critique should go to the current [public validation thread](https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/issues/1). Start from the [review recipes](docs/EXTERNAL_VALIDATION.md#review-recipes) if you want a small, runnable review path. Focused submissions can use the scanner-result or corpus-critique issue forms. Accepted results are tracked in [docs/VALIDATION_LEDGER.md](docs/VALIDATION_LEDGER.md).

## Citation

See [CITATION.cff](CITATION.cff) and [codemeta.json](codemeta.json). Cite the archived release:

> Lovell, J. M. (2026). *Damn Vulnerable Agent Asset Corpus, v0.1.5.* Zenodo. https://doi.org/10.5281/zenodo.20379817.

The v0.1.5 release is archived at <https://doi.org/10.5281/zenodo.20379817>. The superseded `v0.1.3` archive remains available at <https://doi.org/10.5281/zenodo.20345025>, the superseded `v0.1.2` archive remains available at <https://doi.org/10.5281/zenodo.20187301>, and the superseded `v0.1.1` archive remains available at <https://doi.org/10.5281/zenodo.20186918>.

## License

DVAAC is dual-licensed:

- fixtures, documentation, mappings, and corpus content: CC BY 4.0;
- runner code, `Makefile`, and machine-readable schemas: Apache 2.0.

See [LICENSE.md](LICENSE.md).

## Independence Notice

This is personal, independent work by Jason Mark Lovell. It is not authored, sponsored, endorsed, or reviewed by, and does not represent the views of, any employer, client, standards body, or affiliated organization.
