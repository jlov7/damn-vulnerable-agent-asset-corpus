#!/usr/bin/env python3
"""Verify the published DVAAC release fingerprint from current main."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import venv
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RELEASE_EVIDENCE_PATH = ROOT / "docs" / "release-evidence.v0.1.4.json"


def run(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    allowed_exit_codes: set[int] | None = None,
) -> None:
    print(f"$ {' '.join(command)}", flush=True)
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    completed = subprocess.run(command, cwd=cwd, env=merged_env, check=False)
    expected = allowed_exit_codes or {0}
    if completed.returncode not in expected:
        raise subprocess.CalledProcessError(completed.returncode, command)


def output(command: list[str], *, cwd: Path) -> str:
    return subprocess.check_output(command, cwd=cwd, text=True).strip()


def require_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"required tool not found on PATH: {name}")


def load_release_evidence() -> dict[str, Any]:
    return json.loads(RELEASE_EVIDENCE_PATH.read_text(encoding="utf-8"))


def require_equal(label: str, actual: str, expected: str) -> None:
    if actual != expected:
        raise SystemExit(f"{label} mismatch: {actual} != {expected}")


def signed_tag_evidence(
    evidence: dict[str, Any],
    artifact: str,
) -> dict[str, Any]:
    matches = [item for item in evidence["signed_tags"] if item["artifact"] == artifact]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise SystemExit(f"release evidence missing signed tag for {artifact}")
    raise SystemExit(f"release evidence contains duplicate signed tags for {artifact}")


def validate_release_evidence(evidence: dict[str, Any]) -> None:
    release = evidence["release"]
    pinned_aac = evidence["pinned_aac"]
    dvaac_tag = signed_tag_evidence(evidence, "damn-vulnerable-agent-asset-corpus")
    aac_tag = signed_tag_evidence(evidence, "agent-assurance-case")

    require_equal(
        "release evidence filename tag",
        str(release["tag"]),
        RELEASE_EVIDENCE_PATH.stem.removeprefix("release-evidence."),
    )
    require_equal("DVAAC signed tag", str(dvaac_tag["tag"]), str(release["tag"]))
    require_equal(
        "DVAAC signed tag object",
        str(dvaac_tag["expected_object"]),
        str(release["release_commit"]),
    )
    require_equal("pinned AAC signed tag", str(aac_tag["tag"]), str(pinned_aac["tag"]))
    require_equal(
        "pinned AAC signed tag object",
        str(aac_tag["expected_object"]),
        str(pinned_aac["commit"]),
    )

    asset_names = [asset["name"] for asset in evidence["release_assets"]]
    if len(asset_names) != len(set(asset_names)):
        raise SystemExit("release evidence contains duplicate release asset names")
    release_version = str(release["tag"]).removeprefix("v")
    expected_asset_names = {
        "RELEASE-MANIFEST.json",
        "SHA256SUMS",
        f"signed-aac-v{release_version}.tar.gz",
        f"signed-aac-v{release_version}.tar.gz.sha256",
    }
    if set(asset_names) != expected_asset_names:
        raise SystemExit(
            "release evidence asset set mismatch: "
            f"{sorted(asset_names)} != {sorted(expected_asset_names)}"
        )


def write_allowed_signers(
    workdir: Path,
    *,
    signed_tags: list[dict[str, Any]],
) -> Path:
    path = workdir / "allowed_signers"
    signers = {
        f"{item['signer']} {item['public_key']} aac-release-signing"
        for item in signed_tags
    }
    path.write_text("\n".join(sorted(signers)) + "\n", encoding="utf-8")
    return path


def clone_release(url: str, tag: str, destination: Path) -> None:
    run(["git", "clone", "--branch", tag, "--depth", "1", url, str(destination)])


def verify_release_checkout(
    repo: Path,
    *,
    tag: str,
    expected_commit: str,
    allowed_signers: Path,
) -> None:
    head = output(["git", "rev-parse", "HEAD"], cwd=repo)
    if head != expected_commit:
        raise SystemExit(f"{tag} checkout is {head}, expected {expected_commit}")

    tag_commit = output(["git", "rev-list", "-n", "1", tag], cwd=repo)
    if tag_commit != expected_commit:
        raise SystemExit(f"{tag} points to {tag_commit}, expected {expected_commit}")

    run(
        [
            "git",
            "-c",
            f"gpg.ssh.allowedSignersFile={allowed_signers}",
            "tag",
            "-v",
            tag,
        ],
        cwd=repo,
    )


def create_python_env(repo: Path, env_dir: Path) -> Path:
    venv.EnvBuilder(with_pip=True).create(env_dir)
    python = env_dir / "bin" / "python"
    run([str(python), "-m", "pip", "install", "--upgrade", "pip"], cwd=repo)
    run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "-r",
            "runner/requirements.txt",
            "-r",
            "runner/requirements-dev.txt",
        ],
        cwd=repo,
    )
    return python


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_release_assets(
    destination: Path,
    *,
    asset_base_url: str,
    asset_digests: dict[str, str],
) -> None:
    destination.mkdir(parents=True)
    for name, expected_digest in asset_digests.items():
        url = f"{asset_base_url}/{name}"
        target = destination / name
        print(f"download {url}", flush=True)
        with urllib.request.urlopen(url, timeout=30) as response:
            target.write_bytes(response.read())
        actual_digest = sha256(target)
        if actual_digest != expected_digest:
            raise SystemExit(
                f"{name} sha256 mismatch: {actual_digest} != {expected_digest}"
            )


def verify_archive_sidecar(assets_dir: Path) -> None:
    sidecar = assets_dir / "signed-aac-v0.1.4.tar.gz.sha256"
    archive = assets_dir / "signed-aac-v0.1.4.tar.gz"
    expected_digest, filename = sidecar.read_text(encoding="utf-8").split()
    if filename != archive.name:
        raise SystemExit(f"sidecar names {filename}, expected {archive.name}")
    actual_digest = sha256(archive)
    if actual_digest != expected_digest:
        raise SystemExit(
            f"{archive.name} sidecar mismatch: {actual_digest} != {expected_digest}"
        )


def safe_extract_tar(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True)
    destination_root = destination.resolve()
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar.getmembers():
            target = (destination / member.name).resolve()
            if not target.is_relative_to(destination_root):
                raise SystemExit(f"unsafe tar member path: {member.name}")
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile():
                raise SystemExit(f"unsupported tar member type: {member.name}")
            target.parent.mkdir(parents=True, exist_ok=True)
            source = tar.extractfile(member)
            if source is None:
                raise SystemExit(f"could not read tar member: {member.name}")
            with source, target.open("wb") as handle:
                shutil.copyfileobj(source, handle)


def verify_inner_sha256s(extract_dir: Path) -> None:
    signed_dir = extract_dir / "signed-aac"
    sums_path = signed_dir / "SHA256SUMS"
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected_digest, relative_path = line.split(maxsplit=1)
        target = signed_dir / relative_path
        if not target.is_file():
            raise SystemExit(f"SHA256SUMS target missing: {relative_path}")
        actual_digest = sha256(target)
        if actual_digest != expected_digest:
            raise SystemExit(
                f"{relative_path} sha256 mismatch: "
                f"{actual_digest} != {expected_digest}"
            )


def block_pytest_discoverable_fixture_names(repo: Path) -> None:
    bad_names = []
    for path in (repo / "fixtures").rglob("*"):
        if not path.is_file():
            continue
        name = path.name
        if name == "conftest.py" or name.startswith("test_") or name.endswith("_test.py"):
            bad_names.append(str(path.relative_to(repo)))
    if bad_names:
        raise SystemExit(
            "pytest-discoverable fixture payload names found:\n"
            + "\n".join(sorted(bad_names))
        )


def main() -> int:
    require_tool("git")
    evidence = load_release_evidence()
    validate_release_evidence(evidence)
    release = evidence["release"]
    pinned_aac = evidence["pinned_aac"]
    dvaac_tag = signed_tag_evidence(evidence, "damn-vulnerable-agent-asset-corpus")
    aac_tag = signed_tag_evidence(evidence, "agent-assurance-case")
    asset_digests = {
        asset["name"]: asset["github_asset_digest"].removeprefix("sha256:")
        for asset in evidence["release_assets"]
    }
    asset_base_url = f"{release['repository']}/releases/download/{release['tag']}"

    with tempfile.TemporaryDirectory(prefix="dvaac-release-fingerprint-") as tmp:
        tmp_path = Path(tmp)
        allowed_signers = write_allowed_signers(
            tmp_path,
            signed_tags=evidence["signed_tags"],
        )
        aac_repo = tmp_path / "agent-assurance-case"
        dvaac_repo = tmp_path / "damn-vulnerable-agent-asset-corpus"

        clone_release(str(pinned_aac["repository"]), str(pinned_aac["tag"]), aac_repo)
        verify_release_checkout(
            aac_repo,
            tag=str(aac_tag["tag"]),
            expected_commit=str(aac_tag["expected_object"]),
            allowed_signers=allowed_signers,
        )

        clone_release(str(release["repository"]), str(release["tag"]), dvaac_repo)
        verify_release_checkout(
            dvaac_repo,
            tag=str(dvaac_tag["tag"]),
            expected_commit=str(dvaac_tag["expected_object"]),
            allowed_signers=allowed_signers,
        )

        python = create_python_env(dvaac_repo, tmp_path / "fingerprint-venv")
        env = {
            "AAC_VERIFIER_PATH": str(aac_repo / "verifier" / "verify.py"),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_NO_CACHE_DIR": "1",
        }

        run([str(python), "runner/verify_fixtures.py"], cwd=dvaac_repo, env=env)
        if (dvaac_repo / "tests").is_dir():
            run(
                [str(python), "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"],
                cwd=dvaac_repo,
                env=env,
            )
        run(
            [str(python), "-m", "pytest", "--collect-only", "-q"],
            cwd=dvaac_repo,
            env=env,
            allowed_exit_codes={0, 5},
        )
        block_pytest_discoverable_fixture_names(dvaac_repo)

        assets_dir = tmp_path / "release-assets"
        download_release_assets(
            assets_dir,
            asset_base_url=asset_base_url,
            asset_digests=asset_digests,
        )
        verify_archive_sidecar(assets_dir)
        extract_dir = tmp_path / "signed-aac-extract"
        safe_extract_tar(assets_dir / "signed-aac-v0.1.4.tar.gz", extract_dir)
        verify_inner_sha256s(extract_dir)

    print("DVAAC release fingerprint: valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
