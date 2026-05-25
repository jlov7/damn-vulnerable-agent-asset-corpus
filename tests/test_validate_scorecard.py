from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any

from hypothesis import given, settings
from hypothesis import strategies as st

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


def _validate_scorecard_doc(scorecard: dict) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "scorecard.json"
        path.write_text(json.dumps(scorecard, indent=2), encoding="utf-8")
        return validate_scorecard.validate_scorecard(path)


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


def _result_for(scorecard: dict, fixture_id: str) -> dict:
    for result in scorecard["per_fixture_results"]:
        if result["fixture_id"] == fixture_id:
            return result
    raise AssertionError(f"missing generated fixture result: {fixture_id}")


def _required_fixture_ids(claimed_class: str) -> list[str]:
    manifest = verify_fixtures.load_json(verify_fixtures.MANIFEST_PATH)
    return [
        item["fixture_id"]
        for item in manifest["fixtures"]
        if item["expected_coverage"][claimed_class] in {"pass", "catch"}
    ]


@given(
    data=st.data(),
    claimed_class=st.sampled_from(["static-declared", "static-extended", "trace-aware"]),
)
@settings(max_examples=25, database=None)
def test_property_rejects_any_required_fixture_miss(
    data: Any,
    claimed_class: str,
) -> None:
    scorecard = _valid_scorecard_for_claimed_class(claimed_class)
    fixture_id = data.draw(st.sampled_from(_required_fixture_ids(claimed_class)))
    result = _result_for(scorecard, fixture_id)
    result["passed"] = False
    result["emitted_findings"] = []
    scorecard["summary"]["fixtures_passed"] -= 1
    scorecard["summary"]["coverage_at_claimed_class"] = False

    errors = _validate_scorecard_doc(scorecard)

    assert (
        f"{fixture_id}: required for detector_class_claimed={claimed_class} "
        "but passed=false"
    ) in errors


@given(
    data=st.data(),
    claimed_class=st.sampled_from(["static-declared", "static-extended", "trace-aware"]),
)
@settings(max_examples=25, database=None)
def test_property_rejects_blank_evidence_for_any_passed_finding(
    data: Any,
    claimed_class: str,
) -> None:
    scorecard = _valid_scorecard_for_claimed_class(claimed_class)
    passed_with_findings = [
        result
        for result in scorecard["per_fixture_results"]
        if result["passed"] is True and result["emitted_findings"]
    ]
    result = data.draw(st.sampled_from(passed_with_findings))
    finding_index = data.draw(
        st.integers(min_value=0, max_value=len(result["emitted_findings"]) - 1)
    )
    result["emitted_findings"][finding_index]["evidence"] = " "

    errors = _validate_scorecard_doc(scorecard)

    assert f"{result['fixture_id']}: passed=true finding evidence must be populated" in errors


@given(data=st.data())
@settings(max_examples=20, database=None)
def test_property_rejects_duplicate_per_fixture_results(
    data: Any,
) -> None:
    scorecard = _valid_scorecard_for_claimed_class("static-declared")
    fixture_id = data.draw(
        st.sampled_from([result["fixture_id"] for result in scorecard["per_fixture_results"]])
    )
    scorecard["per_fixture_results"].append(copy.deepcopy(_result_for(scorecard, fixture_id)))

    errors = _validate_scorecard_doc(scorecard)

    assert f"duplicate per_fixture_results entry: {fixture_id}" in errors
