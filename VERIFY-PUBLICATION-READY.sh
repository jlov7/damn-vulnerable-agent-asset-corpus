#!/usr/bin/env bash
# Publication-readiness gate for the DVAAC v0.1.4 artifact.
#
# Run this before publishing a new release or after release-facing hardening.
# Exit code 0 = ready for publication review. Non-zero = stop and fix.

set -uo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR" || exit 2

PASS=0
FAIL=0
RESULTS=()
PYTHON_BIN="${PYTHON:-python3}"
TEMP_ROOT=""
AAC_VERIFIER="${AAC_VERIFIER_PATH:-}"
PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/tmp/dvaac_pub_gate_pycache}"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPYCACHEPREFIX

EXPECTED_RELEASE="v0.1.4"
EXPECTED_AAC_TAG="v0.2-candidate.7"
EXPECTED_AAC_COMMIT="689198d9c249a966a0abab6415ae8668efb512d9"

# shellcheck disable=SC2329
cleanup() {
  if [[ -n "$TEMP_ROOT" && -d "$TEMP_ROOT" ]]; then
    rm -rf "$TEMP_ROOT"
  fi
}
trap cleanup EXIT

check() {
  local name="$1"
  local ok="$2"
  local detail="${3:-}"
  if [[ "$ok" == "ok" ]]; then
    RESULTS+=("  [OK  ] $name${detail:+ — $detail}")
    PASS=$((PASS + 1))
  else
    RESULTS+=("  [FAIL] $name${detail:+ — $detail}")
    FAIL=$((FAIL + 1))
  fi
}

tail_detail() {
  printf "%s\n" "$1" | tail -n 6 | tr '\n' ' ' | sed 's/[[:space:]]\+/ /g'
}

require_tool() {
  local tool="$1"
  if command -v "$tool" >/dev/null 2>&1; then
    check "tool available: $tool" "ok"
  else
    check "tool available: $tool" "fail" "required on PATH"
  fi
}

require_tool git
require_tool go
require_tool make
require_tool uv
require_tool uvx

TEMP_ROOT=$(mktemp -d /tmp/dvaac_pub_gate.XXXXXX)
export HYPOTHESIS_STORAGE_DIRECTORY="${HYPOTHESIS_STORAGE_DIRECTORY:-$TEMP_ROOT/hypothesis}"

if [[ -z "${PYTHON:-}" ]]; then
  if python3 -m venv "$TEMP_ROOT/venv" \
    && PIP_NO_CACHE_DIR=1 "$TEMP_ROOT/venv/bin/python" -m pip install --upgrade pip >/dev/null \
    && PIP_NO_CACHE_DIR=1 "$TEMP_ROOT/venv/bin/python" -m pip install -r runner/requirements.txt -r runner/requirements-dev.txt >/dev/null; then
    PYTHON_BIN="$TEMP_ROOT/venv/bin/python"
    check "isolated Python environment" "ok" "$PYTHON_BIN"
  else
    check "isolated Python environment" "fail" "could not create temp venv or install runner dependencies"
  fi
else
  check "Python environment" "ok" "$PYTHON_BIN"
fi

if [[ -z "$AAC_VERIFIER" ]]; then
  if [[ -f "../agent-assurance-case/verifier/verify.py" ]]; then
    AAC_VERIFIER="../agent-assurance-case/verifier/verify.py"
  else
    if git clone --branch "$EXPECTED_AAC_TAG" --depth 1 https://github.com/jlov7/agent-assurance-case "$TEMP_ROOT/agent-assurance-case" >/dev/null 2>&1; then
      AAC_VERIFIER="$TEMP_ROOT/agent-assurance-case/verifier/verify.py"
    fi
  fi
fi

