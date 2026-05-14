# Fixture 06: Medium Overbroad Tool Scope

This fixture exercises a nonblocking `medium` finding. The declared skill asks for broad filesystem access even though its stated task only needs a single output directory.

Expected result: `pass` with one medium finding.

Coverage expectation:

- static-declared: catch
- static-extended: catch
- trace-aware: catch
