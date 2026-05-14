<div align="center">

<img src="assets/dvaac-logo.svg" width="620" alt="Damn Vulnerable Agent Asset Corpus">

# Damn Vulnerable Agent Asset Corpus

**A compact, runnable benchmark for agent-asset assurance tools.**

[![CI](https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/actions/workflows/ci.yml/badge.svg)](https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/actions/workflows/ci.yml)
![Status](https://img.shields.io/badge/status-v0.1.1%20candidate-2f6f9f)
![Fixtures](https://img.shields.io/badge/fixtures-16-0f766e)
![AAC](https://img.shields.io/badge/AAC-v0.2--candidate.5-111827)
![License](https://img.shields.io/badge/license-CC--BY--4.0%20%2B%20Apache--2.0-blue)

[Companion AAC verifier](https://github.com/jlov7/agent-assurance-case) · [Evaluation protocol](docs/EVALUATION_PROTOCOL.md) · [Security policy](SECURITY.md)

</div>

DVAAC ships deliberately vulnerable and deliberately clean agentic AI release fixtures, expected findings, and Agent Assurance Case (AAC) templates that are verified against the AAC v0.2 reference verifier.

## Why This Exists

Agent-asset scanners make different claims about what they detect: skill poisoning, MCP scope escalation, memory poisoning, trace-only shadow behavior, and more. Without a shared fixture corpus, those claims are hard to compare.

DVAAC is a small, reproducible benchmark for those claims. Each fixture has vulnerable or clean input artifacts, expected scanner findings, and an expected AAC template. The runner verifies that the ground truth is internally consistent before anyone uses it to score a scanner.

DVAAC is **not** a scanner, a vulnerability database, or a statistical assurance guarantee. A scanner that passes DVAAC has demonstrated coverage of these fixture classes, not universal agent safety.

## What Ships In Each Fixture

Each `fixtures/NN-name/` directory contains:

- source artifacts such as `SKILL.md`, MCP descriptors, A2A cards, memory seeds, scripts, or trace evidence;
- `README.md` describing the threat and detector expectations;
- `expected-findings.json` listing findings a conformant scanner should emit;
- `expected-aac.json`, an AAC template with placeholder `content_hash` and `signature`;
- local evidence files when the AAC references detector output, AIBOMs, or trace artifacts.

The runner signs AAC templates at conformance time with the AAC demo key. That signature is a plumbing check, not an issuer-trust claim. Production scanners should sign AACs with their own issuer keys.

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
git clone --branch v0.2-candidate.5 --depth 1 https://github.com/jlov7/agent-assurance-case ../agent-assurance-case
python3 -m venv .venv
source .venv/bin/activate
pip install -r runner/requirements.txt
AAC_VERIFIER_PATH=../agent-assurance-case/verifier/verify.py python runner/verify_fixtures.py
```

Expected final line:

```text
DVAAC: all fixtures conform.
```

If you have `make`:

```bash
make install
make verify
make pytest-safety
```

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
- AAC verifier API compatibility and demo-key constants;
- AAC schema/profile/verdict/signature verification through the AAC reference verifier.

To generate demo-signed AACs for release/auditor review:

```bash
make write-signed
```

This writes `dist/signed-aac/*.json` plus `dist/signed-aac/SHA256SUMS`. `dist/` is intentionally ignored by Git; attach those generated artifacts to a release or archival deposit when needed.

## Scanner Author Workflow

1. Run your scanner against each fixture’s source artifacts.
2. Compare emitted findings against `expected-findings.json`.
3. If your scanner emits AAC, compare its case against `expected-aac.json`.
4. Publish results using [scorecard-template.json](scorecard-template.json).
5. State the detector class you claim: `static-declared`, `static-extended`, or `trace-aware`.

DVAAC does not award partial credit. A fixture is covered only when the expected category, severity, and evidence are represented accurately enough for a reviewer to recognize the same finding.

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
fixtures/                  vulnerable and clean benchmark fixtures
mappings/                  informative mappings to external taxonomies
runner/                    conformance runner and runner schemas
.github/workflows/ci.yml   corpus conformance CI
corpus.manifest.json       machine-readable corpus index
scorecard-template.json    scanner result publication template
TAXONOMY.md                detector-class and threat-surface definitions
SECURITY.md                safe inspection rules
```

## Contributing

Fixture contributions are welcome after publication, but they must preserve DVAAC’s safety envelope: no network activity, no real secret access, no destructive behavior, no persistence, no subprocess spawning, and no symlinks under `fixtures/**`.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full fixture acceptance checklist.

## Citation

See [CITATION.cff](CITATION.cff). Once a DOI is minted, cite the archived release:

> Lovell, J. (2026). *Damn Vulnerable Agent Asset Corpus, v0.1.1.* Zenodo. https://doi.org/10.5281/zenodo.{DOI}.

## License

DVAAC is dual-licensed:

- fixtures, documentation, mappings, and corpus content: CC BY 4.0;
- runner code, `Makefile`, and machine-readable schemas: Apache 2.0.

See [LICENSE.md](LICENSE.md).

## Independence Notice

This is personal, independent work by Jason Lovell. It is not authored, sponsored, endorsed, or reviewed by, and does not represent the views of, any employer, client, standards body, or affiliated organization.
