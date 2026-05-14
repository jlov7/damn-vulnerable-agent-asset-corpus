# Fixture 13: Secret Exfiltration Via Allowed Tool

This fixture shows a malicious instruction that uses a declared network tool rather than an undeclared capability. The fixture contains only text; no network call is made.

Expected result: `hold`.

Coverage expectation:

- static-declared: catch
- static-extended: catch
- trace-aware: catch
