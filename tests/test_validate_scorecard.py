from __future__ import annotations

import copy
import json
from pathlib import Path

from runner import validate_scorecard
from runner import verify_fixtures


def _valid_scorecard_for_claimed_class(claimed_class: str) -> dict:
    template = verify_fixtures.load_json(verify_fixtures.SCORECARD_TEMPLATE_PATH)
    manifest = verify_fixtures.load_json(verify_fixtures.MANIFEST_PATH)
    scorecard = copy.deepcopy(template)
    scorecard["scanner"] = {
        "name": "ExampleScanner",
        "version": "1.2.3",
        "vendor_or_project": "example",
        "run_at": "2026-05-24T12:00:00Z",
    }
    scorecard["detector_class_claimed"] = claimed_class

    manifest_by_id = {item["fixture_id"]: item for item in manifest["fixtures"]}
    passed = 0
    for result in scorecard["per_fixture_results"]:
        fixture_id = result["fixture_id"]
        must_pass = manifest_by_id[fixture_id]["expected_coverage"][claimed_class] in {
            "pass",
            "catch",
        }
        result["passed"] = must_pass
        if must_pass:
            expected = verify_fixtures.load_json(
                verify_fixtures.FIXTURES_DIR / fixture_id / "expected-findings.json"
            )
            result["emitted_findings"] = [
                {
                    "finding_id": finding["finding_id"],
                    "category": finding["category"],
                    "severity": finding["severity"],
                    "evidence": "fixture evidence matched",
                }
                for finding in expected["expected_findings"]
            ]
            passed += 1
        else:
            result["emitted_findings"] = []
        result["notes"] = "generated test scorecard"

    scorecard["summary"] = {
        "fixtures_total": len(scorecard["per_fixture_results"]),
        "fixtures_passed": passed,
        "coverage_at_claimed_class": True,
    }
    return scorecard


def _write_scorecard(tmp_path: Path, scorecard: dict) -> Path:
    path = tmp_path / "scorecard.json"
    path.write_text(json.dumps(scorecard, indent=2), encoding="utf-8")
    return path


def test_valid_scorecard_for_static_declared(tmp_path: Path) -> None:
    scorecard = _valid_scorecard_for_claimed_class("static-declared")
    assert validate_scorecard.validate_scorecard(_write_scorecard(tmp_path, scorecard)) == []


def test_cli_accepts_valid_scorecard(tmp_path: Path, capsys) -> None:
    scorecard = _valid_scorecard_for_claimed_class("static-declared")
    path = _write_scorecard(tmp_path, scorecard)

    assert validate_scorecard.main([str(path)]) == 0

    assert capsys.readouterr().out.strip() == "DVAAC scorecard: valid submission."


def test_rejects_unpopulated_scanner_metadata(tmp_path: Path) -> None:
    scorecard = _valid_scorecard_for_claimed_class("static-declared")
    scorecard["scanner"]["name"] = ""

    errors = validate_scorecard.validate_scorecard(_write_scorecard(tmp_path, scorecard))

    assert "scanner.name must be populated for a submitted scorecard" in errors


def test_rejects_summary_passed_count_drift(tmp_path: Path) -> None:
    scorecard = _valid_scorecard_for_claimed_class("static-declared")
    scorecard["summary"]["fixtures_passed"] -= 1

    errors = validate_scorecard.validate_scorecard(_write_scorecard(tmp_path, scorecard))

    assert any(error.startswith("summary.fixtures_passed=") for error in errors)


def test_rejects_required_fixture_miss_for_claimed_class(tmp_path: Path) -> None:
    scorecard = _valid_scorecard_for_claimed_class("static-declared")
    scorecard["per_fixture_results"][1]["passed"] = False
    scorecard["per_fixture_results"][1]["emitted_findings"] = []
    scorecard["summary"]["fixtures_passed"] -= 1
    scorecard["summary"]["coverage_at_claimed_class"] = False

    errors = validate_scorecard.validate_scorecard(_write_scorecard(tmp_path, scorecard))

    assert any(
        error == "02-skill-md-prompt-injection: required for detector_class_claimed=static-declared but passed=false"
        for error in errors
    )


def test_rejects_passed_fixture_with_wrong_finding_category(tmp_path: Path) -> None:
    scorecard = _valid_scorecard_for_claimed_class("static-declared")
    scorecard["per_fixture_results"][1]["emitted_findings"][0]["category"] = "wrong"

    errors = validate_scorecard.validate_scorecard(_write_scorecard(tmp_path, scorecard))

    assert any(
        error.startswith(
            "02-skill-md-prompt-injection: passed=true requires emitted finding"
        )
        for error in errors
    )
