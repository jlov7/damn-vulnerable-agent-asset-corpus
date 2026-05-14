# DVAAC Threat Taxonomy

This taxonomy organizes DVAAC fixtures by *where the threat lives* and *which class of detector is expected to catch it*. It is descriptive, not prescriptive.

## Detector classes

DVAAC distinguishes between three detector classes. The taxonomy uses these terms throughout.

| Class | What it inspects | Examples |
|-------|------------------|----------|
| **Static-declared** | Files declared as skill/tool assets at rest: `SKILL.md`, manifest, declared scripts, declared scopes. | Manifest and declared-source scanning. |
| **Static-extended** | Files in the asset bundle that are not the declared instruction surface: test files, build scripts, fixtures, optional resources, README examples. | Whole-bundle static scanning. |
| **Trace-aware** | Runtime execution evidence: OTel GenAI spans, tool-call sequences, memory mutations, network destinations, side effects, A2A delegations. | Trace and side-effect analysis. |

The differentiation argument for an agent-assurance product is roughly: *what fraction of DVAAC fixtures does it cover, and at which detector class*.

## Threat surfaces

| Surface | Description | Fixtures |
|---------|-------------|----------|
| **Instruction layer** | Natural-language content in `SKILL.md` or equivalent that contains prompt injection, exfiltration directives, remote instruction loading, or accepted-risk directives. | `02-skill-md-prompt-injection`, `11-dynamic-remote-fetch`, `13-secret-exfiltration-via-allowed-tool`, `16-accepted-critical-risk` |
| **Developer execution surface** | Files in the bundle that execute when a developer runs ordinary build/test workflows but that are not part of the agent's runtime instruction set. | `03-hidden-test-payload`, `09-cross-file-logic-split` |
| **Tool/scope surface** | MCP tool definitions, declared scopes, capability requests, approval gates, and the implicit trust boundary between skill and tool. | `06-medium-overbroad-tool-scope`, `12-mcp-tool-scope-escalation` |
| **Runtime behaviour surface** | What the agent actually does at execution time, observed via traces, including shadow patterns that have no declared skill. | `05-shadow-skill-from-trace`, `10-skill-drift` |
| **Delegation surface** | Cross-agent (A2A) authority transfer: agent cards, delegation receipts, scope of delegated authority, audit trail of cross-agent decisions. | `15-a2a-delegation-misuse` |
| **Memory surface** | Persistent state across agent sessions: poisoned memory entries, instruction smuggling via stored context, cross-tenant leakage. | `14-memory-poisoning` |

## Verdict semantics in this corpus

DVAAC uses the AAC v0.2 verdict semantics:

- **PASS** — release MAY proceed.
- **HOLD** — release MUST NOT proceed automatically; MAY proceed after remediation, approval, or risk acceptance.
- **FAIL** — release MUST NOT proceed.

A fixture's `expected-aac.json` carries the verdict a conformant scanner should emit *for the case as a whole*. Individual findings carry their own severity. Verdict computation rules are defined normatively in AAC v0.2 SPEC §5.

## How threat classes map to detector classes

| Threat surface | Static-declared | Static-extended | Trace-aware |
|----------------|:---------------:|:---------------:|:-----------:|
| Instruction layer | YES | YES | YES |
| Developer execution surface | rarely | YES | YES |
| Tool/scope surface | partial | YES | YES |
| Runtime behaviour surface | NO | NO | YES |
| Delegation surface | YES when declared | YES | YES |
| Memory surface | rarely | YES when bundled | YES |

The "YES" rows are the cases where a given detector class is *expected* to catch the threat. Empty cells mean the detector class is structurally unable to see the threat.

DVAAC's main contribution is making these distinctions runnable: a scanner author can cite specific fixture IDs to claim coverage, and a buyer can verify those claims independently.

## Naming convention

Fixtures are numbered `NN-slug` where `NN` is a two-digit ordinal and `slug` is a short kebab-case name. The number is for ordering only; it does not imply severity, priority, or canonical ID.

Finding categories use kebab-case identifiers prefixed by surface, e.g. `skill-prompt-injection`, `skill-developer-execution-surface`, `mcp-scope-creep`. These are stable across fixtures so scanners can claim per-category coverage.

## What this taxonomy is not

- It is not a CVE taxonomy. DVAAC fixtures are illustrative, not bug reports against specific real systems.
- It is not a risk-scoring framework. AIVSS and similar systems are out of scope.
- It is not a compliance framework. Compliance regimes (EU AI Act, ISO 42001) may consume DVAAC outputs as evidence candidates; DVAAC does not certify compliance.
