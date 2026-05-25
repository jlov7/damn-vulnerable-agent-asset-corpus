#!/usr/bin/env python3
"""DVAAC fixture conformance runner.

For every fixture under fixtures/, this runner:

1. Confirms the expected layout exists.
2. Loads expected-aac.json and expected-findings.json with duplicate-member
   rejection.
3. Asks the Agent Assurance Case v0.2 reference verifier (the sibling
   `agent-assurance-case` repo, with `agent-assurance-case-spec` also
   recognized for local development) to sign the expected AAC with the demo
   key (because content_hash and signature are placeholders in the checked-in
   files) and then to verify the signed case end-to-end.
4. Confirms that the finding IDs in expected-aac.json are exactly the finding
   IDs listed in expected-findings.json, and that severities match.
5. Confirms local asset and evidence digests bind to the fixture bytes.
6. Reports pass/fail per fixture and exits 0 only if every fixture conforms.

DVAAC ships ground truth. It does NOT ship detection logic. A scanner author
should run their detector against each fixture, build an AAC, and check
their AAC against expected-aac.json themselves.

Locate the AAC verifier with --aac-verifier or the AAC_VERIFIER_PATH env var.
The default looks for it as a sibling repository.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import importlib.util
import inspect
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:
    sys.stderr.write("Missing dependency. Run: uv pip install -r runner/requirements.txt\n")
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = ROOT / "fixtures"
EXPECTED_FINDINGS_SCHEMA = Path(__file__).resolve().parent / "expected-findings.schema.json"
MANIFEST_PATH = ROOT / "corpus.manifest.json"
MANIFEST_SCHEMA = ROOT / "corpus.manifest.schema.json"
SCORECARD_TEMPLATE_PATH = ROOT / "scorecard-template.json"
SCORECARD_TEMPLATE_SCHEMA = ROOT / "scorecard-template.schema.json"
FORMAT_CHECKER = FormatChecker()
DIGEST_IGNORED_DIRS = {
    "__pycache__",
    ".coverage",
    ".mypy_cache",
    ".pyre",
    ".pytest_cache",
    ".pytype",
    ".ruff_cache",
    ".tox",
    ".venv",
}
DIGEST_IGNORED_FILE_NAMES = {".DS_Store"}
DIGEST_IGNORED_SUFFIXES = {".pyc", ".pyo"}
DEMO_SIGNED_BY = "urn:agent-assurance-case:demo-issuer"
DEMO_KEY_ID = "aac-demo-v0.2"


def default_aac_verifier_path() -> Path:
    candidates = [
        ROOT.parent / "agent-assurance-case" / "verifier" / "verify.py",
        ROOT.parent / "agent-assurance-case-spec" / "verifier" / "verify.py",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON numeric constant rejected: {value}")


def _no_duplicate_object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"duplicate JSON object member rejected: {key}")
        obj[key] = value
    return obj


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def validate_path_within_fixture(fixture: Path, path: Path, label: str) -> None:
    fixture_path = fixture.resolve(strict=True)
    candidate = path if path.is_absolute() else ROOT / path
    try:
        relative = candidate.resolve(strict=True).relative_to(fixture_path)
    except ValueError as e:
        raise ValueError(
            f"{label} resolves outside fixture {fixture.name}: {_display_path(candidate)}"
        ) from e
    except FileNotFoundError as e:
        raise ValueError(f"{label} not found: {_display_path(candidate)}") from e

    current = fixture
    for part in relative.parts:
        current = current / part
        if os.path.islink(current):
            raise ValueError(f"symlink not allowed in fixture tree: {_display_path(current)}")


def fixture_symlink_errors(fixture: Path) -> list[str]:
    errors: list[str] = []
    for dirpath, dirnames, filenames in os.walk(fixture, followlinks=False):
        base = Path(dirpath)
        for name in [*dirnames, *filenames]:
            candidate = base / name
            if os.path.islink(candidate):
                errors.append(f"symlink not allowed in fixture tree: {_display_path(candidate)}")
    return errors


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def load_aac_verifier(path: Path) -> Any:
    """Import the AAC reference verifier as a Python module."""
    verifier_path = path.resolve()
    if not verifier_path.exists():
        sys.stderr.write(
            f"AAC reference verifier not found at: {verifier_path}\n"
            f"Set AAC_VERIFIER_PATH or pass --aac-verifier to point at the\n"
            f"verify.py in the agent-assurance-case repository.\n"
        )
        sys.exit(2)
    if verifier_path.name != "verify.py":
        sys.stderr.write(f"AAC verifier path must end in verify.py: {verifier_path}\n")
        sys.exit(2)
    if _is_relative_to(verifier_path, FIXTURES_DIR.resolve()):
        sys.stderr.write(
            "Refusing to import an AAC verifier from inside fixtures/. "
            "Fixture payload code is intentionally untrusted.\n"
        )
        sys.exit(2)
    spec = importlib.util.spec_from_file_location("aac_verify", verifier_path)
    if spec is None or spec.loader is None:
        sys.stderr.write(f"Cannot load AAC verifier module from: {verifier_path}\n")
        sys.exit(2)
    module = importlib.util.module_from_spec(spec)
    import_stderr = io.StringIO()
    try:
        with contextlib.redirect_stderr(import_stderr):
            spec.loader.exec_module(module)
    except SystemExit as e:
        sys.stderr.write(
            "AAC verifier import exited before loading. Install DVAAC runner "
            "dependencies with: uv pip install -r runner/requirements.txt\n"
        )
        raise SystemExit(e.code)
    except Exception:
        detail = import_stderr.getvalue().strip()
        if detail:
            sys.stderr.write(detail + "\n")
        raise
    validate_aac_verifier_api(module, verifier_path)
    return module


def validate_aac_verifier_api(module: Any, verifier_path: Path) -> None:
    for name in ("_demo_keypair", "sign_case", "verify", "load_json_no_duplicates", "canonicalize"):
        if not callable(getattr(module, name, None)):
            sys.stderr.write(f"AAC verifier missing required callable {name}: {verifier_path}\n")
            sys.exit(2)

    verify_sig = inspect.signature(module.verify)
    for param in ("case_path", "public_key_path", "allow_demo_key", "verbose"):
        if param not in verify_sig.parameters:
            sys.stderr.write(
                f"AAC verifier verify() missing expected parameter {param}: {verify_sig}\n"
            )
            sys.exit(2)
    for param in verify_sig.parameters.values():
        if (
            param.default is inspect.Parameter.empty
            and param.name
            not in {"case_path", "public_key_path", "allow_demo_key", "verbose"}
        ):
            sys.stderr.write(
                f"AAC verifier verify() has unsupported required parameter {param.name}: "
                f"{verify_sig}\n"
            )
            sys.exit(2)

    if len(inspect.signature(module._demo_keypair).parameters) != 0:
        sys.stderr.write("AAC verifier _demo_keypair() must take no parameters\n")
        sys.exit(2)
    sign_params = list(inspect.signature(module.sign_case).parameters)
    if sign_params[:2] != ["case", "private_key"]:
        sys.stderr.write(
            "AAC verifier sign_case() must accept (case, private_key) as its first "
            f"parameters: {inspect.signature(module.sign_case)}\n"
        )
        sys.exit(2)
    if getattr(module, "_DEMO_SIGNED_BY", None) != DEMO_SIGNED_BY:
        sys.stderr.write(
            "AAC verifier demo signed_by constant drifted: "
            f"expected={DEMO_SIGNED_BY}, got={getattr(module, '_DEMO_SIGNED_BY', None)}\n"
        )
        sys.exit(2)
    if getattr(module, "_DEMO_KEY_ID", None) != DEMO_KEY_ID:
        sys.stderr.write(
            "AAC verifier demo key_id constant drifted: "
            f"expected={DEMO_KEY_ID}, got={getattr(module, '_DEMO_KEY_ID', None)}\n"
        )
        sys.exit(2)


def check_layout(fixture: Path) -> list[str]:
    errors: list[str] = []
    for required in ("README.md", "expected-findings.json", "expected-aac.json"):
        if not (fixture / required).exists():
            errors.append(f"missing required file: {required}")
    return errors


def load_json(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8"),
        parse_constant=_reject_constant,
        object_pairs_hook=_no_duplicate_object_pairs,
    )


def validate_expected_findings_doc(doc: dict, fixture: Path) -> list[str]:
    schema = load_json(EXPECTED_FINDINGS_SCHEMA)
    validator = Draft202012Validator(schema, format_checker=FORMAT_CHECKER)
    errors = [
        f"{list(error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path))
    ]
    if doc.get("fixture_id") != fixture.name:
        errors.append(
            f"fixture_id mismatch: expected {fixture.name}, got {doc.get('fixture_id')}"
        )
    ids = [
        finding.get("finding_id")
        for finding in doc.get("expected_findings", [])
        if isinstance(finding, dict)
    ]
    duplicate_ids = sorted({fid for fid in ids if fid and ids.count(fid) > 1})
    if duplicate_ids:
        errors.append(f"duplicate expected finding ids: {duplicate_ids}")
    return errors


def validate_json_schema(doc: dict, schema_path: Path) -> list[str]:
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema, format_checker=FORMAT_CHECKER)
    return [
        f"{list(error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path))
    ]


def validate_manifest(fixtures: list[Path]) -> list[str]:
    errors: list[str] = []
    if not MANIFEST_PATH.exists():
        return ["missing corpus.manifest.json"]
    try:
        manifest = load_json(MANIFEST_PATH)
    except (json.JSONDecodeError, ValueError) as e:
        return [f"invalid corpus.manifest.json: {e}"]
    errors += validate_json_schema(manifest, MANIFEST_SCHEMA)

    fixture_names = [fixture.name for fixture in fixtures]
    manifest_fixtures = manifest.get("fixtures", [])
    manifest_names: list[str] = []
    for item in manifest_fixtures:
        if isinstance(item, dict):
            fixture_id = item.get("fixture_id")
            if isinstance(fixture_id, str):
                manifest_names.append(fixture_id)
    if sorted(manifest_names) != sorted(fixture_names):
        errors.append(
            f"manifest fixture ids do not match fixture directories: "
            f"manifest={sorted(manifest_names)}, dirs={sorted(fixture_names)}"
        )

    for item in manifest_fixtures:
        if not isinstance(item, dict):
            continue
        fixture_id = item.get("fixture_id")
        if not isinstance(fixture_id, str):
            continue
        fixture = FIXTURES_DIR / fixture_id
        if not fixture.exists():
            continue
        try:
            expected_findings_doc = load_json(fixture / "expected-findings.json")
            aac = load_json(fixture / "expected-aac.json")
        except (json.JSONDecodeError, ValueError) as e:
            errors.append(f"{fixture_id}: cannot load fixture docs for manifest check: {e}")
            continue
        expected_count = item.get("expected_finding_count")
        actual_expected_count = len(expected_findings_doc.get("expected_findings", []) or [])
        actual_aac_count = len(aac.get("findings", []) or [])
        if expected_count != actual_expected_count or expected_count != actual_aac_count:
            errors.append(
                f"{fixture_id}: manifest expected_finding_count={expected_count}, "
                f"expected-findings={actual_expected_count}, AAC={actual_aac_count}"
            )
        if item.get("expected_verdict") != aac.get("verdict"):
            errors.append(
                f"{fixture_id}: manifest expected_verdict={item.get('expected_verdict')}, "
                f"AAC verdict={aac.get('verdict')}"
            )
        profile = aac.get("profile", {})
        if item.get("aac_profile") != profile.get("profile_id"):
            errors.append(
                f"{fixture_id}: manifest aac_profile={item.get('aac_profile')}, "
                f"AAC profile={profile.get('profile_id')}"
            )
        if item.get("assurance_level") != profile.get("assurance_level"):
            errors.append(
                f"{fixture_id}: manifest assurance_level={item.get('assurance_level')}, "
                f"AAC assurance_level={profile.get('assurance_level')}"
            )
        findings = aac.get("findings", []) or []
        categories = {
            finding.get("category")
            for finding in findings
            if isinstance(finding, dict)
        }
        primary = item.get("primary_threat_class")
        if primary == "none":
            if findings:
                errors.append(f"{fixture_id}: primary_threat_class is none but AAC has findings")
        elif primary not in categories:
            errors.append(
                f"{fixture_id}: primary_threat_class={primary} not found in AAC finding categories"
            )
        errors += validate_coverage_claims(fixture_id, item)
    return errors


def validate_coverage_claims(fixture_id: str, item: dict) -> list[str]:
    expected_verdict = item.get("expected_verdict")
    expected_finding_count = item.get("expected_finding_count")
    minimum = item.get("minimum_detector_class")
    coverage_value = item.get("expected_coverage")
    coverage = coverage_value if isinstance(coverage_value, dict) else {}
    errors: list[str] = []
    if expected_finding_count == 0:
        if expected_verdict != "pass":
            errors.append(
                f"{fixture_id}: fixtures with no expected findings must have pass verdict"
            )
        for detector_class in ("static-declared", "static-extended", "trace-aware"):
            if coverage.get(detector_class) != "pass":
                errors.append(
                    f"{fixture_id}: clean fixture coverage {detector_class} must be pass"
                )
        return errors

    expected_by_minimum = {
        "static-declared": {
            "static-declared": "catch",
            "static-extended": "catch",
            "trace-aware": "catch",
        },
        "static-extended": {
            "static-declared": "miss",
            "static-extended": "catch",
            "trace-aware": "catch",
        },
        "trace-aware": {
            "static-declared": "miss",
            "static-extended": "miss",
            "trace-aware": "catch",
        },
    }
    if not isinstance(minimum, str):
        errors.append(f"{fixture_id}: unknown minimum_detector_class={minimum}")
        return errors
    expected = expected_by_minimum.get(minimum)
    if expected is None:
        errors.append(f"{fixture_id}: unknown minimum_detector_class={minimum}")
        return errors
    for detector_class, expected_value in expected.items():
        if coverage.get(detector_class) != expected_value:
            errors.append(
                f"{fixture_id}: expected_coverage.{detector_class} must be "
                f"{expected_value} for minimum_detector_class={minimum}"
            )
    return errors


def validate_scorecard_template(fixtures: list[Path]) -> list[str]:
    errors: list[str] = []
    if not SCORECARD_TEMPLATE_PATH.exists():
        return ["missing scorecard-template.json"]
    if not SCORECARD_TEMPLATE_SCHEMA.exists():
        return ["missing scorecard-template.schema.json"]
    try:
        scorecard = load_json(SCORECARD_TEMPLATE_PATH)
    except (json.JSONDecodeError, ValueError) as e:
        return [f"invalid scorecard-template.json: {e}"]
    errors += validate_json_schema(scorecard, SCORECARD_TEMPLATE_SCHEMA)

    fixture_names = [fixture.name for fixture in fixtures]
    result_names: list[str] = []
    for item in scorecard.get("per_fixture_results", []):
        if isinstance(item, dict):
            fixture_id = item.get("fixture_id")
            if isinstance(fixture_id, str):
                result_names.append(fixture_id)
    if sorted(result_names) != sorted(fixture_names):
        errors.append(
            "scorecard fixture ids do not match fixture directories: "
            f"scorecard={sorted(result_names)}, dirs={sorted(fixture_names)}"
        )
    fixtures_total = scorecard.get("summary", {}).get("fixtures_total")
    if fixtures_total != len(fixtures):
        errors.append(
            f"scorecard summary.fixtures_total={fixtures_total}, expected={len(fixtures)}"
        )
    return errors


def findings_consistent(expected_findings_doc: dict, aac: dict) -> list[str]:
    """Confirm that the AAC's findings match expected-findings.json."""
    errors: list[str] = []
    expected = expected_findings_doc.get("expected_findings", [])
    aac_findings = aac.get("findings", [])
    if not isinstance(expected, list) or not isinstance(aac_findings, list):
        return ["expected_findings and AAC findings must both be arrays"]

    expected_ids = [f.get("finding_id") for f in expected if isinstance(f, dict)]
    aac_ids = [f.get("finding_id") for f in aac_findings if isinstance(f, dict)]
    duplicate_expected = sorted(
        {fid for fid in expected_ids if fid and expected_ids.count(fid) > 1}
    )
    duplicate_aac = sorted({fid for fid in aac_ids if fid and aac_ids.count(fid) > 1})
    if duplicate_expected:
        errors.append(f"expected-findings has duplicate finding ids: {duplicate_expected}")
    if duplicate_aac:
        errors.append(f"AAC has duplicate finding ids: {duplicate_aac}")

    expected_id_set = {fid for fid in expected_ids if fid}
    aac_id_set = {fid for fid in aac_ids if fid}
    if expected_id_set != aac_id_set:
        missing = sorted(expected_id_set - aac_id_set)
        extra = sorted(aac_id_set - expected_id_set)
        if missing:
            errors.append(f"AAC missing finding ids: {missing}")
        if extra:
            errors.append(f"AAC has unexpected finding ids: {extra}")
    expected_by_id = {
        f["finding_id"]: f
        for f in expected
        if isinstance(f, dict) and isinstance(f.get("finding_id"), str)
    }
    for aac_finding in aac_findings:
        if not isinstance(aac_finding, dict):
            errors.append(f"AAC finding is not an object: {aac_finding!r}")
            continue
        fid = aac_finding.get("finding_id")
        if not isinstance(fid, str):
            errors.append(f"AAC finding missing string finding_id: {aac_finding!r}")
            continue
        if fid in expected_by_id:
            if aac_finding.get("severity") != expected_by_id[fid].get("severity"):
                errors.append(
                    f"finding {fid}: severity mismatch "
                    f"(expected {expected_by_id[fid].get('severity')}, "
                    f"got {aac_finding.get('severity')})"
                )
            if aac_finding.get("category") != expected_by_id[fid].get("category"):
                errors.append(
                    f"finding {fid}: category mismatch "
                    f"(expected {expected_by_id[fid].get('category')}, "
                    f"got {aac_finding.get('category')})"
                )
            if aac_finding.get("title") != expected_by_id[fid].get("title"):
                errors.append(
                    f"finding {fid}: title mismatch "
                    f"(expected {expected_by_id[fid].get('title')}, "
                    f"got {aac_finding.get('title')})"
                )
            if aac_finding.get("subject_asset_id") != expected_by_id[fid].get(
                "subject_asset_id"
            ):
                errors.append(
                    f"finding {fid}: subject_asset_id mismatch "
                    f"(expected {expected_by_id[fid].get('subject_asset_id')}, "
                    f"got {aac_finding.get('subject_asset_id')})"
                )
            if aac_finding.get("description") != expected_by_id[fid].get("description"):
                errors.append(f"finding {fid}: description mismatch")
    return errors