if [[ -f "$AAC_VERIFIER" ]]; then
  aac_commit=$(git -C "$(dirname "$AAC_VERIFIER")/.." rev-parse HEAD 2>/dev/null || true)
  if [[ "$aac_commit" == "$EXPECTED_AAC_COMMIT" ]]; then
    check "AAC verifier available" "ok" "$AAC_VERIFIER"
  else
    check "AAC verifier available" "fail" "expected $EXPECTED_AAC_COMMIT, got ${aac_commit:-unknown}"
  fi
else
  check "AAC verifier available" "fail" "set AAC_VERIFIER_PATH or keep the AAC checkout adjacent"
fi

junk=$(find . \
  \( -path ./.git -o -path ./.venv \) -prune -o \
  \( -name ".pytest_cache" -o -name ".ruff_cache" -o -name ".hypothesis" -o -name "__pycache__" -o -name "pytest-cache-files-*" -o -name "__MACOSX" -o -name "*.pyc" -o -name ".DS_Store" \) \
  -print 2>/dev/null | sort)
if [[ -n "$junk" ]]; then
  count=$(printf "%s\n" "$junk" | wc -l | tr -d ' ')
  first=$(printf "%s\n" "$junk" | head -1)
  check "no build cache or junk artifacts" "fail" "$count item(s) found; first: $first"
else
  check "no build cache or junk artifacts" "ok"
fi

if grep -Fq "This release is pinned to AAC \`$EXPECTED_AAC_TAG\` at commit \`$EXPECTED_AAC_COMMIT\`." README.md \
  && grep -Fq "version: \"${EXPECTED_RELEASE#v}\"" CITATION.cff \
  && [[ -f "docs/release-evidence.${EXPECTED_RELEASE}.json" ]]; then
  check "release metadata synchronized" "ok" "$EXPECTED_RELEASE / $EXPECTED_AAC_TAG"
else
  check "release metadata synchronized" "fail" "README, CITATION.cff, and release evidence must agree"
fi

json_out=$("$PYTHON_BIN" - <<'PY' 2>&1
import json
from pathlib import Path

for path in sorted(Path(".").rglob("*.json")):
    if any(part in {".git", ".venv", "dist"} for part in path.parts):
        continue
    json.loads(path.read_text(encoding="utf-8"))
PY
)
json_rc=$?
if [[ $json_rc -eq 0 ]]; then
  check "tracked JSON parses" "ok"
else
  check "tracked JSON parses" "fail" "$(tail_detail "$json_out")"
fi

