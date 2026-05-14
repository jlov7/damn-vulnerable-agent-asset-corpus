# Fixture 07: Low Missing Owner Metadata

This fixture exercises a `low` metadata-quality finding. The skill is harmless, but its manifest leaves ownership unresolved.

Expected result: `pass` with one low finding.

Coverage expectation:

- static-declared: catch
- static-extended: catch
- trace-aware: catch
