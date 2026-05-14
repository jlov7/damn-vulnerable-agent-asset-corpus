# Fixture 08: Info Local-Only Skill

This fixture exercises an `info` finding. The skill explicitly declares local-only operation and no tool use, so a scanner can emit an informational release note without changing the verdict.

Expected result: `pass` with one info finding.

Coverage expectation:

- static-declared: catch
- static-extended: catch
- trace-aware: catch
