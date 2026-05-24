# External Validation Guide

This guide defines how third parties should critique DVAAC or submit scanner results without overstating what the corpus proves.

## Release Under Review

- Repository: <https://github.com/jlov7/damn-vulnerable-agent-asset-corpus>
- Release: `v0.1.3`
- Release commit: `80d9f3ae8f80af273ce311a0b5071cc42d55c8c4`
- DOI: <https://doi.org/10.5281/zenodo.20345025>
- Pinned AAC verifier: `v0.2-candidate.6`
- Pinned AAC verifier commit: `a51c7bd4a2de326333b149ad321785a276376cfa`

This file is a living validation guide on `main`. For an immutable corpus target, use the release tag and DOI above.

## Fast Verification Path

```bash
mkdir dvaac-review
cd dvaac-review
git clone --branch v0.2-candidate.6 --depth 1 https://github.com/jlov7/agent-assurance-case
test "$(git -C agent-assurance-case rev-parse HEAD)" = "a51c7bd4a2de326333b149ad321785a276376cfa"

git clone --branch v0.1.3 --depth 1 https://github.com/jlov7/damn-vulnerable-agent-asset-corpus
cd damn-vulnerable-agent-asset-corpus
uv venv
source .venv/bin/activate
uv pip install -r runner/requirements.txt
AAC_VERIFIER_PATH=../agent-assurance-case/verifier/verify.py python runner/verify_fixtures.py
```

Expected final line:

```text
DVAAC: all fixtures conform.
```

The conformance runner validates the corpus. It is not a scanner and it does not execute fixture payloads.

## Current External Validation Status

As of 2026-05-24, this repository has no accepted third-party scanner submissions recorded in-tree.

| Source | Scanner | Version | Claimed detector class | Status |
|---|---|---:|---|---|
| none yet | none yet | n/a | n/a | no accepted external result |

This is intentional claim discipline. DVAAC is ready to receive independent results, but a DOI-backed release is not the same thing as independent validation.

## Valid Scanner Result Submission

A useful result submission should include:

- scanner name, version, commit, and release URL if public;
- detector class claimed: `static-declared`, `static-extended`, or `trace-aware`;
- exact DVAAC release tag or commit tested;
- exact AAC verifier tag or commit used if AAC output is generated or checked;
- operating system, runtime, and command line used;
- full `scorecard-template.json` with every fixture represented;
- per-fixture emitted finding IDs, categories, severities, and evidence references;
- line numbers, file paths, or trace IDs sufficient for a reviewer to recognize the same finding;
- false-positive treatment for clean fixtures;
- notes for misses or intentionally unsupported detector classes.

If a scanner claims a detector class, it should pass every fixture whose `minimum_detector_class` is that class or weaker. DVAAC does not award partial credit at the fixture level.

## What A Passing Result Means

A passing DVAAC result can support a narrow claim:

> This scanner covers the DVAAC v0.1.3 fixture classes for the detector class it claims.

It does not prove:

- universal agent safety;
- product safety;
- statistical vulnerability coverage;
- legal or regulatory compliance;
- endorsement by the DVAAC maintainer;
- endorsement by any employer, client, standards body, or lab.

## Useful Critique

Good critiques are specific enough to become a fixture, test, schema change, or README correction:

- a fixture is unsafe to inspect or violates `SECURITY.md`;
- expected findings do not match the artifact evidence;
- the fixture taxonomy is unclear or mixes threat classes;
- an expected verdict is too strict or too permissive;
- a scanner can game the corpus without detecting the real failure mode;
- the scorecard template omits data needed to reproduce a result;
- a fixture should move between `static-declared`, `static-extended`, and `trace-aware`;
- a missing threat class should be added as a new fixture.

Security-sensitive runner issues should be reported privately according to `SECURITY.md`. Ordinary benchmark critique and scanner results can be opened with the [scanner result issue form](https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/issues/new?template=scanner-result.yml) or as public pull requests.
