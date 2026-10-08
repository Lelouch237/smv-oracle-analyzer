from __future__ import annotations

from typing import Any
import requests

class ClustlyClient:
    """Read/execute adapter for Clustly's agent API.

    The API key must come from the operator console and is never committed.
    """

    def __init__(self, api_key: str, base_url: str = "https://www.clustly.ai"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.s = requests.Session()

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-agent-key": self.api_key,
            "User-Agent": "AI-Worker/1.1",
        }

    def list_jobs(self) -> list[dict[str, Any]]:
        r = self.s.get(f"{self.base_url}/api/v1/agent/orders",
                       headers=self._headers(), params={"status": "enrolled"},
                       timeout=30)
        r.raise_for_status()
        data = r.json()
        return data.get("orders", data if isinstance(data, list) else [])

    def identity_status(self) -> dict[str, Any]:
        r = self.s.get(f"{self.base_url}/api/v1/agent/identity/status",
                       headers=self._headers(), timeout=30)
        r.raise_for_status()
        return r.json()

    def accept(self, order_id: str) -> dict[str, Any]:
        r = self.s.post(f"{self.base_url}/api/v1/orders/{order_id}/accept",
                        headers=self._headers(), timeout=30)
        r.raise_for_status()
        return r.json()

    def submit(self, order_id: str, content: str) -> dict[str, Any]:
        r = self.s.post(f"{self.base_url}/api/v1/orders/{order_id}/submit",
                        headers=self._headers(),
                        json={"content": content},
                        timeout=30)
        r.raise_for_status()
        return r.json()
