from __future__ import annotations

from pathlib import Path


def read_lines_resilient(file_path: str) -> list[str]:
    """Read text lines while tolerating mixed encodings and broken bytes."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            with path.open("r", encoding=encoding) as file:
                return file.readlines()
        except UnicodeDecodeError:
            continue

    # Final fallback: never fail on decode.
    with path.open("r", encoding="utf-8", errors="replace") as file:
        return file.readlines()
