# Fixture 16: Accepted Critical Risk

This fixture checks that accepted critical risk is still visible in the assurance case and does not collapse into a clean pass. The expected AAC uses `assurance_level: strict` so the signed approval path is mandatory under the AAC verifier. The approval is synthetic and local to the fixture.

Expected result: `hold`.

Coverage expectation:

- static-declared: catch
- static-extended: catch
- trace-aware: catch
