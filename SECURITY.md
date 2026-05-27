# DVAAC Security Policy

DVAAC fixtures are **intentionally vulnerable**. Read this before running anything outside an inspection workflow.

Repository-level security posture and unresolved automated supply-chain signals are summarized in `SECURITY_POSTURE.md`.

## What the fixtures contain

Each fixture under `fixtures/NN-name/` represents one specific failure mode in an agentic AI release. The vulnerable input artifacts — `SKILL.md`, bundled scripts, MCP descriptors, A2A cards, memory seeds, and trace evidence — are deliberately constructed to exercise that failure mode.

## What the conformance runner does NOT do

`runner/verify_fixtures.py` does NOT execute fixture payloads. It only:

1. validates fixture layout and JSON structure;
2. signs the expected AAC template with the AAC reference demo key;
3. recomputes local asset, evidence, source-excerpt, and policy-input digests;
4. asks the AAC v0.2 reference verifier to verify the signed AAC.

The runner never imports, exec's, or otherwise runs code from `fixtures/NN-name/skill/`. It also refuses symlinks anywhere under fixture trees.

## What you MUST NOT do

- **Do not run** `pytest`, `python3 -m unittest`, IDE auto-test-discovery, or any other test runner against the contents of `fixtures/NN-name/skill/tests/`. The repository includes top-level pytest collection guards and fixture payload demo files avoid `test_*.py` names, but those safeguards are not a sandbox.
- **Do not set** `DVAAC_DANGER_RUN_PAYLOAD=1` unless you are inside a disposable sandbox and intentionally demonstrating fixture 03's guarded payload path.
- **Do not run** `python3 fixtures/NN-name/skill/scripts/*.py` outside a disposable sandbox.
- **Do not** copy fixture skills into a real Claude, Codex, Cursor, or other agent runtime.

The checked-in payloads in the current corpus are deliberately safe — non-network, no real secrets, local-only — and future payloads must stay within the same safety envelope. If a fork changes fixture payload text, those safety properties must be re-reviewed; DVAAC is inspectable source, not a sandbox. Treat the entire `fixtures/*/` tree as untrusted.

## What DVAAC payloads are allowed to do

Contributors adding new fixtures MUST keep payloads:

- **non-network** — no outbound HTTP, DNS, or other connections;
- **no real-secret access** — no reading `~/.ssh/`, `~/.aws/`, env vars containing real credentials, or any path likely to contain production secrets;
- **local-sink only** — if the payload demonstrates a side effect, create a new regular file under `/tmp/dvaac_*` with an obviously-fake marker like `DVAAC_FAKE_SECRET=demo-only-do-not-use`;
- **non-destructive** — no deletion, overwrite of existing files, permission changes, persistence/autostart writes, shell execution, subprocess spawning, or writes through symlinks;
- **no symlinks** — fixtures MUST NOT contain checked-in symlinks anywhere under `fixtures/**`;
- **deterministic** — the same payload should produce the same observable effect every run;
- **inspectable** — every payload behaviour MUST be documented in the fixture's README so reviewers can confirm what the payload does without executing it.

PRs that add aggressive, network-touching, secret-reading, destructive, persistence-seeking, subprocess-spawning, or non-deterministic payloads will be rejected.

## Reporting issues

Preferred private reporting channel for runner bugs that could execute fixture payloads:
<https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/security/advisories/new>.

If you discover that a DVAAC payload does something the fixture README does not declare — for example, a payload that touches the network when the README claims it does not — open an issue with the label `security`. This is a payload-correctness bug, not a vulnerability in a third-party system, and it will be triaged within seven days.

If you discover a bug in the **runner** (`runner/verify_fixtures.py`) that allows the runner itself to execute fixture payloads, please email the maintainer privately before opening a public issue. Treat that as a confidentiality-7-day responsible disclosure window.

## Why this policy exists

A repository of intentionally vulnerable agent-asset bundles is a useful research artifact and a foot-gun. The same package that lets a scanner author measure their coverage can, if mishandled, run code on a contributor's machine. This policy keeps the corpus safe to inspect, fork, and cite — and explicit about the boundary between inspection and execution.
