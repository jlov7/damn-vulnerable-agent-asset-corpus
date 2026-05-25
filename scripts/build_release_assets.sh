#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "usage: scripts/build_release_assets.sh vX.Y.Z [out-dir]" >&2
  exit 2
fi

TAG="$1"
OUT_DIR="${2:-dist/release}"
SIGNED_DIR="dist/signed-aac"
AAC_VERIFIER="${AAC_VERIFIER_PATH:-../agent-assurance-case/verifier/verify.py}"

if [[ "$TAG" != v* ]]; then
  echo "release tag must start with v: $TAG" >&2
  exit 2
fi

expected_version="${TAG#v}"
corpus_version="$(
  python3 - <<'PY'
import json
from pathlib import Path

print(json.loads(Path("corpus.manifest.json").read_text())["corpus_version"])
PY
)"

if [[ "$corpus_version" != "$expected_version" ]]; then
  echo "tag $TAG does not match corpus version $corpus_version" >&2
  exit 1
fi

rm -rf "$SIGNED_DIR" "$OUT_DIR"
mkdir -p "$OUT_DIR"

make write-signed SIGNED_AAC_DIR="$SIGNED_DIR" AAC_VERIFIER_PATH="$AAC_VERIFIER"

archive_name="signed-aac-${TAG}.tar.gz"
archive="$OUT_DIR/$archive_name"
tar -czf "$archive" -C dist signed-aac
shasum -a 256 "$archive" | sed "s#  $archive#  $archive_name#" > "${archive}.sha256"

cp "$SIGNED_DIR/RELEASE-MANIFEST.json" "$OUT_DIR/RELEASE-MANIFEST.json"
cp "$SIGNED_DIR/SHA256SUMS" "$OUT_DIR/SHA256SUMS"

(cd "$OUT_DIR" && shasum -a 256 -c "${archive_name}.sha256")

printf 'release assets written to %s\n' "$OUT_DIR"
find "$OUT_DIR" -maxdepth 1 -type f -print | sort
