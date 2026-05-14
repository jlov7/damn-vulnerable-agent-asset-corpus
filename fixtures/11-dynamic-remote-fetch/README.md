# Fixture 11: Dynamic Remote Fetch

This fixture declares that runtime instructions should be fetched from a remote URL before every run. The URL is inert documentation data; the fixture is meant to test whether scanners flag dynamic remote instruction loading.

Expected result: `hold`.

Coverage expectation:

- static-declared: catch
- static-extended: catch
- trace-aware: catch
