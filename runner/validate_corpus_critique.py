#!/usr/bin/env python3
"""Validate a third-party DVAAC corpus critique report.

This checks report structure, target identity, fixture references, and public
reproducibility fields. It does not prove the critique is correct or accepted.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

try:
    from . import verify_fixtures
except ImportError:
    import verify_fixtures  # type: ignore[no-redef]

ROOT = Path(__file__).resolve().parents[1]
CRITIQUE_SCHEMA_PATH = ROOT / "corpus-critique.schema.json"
UTC_SECOND_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _is_populated(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _manifest_fixture_ids() -> set[str]:
    manifest = verify_fixtures.load_json(verify_fixtures.MANIFEST_PATH)
    return {
        item["fixture_id"]
        for item in manifest.get("fixtures", [])
        if isinstance(item, dict) and isinstance(item.get("fixture_id"), str)
    }


def validate_corpus_critique(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        report = verify_fixtures.load_json(path)
    except Exception as e:
        return [f"invalid corpus critique JSON: {e}"]
    if not isinstance(report, dict):
        return ["corpus critique root must be an object"]

    errors += verify_fixtures.validate_json_schema(report, CRITIQUE_SCHEMA_PATH)

    reviewer = report.get("reviewer", {})
    if isinstance(reviewer, dict):
        for field in ("name", "affiliation_or_project", "contact"):
            if not _is_populated(reviewer.get(field)):
                errors.append(f"reviewer.{field} must be populated for a submitted critique")
        reviewed_at = reviewer.get("reviewed_at")
        if not isinstance(reviewed_at, str) or not UTC_SECOND_RE.fullmatch(reviewed_at):
            errors.append("reviewer.reviewed_at must be UTC RFC3339 seconds: YYYY-MM-DDTHH:MM:SSZ")

    fixture_ids = _manifest_fixture_ids()
    scope = report.get("scope", {})
    if isinstance(scope, dict):
        for fixture_id in scope.get("fixture_ids", []):
            if isinstance(fixture_id, str) and fixture_id not in fixture_ids:
                errors.append(f"scope.fixture_ids contains unknown fixture: {fixture_id}")
        if not _is_populated(scope.get("environment")):
            errors.append("scope.environment must describe the review environment")

    seen_finding_ids: set[str] = set()
    for index, finding in enumerate(report.get("findings", [])):
        if not isinstance(finding, dict):
            continue
        finding_id = finding.get("finding_id")
        if isinstance(finding_id, str):
            if finding_id in seen_finding_ids:
                errors.append(f"duplicate finding_id: {finding_id}")
            seen_finding_ids.add(finding_id)
        for field in ("title", "description", "evidence", "recommendation"):
            if not _is_populated(finding.get(field)):
                errors.append(f"findings[{index}].{field} must be populated")
        subject = finding.get("subject", {})
        if isinstance(subject, dict) and subject.get("type") == "fixture":
            subject_ref = subject.get("ref")
            if not isinstance(subject_ref, str) or subject_ref not in fixture_ids:
                errors.append(f"findings[{index}].subject.ref unknown fixture: {subject_ref}")

    public_repro = report.get("public_reproducibility", {})
    if isinstance(public_repro, dict):
        if public_repro.get("can_summarize_publicly") is not True:
            errors.append("public_reproducibility.can_summarize_publicly must be true for ledger candidates")
        for field in ("redactions", "reproduction_notes"):
            if not _is_populated(public_repro.get(field)):
                errors.append(f"public_reproducibility.{field} must be populated")

    claim_boundary = report.get("claim_boundary", {})
    if isinstance(claim_boundary, dict):
        for field in (
            "scanner_validation_claimed",
            "corpus_correctness_claimed",
            "endorsement_claimed",
        ):
            if claim_boundary.get(field) is not False:
                errors.append(f"claim_boundary.{field} must be false")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="Path to submitted corpus critique JSON")
    args = parser.parse_args(argv)

    errors = validate_corpus_critique(args.report)
    if errors:
        print("DVAAC corpus critique: NOT VALID")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("DVAAC corpus critique: valid submission.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
