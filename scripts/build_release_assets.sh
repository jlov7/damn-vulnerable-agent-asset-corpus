#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "usage: scripts/build_release_assets.sh vX.Y.Z [out-dir]" >&2
  exit 2
fi

TAG="$1"
OUT_DIR="${2:-dist/release}"
# Locate the AAC reference verifier in a sibling checkout. Accept both the
# published repo name (agent-assurance-case) and the local spec working-copy
# name (agent-assurance-case-spec), matching the Makefile's discovery so the
# release builder works in either layout. Honour an explicit AAC_VERIFIER_PATH.
if [[ -n "${AAC_VERIFIER_PATH:-}" ]]; then
  AAC_VERIFIER="$AAC_VERIFIER_PATH"
elif [[ -f ../agent-assurance-case/verifier/verify.py ]]; then
  AAC_VERIFIER="../agent-assurance-case/verifier/verify.py"
elif [[ -f ../agent-assurance-case-spec/verifier/verify.py ]]; then
  AAC_VERIFIER="../agent-assurance-case-spec/verifier/verify.py"
else
  AAC_VERIFIER="../agent-assurance-case/verifier/verify.py"
fi
# Resolve to an absolute path. write-signed runs `make` from a temporary archive
# of the tag, so a relative AAC_VERIFIER would resolve against that temp dir
# rather than this checkout and the verifier would not be found.
if [[ -f "$AAC_VERIFIER" ]]; then
  AAC_VERIFIER="$(cd "$(dirname "$AAC_VERIFIER")" && pwd)/$(basename "$AAC_VERIFIER")"
fi
PYTHON_BIN="${PYTHON:-python3}"
TEMP_ROOT="$(mktemp -d)"

cleanup() {
  rm -rf "$TEMP_ROOT"
}
trap cleanup EXIT

if [[ "$TAG" != v* ]]; then
  echo "release tag must start with v: $TAG" >&2
  exit 2
fi

expected_version="${TAG#v}"
commit="$(git rev-parse --verify "${TAG}^{commit}")"
SOURCE_DIR="$TEMP_ROOT/source"
SIGNED_DIR="$TEMP_ROOT/signed-aac"
mkdir -p "$SOURCE_DIR"
git archive --format=tar "$commit" | tar -x -C "$SOURCE_DIR"

corpus_version="$(
  "$PYTHON_BIN" - "$SOURCE_DIR" <<'PY'
import json
import sys
from pathlib import Path

source_dir = Path(sys.argv[1])
print(json.loads((source_dir / "corpus.manifest.json").read_text())["corpus_version"])
PY
)"

if [[ "$corpus_version" != "$expected_version" ]]; then
  echo "tag $TAG does not match corpus version $corpus_version" >&2
  exit 1
fi

out_parent="$(dirname "$OUT_DIR")"
out_base="$(basename "$OUT_DIR")"
mkdir -p "$out_parent"
OUT_DIR="$(cd "$out_parent" && pwd)/$out_base"

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

make -C "$SOURCE_DIR" write-signed \
  PYTHON="$PYTHON_BIN" \
  SIGNED_AAC_DIR="$SIGNED_DIR" \
  AAC_VERIFIER_PATH="$AAC_VERIFIER"

archive_name="signed-aac-${TAG}.tar.gz"
archive="$OUT_DIR/$archive_name"
"$PYTHON_BIN" - "$SIGNED_DIR" "$archive" <<'PY'
import gzip
import sys
import tarfile
from pathlib import Path

source_dir = Path(sys.argv[1])
archive = Path(sys.argv[2])


def stable_info(path: Path, arcname: str) -> tarfile.TarInfo:
    info = tarfile.TarInfo(arcname)
    info.mtime = 0
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    if path.is_dir():
        info.type = tarfile.DIRTYPE
        info.mode = 0o755
    else:
        info.size = path.stat().st_size
        info.mode = 0o644
    return info


with archive.open("wb") as raw:
    with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode="w") as tar:
            tar.addfile(stable_info(source_dir, "signed-aac"))
            for path in sorted(source_dir.rglob("*")):
                relative = path.relative_to(source_dir)
                arcname = str(Path("signed-aac") / relative)
                info = stable_info(path, arcname)
                if path.is_dir():
                    tar.addfile(info)
                else:
                    with path.open("rb") as file_obj:
                        tar.addfile(info, file_obj)
PY
shasum -a 256 "$archive" | sed "s#  $archive#  $archive_name#" > "${archive}.sha256"

cp "$SIGNED_DIR/RELEASE-MANIFEST.json" "$OUT_DIR/RELEASE-MANIFEST.json"
cp "$SIGNED_DIR/SHA256SUMS" "$OUT_DIR/SHA256SUMS"

(cd "$OUT_DIR" && shasum -a 256 -c "${archive_name}.sha256")

printf 'release assets written to %s\n' "$OUT_DIR"
find "$OUT_DIR" -maxdepth 1 -type f -print | sort
