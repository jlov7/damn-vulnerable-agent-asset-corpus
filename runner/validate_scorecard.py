#!/usr/bin/env python3
"""Validate a third-party DVAAC scanner scorecard.

This checks scorecard structure and self-consistency against the current corpus
manifest and fixture ground truth. It does not run a scanner and it cannot prove
that emitted evidence is semantically correct.
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

UTC_SECOND_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
DETECTOR_CLASS_ORDER = ["static-declared", "static-extended", "trace-aware"]
PLACEHOLDER_STRINGS = {"", "n/a", "none", "todo", "tbd", "placeholder"}


def _finding_key(finding: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(finding.get("finding_id", "")),
        str(finding.get("category", "")),
        str(finding.get("severity", "")),
    )


def _load_expected_finding_keys(fixture_id: str) -> list[tuple[str, str, str]]:
    doc = verify_fixtures.load_json(
        verify_fixtures.FIXTURES_DIR / fixture_id / "expected-findings.json"
    )
    findings = doc.get("expected_findings", [])
    if not isinstance(findings, list):
        return []
    return sorted(_finding_key(finding) for finding in findings if isinstance(finding, dict))


def _is_placeholder(value: object) -> bool:
    return str(value).strip().lower() in PLACEHOLDER_STRINGS


def _fixture_results(scorecard: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    results: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for index, item in enumerate(scorecard.get("per_fixture_results", [])):
        if not isinstance(item, dict):
            continue
        fixture_id = item.get("fixture_id")
        if not isinstance(fixture_id, str):
            continue
        if fixture_id in results:
            errors.append(f"duplicate per_fixture_results entry: {fixture_id}")
        results[fixture_id] = item
        emitted_ids = [
            finding.get("finding_id")
            for finding in item.get("emitted_findings", [])
            if isinstance(finding, dict)
        ]
        duplicates = sorted({fid for fid in emitted_ids if fid and emitted_ids.count(fid) > 1})
        if duplicates:
            errors.append(
                f"per_fixture_results[{index}] {fixture_id}: duplicate emitted finding ids: "
                f"{duplicates}"
            )
    return results, errors


def _required_fixture_ids_for_class(
    manifest_by_id: dict[str, dict[str, Any]],
    detector_class: str,
) -> list[str]:
    required_fixture_ids: list[str] = []
    for fixture_id, manifest_item in manifest_by_id.items():
        coverage = manifest_item.get("expected_coverage", {})
        if isinstance(coverage, dict) and coverage.get(detector_class) in {"pass", "catch"}:
            required_fixture_ids.append(str(fixture_id))
    return required_fixture_ids


def _coverage_at_class(
    results: dict[str, dict[str, Any]],
    manifest_by_id: dict[str, dict[str, Any]],
    detector_class: str,
) -> bool:
    return all(
        results.get(fixture_id, {}).get("passed") is True
        for fixture_id in _required_fixture_ids_for_class(manifest_by_id, detector_class)
    )


def validate_scorecard(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        scorecard = verify_fixtures.load_json(path)
    except Exception as e:
        return [f"invalid scorecard JSON: {e}"]
    if not isinstance(scorecard, dict):
        return ["scorecard root must be an object"]

    errors += verify_fixtures.validate_json_schema(
        scorecard, verify_fixtures.SCORECARD_TEMPLATE_SCHEMA
    )

    try:
        manifest = verify_fixtures.load_json(verify_fixtures.MANIFEST_PATH)
    except Exception as e:
        return errors + [f"cannot load corpus manifest: {e}"]
    manifest_fixtures = [
        item for item in manifest.get("fixtures", []) if isinstance(item, dict)
    ]
    manifest_by_id: dict[str, dict[str, Any]] = {}
    for item in manifest_fixtures:
        fixture_id = item.get("fixture_id")
        if isinstance(fixture_id, str):
            manifest_by_id[fixture_id] = item

    scanner = scorecard.get("scanner", {})
    if isinstance(scanner, dict):
        for field in ("name", "version", "vendor_or_project", "source_url_or_commit"):
            if _is_placeholder(scanner.get(field, "")):
                errors.append(f"scanner.{field} must be populated for a submitted scorecard")
        run_at = scanner.get("run_at")
        if not isinstance(run_at, str) or not UTC_SECOND_RE.fullmatch(run_at):
            errors.append("scanner.run_at must be UTC RFC3339 seconds: YYYY-MM-DDTHH:MM:SSZ")

    run_context = scorecard.get("run_context", {})
    if isinstance(run_context, dict):
        for field in ("command", "environment", "configuration"):
            if _is_placeholder(run_context.get(field, "")):
                errors.append(f"run_context.{field} must be populated for a submitted scorecard")
        if run_context.get("evidence_publicly_reproducible") is not True:
            errors.append(
                "run_context.evidence_publicly_reproducible must be true for validation-ledger candidates"
            )

    results, result_errors = _fixture_results(scorecard)
    errors += result_errors
    if sorted(results) != sorted(manifest_by_id):
        errors.append(
            "scorecard fixture ids do not match corpus manifest: "
            f"scorecard={sorted(results)}, manifest={sorted(manifest_by_id)}"
        )

    summary = scorecard.get("summary", {})
    passed_count = sum(1 for result in results.values() if result.get("passed") is True)
    if isinstance(summary, dict):
        if summary.get("fixtures_total") != len(manifest_by_id):
            errors.append(
                f"summary.fixtures_total={summary.get('fixtures_total')}, "
                f"expected={len(manifest_by_id)}"
            )
        if summary.get("fixtures_passed") != passed_count:
            errors.append(
                f"summary.fixtures_passed={summary.get('fixtures_passed')}, "
                f"expected={passed_count}"
            )

    claimed_class = scorecard.get("detector_class_claimed")
    required_fixture_ids: list[str] = []
    if isinstance(claimed_class, str):
        required_fixture_ids = _required_fixture_ids_for_class(manifest_by_id, claimed_class)
        coverage_at_claimed_class = _coverage_at_class(results, manifest_by_id, claimed_class)
        declared = summary.get("coverage_at_claimed_class") if isinstance(summary, dict) else None
        if declared != coverage_at_claimed_class:
            errors.append(
                "summary.coverage_at_claimed_class="
                f"{declared}, expected={coverage_at_claimed_class}"
            )
        fully_covered_classes = [
            detector_class
            for detector_class in DETECTOR_CLASS_ORDER
            if _coverage_at_class(results, manifest_by_id, detector_class)
        ]
        strongest_fully_covered = fully_covered_classes[-1] if fully_covered_classes else None
        if strongest_fully_covered and claimed_class != strongest_fully_covered:
            errors.append(
                f"detector_class_claimed={claimed_class}, expected strongest fully "
                f"covered detector class: {strongest_fully_covered}"
            )

    for fixture_id, result in sorted(results.items()):
        if fixture_id not in manifest_by_id:
            continue
        emitted = result.get("emitted_findings", [])
        emitted_keys = sorted(
            _finding_key(finding) for finding in emitted if isinstance(finding, dict)
        )
        expected_keys = _load_expected_finding_keys(fixture_id)
        if result.get("passed") is True:
            if emitted_keys != expected_keys:
                errors.append(
                    f"{fixture_id}: passed=true requires emitted finding "
                    f"(finding_id, category, severity) set to match expected findings"
                )
            if expected_keys:
                for finding in emitted:
                    if isinstance(finding, dict) and not str(finding.get("evidence", "")).strip():
                        errors.append(f"{fixture_id}: passed=true finding evidence must be populated")
        elif fixture_id in required_fixture_ids:
            errors.append(
                f"{fixture_id}: required for detector_class_claimed={claimed_class} "
                "but passed=false"
            )

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scorecard", type=Path, help="Path to submitted scorecard JSON")
    args = parser.parse_args(argv)

    errors = validate_scorecard(args.scorecard)
    if errors:
        print("DVAAC scorecard: NOT VALID")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("DVAAC scorecard: valid submission.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
