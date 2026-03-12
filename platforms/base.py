from __future__ import annotations

import requests


class AuthenticationError(RuntimeError):
    """Raised when platform authentication fails."""


class BasePlatformClient:
    platform_label = "Platform"

    def __init__(self, config: dict):
        self.config = config

    def request(self, url: str, headers: dict, method: str = "GET", json_data: dict | None = None) -> requests.Response:
        try:
            response = requests.request(method=method, url=url, headers=headers, json=json_data, timeout=30)
        except requests.RequestException as exc:
            raise RuntimeError(f"Network error while requesting {url}: {exc}") from exc

        if response.status_code in (401, 403):
            raise AuthenticationError(
                f"{self.platform_label} authentication failed with status {response.status_code}. Refresh your credentials."
            )

        return response
