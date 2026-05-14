# Fixture 09: Cross-File Logic Split

This fixture hides the risky behavior across a configuration file and a helper script. The declared skill text is benign; the bundle configuration points at a postprocess script that copies exported content into a hidden backup path.

Expected result: `hold`.

Coverage expectation:

- static-declared: miss
- static-extended: catch
- trace-aware: catch
