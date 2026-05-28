from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest


BASE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "verify_release_fingerprints",
    BASE / "scripts" / "verify_release_fingerprints.py",
)
assert spec is not None and spec.loader is not None
release_fingerprints = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release_fingerprints)


def _release_evidence() -> dict:
    return json.loads((BASE / "docs" / "release-evidence.v0.1.5.json").read_text())


def test_release_evidence_consistency_accepts_current_file() -> None:
    release_fingerprints.validate_release_evidence(_release_evidence())


def test_release_evidence_consistency_rejects_pinned_aac_commit_drift() -> None:
    evidence = copy.deepcopy(_release_evidence())
    evidence["pinned_aac"]["commit"] = "0" * 40

    with pytest.raises(SystemExit, match="pinned AAC signed tag object mismatch"):
        release_fingerprints.validate_release_evidence(evidence)


def test_release_evidence_consistency_rejects_duplicate_signed_tag() -> None:
    evidence = copy.deepcopy(_release_evidence())
    evidence["signed_tags"].append(copy.deepcopy(evidence["signed_tags"][0]))

    with pytest.raises(
        SystemExit,
        match="release evidence contains duplicate signed tags for agent-assurance-case",
    ):
        release_fingerprints.validate_release_evidence(evidence)


def test_release_evidence_consistency_rejects_duplicate_release_asset() -> None:
    evidence = copy.deepcopy(_release_evidence())
    evidence["release_assets"].append(copy.deepcopy(evidence["release_assets"][0]))

    with pytest.raises(SystemExit, match="duplicate release asset names"):
        release_fingerprints.validate_release_evidence(evidence)


def test_release_evidence_consistency_rejects_unexpected_release_asset_name() -> None:
    evidence = copy.deepcopy(_release_evidence())
    evidence["release_assets"][0]["name"] = "unexpected.json"

    with pytest.raises(SystemExit, match="release evidence asset set mismatch"):
        release_fingerprints.validate_release_evidence(evidence)


def test_release_evidence_consistency_rejects_attestation_expectation_drift() -> None:
    evidence = copy.deepcopy(_release_evidence())
    evidence["asset_attestations"]["github_artifact_attestations_expected"] = False

    with pytest.raises(SystemExit, match="release asset attestation expectation"):
        release_fingerprints.validate_release_evidence(evidence)


def test_release_evidence_consistency_rejects_fail_closed_drift() -> None:
    evidence = copy.deepcopy(_release_evidence())
    evidence["asset_attestations"]["current_main_release_workflow_fail_closed"] = False

    with pytest.raises(SystemExit, match="release workflow fail-closed status"):
        release_fingerprints.validate_release_evidence(evidence)