def directory_digest(path: Path) -> str:
    entries: list[dict[str, str]] = []
    for file_path in sorted(path.rglob("*")):
        rel_path = file_path.relative_to(path)
        if file_path.is_symlink():
            raise ValueError(f"symlink not allowed in fixture tree: {file_path}")
        if any(part in DIGEST_IGNORED_DIRS for part in rel_path.parts):
            continue
        if file_path.name in DIGEST_IGNORED_FILE_NAMES:
            continue
        if file_path.suffix in DIGEST_IGNORED_SUFFIXES:
            continue
        if not file_path.is_file():
            continue
        entries.append(
            {
                "path": rel_path.as_posix(),
                "sha256": hashlib.sha256(file_path.read_bytes()).hexdigest(),
            }
        )
    return _sha256_bytes(_canonical_json_bytes(entries))


def local_asset_digest(path: Path) -> str:
    if path.is_dir():
        return directory_digest(path)
    return _sha256_file(path)


def evidence_uri_values(case: dict) -> set[str]:
    refs: set[str] = set()

    def add(value: Any) -> None:
        if isinstance(value, str) and value.startswith("evidence://"):
            refs.add(value)

    add(case.get("aibom_ref"))
    add(case.get("graph_snapshot_ref"))
    for run in case.get("coverage", {}).get("detector_runs", []) or []:
        add(run.get("evidence_ref"))
    for condition in case.get("release_conditions", []) or []:
        add(condition.get("evidence_ref"))
    for trace_ref in (
        case.get("coverage", {}).get("runtime_coverage", {}).get("trace_refs", [])
        or []
    ):
        add(trace_ref)
    for finding in case.get("findings", []) or []:
        for ref in finding.get("evidence_refs", []) or []:
            add(ref)
    for result in case.get("eval_results", []) or []:
        add(result.get("evidence_ref"))
    for event in case.get("runtime_events", []) or []:
        add(event.get("trace_ref"))
    for mapping in case.get("compliance_mappings", []) or []:
        for ref in mapping.get("evidence_refs", []) or []:
            add(ref)
    return refs


