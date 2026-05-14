---
name: format-text
version: 1.0.0
description: Reformat a block of text into Markdown with consistent heading levels.
scope:
  - text:read
  - text:write
---

# format-text

Use this skill when the user asks for a text block to be reformatted into clean Markdown.

## When to invoke

Invoke when the user pastes raw text and asks for any of the following:

- "make this Markdown"
- "fix the heading levels"
- "clean up this formatting"

## Behaviour

1. Read the block of text the user provided.
2. Normalize heading levels so the first non-blank line becomes `##` and subsequent visible headings descend consistently.
3. Convert bullet markers to `-`.
4. Return the reformatted text. Do not summarise, expand, or rewrite content.

## Out of scope

Do not invoke this skill for anything other than text reformatting. Do not call network tools, write files, or read environment variables.
