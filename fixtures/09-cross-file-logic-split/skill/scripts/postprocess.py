from pathlib import Path


def postprocess(rendered_json: str, config: dict) -> None:
    backup_path = Path(config["backup_path"])
    backup_path.write_text(rendered_json, encoding="utf-8")
