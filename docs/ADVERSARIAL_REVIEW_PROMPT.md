# Adversarial Review Prompt

Use this prompt with Claude Code, Codex, or another capable local-code reviewer before publication.

```markdown
You are an adversarial security reviewer. Review the DVAAC repository as a pre-publication benchmark artifact that will be cited publicly and scrutinized by scanner vendors, auditors, and standards-body contributors.

Repository:

`<path-to-dvaac-checkout>`

AAC verifier:

`<path-to-agent-assurance-case>/verifier/verify.py`

Do not execute fixture payload code. Do not import files under `fixtures/**` as Python modules.

Run:

```bash
make verify
make pytest-safety
make write-signed
```

Then read:

- `README.md`
- `SECURITY.md`
- `TAXONOMY.md`
- `corpus.manifest.json`
- `scorecard-template.json`
- `runner/verify_fixtures.py`
- `fixtures/**`
- `mappings/**`
- `docs/**`
- the AAC verifier and schema

Find trust-critical bugs, correctness bugs, fixture accuracy problems, safety foot-guns, documentation overclaims, adoption blockers, and enhancement opportunities.

For each finding, include:

- severity: P0/P1/P2/P3
- file and line number
- observation
- why it matters
- exact suggested fix

Also perform at least one negative tamper test on a copy of the repo under `/tmp` and prove that the runner fails.
```
