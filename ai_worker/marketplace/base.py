from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class Job:
    job_id: str
    title: str
    description: str
    reward: float
    reward_currency: str
    tags: set[str] = field(default_factory=set)
    bids: int = 0
    deadline_hours: float | None = None
    raw: dict[str, Any] = field(default_factory=dict)