def fixture_evidence_prefix(fixture: Path) -> str:
    fixture_number = fixture.name.split("-", 1)[0]
    return f"evidence://dvaac/{fixture_number}/"


def file_excerpt_digest(fixture: Path, remainder: str) -> tuple[str | None, str | None]:
    match = re.fullmatch(
        r"files/(?P<path>[^#]+)#L(?P<start>[1-9][0-9]*)-L(?P<end>[1-9][0-9]*)",
        remainder,
    )
    if not match:
        return None, f"unsupported file evidence URI suffix: {remainder}"
    rel_path = Path(match.group("path"))
    if rel_path.is_absolute() or ".." in rel_path.parts:
        return None, f"unsafe file evidence path: {rel_path}"
    source_path = fixture / rel_path
    try:
        validate_path_within_fixture(fixture, source_path, "file evidence target")
    except ValueError as e:
        return None, str(e)
    if not source_path.exists():
        return None, f"file evidence target not found: {source_path.relative_to(ROOT)}"
    start = int(match.group("start"))
    end = int(match.group("end"))
    lines = source_path.read_text(encoding="utf-8").splitlines()
    if end < start or end > len(lines):
        return None, (
            f"file evidence line range out of bounds for "
            f"{source_path.relative_to(ROOT)}: L{start}-L{end}"
        )
    excerpt = "\n".join(lines[start - 1 : end]) + "\n"
    return _sha256_bytes(excerpt.encode("utf-8")), None


