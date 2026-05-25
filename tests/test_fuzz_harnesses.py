from __future__ import annotations

import importlib.util
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def _load_harness(name: str):
    spec = importlib.util.spec_from_file_location(name, BASE / "fuzz" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dvaac_scorecard_fuzzer_seed_inputs_do_not_crash() -> None:
    harness = _load_harness("dvaac_scorecard_fuzzer")

    for seed in (
        b"",
        b"{",
        b'{"scanner":{"name":""}}',
        b'{"per_fixture_results":[{"fixture_id":"01-clean-declared-skill"}]}',
    ):
        harness.TestOneInput(seed)
