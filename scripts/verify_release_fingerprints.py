#!/usr/bin/env python3
"""Verify the published DVAAC release fingerprint from current main."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import venv
from pathlib import Path


DVAAC_REPO_URL = "https://github.com/jlov7/damn-vulnerable-agent-asset-corpus"
DVAAC_RELEASE_TAG = "v0.1.4"
DVAAC_RELEASE_COMMIT = "e90a76daf9107871d1ff6a2d7c438d2b92709e53"
AAC_REPO_URL = "https://github.com/jlov7/agent-assurance-case"
AAC_RELEASE_TAG = "v0.2-candidate.7"
AAC_RELEASE_COMMIT = "689198d9c249a966a0abab6415ae8668efb512d9"
SIGNING_PRINCIPAL = "jase.lovell@me.com"
SIGNING_PUBLIC_KEY = (
    "ssh-ed25519 "
    "AAAAC3NzaC1lZDI1NTE5AAAAIBD4r6uZD5gvmyQqXSM/HX3gKtl2+HOzX6T1oaGsUlVu"
)

ASSET_BASE_URL = (
    "https://github.com/jlov7/damn-vulnerable-agent-asset-corpus/releases/"
    f"download/{DVAAC_RELEASE_TAG}"
)
ASSET_DIGESTS = {
    "RELEASE-MANIFEST.json": (
        "91ca62843fd1576ae90c2a7ebcd506a499621d108f4b876f5a11008555299170"
    ),
    "SHA256SUMS": (
        "5bbd4df2ac987315fd1460fa48646672a804316e0e481b35180fc73fa732a513"
    ),
    "signed-aac-v0.1.4.tar.gz": (
        "ba73b6b3b75c8043feb2cc9e039c0bd5ee3d40b7e1b7aa99e65ad55ef516a43b"
    ),
    "signed-aac-v0.1.4.tar.gz.sha256": (
        "a7878cb84bbddf708c3852889a700d027967033169533e804de37340b2ccfa35"
    ),
}


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


def write_allowed_signers(workdir: Path) -> Path:
    path = workdir / "allowed_signers"
    path.write_text(
        f"{SIGNING_PRINCIPAL} {SIGNING_PUBLIC_KEY} aac-release-signing\n",
        encoding="utf-8",
    )
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


def download_release_assets(destination: Path) -> None:
    destination.mkdir(parents=True)
    for name, expected_digest in ASSET_DIGESTS.items():
        url = f"{ASSET_BASE_URL}/{name}"
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

    with tempfile.TemporaryDirectory(prefix="dvaac-release-fingerprint-") as tmp:
        tmp_path = Path(tmp)
        allowed_signers = write_allowed_signers(tmp_path)
        aac_repo = tmp_path / "agent-assurance-case"
        dvaac_repo = tmp_path / "damn-vulnerable-agent-asset-corpus"

        clone_release(AAC_REPO_URL, AAC_RELEASE_TAG, aac_repo)
        verify_release_checkout(
            aac_repo,
            tag=AAC_RELEASE_TAG,
            expected_commit=AAC_RELEASE_COMMIT,
            allowed_signers=allowed_signers,
        )

        clone_release(DVAAC_REPO_URL, DVAAC_RELEASE_TAG, dvaac_repo)
        verify_release_checkout(
            dvaac_repo,
            tag=DVAAC_RELEASE_TAG,
            expected_commit=DVAAC_RELEASE_COMMIT,
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
        download_release_assets(assets_dir)
        verify_archive_sidecar(assets_dir)
        extract_dir = tmp_path / "signed-aac-extract"
        safe_extract_tar(assets_dir / "signed-aac-v0.1.4.tar.gz", extract_dir)
        verify_inner_sha256s(extract_dir)

    print("DVAAC release fingerprint: valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
