# Fixture 10: Skill Drift

This fixture models drift between the declared release manifest and the runtime override file shipped in the bundle. The primary skill text is clean, but the bundle also contains an override instruction that changes runtime behavior.

Expected result: `hold`.

Coverage expectation:

- static-declared: miss
- static-extended: catch
- trace-aware: catch