schema_out=$("$PYTHON_BIN" - <<'PY' 2>&1
import json
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

for schema_path, instance_path in [
    (Path("corpus.manifest.schema.json"), Path("corpus.manifest.json")),
    (Path("scorecard-template.schema.json"), Path("scorecard-template.json")),
    (Path("docs/release-evidence.schema.json"), Path("docs/release-evidence.v0.1.4.json")),
]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    instance = json.loads(instance_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(instance)
PY
)
schema_rc=$?
if [[ $schema_rc -eq 0 ]]; then
  check "schemas validate shipped instances" "ok"
else
  check "schemas validate shipped instances" "fail" "$(tail_detail "$schema_out")"
fi

conformance_out=$(AAC_VERIFIER_PATH="$AAC_VERIFIER" "$PYTHON_BIN" runner/verify_fixtures.py 2>&1)
conformance_rc=$?
if [[ $conformance_rc -eq 0 && "$conformance_out" == *"DVAAC: all fixtures conform."* ]]; then
  check "fixture conformance" "ok" "16 fixtures"
else
  check "fixture conformance" "fail" "$(tail_detail "$conformance_out")"
fi

pytest_out=$("$PYTHON_BIN" -m pytest tests/ -q -p no:cacheprovider 2>&1)
pytest_rc=$?
if [[ $pytest_rc -eq 0 && "$pytest_out" =~ [0-9]+\ passed ]]; then
  passed=$(printf "%s\n" "$pytest_out" | grep -oE '[0-9]+ passed' | tail -1)
  check "pytest suite passes" "ok" "$passed"
else
  check "pytest suite passes" "fail" "$(tail_detail "$pytest_out")"
fi

if safety_out=$(rm -f /tmp/dvaac_hidden_test_payload.txt \
  && matches="$(find fixtures -type f \( -name 'test_*.py' -o -name '*_test.py' -o -name 'conftest.py' \) -print)" \
  && test -z "$matches" \
  && "$PYTHON_BIN" -m pytest --collect-only -q >/dev/null \
  && test ! -e /tmp/dvaac_hidden_test_payload.txt 2>&1); then
  check "pytest collection safety" "ok"
else
  check "pytest collection safety" "fail" "$(tail_detail "$safety_out")"
fi

signed_dir="$TEMP_ROOT/signed-aac"
signed_out=$(PYTHON="$PYTHON_BIN" AAC_VERIFIER_PATH="$AAC_VERIFIER" SIGNED_AAC_DIR="$signed_dir" make write-signed 2>&1)
signed_rc=$?
signed_count=$(find "$signed_dir" -type f -name '*-signed-aac.json' 2>/dev/null | wc -l | tr -d ' ')
sha_lines=0
[[ -f "$signed_dir/SHA256SUMS" ]] && sha_lines=$(wc -l < "$signed_dir/SHA256SUMS" | tr -d ' ')
if [[ $signed_rc -eq 0 && "$signed_count" == "16" && -f "$signed_dir/RELEASE-MANIFEST.json" && "$sha_lines" == "22" ]]; then
  check "signed AAC release artifacts generate" "ok" "16 signed AACs, 22 checksum lines"
else
  check "signed AAC release artifacts generate" "fail" "$(tail_detail "$signed_out")"
fi

fingerprint_out=$("$PYTHON_BIN" scripts/verify_release_fingerprints.py 2>&1)
fingerprint_rc=$?
if [[ $fingerprint_rc -eq 0 && "$fingerprint_out" == *"DVAAC release fingerprint: valid"* ]]; then
  check "published release fingerprint verifies" "ok"
else
  check "published release fingerprint verifies" "fail" "$(tail_detail "$fingerprint_out")"
fi

if hygiene_out=$("$PYTHON_BIN" scripts/check_public_hygiene.py 2>&1); then
  check "public artifact hygiene" "ok"
else
  check "public artifact hygiene" "fail" "$(tail_detail "$hygiene_out")"
fi

if links_out=$("$PYTHON_BIN" scripts/check_markdown_links.py 2>&1); then
  check "Markdown local links" "ok"
else
  check "Markdown local links" "fail" "$(tail_detail "$links_out")"
fi

if ruff_out=$(uvx ruff check --no-cache runner tests scripts fuzz 2>&1); then
  check "ruff" "ok"
else
  check "ruff" "fail" "$(tail_detail "$ruff_out")"
fi

if pyright_out=$(uv run --with-requirements runner/requirements-dev.txt --with pyright pyright runner tests scripts fuzz 2>&1); then
  check "pyright" "ok"
else
  check "pyright" "fail" "$(tail_detail "$pyright_out")"
fi

if pip_audit_out=$(uv run --with-requirements runner/requirements-dev.txt --with pip-audit pip-audit 2>&1); then
  check "Python dependency audit" "ok"
else
  check "Python dependency audit" "fail" "$(tail_detail "$pip_audit_out")"
fi

if bandit_out=$(uvx bandit -q -r runner scripts fuzz -x tests -s B404,B603,B607 2>&1); then
  check "Bandit static security scan" "ok"
else
  check "Bandit static security scan" "fail" "$(tail_detail "$bandit_out")"
fi

if sbom_out=$("$PYTHON_BIN" scripts/validate_dependency_sbom.py 2>&1); then
  check "runtime dependency SBOM" "ok"
else
  check "runtime dependency SBOM" "fail" "$(tail_detail "$sbom_out")"
fi

if lock_out=$(scripts/validate_dependency_lock.sh 2>&1); then
  check "runtime dependency lock" "ok"
else
  check "runtime dependency lock" "fail" "$(tail_detail "$lock_out")"
fi

if codespell_out=$(uvx codespell . --skip './.git,./.venv,./dist' 2>&1); then
  check "codespell" "ok"
else
  check "codespell" "fail" "$(tail_detail "$codespell_out")"
fi

if reuse_out=$(uvx reuse lint 2>&1); then
  covered=$(printf "%s\n" "$reuse_out" | sed -nE 's#^\* Files with license information: ([0-9]+ / [0-9]+)$#\1#p' | head -1)
  check "REUSE licensing metadata" "ok" "${covered:-all tracked files covered}"
else
  check "REUSE licensing metadata" "fail" "$(tail_detail "$reuse_out")"
fi

if security_insights_out=$(scripts/validate_security_insights.sh 2>&1); then
  check "Security Insights metadata" "ok"
else
  check "Security Insights metadata" "fail" "$(tail_detail "$security_insights_out")"
fi

if repository_posture_out=$("$PYTHON_BIN" scripts/verify_repository_posture.py 2>&1); then
  check "repository posture metadata" "ok"
else
  check "repository posture metadata" "fail" "$(tail_detail "$repository_posture_out")"
fi

if codemeta_out=$("$PYTHON_BIN" scripts/validate_codemeta.py 2>&1); then
  check "CodeMeta metadata" "ok"
else
  check "CodeMeta metadata" "fail" "$(tail_detail "$codemeta_out")"
fi

if citation_out=$("$PYTHON_BIN" scripts/validate_citation.py 2>&1); then
  check "citation metadata consistency" "ok"
else
  check "citation metadata consistency" "fail" "$(tail_detail "$citation_out")"
fi

if cff_out=$(uvx --from cffconvert cffconvert --validate --infile CITATION.cff 2>&1); then
  check "citation metadata" "ok"
else
  check "citation metadata" "fail" "$(tail_detail "$cff_out")"
fi

release_assets_dir="$TEMP_ROOT/release-assets"
if release_asset_out=$(PYTHON="$PYTHON_BIN" AAC_VERIFIER_PATH="$AAC_VERIFIER" scripts/build_release_assets.sh "$EXPECTED_RELEASE" "$release_assets_dir" 2>&1); then
  check "release asset builder dry-run" "ok"
else
  check "release asset builder dry-run" "fail" "$(tail_detail "$release_asset_out")"
fi

if shellcheck_out=$(uvx --from shellcheck-py shellcheck .clusterfuzzlite/build.sh VERIFY-PUBLICATION-READY.sh scripts/build_release_assets.sh scripts/validate_dependency_lock.sh scripts/validate_security_insights.sh 2>&1); then
  check "shellcheck" "ok"
else
  check "shellcheck" "fail" "$(tail_detail "$shellcheck_out")"
fi

post_junk=$(find . \
  \( -path ./.git -o -path ./.venv \) -prune -o \
  \( -name ".pytest_cache" -o -name ".ruff_cache" -o -name ".hypothesis" -o -name "__pycache__" -o -name "pytest-cache-files-*" -o -name "__MACOSX" -o -name "*.pyc" -o -name ".DS_Store" \) \
  -print 2>/dev/null | sort)
if [[ -n "$post_junk" ]]; then
  count=$(printf "%s\n" "$post_junk" | wc -l | tr -d ' ')
  first=$(printf "%s\n" "$post_junk" | head -1)
  check "no post-test cache or junk artifacts" "fail" "$count item(s) found; first: $first"
else
  check "no post-test cache or junk artifacts" "ok"
fi

echo
printf '%s\n' "${RESULTS[@]}"
echo
echo "Summary: $PASS passed, $FAIL failed."
if [[ $FAIL -eq 0 ]]; then
  echo "DVAAC $EXPECTED_RELEASE publication gate: PASSED"
  echo "Ready for publication review."
  exit 0
else
  echo "DVAAC $EXPECTED_RELEASE publication gate: FAILED"
  echo "Fix the failed items before pushing public."
  exit 1
fi
