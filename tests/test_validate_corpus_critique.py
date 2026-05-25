from __future__ import annotations

import copy
import json
from pathlib import Path

from runner import validate_corpus_critique
from runner import verify_fixtures


def _valid_critique() -> dict:
    report = verify_fixtures.load_json(Path("corpus-critique-template.json"))
    critique = copy.deepcopy(report)
    critique["reviewer"] = {
        "name": "Example Reviewer",
        "affiliation_or_project": "example",
        "contact": "https://example.com/reviewer",
        "reviewed_at": "2026-05-25T12:00:00Z",
    }
    critique["scope"]["environment"] = "macOS, Python 3.13, uv"
    critique["scope"]["corpus_conformance_result"] = "pass"
    critique["findings"][0].update(
        {
            "title": "Fixture realism note",
            "description": "The fixture is reviewable and maps to the documented threat.",
            "evidence": "fixtures/02-skill-md-prompt-injection/README.md",
            "recommendation": "No change required for this synthetic validator test.",
        }
    )
    critique["public_reproducibility"]["reproduction_notes"] = (
        "Reviewed the named fixture files and ran corpus conformance."
    )
    return critique


def _write_critique(tmp_path: Path, report: dict) -> Path:
    path = tmp_path / "corpus-critique.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path


def test_valid_corpus_critique(tmp_path: Path) -> None:
    report = _valid_critique()

    assert validate_corpus_critique.validate_corpus_critique(
        _write_critique(tmp_path, report)
    ) == []


def test_cli_accepts_valid_corpus_critique(tmp_path: Path, capsys) -> None:
    report = _valid_critique()
    path = _write_critique(tmp_path, report)

    assert validate_corpus_critique.main([str(path)]) == 0

    assert capsys.readouterr().out.strip() == "DVAAC corpus critique: valid submission."


def test_rejects_unknown_scope_fixture(tmp_path: Path) -> None:
    report = _valid_critique()
    report["scope"]["fixture_ids"] = ["99-missing-fixture"]

    errors = validate_corpus_critique.validate_corpus_critique(
        _write_critique(tmp_path, report)
    )

    assert "scope.fixture_ids contains unknown fixture: 99-missing-fixture" in errors


def test_rejects_unknown_finding_subject_fixture(tmp_path: Path) -> None:
    report = _valid_critique()
    report["findings"][0]["subject"]["ref"] = "99-missing-fixture"

    errors = validate_corpus_critique.validate_corpus_critique(
        _write_critique(tmp_path, report)
    )

    assert "findings[0].subject.ref unknown fixture: 99-missing-fixture" in errors


def test_rejects_duplicate_finding_ids(tmp_path: Path) -> None:
    report = _valid_critique()
    report["findings"].append(copy.deepcopy(report["findings"][0]))

    errors = validate_corpus_critique.validate_corpus_critique(
        _write_critique(tmp_path, report)
    )

    assert "duplicate finding_id: DVAAC-CRITIQUE-001" in errors


def test_rejects_private_only_report_as_ledger_candidate(tmp_path: Path) -> None:
    report = _valid_critique()
    report["public_reproducibility"]["can_summarize_publicly"] = False

    errors = validate_corpus_critique.validate_corpus_critique(
        _write_critique(tmp_path, report)
    )

    assert (
        "public_reproducibility.can_summarize_publicly must be true for ledger candidates"
        in errors
    )


def test_rejects_scanner_validation_claim(tmp_path: Path) -> None:
    report = _valid_critique()
    report["claim_boundary"]["scanner_validation_claimed"] = True

    errors = validate_corpus_critique.validate_corpus_critique(
        _write_critique(tmp_path, report)
    )

    assert "claim_boundary.scanner_validation_claimed must be false" in errors
