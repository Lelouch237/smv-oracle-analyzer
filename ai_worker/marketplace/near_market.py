from __future__ import annotations
import requests
from marketplace.base import Job

class NearMarketClient:
    def __init__(self, base_url: str, api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()

    def _headers(self):
        h = {"Accept":"application/json","User-Agent":"AI-Worker/1.0"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def _get(self, path: str, **params):
        r = self.session.get(f"{self.base_url}{path}", headers=self._headers(), params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, payload):
        r = self.session.post(f"{self.base_url}{path}", headers={**self._headers(),"Content-Type":"application/json"}, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()

    def list_open_jobs(self, limit: int = 100):
        data = self._get("/v1/jobs", status="open", limit=min(limit,100))
        rows = data.get("jobs", data if isinstance(data,list) else [])
        jobs = []
        for x in rows:
            jobs.append(Job(
                job_id=str(x.get("job_id") or x.get("id")),
                title=str(x.get("title","")),
                description=str(x.get("description") or x.get("task_spec") or ""),
                reward=float(x.get("budget_amount") or x.get("reward") or x.get("budget") or 0),
                reward_currency=str(x.get("currency") or "NEAR"),
                tags={str(t).lower() for t in (x.get("tags") or [])},
                bids=int(x.get("bid_count") or x.get("bids_count") or x.get("bids") or 0),
                deadline_hours=(float(x["deadline_hours"]) if x.get("deadline_hours") is not None else None),
                raw=x,
            ))
        return jobs

    def place_bid(self, job_id: str, amount: float, message: str):
        return self._post(f"/v1/jobs/{job_id}/bids", {"amount":amount,"proposal":message,"message":message})
