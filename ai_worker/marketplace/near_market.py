from __future__ import annotations

import hashlib
import time
from typing import Any

import requests

from marketplace.base import Job


class NearMarketError(RuntimeError):
    def __init__(self, status_code: int, message: str, payload: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class NearMarketClient:
    """Client for the NEAR AI Agent Market /v1 API.

    API credentials are supplied at runtime through MARKET_API_KEY.
    No credential is stored in source code.
    """

    def __init__(self, base_url: str, api_key: str = "", timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key.strip()
        self.timeout = timeout
        self.session = requests.Session()

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "AI-Worker/1.2",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _request(self, method: str, path: str, *, params=None, payload=None):
        url = f"{self.base_url}{path}"
        response = self.session.request(
            method,
            url,
            headers=self._headers(),
            params=params,
            json=payload,
            timeout=self.timeout,
        )
        try:
            data = response.json()
        except ValueError:
            data = response.text

        if not response.ok:
            detail = data.get("message") if isinstance(data, dict) else str(data)
            raise NearMarketError(response.status_code, detail or response.reason, data)
        return data

    @staticmethod
    def _rows(data: Any, *keys: str) -> list[dict[str, Any]]:
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        if isinstance(data, dict):
            for key in keys:
                value = data.get(key)
                if isinstance(value, list):
                    return [x for x in value if isinstance(x, dict)]
        return []

    @staticmethod
    def _num(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _int(value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def me(self) -> dict[str, Any]:
        return self._request("GET", "/v1/agents/me")

    def list_open_jobs(self, limit: int = 100, *, tags: str | None = None, search: str | None = None) -> list[Job]:
        params: dict[str, Any] = {"status": "open", "limit": min(max(1, limit), 300)}
        if tags:
            params["tags"] = tags
        if search:
            params["search"] = search

        data = self._request("GET", "/v1/jobs", params=params)
        rows = self._rows(data, "jobs", "assignments", "results")

        jobs: list[Job] = []
        for x in rows:
            budget = x.get("budget_amount", x.get("reward", x.get("budget", 0)))
            currency = x.get("budget_currency", x.get("reward_currency", x.get("currency", "NEAR")))
            deadline_hours = x.get("deadline_hours")
            if deadline_hours is None:
                eta = x.get("estimated_completion_time")
                if isinstance(eta, (int, float)):
                    deadline_hours = float(eta) / 3600

            jobs.append(
                Job(
                    job_id=str(x.get("job_id") or x.get("id") or ""),
                    title=str(x.get("title") or ""),
                    description=str(x.get("description") or x.get("task_spec") or ""),
                    reward=self._num(budget),
                    reward_currency=str(currency or "NEAR"),
                    tags={str(t).lower() for t in (x.get("tags") or [])},
                    bids=self._int(x.get("bid_count", x.get("bids_count", x.get("bids", 0)))),
                    deadline_hours=self._num(deadline_hours, 0.0) if deadline_hours is not None else None,
                    raw=x,
                )
            )
        return [j for j in jobs if j.job_id]

    def get_job(self, job_id: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/jobs/{job_id}")

    def list_my_bids(self, limit: int = 100) -> list[dict[str, Any]]:
        data = self._request("GET", "/v1/agents/me/bids", params={"limit": min(max(1, limit), 300)})
        return self._rows(data, "bids", "results")

    def place_bid(self, job_id: str, amount: float, proposal: str, eta_seconds: int) -> dict[str, Any]:
        payload = {
            "amount": str(amount),
            "proposal": proposal,
            "eta_seconds": int(eta_seconds),
        }
        return self._request("POST", f"/v1/jobs/{job_id}/bids", payload=payload)

    def submit_work(self, job_id: str, deliverable: str, artifact_bytes: bytes) -> dict[str, Any]:
        digest = hashlib.sha256(artifact_bytes).hexdigest()
        payload = {
            "deliverable": deliverable,
            "deliverable_hash": f"sha256:{digest}",
        }
        return self._request("POST", f"/v1/jobs/{job_id}/submit", payload=payload)

    def list_balance(self) -> dict[str, Any]:
        return self._request("GET", "/v1/wallet/balance")

    def withdraw(self, to_account_id: str, amount: str, idempotency_key: str | None = None) -> dict[str, Any]:
        if not idempotency_key:
            idempotency_key = f"ai-worker-{int(time.time())}"
        payload = {
            "to_account_id": to_account_id,
            "amount": str(amount),
            "idempotency_key": idempotency_key,
        }
        return self._request("POST", "/v1/wallet/withdraw", payload=payload)


def sha256_bytes(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"
