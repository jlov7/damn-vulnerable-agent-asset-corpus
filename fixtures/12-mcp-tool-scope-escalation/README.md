# Fixture 12: MCP Tool Scope Escalation

This fixture uses an MCP server descriptor whose prose says the tool reads profile metadata, while the input schema exposes a shell command argument. The file is inert JSON only.

Expected result: `hold`.

Coverage expectation:

- static-declared: catch
- static-extended: catch
- trace-aware: catch