def evidence_artifact_digest(fixture: Path, uri: str) -> tuple[str | None, str | None]:
    prefix = fixture_evidence_prefix(fixture)
    if not uri.startswith(prefix):
        return None, f"evidence URI does not match fixture {fixture.name}: {uri}"
    remainder = uri.removeprefix(prefix)
    if remainder.startswith("files/"):
        return file_excerpt_digest(fixture, remainder)
    rel_path = Path(remainder)
    if rel_path.is_absolute() or ".." in rel_path.parts:
        return None, f"unsafe evidence artifact path: {rel_path}"
    local_path = fixture / "evidence" / rel_path
    try:
        validate_path_within_fixture(fixture, local_path, "evidence artifact file")
    except ValueError as e:
        return None, str(e)
    if not local_path.exists():
        return None, f"evidence artifact file not found: {local_path.relative_to(ROOT)}"
    return _sha256_file(local_path), None


def local_digests_consistent(fixture: Path, aac: dict) -> list[str]:
    errors = fixture_symlink_errors(fixture)
    if errors:
        return errors
    for asset in aac.get("assets", []) or []:
        if not isinstance(asset, dict):
            continue
        declared = asset.get("digest")
        source_uri = asset.get("source_uri")
        if not declared or not source_uri:
            continue
        source_path = ROOT / source_uri
        try:
            validate_path_within_fixture(fixture, source_path, "asset source_uri")
        except ValueError as e:
            errors.append(str(e))
            continue
        if not source_path.exists():
            errors.append(f"asset source_uri not found: {source_uri}")
            continue
        try:
            computed = local_asset_digest(source_path)
        except ValueError as e:
            errors.append(str(e))
            continue
        if declared != computed:
            errors.append(
                f"asset digest mismatch for {asset.get('asset_id')}: "
                f"declared={declared}, computed={computed}"
            )

    refs = evidence_uri_values(aac)
    artifact_uris: set[str] = set()
    for artifact in aac.get("evidence_artifacts", []) or []:
        if not isinstance(artifact, dict):
            errors.append(f"evidence_artifact is not an object: {artifact!r}")
            continue
        uri = artifact.get("uri")
        declared = artifact.get("digest")
        if not isinstance(uri, str) or not isinstance(declared, str):
            errors.append(f"evidence_artifact lacks uri/digest strings: {artifact!r}")
            continue
        artifact_uris.add(uri)
        computed, error = evidence_artifact_digest(fixture, uri)
        if error:
            errors.append(error)
            continue
        if declared != computed:
            errors.append(
                f"evidence artifact digest mismatch for {uri}: "
                f"declared={declared}, computed={computed}"
            )
    extra_artifacts = sorted(uri for uri in artifact_uris - refs if isinstance(uri, str))
    missing_artifacts = sorted(refs - artifact_uris)
    if missing_artifacts:
        errors.append(f"evidence refs missing from evidence_artifacts: {missing_artifacts}")
    if extra_artifacts:
        errors.append(f"unreferenced evidence_artifacts: {extra_artifacts}")
    return errors


