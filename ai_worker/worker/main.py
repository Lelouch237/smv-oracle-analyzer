from __future__ import annotations

import argparse
import json
import logging
import time

from marketplace.base import Job
from marketplace.near_market import NearMarketClient, NearMarketError
from worker.config import SETTINGS
from worker.scoring import score_job

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


def sample_jobs() -> list[Job]:
    return [
        Job(
            "sample-001",
            "Write Python script to normalize CSV data",
            "Create a small Python utility that reads a CSV and cleans headers. Include README.",
            5,
            "NEAR",
            {"python", "data"},
            1,
            24,
        ),
        Job(
            "sample-002",
            "Research two API providers",
            "Produce a short comparison with public sources.",
            1,
            "NEAR",
            {"research", "api"},
            8,
            8,
        ),
        Job(
            "sample-003",
            "Vague task",
            "",
            0.5,
            "NEAR",
            {"other"},
            20,
            1,
        ),
    ]


def rank(jobs: list[Job]) -> list[dict]:
    out = []
    for job in jobs:
        o = score_job(job, SETTINGS)
        out.append(
            {
                "job_id": job.job_id,
                "title": job.title,
                "score": o.score,
                "reward": job.reward,
                "currency": job.reward_currency,
                "bids": job.bids,
                "deadline_hours": job.deadline_hours,
                "reasons": o.reasons,
            }
        )
    return sorted(out, key=lambda x: x["score"], reverse=True)


def run_sample() -> None:
    ranked = rank(sample_jobs())
    print(json.dumps(ranked, ensure_ascii=False, indent=2))
    logging.info(
        "Mode sécurisé: DRY_RUN=%s ENABLE_AUTONOMY=%s",
        SETTINGS.dry_run,
        SETTINGS.enable_autonomy,
    )


def run_scan() -> int:
    if not SETTINGS.market_api_key:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "reason": "Missing market API key",
                    "next_step": (
                        "Register an agent on market.near.ai and store the returned "
                        "key as MARKET_API_KEY (or AGENT_MARKET_API_KEY)."
                    ),
                    "dry_run": SETTINGS.dry_run,
                    "autonomy": SETTINGS.enable_autonomy,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    client = NearMarketClient(SETTINGS.market_base_url, SETTINGS.market_api_key)

    try:
        me = client.me()
        jobs = client.list_open_jobs(SETTINGS.open_jobs_limit)
    except NearMarketError as exc:
        logging.error("NEAR Market API error %s: %s", exc.status_code, str(exc))
        print(
            json.dumps(
                {
                    "status": "api_error",
                    "http_status": exc.status_code,
                    "message": str(exc),
                    "hint": "Check the API key, market availability and API version.",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except Exception as exc:
        logging.exception("NEAR Market scan failed")
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False, indent=2))
        return 0

    ranked = rank(jobs)
    print(
        json.dumps(
            {
                "agent": me,
                "jobs_found": len(jobs),
                "top_opportunities": ranked[:20],
                "actions_taken": [],
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    if SETTINGS.dry_run or not SETTINGS.enable_autonomy:
        logging.info("DRY RUN / AUTONOMY OFF: aucun bid envoyé.")
        return 0

    try:
        my_bids = client.list_my_bids(300)
        already_bid = {
            str(x.get("job_id") or x.get("jobId") or "")
            for x in my_bids
            if isinstance(x, dict)
        }
    except Exception:
        already_bid = set()

    selected = [
        x
        for x in ranked
        if x["score"] >= SETTINGS.min_score
        and x["job_id"] not in already_bid
        and x["reward"] > 0
    ][: SETTINGS.max_bids_per_run]

    for item in selected:
        eta_hours = SETTINGS.default_eta_hours
        if item.get("deadline_hours"):
            eta_hours = min(
                eta_hours,
                max(1.0, float(item["deadline_hours"]) * 0.5),
            )

        proposal = (
            f"I can deliver a verifiable result for '{item['title']}'. "
            "I will follow the exact task requirements, validate the deliverable, "
            "and provide clear verification details."
        )

        try:
            response = client.place_bid(
                item["job_id"],
                item["reward"],
                proposal,
                int(eta_hours * 3600),
            )
            logging.info("Bid sent for %s: %s", item["job_id"], response)
        except Exception as exc:
            logging.error("Bid failed for %s: %s", item["job_id"], exc)

    return len(selected)


def main() -> None:
    parser = argparse.ArgumentParser(description="AI WORKER for NEAR AI Agent Market")
    parser.add_argument("--sample", action="store_true")
    parser.add_argument("--scan", action="store_true")
    parser.add_argument("--loop", action="store_true")
    args = parser.parse_args()

    if args.sample or not (args.scan or args.loop):
        run_sample()
        return

    if args.loop:
        while True:
            run_scan()
            time.sleep(max(60, SETTINGS.poll_seconds))
    else:
        run_scan()


if __name__ == "__main__":
    main()
