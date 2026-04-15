import csv
import json
import os
from pathlib import Path
from typing import Any


class OutputError(RuntimeError):
    pass


def flatten_dict(entry: dict[str, Any], prefix: str = "", sep: str = "_") -> dict[str, str]:
    flat: dict[str, str] = {}
    for key, value in entry.items():
        full_key = f"{prefix}{sep}{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(flatten_dict(value, prefix=full_key, sep=sep))
        elif isinstance(value, list):
            flat[full_key] = ", ".join(str(v) for v in value)
        else:
            flat[full_key] = str(value) if value is not None else ""
    return flat


def ensure_writable(output_file: Path) -> Path:
    path = output_file.resolve()
    if not path.parent.exists():
        raise OutputError(f"Directory does not exist: {path.parent}")
    if not os.access(path.parent, os.W_OK):
        raise OutputError(f"Directory is not writable: {path.parent}")
    if path.exists() and not os.access(path, os.W_OK):
        raise OutputError(f"File is not writable: {path}")
    return path


def write_output(results: list[dict[str, Any]], output_file: Path | None) -> None:
    if output_file is None:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    output_file = ensure_writable(output_file)

    if output_file.suffix == ".json":
        output_file.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    elif output_file.suffix == ".csv":
        if not results:
            output_file.write_text("", encoding="utf-8")
            return
        rows = [flatten_dict(r) for r in results]
        with output_file.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
