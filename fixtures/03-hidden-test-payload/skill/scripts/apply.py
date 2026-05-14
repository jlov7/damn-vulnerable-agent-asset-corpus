"""Apply a configuration file to a target directory.

This file is the declared executable surface of the apply-config skill.
A static-declared scanner inspecting this file will find nothing notable:
a small, well-mannered config applier.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    return json.loads(text)


def apply_config(config_path: str, target_dir: str) -> list[str]:
    config = load_config(Path(config_path))
    target = Path(target_dir)
    if not target.exists() or not target.is_dir():
        raise ValueError(f"target directory not found: {target}")
    target_root = target.resolve()
    modified: list[str] = []
    for filename, contents in (config.get("files") or {}).items():
        dest = (target_root / filename).resolve()
        if dest != target_root and target_root not in dest.parents:
            raise ValueError(f"config entry escapes target directory: {filename}")
        dest.write_text(contents, encoding="utf-8")
        modified.append(str(dest))
    return modified


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("usage: apply.py <config.json> <target_dir>", file=sys.stderr)
        sys.exit(2)
    for path in apply_config(sys.argv[1], sys.argv[2]):
        print(path)
