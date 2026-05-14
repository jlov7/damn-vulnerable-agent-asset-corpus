# License

DVAAC is dual-licensed.

## Specification text, documentation, fixture content, and mappings

Licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)**.
https://creativecommons.org/licenses/by/4.0/

You may share and adapt this material for any purpose, including commercial, provided you give appropriate credit and indicate any changes.

This includes every file under `fixtures/**`, including fixture test files. Those tests are dataset content, not runner test scaffolding.

## Runner code and machine-readable schemas

Licensed under **Apache License 2.0**.
https://www.apache.org/licenses/LICENSE-2.0

This includes `runner/**`, `Makefile`, `corpus.manifest.schema.json`, `scorecard-template.schema.json`, and future tests for the runner itself.

## What "attribution" means in practice

When citing DVAAC in a paper, blog post, vendor comparison, or standards-body submission, please use the citation form in `CITATION.cff` and include the Zenodo DOI once minted.

When using individual fixtures (the vulnerable input artifacts) in your own scanner test suite, please retain the DVAAC fixture identifier (e.g. `dvaac/01-clean-declared-skill`) in your output so users can cross-reference your scanner's behaviour against the corpus.

## Independence

This corpus is published as an independent research artifact. It is not affiliated with or endorsed by Anthropic, OpenAI, OWASP, NIST, CSA, or the Linux Foundation. References to those organizations and their published materials are descriptive, not endorsements.
