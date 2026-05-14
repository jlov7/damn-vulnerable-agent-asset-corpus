#!/usr/bin/env python3
"""Write the DVAAC release manifest for generated signed AAC artifacts."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
from typing import Any

import verify_fixtures

ROOT = verify_fixtures.ROOT
STATIC_RELEASE_FILES = [
    Path("corpus.manifest.json"),
    Path("scorecard-template.json"),
    Path("corpus.manifest.schema.json"),
    Path("scorecard-template.schema.json"),
    Path("runner/expected-findings.schema.json"),
]


def sha256_hex(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = verify_fixtures.load_json(path)
    if not isinstance(value, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    return value


def release_label(path: Path, signed_dir: Path) -> str:
    if path.parent == signed_dir:
        return path.name
    return path.relative_to(ROOT).as_posix()


def release_files(signed_dir: Path) -> list[Path]:
    signed_cases = sorted(signed_dir.glob("*-signed-aac.json"))
    if not signed_cases:
        raise SystemExit(f"no signed AAC artifacts found in {signed_dir}")
    return [ROOT / rel for rel in STATIC_RELEASE_FILES] + signed_cases


def write_sha256sums(signed_dir: Path, paths: list[Path]) -> None:
    manifest_path = signed_dir / "RELEASE-MANIFEST.json"
    rows = [
        f"{sha256_hex(path)}  {release_label(path, signed_dir)}"
        for path in [*paths, manifest_path]
    ]
    (signed_dir / "SHA256SUMS").write_text("\n".join(rows) + "\n", encoding="utf-8")


def write_release_manifest(signed_dir: Path, aac_verifier_path: Path) -> None:
    aac_module = verify_fixtures.load_aac_verifier(aac_verifier_path)
    private_key, _public_key = aac_module._demo_keypair()
    corpus_manifest = load_json(ROOT / "corpus.manifest.json")
    compatibility = corpus_manifest["aac_compatibility"]
    paths = release_files(signed_dir)
    entries = [
        {
            "path": release_label(path, signed_dir),
            "sha256": sha256_hex(path),
        }
        for path in paths
    ]
    unsigned = {
        "schema_version": "dvaac.release-manifest.v0.1",
        "corpus_id": corpus_manifest["corpus_id"],
        "corpus_version": corpus_manifest["corpus_version"],
        "aac_version": compatibility["aac_version"],
        "aac_commit": compatibility["aac_commit"],
        "entries": entries,
        "signature_note": "Demo-key signature for release artifact binding; not an issuer-trust claim.",
    }
    signature = private_key.sign(aac_module.canonicalize(unsigned))
    release_manifest = {
        **unsigned,
        "signature": {
            "algorithm": "Ed25519",
            "canonicalization": "AAC/JCS canonical JSON",
            "signed_by": verify_fixtures.DEMO_SIGNED_BY,
            "key_id": verify_fixtures.DEMO_KEY_ID,
            "value": "ed25519:" + base64.b64encode(signature).decode("ascii"),
        },
    }
    (signed_dir / "RELEASE-MANIFEST.json").write_text(
        json.dumps(release_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_sha256sums(signed_dir, paths)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("signed_dir", type=Path)
    parser.add_argument("--aac-verifier", type=Path, default=verify_fixtures.default_aac_verifier_path())
    args = parser.parse_args()
    write_release_manifest(args.signed_dir, args.aac_verifier)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