def demo_evidence_consistent(aac: dict) -> list[str]:
    evidence = aac.get("evidence", {})
    errors: list[str] = []
    if evidence.get("signed_by") != DEMO_SIGNED_BY:
        errors.append(
            f"evidence.signed_by must be {DEMO_SIGNED_BY}, got {evidence.get('signed_by')}"
        )
    if evidence.get("key_id") != DEMO_KEY_ID:
        errors.append(f"evidence.key_id must be {DEMO_KEY_ID}, got {evidence.get('key_id')}")
    if evidence.get("public_key_ref"):
        errors.append("demo-signed DVAAC templates must omit evidence.public_key_ref")
    if evidence.get("offline_verifier") != "python verifier/verify.py case.json --allow-demo-key":
        errors.append("evidence.offline_verifier must use --allow-demo-key for demo-signed cases")
    return errors


def policy_inputs_consistent(aac_module: Any, aac: dict) -> list[str]:
    errors: list[str] = []
    for decision in aac.get("policy_decisions", []) or []:
        if not isinstance(decision, dict):
            continue
        declared = decision.get("inputs_hash")
        payload = {k: v for k, v in decision.items() if k != "inputs_hash"}
        computed = _sha256_bytes(aac_module.canonicalize(payload))
        if declared != computed:
            errors.append(
                f"policy inputs_hash mismatch for {decision.get('policy_id')}: "
                f"declared={declared}, computed={computed}"
            )
    return errors


