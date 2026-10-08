from __future__ import annotations
import re
from dataclasses import dataclass
from marketplace.base import Job
from worker.config import Settings

@dataclass(frozen=True)
class Opportunity:
    job: Job
    score: float
    reasons: list[str]

def score_job(job: Job, settings: Settings) -> Opportunity:
    score = 0.0
    reasons = []
    text = (job.title + " " + job.description).lower()
    tags = {t.lower() for t in job.tags}

    matches = tags & settings.allowed_tags
    if matches:
        score += min(25, 8 * len(matches))
        reasons.append("compatible tags: " + ", ".join(sorted(matches)))

    keywords = {k for k in settings.required_keywords if re.search(rf"\b{re.escape(k)}\b", text)}
    if keywords:
        score += min(25, 5 * len(keywords))
        reasons.append("keywords: " + ", ".join(sorted(keywords)))

    if job.reward >= settings.min_reward_near:
        score += 20
        reasons.append("reward above minimum")

    if job.bids == 0:
        score += 15
        reasons.append("no visible competition")
    elif job.bids <= 3:
        score += 10
        reasons.append("low competition")
    elif job.bids <= 10:
        score += 5
        reasons.append("moderate competition")

    if job.deadline_hours is not None:
        if job.deadline_hours < 2:
            score -= 20
            reasons.append("deadline too close")
        elif job.deadline_hours >= 12:
            score += 10
            reasons.append("reasonable deadline")

    estimated_hours = max(0.5, (job.deadline_hours / 24) if job.deadline_hours else 4)
    estimated_usd = job.reward * settings.usd_per_near_estimate
    if estimated_usd / estimated_hours < settings.min_hourly_target_usd:
        score -= 15
        reasons.append("estimated hourly ROI below target")

    if not job.title.strip() or not job.description.strip():
        score -= 30
        reasons.append("insufficient description")

    return Opportunity(job, round(max(0, min(100, score)), 2), reasons)
