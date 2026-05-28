"""Negative-control unit tests for the DVAAC conformance runner.

These tests exercise the runner's trust-boundary and integrity checks directly,
without needing the sibling AAC verifier checkout. Each test corrupts one
property (a tampered digest, a duplicate JSON member, a symlink, a path-traversal
attempt, an inconsistent finding, an out-of-bounds evidence excerpt, or a
drifted verifier API) and asserts the runner rejects it. The corresponding
"happy path" is already covered by the full `make verify` conformance run; here
we pin the failure modes so a regression that silently weakens a guard is caught
by `pytest` alone.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from runner import verify_fixtures


# --- JSON hardening: duplicate members and non-standard numeric constants -----


def test_load_json_rejects_duplicate_object_members(tmp_path: Path) -> None:
    bad = tmp_path / "dup.json"
    bad.write_text('{"a": 1, "a": 2}', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate JSON object member"):
        verify_fixtures.load_json(bad)


def test_load_json_rejects_nan_and_infinity(tmp_path: Path) -> None:
    for token in ("NaN", "Infinity", "-Infinity"):
        bad = tmp_path / f"{token}.json"
        bad.write_text(f'{{"value": {token}}}', encoding="utf-8")
        with pytest.raises(ValueError, match="non-standard JSON numeric constant"):
            verify_fixtures.load_json(bad)


def test_no_duplicate_object_pairs_helper_rejects_repeat_key() -> None:
    with pytest.raises(ValueError, match="duplicate JSON object member"):
        verify_fixtures._no_duplicate_object_pairs([("k", 1), ("k", 2)])


# --- Path containment and symlink rejection -----------------------------------


def test_validate_path_within_fixture_rejects_escape(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(verify_fixtures, "ROOT", tmp_path)
    fixture = tmp_path / "fixtures" / "01-x"
    fixture.mkdir(parents=True)
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    with pytest.raises(ValueError, match="resolves outside fixture"):
        verify_fixtures.validate_path_within_fixture(
            fixture, outside, "asset source_uri"
        )


def test_validate_path_within_fixture_reports_missing_target(tmp_path: Path) -> None:
    fixture = tmp_path / "fixtures" / "01-x"
    fixture.mkdir(parents=True)
    missing = fixture / "does-not-exist.txt"
    with pytest.raises(ValueError, match="not found"):
        verify_fixtures.validate_path_within_fixture(
            fixture, missing, "asset source_uri"
        )


def test_fixture_symlink_errors_detects_symlink(tmp_path: Path) -> None:
    fixture = tmp_path / "fixtures" / "01-x"
    fixture.mkdir(parents=True)
    target = fixture / "real.txt"
    target.write_text("ok", encoding="utf-8")
    link = fixture / "link.txt"
    os.symlink(target, link)
    errors = verify_fixtures.fixture_symlink_errors(fixture)
    assert any("symlink not allowed" in e for e in errors)


def test_directory_digest_rejects_symlink(tmp_path: Path) -> None:
    fixture = tmp_path / "fixtures" / "01-x"
    fixture.mkdir(parents=True)
    target = fixture / "real.txt"
    target.write_text("ok", encoding="utf-8")
    os.symlink(target, fixture / "link.txt")
    with pytest.raises(ValueError, match="symlink not allowed"):
        verify_fixtures.directory_digest(fixture)


# --- Expected-findings document and finding-consistency checks ----------------


def _finding(**overrides: object) -> dict:
    base: dict[str, object] = {
        "finding_id": "F-1",
        "category": "skill-secret-exposure",
        "severity": "high",
        "title": "Secret in skill",
        "description": "A secret is exposed.",
        "subject_asset_id": "asset-1",
    }
    base.update(overrides)
    return base


def test_findings_consistent_detects_severity_mismatch() -> None:
    expected = {"expected_findings": [_finding(severity="critical")]}
    aac = {"findings": [_finding(severity="high")]}
    errors = verify_fixtures.findings_consistent(expected, aac)
    assert any("severity mismatch" in e for e in errors)


def test_findings_consistent_detects_missing_and_extra_ids() -> None:
    expected = {"expected_findings": [_finding(finding_id="F-1")]}
    aac = {"findings": [_finding(finding_id="F-2")]}
    errors = verify_fixtures.findings_consistent(expected, aac)
    assert any("missing finding ids" in e for e in errors)
    assert any("unexpected finding ids" in e for e in errors)


def test_findings_consistent_detects_duplicate_ids() -> None:
    expected = {"expected_findings": [_finding(), _finding()]}
    aac = {"findings": [_finding(), _finding()]}
    errors = verify_fixtures.findings_consistent(expected, aac)
    assert any("duplicate finding ids" in e for e in errors)


def test_validate_expected_findings_doc_detects_fixture_id_mismatch(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "07-low-missing-owner-metadata"
    fixture.mkdir(parents=True)
    doc = {"fixture_id": "99-wrong", "expected_findings": []}
    errors = verify_fixtures.validate_expected_findings_doc(doc, fixture)
    assert any("fixture_id mismatch" in e for e in errors)


# --- Local digest binding -----------------------------------------------------


def test_local_digests_consistent_detects_tampered_asset_digest(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(verify_fixtures, "ROOT", tmp_path)
    monkeypatch.setattr(verify_fixtures, "FIXTURES_DIR", tmp_path / "fixtures")
    fixture = tmp_path / "fixtures" / "01-clean-declared-skill"
    fixture.mkdir(parents=True)
    asset = fixture / "SKILL.md"
    asset.write_text("real bytes", encoding="utf-8")
    aac = {
        "assets": [
            {
                "asset_id": "asset-1",
                "source_uri": "fixtures/01-clean-declared-skill/SKILL.md",
                "digest": "sha256:" + "0" * 64,  # deliberately wrong
            }
        ]
    }
    errors = verify_fixtures.local_digests_consistent(fixture, aac)
    assert any("asset digest mismatch" in e for e in errors)


def test_local_digests_consistent_accepts_correct_digest(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(verify_fixtures, "ROOT", tmp_path)
    monkeypatch.setattr(verify_fixtures, "FIXTURES_DIR", tmp_path / "fixtures")
    fixture = tmp_path / "fixtures" / "01-clean-declared-skill"
    fixture.mkdir(parents=True)
    asset = fixture / "SKILL.md"
    asset.write_text("real bytes", encoding="utf-8")
    correct = verify_fixtures.local_asset_digest(asset)
    aac = {
        "assets": [
            {
                "asset_id": "asset-1",
                "source_uri": "fixtures/01-clean-declared-skill/SKILL.md",
                "digest": correct,
            }
        ]
    }
    assert verify_fixtures.local_digests_consistent(fixture, aac) == []


# --- Evidence URI safety ------------------------------------------------------


def test_evidence_artifact_digest_rejects_path_traversal(tmp_path: Path) -> None:
    fixture = tmp_path / "01-clean-declared-skill"
    fixture.mkdir(parents=True)
    uri = "evidence://dvaac/01/../../../etc/passwd"
    digest, error = verify_fixtures.evidence_artifact_digest(fixture, uri)
    assert digest is None
    assert error is not None and "unsafe evidence artifact path" in error


def test_file_excerpt_digest_rejects_out_of_bounds_range(
    tmp_path: Path, monkeypatch
) -> None:
    # The "files/" URI prefix is a namespace marker; the source resolves to
    # fixture/<path>, so the file lives directly under the fixture root.
    monkeypatch.setattr(verify_fixtures, "ROOT", tmp_path)
    fixture = tmp_path / "01-clean-declared-skill"
    fixture.mkdir(parents=True)
    source = fixture / "snippet.txt"
    source.write_text("line1\nline2\n", encoding="utf-8")
    digest, error = verify_fixtures.file_excerpt_digest(
        fixture, "files/snippet.txt#L1-L99"
    )
    assert digest is None
    assert error is not None and "out of bounds" in error


def test_file_excerpt_digest_accepts_valid_range(tmp_path: Path) -> None:
    fixture = tmp_path / "01-clean-declared-skill"
    fixture.mkdir(parents=True)
    (fixture / "snippet.txt").write_text("line1\nline2\nline3\n", encoding="utf-8")
    digest, error = verify_fixtures.file_excerpt_digest(
        fixture, "files/snippet.txt#L1-L2"
    )
    assert error is None
    assert digest is not None and digest.startswith("sha256:")


# --- Verifier trust boundary --------------------------------------------------


def test_load_aac_verifier_refuses_import_from_fixtures(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(verify_fixtures, "FIXTURES_DIR", tmp_path / "fixtures")
    planted = tmp_path / "fixtures" / "evil" / "verify.py"
    planted.parent.mkdir(parents=True)
    planted.write_text("raise RuntimeError('should never import')\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        verify_fixtures.load_aac_verifier(planted)
    assert exc.value.code == 2


def test_validate_aac_verifier_api_rejects_missing_callable(tmp_path: Path) -> None:
    # A module that is missing required callables must be rejected with exit 2,
    # so a drifted or hostile verifier cannot be silently accepted.
    incomplete = SimpleNamespace(verify=lambda **_kwargs: 0)
    with pytest.raises(SystemExit) as exc:
        verify_fixtures.validate_aac_verifier_api(incomplete, tmp_path / "verify.py")
    assert exc.value.code == 2


def test_load_json_round_trips_valid_document(tmp_path: Path) -> None:
    good = tmp_path / "good.json"
    payload = {"a": 1, "b": ["x", "y"], "c": {"d": True}}
    good.write_text(json.dumps(payload), encoding="utf-8")
    assert verify_fixtures.load_json(good) == payload
