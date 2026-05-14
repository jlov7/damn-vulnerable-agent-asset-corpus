# Fixture 05: Shadow Skill From Trace

This fixture is trace-aware only. The checked artifact is a minimal OTel-style JSONL trace showing a runtime-installed shadow skill that was not present in the declared release inventory.

Expected result: `hold`.

Coverage expectation:

- static-declared: miss
- static-extended: miss
- trace-aware: catch

No fixture code is executable. The trace is evidence data only.
