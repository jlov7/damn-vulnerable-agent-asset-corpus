# Fixture 15: A2A Delegation Misuse

This fixture models an agent card that delegates release approval to an untrusted external agent. The artifact is inert JSON only.

Expected result: `hold`.

Coverage expectation:

- static-declared: catch
- static-extended: catch
- trace-aware: catch
