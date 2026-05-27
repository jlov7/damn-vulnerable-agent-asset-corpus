# Scanner Integration Guide

This guide is for scanner authors who want to run against DVAAC and produce a
reviewable scorecard. It is not a new scoring system. The normative result
format remains [`scorecard-template.json`](../scorecard-template.json), and
accepted submissions are tracked only in [VALIDATION_LEDGER.md](VALIDATION_LEDGER.md)
after maintainer review.

## Target

- DVAAC release: `v0.1.4`
- DVAAC release commit: `e90a76daf9107871d1ff6a2d7c438d2b92709e53`
- AAC verifier: `v0.2-candidate.7`
- AAC verifier commit: `689198d9c249a966a0abab6415ae8668efb512d9`
- Scorecard template: [`scorecard-template.json`](../scorecard-template.json)
- Field guide: [SCORECARD_FIELD_GUIDE.md](SCORECARD_FIELD_GUIDE.md)
- External validation guide: [EXTERNAL_VALIDATION.md](EXTERNAL_VALIDATION.md)

## Integration Flow

1. Clone the exact DVAAC release or commit under test.
2. Run the DVAAC conformance check to confirm the corpus itself is intact.
3. Run your scanner against each fixture's source artifacts.
4. Map emitted findings to each fixture's `expected-findings.json`.
5. Fill every fixture entry in `scorecard-template.json`.
6. Claim only a detector class your scorecard fully covers.
7. Validate the scorecard.
8. Submit the scorecard, command, environment, and supported claim wording.

The runner validates corpus truth. It is not a scanner and it does not execute
fixture payloads.

## Fixture Inputs

Each fixture under `fixtures/NN-name/` contains the artifacts a scanner should
inspect. Depending on the fixture, these may include:

- declared skill or tool metadata;
- MCP descriptors;
- A2A cards;
- memory seeds;
- local scripts or source files;
- trace evidence under `evidence/`.

Do not execute fixture payloads unless your scanner normally executes untrusted
artifacts inside an appropriate sandbox. DVAAC conformance does not require
execution.

## Detector Class Claim

Do not overclaim detector coverage:

- `static-declared`: the scanner inspects declared instruction or tool surfaces.
- `static-extended`: the scanner reasons across the full checked-in asset
  bundle or non-declared local artifacts.
- `trace-aware`: the scanner uses runtime traces, tool-call sequences, memory
  mutations, or side-effect evidence.

A scorecard claiming a detector class must pass every fixture whose
`minimum_detector_class` is that class or weaker. DVAAC does not award partial
credit at the fixture level. Claim the strongest detector class only when that
full class requirement is satisfied.

If your scanner only covers some fixtures, submit the scorecard as partial
evidence and do not claim detector-class coverage.

## Finding Mapping

A fixture is covered only when the scanner emits the expected finding set with:

- matching finding IDs, categories, and severities;
- enough evidence for a reviewer to identify the same artifact;
- no blocking false positives on clean fixtures;
- notes for misses, unsupported surfaces, or intentional non-detection.

If the scanner uses different rule IDs internally, include both the scanner rule
ID and the DVAAC expected finding ID in the scorecard evidence or notes.

## Scorecard Validation

For validation-ledger candidates, prefer current `main` because it includes the
latest intake checks for scanner source provenance, runnable context, and public
reproducibility:

```bash
make validate-scorecard SCORECARD=path/to/scorecard.json
```

The immutable `v0.1.4` checkout remains useful for validating against the
release-shipped validator:

```bash
python3 runner/validate_scorecard.py path/to/scorecard.json
```

Expected output:

```text
DVAAC scorecard: valid submission.
```

Validator success proves scorecard structure, fixture-level self-consistency,
and, on current `main`, public run provenance. It does not prove that scanner
evidence is semantically correct, that the scanner is safe, or that the scanner
has general agent-security coverage.

## Submission Packet

A useful public submission includes:

- scanner name, version, commit, and release URL if public;
- exact DVAAC release or commit tested;
- exact AAC verifier release or commit used, if AAC output is generated or
  checked;
- operating system, runtime, scanner command, and relevant configuration;
- filled scorecard JSON or a public artifact link;
- validator command and output;
- detector class claimed, or an explicit statement that no detector-class claim
  is made;
- short claim wording supported by the result;
- known misses, unsupported fixture classes, and false-positive handling.

Use the public scanner/corpus thread or scanner-result issue form linked from
[EXTERNAL_VALIDATION.md](EXTERNAL_VALIDATION.md). Do not submit private customer
data, secrets, internal hostnames, or non-public evidence.

## Claim Boundary

An accepted scorecard supports only a narrow statement:

> This scanner covers the DVAAC v0.1.4 fixture classes for the detector class it
> claims.

It does not imply product safety, universal agent safety, legal compliance,
endorsement, statistical vulnerability coverage, or accepted validation beyond
the submitted scorecard.
