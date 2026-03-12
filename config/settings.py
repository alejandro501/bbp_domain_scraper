from __future__ import annotations

import os
from pathlib import Path


def load_dotenv(dotenv_path: str = ".env") -> dict[str, str]:
    """Load key-value pairs from a local .env file into process env and return them."""
    path = Path(dotenv_path)
    loaded: dict[str, str] = {}

    if not path.exists():
        return loaded

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ[key] = value
        loaded[key] = value

    return loaded


def load_runtime_config() -> dict:
    """Build runtime config from environment variables only."""
    return {
        "credentials": {
            "bc": {"token": os.getenv("BC_TOKEN") or os.getenv("BC_COOKIE")},
            "h1": {"token": os.getenv("H1_TOKEN") or os.getenv("H1_COOKIE")},
            "ywh": {"token": os.getenv("YWH_TOKEN") or os.getenv("YWH_PAT")},
        },
        "webhooks": {
            "discord": {"general_vps_output": os.getenv("DISCORD_GENERAL_VPS_OUTPUT_WEBHOOK")},
        },
    }