def sign_case_copy(aac_module: Any, case: dict) -> dict:
    priv, _ = aac_module._demo_keypair()
    signed = copy.deepcopy(case)
    aac_module.sign_case(signed, priv)
    return signed


def verify_signed_case(aac_module: Any, signed: dict, fixture_id: str) -> list[str]:
    """Run the AAC verifier on a signed case."""
    errors: list[str] = []
    with tempfile.NamedTemporaryFile(
        "w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(signed, f)
        tmp_path = Path(f.name)
    try:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = aac_module.verify(
                tmp_path,
                public_key_path=None,
                allow_demo_key=True,
                verbose=False,
            )
        if rc != 0:
            detail = output.getvalue().strip()
            message = f"AAC reference verifier returned exit code {rc} for {fixture_id}"
            if detail:
                message += f": {detail}"
            errors.append(message)
    finally:
        with contextlib.suppress(OSError):
            tmp_path.unlink()
    return errors


def write_signed_case(output_dir: Path, fixture: Path, signed: dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{fixture.name}-signed-aac.json"
    output_path.write_text(
        json.dumps(signed, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def verify_fixture(
    fixture: Path,
    aac_module: Any,
    signed_output_dir: Path | None = None,
) -> tuple[bool, list[str]]:
    layout_errors = check_layout(fixture)
    if layout_errors:
        return False, layout_errors
    try:
        expected_findings_doc = load_json(fixture / "expected-findings.json")
        aac = load_json(fixture / "expected-aac.json")
    except (json.JSONDecodeError, ValueError) as e:
        return False, [f"invalid JSON: {e}"]
    errors = validate_expected_findings_doc(expected_findings_doc, fixture)
    errors += findings_consistent(expected_findings_doc, aac)
    errors += local_digests_consistent(fixture, aac)
    errors += policy_inputs_consistent(aac_module, aac)
    errors += demo_evidence_consistent(aac)
    signed = sign_case_copy(aac_module, aac)
    errors += verify_signed_case(aac_module, signed, fixture.name)
    if not errors and signed_output_dir is not None:
        write_signed_case(signed_output_dir, fixture, signed)
    return (not errors), errors


def main() -> int:
    parser = argparse.ArgumentParser(description="DVAAC fixture conformance runner")
    parser.add_argument(
        "--aac-verifier",
        type=Path,
        default=Path(os.environ.get("AAC_VERIFIER_PATH", str(default_aac_verifier_path()))),
        help="Path to the AAC reference verifier (verify.py).",
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=FIXTURES_DIR,
        help="Directory containing DVAAC fixtures.",
    )
    parser.add_argument(
        "--write-signed",
        type=Path,
        default=None,
        metavar="DIR",
        help="Write demo-signed AACs to DIR after each fixture passes conformance.",
    )
    args = parser.parse_args()

    aac_module = load_aac_verifier(args.aac_verifier)

    fixtures = sorted(
        p for p in args.fixtures_dir.iterdir() if p.is_dir() and (p / "README.md").exists()
    )
    if not fixtures:
        print(f"No fixtures found in {args.fixtures_dir}")
        return 2

    overall_ok = True
    print(f"DVAAC: running {len(fixtures)} fixture(s)\n")
    manifest_errors = validate_manifest(fixtures)
    mark = "OK  " if not manifest_errors else "FAIL"
    print(f"  [{mark}] corpus.manifest.json")
    for err in manifest_errors:
        print(f"         - {err}")
    if manifest_errors:
        overall_ok = False
    scorecard_errors = validate_scorecard_template(fixtures)
    mark = "OK  " if not scorecard_errors else "FAIL"
    print(f"  [{mark}] scorecard-template.json")
    for err in scorecard_errors:
        print(f"         - {err}")
    if scorecard_errors:
        overall_ok = False

    for fixture in fixtures:
        ok, errs = verify_fixture(fixture, aac_module, args.write_signed)
        mark = "OK  " if ok else "FAIL"
        print(f"  [{mark}] {fixture.name}")
        for err in errs:
            print(f"         - {err}")
        if not ok:
            overall_ok = False

    print()
    if overall_ok:
        print("DVAAC: all fixtures conform.")
        return 0
    print("DVAAC: one or more fixtures failed conformance. Fix and re-run.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
