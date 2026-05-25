#!/usr/bin/env python3
# pyright: reportMissingModuleSource=false
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    import atheris
except ImportError:  # pragma: no cover - normal unit-test smoke path.
    atheris = None

from runner import validate_scorecard  # noqa: E402


def TestOneInput(data: bytes) -> None:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return

    with tempfile.TemporaryDirectory() as tmp_dir:
        scorecard_path = Path(tmp_dir) / "scorecard.json"
        scorecard_path.write_text(text, encoding="utf-8")
        validate_scorecard.validate_scorecard(scorecard_path)


def main() -> None:
    if atheris is None:
        raise RuntimeError("atheris is required for coverage-guided fuzzing")
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
