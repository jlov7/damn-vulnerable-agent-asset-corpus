#!/usr/bin/env python3
"""Validate DVAAC external-validation status against release evidence and docs."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import NoReturn

ROOT = Path(__file__).resolve().parents[1]
RELEASE_EVIDENCE_PATH = ROOT / "docs" / "release-evidence.v0.1.4.json"
LEDGER_PATH = ROOT / "docs" / "VALIDATION_LEDGER.md"
README_PATH = ROOT / "README.md"
VALIDATION_GUIDE_PATH = ROOT / "docs" / "EXTERNAL_VALIDATION.md"

EXPECTED_LEDGER = "docs/VALIDATION_LEDGER.md"
EXPECTED_PUBLIC_ISSUE = "https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/issues/1"
EXPECTED_MATURITY = "public validation candidate"
EXPECTED_FINGERPRINT_COMMAND = "python3 scripts/verify_release_fingerprints.py"
EXPECTED_NOT_CLAIMED = {
    "scanner quality",
    "product safety",
    "statistical vulnerability coverage",
    "legal certification",
    "employer endorsement",
    "standards-body endorsement",
}


def fail(message: str) -> NoReturn:
    print(f"External validation status invalid: {message}", file=sys.stderr)
    raise SystemExit(1)


def duplicate_rejecting_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    seen: set[str] = set()
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in seen:
            fail(f"duplicate JSON member {key!r}")
        seen.add(key)
        result[key] = value
    return result


def load_json(path: Path) -> Mapping[str, object]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=duplicate_rejecting_object,
        )
    except json.JSONDecodeError as exc:
        fail(f"{path.name} is not valid JSON: {exc}")
    if not isinstance(value, Mapping):
        fail(f"{path.name} must be a JSON object")
    return value


def require_mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        fail(f"{field} must be an object")
    return value


def require_equal(actual: object, expected: object, field: str) -> None:
    if actual != expected:
        fail(f"{field} must be {expected!r}, got {actual!r}")


def require_contains(text: str, needle: str, path: Path) -> None:
    if needle not in text:
        fail(f"{path.as_posix()} must contain {needle!r}")


def main() -> int:
    evidence = load_json(RELEASE_EVIDENCE_PATH)
    release_checks = require_mapping(evidence.get("release_checks"), "release_checks")
    external_validation = require_mapping(
        evidence.get("external_validation"),
        "external_validation",
    )
    claim_boundary = require_mapping(evidence.get("claim_boundary"), "claim_boundary")

    require_equal(external_validation.get("ledger"), EXPECTED_LEDGER, "external_validation.ledger")
    require_equal(
        external_validation.get("public_issue"),
        EXPECTED_PUBLIC_ISSUE,
        "external_validation.public_issue",
    )
    require_equal(
        external_validation.get("accepted_third_party_scanner_result"),
        False,
        "external_validation.accepted_third_party_scanner_result",
    )
    require_equal(
        external_validation.get("accepted_independent_corpus_critique"),
        False,
        "external_validation.accepted_independent_corpus_critique",
    )
    require_equal(claim_boundary.get("maturity"), EXPECTED_MATURITY, "claim_boundary.maturity")
    require_equal(
        claim_boundary.get("self_verification_evidence"),
        True,
        "claim_boundary.self_verification_evidence",
    )
    require_equal(
        claim_boundary.get("third_party_validation_claimed"),
        False,
        "claim_boundary.third_party_validation_claimed",
    )
    require_equal(
        release_checks.get("current_main_release_fingerprint_command"),
        EXPECTED_FINGERPRINT_COMMAND,
        "release_checks.current_main_release_fingerprint_command",
    )

    not_claimed = claim_boundary.get("not_claimed")
    if not isinstance(not_claimed, list):
        fail("claim_boundary.not_claimed must be an array")
    missing_not_claimed = sorted(EXPECTED_NOT_CLAIMED - {str(item) for item in not_claimed})
    if missing_not_claimed:
        fail(f"claim_boundary.not_claimed missing {missing_not_claimed!r}")

    ledger = LEDGER_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    validation_guide = VALIDATION_GUIDE_PATH.read_text(encoding="utf-8")

    require_contains(
        ledger,
        "No third-party scanner result or independent corpus critique has been accepted",
        LEDGER_PATH,
    )
    require_contains(ledger, "| none yet | none yet | none yet | n/a | none yet |", LEDGER_PATH)
    require_contains(ledger, "it is not yet externally validated", LEDGER_PATH)
    require_contains(
        readme,
        "third-party scanner submissions and critique boundaries",
        README_PATH,
    )
    require_contains(readme, EXPECTED_PUBLIC_ISSUE, README_PATH)
    require_contains(
        validation_guide,
        "currently has no accepted third-party scanner submissions recorded in-tree",
        VALIDATION_GUIDE_PATH,
    )
    require_contains(validation_guide, "VALIDATION_LEDGER.md", VALIDATION_GUIDE_PATH)

    print("External validation status: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
