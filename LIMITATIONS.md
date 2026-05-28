# Limitations

DVAAC is deliberately narrow. These are the boundaries a reviewer or adopter
should keep in mind.

- **Small, non-representative sample.** DVAAC ships 16 hand-authored fixtures.
  It is a conformance corpus, not a statistical benchmark. Coverage of these
  fixture classes does not generalize to a measured detection rate or to
  universal agent safety.
- **Ground truth only, no detection logic.** DVAAC ships expected findings and
  expected Agent Assurance Case (AAC) templates. It does not ship a scanner. A
  scanner author runs their own detector against each fixture and compares.
  Expected failure mode: a weak detector can still be scored against an
  internally consistent corpus.
- **Corpus consistency, not scanner accuracy.** A passing `make verify` proves
  the corpus's own ground truth is self-consistent and that the AAC templates
  verify against the reference verifier. It does **not** validate any scanner.
- **Demo key is not a trust anchor.** The runner demo-signs AAC templates at
  conformance time to exercise verifier plumbing and reproducibility. It does
  not assert author or issuer identity. Production scanners must sign with their
  own issuer keys.
- **Checked-in AAC templates carry placeholder hash/signature.** `expected-aac.json`
  files ship with placeholder `content_hash` and `signature`; the runner
  computes and verifies real values at conformance time. DVAAC does not ship
  statically signed AACs.
- **Cross-repository dependency.** Conformance requires the AAC v0.2 reference
  verifier from the sibling [`agent-assurance-case`](https://github.com/jlov7/agent-assurance-case)
  repository (or a local `agent-assurance-case-spec` checkout). The corpus is
  pinned to a specific AAC commit; see the README.
- **Not independently validated.** No third-party scanner result or corpus
  critique has been accepted yet. Status is tracked in
  [docs/VALIDATION_LEDGER.md](docs/VALIDATION_LEDGER.md) and
  [docs/EXTERNAL_VALIDATION.md](docs/EXTERNAL_VALIDATION.md).
- **Mappings are informative.** The OWASP/AAC mappings under `mappings/` are not
  endorsements by OWASP, CSA, NIST, or any standards body.
- **Fixtures are intentionally vulnerable and are not sandboxed.** The runner
  never imports or executes fixture payloads, and CI guards block
  pytest-discoverable payload filenames, but those controls are not a sandbox.
  Read [SECURITY.md](SECURITY.md) before running anything beyond the documented
  commands.
